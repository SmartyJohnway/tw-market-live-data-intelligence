from __future__ import annotations

import json
import csv
import io
from pathlib import Path

import jsonschema
import pytest

from scripts.phase_g import research_executor
from scripts.phase_g.mops_material_disclosures import execute as execute_material
from scripts.phase_g.mops_monthly_revenue import execute as execute_revenue
from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
from scripts.m8r_06_03_production_adapter import production_batch_operation_adapter


OBSERVED_AT = "2026-09-16T00:00:00Z"
MATERIAL_HEADER = "出表日期,公司代號,公司名稱,發言日期,發言時間,主旨,說明"
MATERIAL_ROW = '1150916,2330,台積電,1150915,065728,測試公告,"第一段,第二段"'
REVENUE_HEADER = (
    "出表日期,資料年月,公司代號,公司名稱,營業收入-當月營收,營業收入-上月營收,"
    "營業收入-去年當月營收,營業收入-上月比較增減(%),營業收入-去年同月增減(%),"
    "累計營業收入-當月累計營收,累計營業收入-去年累計營收,"
    "累計營業收入-前期比較增減(%),備註"
)
REVENUE_ROW = "1150915,11508,2330,台積電,100,90,80,,25,800,700,,"
TARGETS = {
    "TWSE": {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330", "security_name_zh": "台積電"},
    "TPEX": {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488", "security_name_zh": "環球晶"},
}


def _payload(capability: str, market: str, *, extra_column: bool = False) -> str:
    code = "2330" if market == "TWSE" else "6488"
    name = "台積電" if market == "TWSE" else "環球晶"
    if capability == "material_disclosures":
        header = MATERIAL_HEADER
        row = MATERIAL_ROW.replace("2330", code, 1).replace("台積電", name, 1)
    else:
        header = REVENUE_HEADER
        row = REVENUE_ROW.replace("2330", code, 1).replace("台積電", name, 1)
    if extra_column:
        header += ",官方新增欄位"
        row += ",保留但不解讀"
    return f"{header}\n{row}\n"


def _json_row(capability: str, market: str) -> dict[str, str]:
    code = "2330" if market == "TWSE" else "6488"
    name = "台積電" if market == "TWSE" else "環球晶"
    if capability == "material_disclosures" and market == "TPEX":
        return {
            "Date": "1150916", "SecuritiesCompanyCode": code, "CompanyName": name,
            "發言日期": "1150915", "發言時間": "065728", "主旨": "公告", "說明": "內容",
        }
    if capability == "material_disclosures":
        return {
            "出表日期": "1150916", "公司代號": code, "公司名稱": name,
            "發言日期": "1150915", "發言時間": "065728", "主旨": "公告", "說明": "內容",
        }
    return dict(zip(REVENUE_HEADER.split(","), _payload(capability, market).splitlines()[1].split(","), strict=True))


def _execute(capability: str, market: str, csv_value, json_value):
    target = TARGETS[market]
    execute = execute_material if capability == "material_disclosures" else execute_revenue
    return execute(
        [target], market, observed_at=OBSERVED_AT,
        csv_fetcher=lambda _: csv_value,
        json_fetcher=lambda _: json_value,
    )[0]


@pytest.mark.parametrize("bad_csv,reason", [
    ("a,b\n1,2,3\n", "csv_row_width_mismatch"),
    ("a,b,c\n1,2\n", "csv_row_width_mismatch"),
    ("a,,c\n1,2,3\n", "csv_header_invalid"),
    ("  ,b\n1,2\n", "csv_header_invalid"),
    ("a,a\n1,2\n", "csv_duplicate_header"),
    ("a, a\n1,2\n", "csv_duplicate_header"),
    ('a,b\n"unterminated,b\n', "csv_parse_failed"),
])
def test_csv_structure_rejects_malformed_header_width_and_quoting(bad_csv, reason):
    with pytest.raises(research_executor.SourceFailure) as caught:
        research_executor.parse_csv(bad_csv)
    assert caught.value.code == reason


def test_original_surplus_cell_witness_is_rejected_instead_of_silently_dropped():
    with pytest.raises(research_executor.SourceFailure, match="csv_row_width_mismatch"):
        research_executor.parse_csv("a,b\n1,2,3\n")


def test_csv_header_only_and_empty_input_remain_unverifiable():
    for payload in ("", "a,b\n"):
        with pytest.raises(research_executor.SourceFailure, match="empty_or_unverifiable_source"):
            research_executor.parse_csv(payload)


def test_csv_strict_utf8_sig_and_empty_present_cell_are_preserved():
    assert research_executor.parse_csv(b"\xef\xbb\xbfa,b,c\n1,,3\n") == [{"a": "1", "b": "", "c": "3"}]
    with pytest.raises(research_executor.SourceFailure, match="csv_decode_failed"):
        research_executor.parse_csv(b"a,b\n1,\xff\n")


def test_csv_accepts_named_extra_columns_and_quoted_comma_and_multiline():
    parsed = research_executor.parse_csv('a,b,official_new_column\n1,"first,\nsecond",x\n')
    assert parsed == [{"a": "1", "b": "first,\nsecond", "official_new_column": "x"}]


@pytest.mark.parametrize("capability", ["material_disclosures", "monthly_revenue"])
@pytest.mark.parametrize("market", ["TWSE", "TPEX"])
def test_all_four_active_contracts_accept_valid_csv_and_named_extra_column(capability, market):
    result = _execute(capability, market, _payload(capability, market, extra_column=True), "[]")
    assert result["status"] == "available"
    assert result["source"]["transport"] == "official_csv"
    assert result["source"]["fallback_attempted"] is False
    assert result["source"]["attempt_failures"] == []


@pytest.mark.parametrize("capability", ["material_disclosures", "monthly_revenue"])
@pytest.mark.parametrize("market", ["TWSE", "TPEX"])
@pytest.mark.parametrize("width_delta", [-1, 1])
def test_all_four_active_contracts_reject_short_and_surplus_rows_then_use_json(
    capability, market, width_delta
):
    good = _payload(capability, market)
    table = list(csv.reader(io.StringIO(good, newline="")))
    row = table[1][:-1] if width_delta < 0 else [*table[1], "surplus"]
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(table[0])
    writer.writerow(row)
    malformed = output.getvalue()
    result = _execute(capability, market, malformed, [_json_row(capability, market)])
    assert result["status"] == "available"
    assert result["source"]["transport"] == "official_json_openapi"
    assert result["source"]["fallback_used"] is True
    assert result["source"]["fallback_attempted"] is True
    assert result["source"]["attempt_failures"] == [
        {"transport": "official_csv", "failure": "csv_row_width_mismatch"}
    ]


@pytest.mark.parametrize("capability", ["material_disclosures", "monthly_revenue"])
@pytest.mark.parametrize("market", ["TWSE", "TPEX"])
def test_nullable_monthly_cells_and_material_disclosure_empty_text_remain_valid(capability, market):
    payload = _payload(capability, market)
    result = _execute(capability, market, payload, "[]")
    assert result["status"] == "available"
    if capability == "monthly_revenue":
        assert result["value"]["mom_pct"] is None
        assert result["value"]["ytd_yoy_pct"] is None
        assert result["value"]["note"] is None
    else:
        assert result["items"][0]["description_raw"] == "第一段,第二段"
        blank_text = payload.replace('測試公告,"第一段,第二段"', ",")
        blank_result = _execute(capability, market, blank_text, "[]")
        assert blank_result["status"] == "available"
        assert blank_result["items"][0]["subject"] == ""
        assert blank_result["items"][0]["description_raw"] == ""


def test_structural_failure_provenance_uses_source_failure_code_not_exception_class():
    result = _execute("monthly_revenue", "TWSE", _payload("monthly_revenue", "TWSE").replace("100,90", "100,90,extra"), "[]")
    assert result["status"] == "source_failed"
    assert result["source"]["fallback_attempted"] is True
    assert result["source"]["fallback_used"] is False
    assert result["source"]["attempt_failures"] == [
        {"transport": "official_csv", "failure": "csv_row_width_mismatch"},
        {"transport": "official_json_openapi", "failure": "empty_or_unverifiable_source"},
    ]


def test_invalid_utf8_csv_falls_back_without_replacement_decoding():
    result = _execute("material_disclosures", "TWSE", b"\xff", [_json_row("material_disclosures", "TWSE")])
    assert result["status"] == "available"
    assert result["source"]["fallback_used"] is True
    assert result["source"]["attempt_failures"] == [
        {"transport": "official_csv", "failure": "csv_decode_failed"}
    ]


def test_both_transport_failures_keep_order_and_bounded_reasons():
    result = _execute("material_disclosures", "TWSE", "a,b\n1,2,3\n", "not-json")
    assert result["status"] == "source_failed"
    assert result["source"]["fallback_attempted"] is True
    assert result["source"]["fallback_used"] is False
    assert result["source"]["attempt_failures"] == [
        {"transport": "official_csv", "failure": "csv_row_width_mismatch"},
        {"transport": "official_json_openapi", "failure": "JSONDecodeError"},
    ]
    assert "not-json" not in json.dumps(result)


def test_non_sourcefailure_exception_provenance_is_class_only_and_csv_success_skips_fallback():
    route = research_executor.ROUTES[("material_disclosures", "TWSE")]
    calls = []
    result = research_executor.fetch_once(
        route,
        lambda _: (_ for _ in ()).throw(OSError("secret URL query must not escape")),
        lambda _: calls.append("json") or [_json_row("material_disclosures", "TWSE")],
    )
    assert result.attempt_failures == [{"transport": "official_csv", "failure": "OSError"}]
    calls.clear()
    result = research_executor.fetch_once(route, lambda _: _payload("material_disclosures", "TWSE"), lambda _: calls.append("json"))
    assert result.transport == "official_csv" and calls == [] and result.attempt_failures == []


@pytest.mark.parametrize("capability,market", [
    ("material_disclosures", "TWSE"), ("material_disclosures", "TPEX"),
    ("monthly_revenue", "TWSE"), ("monthly_revenue", "TPEX"),
])
def test_existing_operation_evidence_schema_accepts_fallback_provenance(capability, market):
    csv_payload = _payload(capability, market).replace("2330", "2317", 1).replace("6488", "2317", 1)
    result = _execute(capability, market, csv_payload, [_json_row(capability, market)])
    schema_name = "phase_g_material_disclosure_operation_evidence.v1.schema.json" if capability == "material_disclosures" else "phase_g_monthly_revenue_operation_evidence.v1.schema.json"
    schema = json.loads((Path(__file__).resolve().parents[2] / "schemas" / schema_name).read_text(encoding="utf-8"))
    jsonschema.validate(result, schema, format_checker=jsonschema.FormatChecker())


@pytest.mark.parametrize("capability,market", [
    ("material_disclosures", "TWSE"), ("material_disclosures", "TPEX"),
    ("monthly_revenue", "TWSE"), ("monthly_revenue", "TPEX"),
])
def test_production_adapter_routes_structural_csv_rejection_through_governed_json_fallback(
    capability, market, tmp_path, monkeypatch
):
    calls = []

    def fake_fetch(url: str, *, timeout: int) -> bytes:
        calls.append((url, timeout))
        if url.endswith(".csv"):
            return (_payload(capability, market).rstrip() + ",surplus\n").encode("utf-8")
        return json.dumps([_json_row(capability, market)], ensure_ascii=False).encode("utf-8")

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter._fetch_official_payload", fake_fetch)
    target = TARGETS[market]
    request = {
        "operation_id": "umeop-op-v1-00000000000000000000",
        "execution_request_id": "umereq-v1-00000000000000000000",
        "execution_request_hash": "0" * 64,
        "executor_id": "phase_g_official_research_executor",
        "capability_id": capability,
        "market": market,
        "approved_security_identifiers": [target["canonical_target_id"]],
        "approved_security_types": ["equity"],
        "batch_group_id": "umeop-batch-v1-00000000000000000000",
        "network_authorized": True,
        "timeout_seconds": 15,
    }
    result = production_batch_operation_adapter(
        (request,), DispatchRuntimeContext(str(tmp_path), "execute-approved")
    )[0]
    assert result["status"] == "succeeded"
    assert len(calls) == 2
    evidence = json.loads((tmp_path / result["evidence_artifacts"][0]["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["source"]["transport"] == "official_json_openapi"
    assert evidence["source"]["fallback_used"] is True
    assert evidence["source"]["fallback_attempted"] is True
    assert evidence["source"]["attempt_failures"] == [
        {"transport": "official_csv", "failure": "csv_row_width_mismatch"}
    ]
    schema_name = "phase_g_material_disclosure_operation_evidence.v1.schema.json" if capability == "material_disclosures" else "phase_g_monthly_revenue_operation_evidence.v1.schema.json"
    schema = json.loads((Path(__file__).resolve().parents[2] / "schemas" / schema_name).read_text(encoding="utf-8"))
    jsonschema.validate(evidence, schema, format_checker=jsonschema.FormatChecker())
