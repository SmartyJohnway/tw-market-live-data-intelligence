from __future__ import annotations

import json
import hashlib
import urllib.request
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext, RuntimeAdapterRegistry, dispatch_prepared, prepare_dispatch
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.citation_builder import build_citation_index
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.models import ProjectionInputs
from scripts.m8r_05c.result_builder import build_result
from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
from server.services.phase_i_i1_production_candidate import (
    CAPABILITY_ID,
    EVIDENCE_CONTRACT,
    EXECUTOR_ID,
    MAX_BATCH_TARGETS,
    MAX_RESPONSE_BYTES,
    SOURCE_DESCRIPTORS,
    TIMEOUT_SECONDS,
    I1ProductionSourceError,
    _fetch_source,
    _observe_market,
    _selected_fmtqik,
    _selected_twse_breadth,
    build_i1_candidate_runtime_adapter_registry,
    _http_transport,
    production_batch_operation_adapter_candidate,
)


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-09-29T06:00:00Z"


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _fmt(date="1150924", **extra):
    return {"Date": date, "TradeVolume": "1200", "TradeValue": "345600", "Transaction": "42", "TAIEX": "23000.25", "Change": "-12.5", **extra}


def _breadth(date="1150924", kind="股票"):
    return {"出表日期": date, "類型": kind, "上漲": "4", "漲停": "1", "下跌": "3", "跌停": "0", "持平": "2", "未成交": "1", "無比價": "0"}


def _tpex(date="1150924"):
    return {"Date": date, "DailyTradingValue": "12.5", "DailyTradingVolume": "23.4", "CloseIndex": "200.5", "IndexChange": "-1.25", "PriceRiseCompanyNumbers": "4", "LimitUpCompanyNumbers": "1", "PriceDeclineCompanyNumbers": "3", "LimitDownCompanyNumbers": "0", "PriceFlatCompanyNumbers": "2", "UnmatchedCompanyNumbersSuspensionStocksIncluded": "1"}


def _transport_for(payload_by_url, calls):
    def transport(url, timeout):
        calls.append((url, timeout))
        value = payload_by_url[url]
        if isinstance(value, Exception):
            raise value
        return value
    return transport


def _ok(payload, content_type="application/json"):
    return 200, {"Content-Type": content_type}, payload


@pytest.mark.parametrize("source_id", list(SOURCE_DESCRIPTORS))
def test_transport_accepts_json_utf8_and_json_charset(source_id):
    calls = []
    body = _json_bytes([{"Date": "1150924"}])
    result = _fetch_source(source_id, retrieved_at=NOW,
                           transport=_transport_for({SOURCE_DESCRIPTORS[source_id]["url"]: _ok(body, "application/json; charset=utf-8")}, calls))
    assert result.status == "available"
    assert result.response_byte_count == len(body)
    assert len(result.response_sha256) == 64
    assert calls == [(SOURCE_DESCRIPTORS[source_id]["url"], 15)]


@pytest.mark.parametrize("response", [
    (403, {"Content-Type": "application/json"}, b"[]"),
    (429, {"Content-Type": "application/json"}, b"[]"),
    (200, {"Content-Type": "text/html"}, b"[]"),
    (200, {"Content-Type": "application/json"}, b"\xff"),
    (200, {"Content-Type": "application/json"}, b"{"),
    (200, {"Content-Type": "application/json"}, b"{}"),
    (200, {"Content-Type": "application/json"}, b"[1]"),
])
def test_transport_rejects_http_content_encoding_json_and_root_failures(response):
    source_id = "I1-TWSE-FMTQIK-OPENAPI"
    url = SOURCE_DESCRIPTORS[source_id]["url"]
    result = _fetch_source(source_id, retrieved_at=NOW, transport=lambda _url, _timeout: response)
    assert result.status == "source_failed"
    assert result.error_code


def test_transport_timeout_is_source_failed_without_retry():
    calls = []
    url = SOURCE_DESCRIPTORS["I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]["url"]
    result = _fetch_source("I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI", retrieved_at=NOW,
                           transport=_transport_for({url: TimeoutError("offline fixture")}, calls))
    assert result.status == "source_failed"
    assert len(calls) == 1


def test_real_transport_reads_only_cap_plus_one_and_refuses_redirect_handler(monkeypatch):
    calls = []

    class Response:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, limit):
            calls.append(("read", limit))
            return b"[]"

    class Opener:
        def open(self, request, timeout):
            calls.append((request.full_url, timeout))
            return Response()

    monkeypatch.setattr("urllib.request.build_opener", lambda *handlers: (calls.append(("handlers", handlers)), Opener())[1])
    url = SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]
    status, headers, body = _http_transport(url, 15)
    assert status == 200 and headers["Content-Type"] == "application/json" and body == b"[]"
    assert (url, 15) in calls
    assert ("read", MAX_RESPONSE_BYTES + 1) in calls
    handler = next(item for item in calls[0][1] if isinstance(item, urllib.request.HTTPRedirectHandler))
    assert handler.redirect_request(None, None, 302, "Found", {}, "https://unapproved.example/") is None


def test_transport_enforces_max_bytes_independent_of_content_length_hint():
    source_id = "I1-TWSE-FMTQIK-OPENAPI"
    url = SOURCE_DESCRIPTORS[source_id]["url"]
    exact = b"[]" + (b" " * (MAX_RESPONSE_BYTES - 2))
    accepted = _fetch_source(source_id, retrieved_at=NOW, transport=lambda *_: _ok(exact))
    assert accepted.status == "unavailable"
    assert accepted.response_byte_count == MAX_RESPONSE_BYTES
    over = _fetch_source(source_id, retrieved_at=NOW,
                         transport=lambda *_: (200, {"Content-Type": "application/json", "Content-Length": "2"}, exact + b" "))
    assert over.status == "source_failed"
    assert over.error_code == "source_failed:response_too_large"
    assert over.response_byte_count == MAX_RESPONSE_BYTES + 1


def test_fmtqik_selects_max_date_without_relying_on_array_order():
    selected = _selected_fmtqik((_fmt("1150923"), _fmt("1150924"), _fmt("1150922")))
    assert selected["Date"] == "1150924"


@pytest.mark.parametrize("rows,match", [
    (( _fmt("bad"),), "unparseable"),
    ((_fmt("1150924"), _fmt("1150924")), "duplicate_latest"),
])
def test_fmtqik_unprovable_latest_selection_fails_closed(rows, match):
    with pytest.raises(I1ProductionSourceError, match=match):
        _selected_fmtqik(rows)


def test_twse_breadth_exact_stock_selector_never_falls_back():
    selected = _selected_twse_breadth((_breadth(kind="整體市場"), _breadth(kind="股票")))
    assert len(selected) == 1 and selected[0]["類型"] == "股票"
    assert _selected_twse_breadth((_breadth(kind="整體市場"),)) == []
    with pytest.raises(I1ProductionSourceError, match="duplicate_stock"):
        _selected_twse_breadth((_breadth(), _breadth()))


def test_twse_unordered_source_rows_and_breadth_mismatch_are_preserved():
    responses = {
        SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]: _ok(_json_bytes([_fmt("1150923"), _fmt("1150924"), _fmt("1150922")])),
        SOURCE_DESCRIPTORS["I1-TWSE-BREADTH-TWTAZU-OPENAPI"]["url"]: _ok(_json_bytes([_breadth("1150605", "整體市場"), _breadth("1150605", "股票")])),
    }
    evidence, attempts = _observe_market("TWSE", retrieved_at=NOW, transport=_transport_for(responses, []))
    assert evidence["status"] == "partial"
    assert evidence["trade_date"] == "2026-09-24"
    assert evidence["components"]["fmtqik"]["official_date"] == "2026-09-24"
    assert evidence["components"]["breadth"]["official_date"] == "2026-06-05"
    assert any("dates preserved" in item for item in evidence["caveats"])
    assert len(attempts) == 2


def test_twse_empty_breadth_is_partial_with_preserved_values_and_no_stock_is_unavailable():
    urls = [SOURCE_DESCRIPTORS[x]["url"] for x in ("I1-TWSE-FMTQIK-OPENAPI", "I1-TWSE-BREADTH-TWTAZU-OPENAPI")]
    partial, _ = _observe_market("TWSE", retrieved_at=NOW, transport=lambda url, _timeout: _ok(_json_bytes([]) if url == urls[0] else _json_bytes([_breadth()])))
    assert partial["status"] == "partial"
    assert partial["breadth"] == {"up": 4, "limit_up": 1, "down": 3, "limit_down": 0, "flat": 2, "unmatched": 1, "no_comparison": 0}
    assert partial["breadth_unit"] == "security_count"
    assert partial["source_unit_metadata"]["I1-TWSE-BREADTH-TWTAZU-OPENAPI"]["up"] == "security_count"
    assert partial["components"]["fmtqik"]["status"] == "unavailable"
    breadth_component = partial["components"]["breadth"]
    assert breadth_component["status"] == "available"
    assert breadth_component["official_date"] == "2026-09-24"
    assert breadth_component["observed_fields"] == partial["breadth"]
    assert breadth_component["unit_metadata"]["up"] == "security_count"
    evidence_schema = json.loads((ROOT / "schemas/market_state_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(evidence_schema, format_checker=jsonschema.FormatChecker()).validate(partial)

    unavailable, _ = _observe_market(
        "TWSE", retrieved_at=NOW,
        transport=lambda url, _timeout: _ok(
            _json_bytes([]) if url == urls[0] else _json_bytes([_breadth(kind="整體市場")])
        ),
    )
    assert unavailable["status"] == "unavailable"
    assert unavailable["components"]["breadth"]["status"] == "missing"


@pytest.mark.parametrize("mutation", ["invalid_date", "missing_field", "non_integer", "negative"])
def test_twse_empty_fmtqik_rejects_malformed_stock_breadth(mutation):
    fmt_url = SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]
    row = _breadth()
    if mutation == "invalid_date":
        row["出表日期"] = "not-a-date"
    elif mutation == "missing_field":
        row.pop("上漲")
    elif mutation == "non_integer":
        row["上漲"] = "4.5"
    elif mutation == "negative":
        row["上漲"] = "-1"
    evidence, attempts = _observe_market(
        "TWSE", retrieved_at=NOW,
        transport=lambda url, _timeout: _ok(b"[]") if url == fmt_url else _ok(_json_bytes([row])),
    )
    assert evidence["status"] == "source_failed"
    assert evidence["components"]["fmtqik"]["status"] == "unavailable"
    assert evidence["components"]["breadth"]["status"] == "source_failed"
    assert evidence["components"]["breadth"]["transport"]["status"] == "available"
    assert len(attempts) == 2


def test_fmtqik_selected_latest_semantic_field_missing_is_source_failed():
    fmt_url = SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]
    breadth_url = SOURCE_DESCRIPTORS["I1-TWSE-BREADTH-TWTAZU-OPENAPI"]["url"]
    bad = _fmt()
    bad.pop("TAIEX")
    evidence, _ = _observe_market("TWSE", retrieved_at=NOW, transport=lambda url, _timeout: _ok(_json_bytes([bad])) if url == fmt_url else _ok(_json_bytes([_breadth()])))
    assert evidence["status"] == "source_failed"
    assert evidence["components"]["fmtqik"]["status"] == "source_failed"


def test_transport_failure_remains_source_failed_even_if_other_component_is_valid():
    fmt_url = SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]
    breadth_url = SOURCE_DESCRIPTORS["I1-TWSE-BREADTH-TWTAZU-OPENAPI"]["url"]
    evidence, _ = _observe_market("TWSE", retrieved_at=NOW,
                                  transport=lambda url, _timeout: (_ for _ in ()).throw(TimeoutError()) if url == fmt_url else _ok(_json_bytes([_breadth()])))
    assert evidence["status"] == "source_failed"
    assert evidence["components"]["fmtqik"]["status"] == "source_failed"
    assert evidence["components"]["breadth"]["status"] == "available"


def test_tpex_row_count_and_units_are_governed():
    url = SOURCE_DESCRIPTORS["I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]["url"]
    evidence, _ = _observe_market("TPEX", retrieved_at=NOW, transport=lambda *_: _ok(_json_bytes([_tpex()])))
    assert evidence["status"] == "complete"
    assert evidence["turnover"]["value_unit"] == "TWD_million"
    assert evidence["turnover"]["volume_unit"] == "thousand_share"
    empty, _ = _observe_market("TPEX", retrieved_at=NOW, transport=lambda *_: _ok(b"[]"))
    assert empty["status"] == "unavailable"
    multiple, _ = _observe_market("TPEX", retrieved_at=NOW, transport=lambda *_: _ok(_json_bytes([_tpex(), _tpex()])))
    assert multiple["status"] == "source_failed"
    assert multiple["components"]["tpex_mainborad_highlight"]["status"] == "source_failed"
    assert multiple["components"]["tpex_mainborad_highlight"]["transport"]["status"] == "available"
    malformed_row = _tpex()
    malformed_row.pop("CloseIndex")
    malformed, _ = _observe_market("TPEX", retrieved_at=NOW, transport=lambda *_: _ok(_json_bytes([malformed_row])))
    assert malformed["status"] == "source_failed"
    assert malformed["components"]["tpex_mainborad_highlight"]["status"] == "source_failed"
    assert malformed["components"]["tpex_mainborad_highlight"]["transport"]["status"] == "available"


def _request(index, market, security_code):
    return {
        "schema_version": "unified_market_evidence_execution_request.v1",
        "operation_id": f"umeop-op-v1-{index:020d}",
        "execution_request_id": f"umereq-v1-{index:020d}",
        "execution_request_hash": f"{index:064x}",
        "executor_id": EXECUTOR_ID,
        "capability_id": CAPABILITY_ID,
        "market": market,
        "batch_group_id": f"batch-{market}",
        "approved_security_identifiers": [f"{market}:{security_code}"],
        "approved_security_types": ["equity"],
        "timeout_seconds": TIMEOUT_SECONDS,
        "maximum_records": 1,
        "network_authorized": True,
    }


@pytest.mark.parametrize("market,codes,expected_gets", [
    ("TWSE", ["2330"], 2),
    ("TWSE", [str(2000 + i) for i in range(10)], 2),
    ("TPEX", [str(6000 + i) for i in range(10)], 1),
])
def test_same_market_batch_fetches_sources_once_and_fans_out(tmp_path, market, codes, expected_gets):
    responses = {
        SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]: _ok(_json_bytes([_fmt()])),
        SOURCE_DESCRIPTORS["I1-TWSE-BREADTH-TWTAZU-OPENAPI"]["url"]: _ok(_json_bytes([_breadth()])),
        SOURCE_DESCRIPTORS["I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]["url"]: _ok(_json_bytes([_tpex()])),
    }
    calls = []
    context = DispatchRuntimeContext(str(tmp_path), "execute-approved")
    requests = tuple(_request(i + 1, market, code) for i, code in enumerate(codes))
    result = production_batch_operation_adapter_candidate(
        requests, context, transport=_transport_for(responses, calls), retrieved_at=NOW
    )
    assert len(result) == len(codes)
    assert len(calls) == expected_gets
    assert all(item["schema_version"] == "unified_market_evidence_operation_result.v1" for item in result)
    assert all(item["evidence_artifacts"][0]["schema_version"] == EVIDENCE_CONTRACT for item in result)
    assert len(list((tmp_path / "evidence/phase_i/i1").glob("*.json"))) == len(codes)


def test_mixed_market_execution_groups_stay_within_three_source_gets(tmp_path):
    responses = {
        SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]: _ok(_json_bytes([_fmt()])),
        SOURCE_DESCRIPTORS["I1-TWSE-BREADTH-TWTAZU-OPENAPI"]["url"]: _ok(_json_bytes([_breadth()])),
        SOURCE_DESCRIPTORS["I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]["url"]: _ok(_json_bytes([_tpex()])),
    }
    calls = []
    context = DispatchRuntimeContext(str(tmp_path), "execute-approved")
    twse = tuple(_request(i + 1, "TWSE", str(2000 + i)) for i in range(10))
    tpex = tuple(_request(i + 101, "TPEX", str(6000 + i)) for i in range(10))
    production_batch_operation_adapter_candidate(twse, context, transport=_transport_for(responses, calls), retrieved_at=NOW)
    production_batch_operation_adapter_candidate(tpex, context, transport=_transport_for(responses, calls), retrieved_at=NOW)
    assert len(calls) == 3


def test_candidate_batch_limit_matches_unified_hard_target_limit(tmp_path):
    assert MAX_BATCH_TARGETS == 50
    responses = {
        SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]: _ok(_json_bytes([_fmt()])),
        SOURCE_DESCRIPTORS["I1-TWSE-BREADTH-TWTAZU-OPENAPI"]["url"]: _ok(_json_bytes([_breadth()])),
    }
    calls = []
    context = DispatchRuntimeContext(str(tmp_path), "execute-approved")
    fifty = tuple(_request(i + 1000, "TWSE", str(2000 + i)) for i in range(50))
    result = production_batch_operation_adapter_candidate(
        fifty, context, transport=_transport_for(responses, calls), retrieved_at=NOW
    )
    assert len(result) == 50
    assert len(calls) == 2

    calls.clear()
    fifty_one = tuple(_request(i + 2000, "TWSE", str(3000 + i)) for i in range(51))
    with pytest.raises(Exception, match="i1_batch_target_count_invalid"):
        production_batch_operation_adapter_candidate(
            fifty_one, context, transport=_transport_for(responses, calls), retrieved_at=NOW
        )
    assert calls == []


def test_candidate_registry_is_separate_from_normal_runtime():
    assert build_production_runtime_adapter_registry().routes_for_executor(EXECUTOR_ID) == ()
    candidate = build_i1_candidate_runtime_adapter_registry()
    assert {item.market for item in candidate.routes_for_executor(EXECUTOR_ID)} == {"TWSE", "TPEX"}


def test_wrong_route_or_missing_authorization_fails_before_transport(tmp_path):
    request = _request(1, "TWSE", "2330")
    request["network_authorized"] = False
    calls = []
    with pytest.raises(Exception, match="network_required_not_authorized"):
        production_batch_operation_adapter_candidate((request,), DispatchRuntimeContext(str(tmp_path), "execute-approved"), transport=_transport_for({}, calls), retrieved_at=NOW)
    assert calls == []
    request = _request(2, "TWSE", "2330")
    request["executor_id"] = "wrong-executor"
    with pytest.raises(Exception):
        production_batch_operation_adapter_candidate((request,), DispatchRuntimeContext(str(tmp_path), "execute-approved"), transport=_transport_for({}, calls), retrieved_at=NOW)
    assert calls == []


def test_candidate_artifact_projects_through_result_v3_and_audit_v3(tmp_path):
    request = _request(77, "TPEX", "6488")
    request.update({"execution_request_id": "umereq-v2-0123456789abcdef0123"})
    responses = {
        SOURCE_DESCRIPTORS["I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]["url"]: _ok(_json_bytes([_tpex()])),
    }
    outcome = production_batch_operation_adapter_candidate(
        (request,), DispatchRuntimeContext(str(tmp_path), "execute-approved"),
        transport=_transport_for(responses, []), retrieved_at=NOW,
    )[0]
    artifact_ref = outcome["evidence_artifacts"][0]
    content = (tmp_path / artifact_ref["relative_path"]).read_bytes()
    artifact = json.loads(content)
    actual_sha = hashlib.sha256(content).hexdigest()
    assert artifact["citation_ids"]
    inventory_entry = {**artifact_ref, "evidence_contract": EVIDENCE_CONTRACT, "sha256": actual_sha, "byte_size": len(content)}
    target_id = "TPEX:6488"
    identity = {
        "canonical_target_id": target_id, "isin": None, "market": "TPEX", "security_code": "6488",
        "security_name_zh": "fixture", "security_name_en": None,
        "instrument_family": "company_share", "instrument_type": "common_share",
    }
    request_input = {
        "schema_version": "unified_market_evidence_request.v3", "request_id": "i1-candidate-e2e",
        "execution_mode": "execute", "targets": [{"input": "6488", "market_hint": "TPEX"}],
        "data_needs": [{"type": CAPABILITY_ID, "priority": "required", "parameters": {}}],
    }
    plan_id = "umeop-v1-0123456789abcdef0123"
    operation_id = request["operation_id"]
    plan = {
        "plan_id": plan_id, "plan_hash": "a" * 64,
        "schema_version": "unified_market_evidence_orchestration_plan.v1", "plan_status": "plan_ready",
        "input_bindings": {"f3_validation_output_hash": "b" * 64},
        "operations": [{
            "operation_id": operation_id, "capability_id": CAPABILITY_ID,
            "canonical_target_ids": [target_id], "market": "TPEX", "executor_id": EXECUTOR_ID,
            "operation_status": "executable_pending_approval",
            "expected_evidence_contract": EVIDENCE_CONTRACT, "parameters": {},
        }],
    }
    bundle = {
        "bundle_id": "umeb-v1-0123456789abcdef0123", "bundle_hash": "d" * 64,
        "schema_version": "unified_market_evidence_bundle.v1", "finalized_at": NOW,
        "artifact_inventory": [inventory_entry],
        "operation_evidence_entries": [{"operation_id": operation_id, "status": "succeeded", "artifacts": [inventory_entry]}],
    }
    receipt = {
        "execution_receipt_id": "umerec-v1-0123456789abcdef0123", "execution_receipt_hash": "e" * 64,
        "schema_version": "unified_market_evidence_execution_receipt.v1", "overall_status": "succeeded", "finalized_at": NOW,
    }
    inputs = ProjectionInputs(
        request=request_input,
        f3_validation={"target_results": [{"target_index": 0, "original_input": "6488", "resolution_status": "resolved", "canonical_identity": identity}]},
        plan=plan,
        authorization={"authorization_id": "umea-v1-0123456789abcdef0123", "authorization_hash": "f" * 64, "schema_version": "unified_market_evidence_execution_authorization.v1"},
        consumption_binding={"consumption_binding_id": "umecb-v1-0123456789abcdef0123", "consumption_binding_hash": "1" * 64},
        claim={"claim_id": "umecl-v1-0123456789abcdef0123", "consumption_binding_id": "umecb-v1-0123456789abcdef0123", "consumption_binding_hash": "1" * 64, "authorization_id": "umea-v1-0123456789abcdef0123", "plan_id": plan_id, "operator_confirmation_reference": "offline fixture", "state": "consumed_success", "finalized_at": NOW},
        receipt=receipt, bundle=bundle, artifact_root=str(tmp_path), calculated_at=NOW,
        evidence_artifacts={artifact_ref["relative_path"]: artifact},
    )
    lineage = build_lineage_map(inputs)
    assert lineage.bindings[target_id][CAPABILITY_ID].status == "succeeded"
    citations = build_citation_index(lineage, bundle, "unified_market_evidence_result.v3")
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(result_schema, format_checker=jsonschema.FormatChecker()).validate(result)
    typed = result["targets"][0]["evidence"][CAPABILITY_ID]
    assert set(typed["citation_ids"]).issubset(set(citations.all_citations))
    assert typed["components"]["tpex_mainborad_highlight"]["transport"]["response_byte_count"] > 0
    audit = build_audit_package(
        result, inputs, citations, "ai_context/unified_market_evidence_result.v3.json",
        output_schema_version="unified_market_evidence_audit_package.v3",
    )
    audit_schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(audit_schema, format_checker=jsonschema.FormatChecker()).validate(audit)
    assert audit["phase_i_evidence"]["evidence_artifact_references"][0]["relative_path"] == artifact_ref["relative_path"]


def test_candidate_uses_existing_05b_dispatch_contract_with_offline_transport(tmp_path):
    operation_id = "umeop-op-v1-0123456789abcdef0123"
    execution_id = "umereq-v1-0123456789abcdef0123"
    request = {
        "schema_version": "unified_market_evidence_execution_request.v1",
        "execution_request_id": execution_id, "execution_request_hash": "a" * 64,
        "operation_id": operation_id, "batch_group_id": "umeop-batch-v1-0123456789abcdef0123",
        "plan_id": "umeop-v1-0123456789abcdef0123", "plan_hash": "b" * 64,
        "authorization_id": "umea-v1-0123456789abcdef0123", "authorization_hash": "c" * 64,
        "consumption_binding_id": "umeacb-v1-0123456789abcdef0123", "consumption_binding_hash": "d" * 64,
        "market": "TPEX", "approved_security_identifiers": ["TPEX:6488"],
        "approved_security_types": ["equity"], "capability_id": CAPABILITY_ID,
        "executor_id": EXECUTOR_ID, "requested_fields": [], "currentness_requirement": None,
        "maximum_records": 1, "timeout_seconds": TIMEOUT_SECONDS, "network_authorized": True,
        "relative_contained_output_path": f"operations/{operation_id}.execution-request.json",
    }
    binding = {"capability_id": CAPABILITY_ID, "market": "TPEX", "executor_id": EXECUTOR_ID,
               "security_types": ["equity"], "expected_evidence_contract": EVIDENCE_CONTRACT}
    preflight = {"bounded_execution_requests": [request], "approved_operation_order": [operation_id],
                 "resolved_operation_bindings": {operation_id: binding}}
    meta_payload = json.loads((ROOT / "config/phase_i_i1_production_executor_candidate.json").read_text(encoding="utf-8"))["executor_metadata"]
    metadata = ExecutorMetadataRegistry.from_json(meta_payload)
    base_registry = build_i1_candidate_runtime_adapter_registry()
    base = base_registry.get_route(EXECUTOR_ID, CAPABILITY_ID, "TPEX")
    responses = {SOURCE_DESCRIPTORS["I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]["url"]: _ok(_json_bytes([_tpex()]))}
    calls = []
    transport = _transport_for(responses, calls)
    runtime = RuntimeAdapterRegistry([replace(
        base,
        adapter=lambda req, ctx: production_batch_operation_adapter_candidate((req,), ctx, transport=transport, retrieved_at=NOW)[0],
        batch_adapter=lambda reqs, ctx: production_batch_operation_adapter_candidate(reqs, ctx, transport=transport, retrieved_at=NOW),
    )])
    prepared = prepare_dispatch(preflight, metadata, runtime, mode="execute-approved")
    outcomes = dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")
    assert outcomes[0]["status"] == "succeeded"
    assert outcomes[0]["schema_version"] == "unified_market_evidence_operation_result.v1"
    assert len(calls) == 1
