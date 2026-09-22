"""Fixture-only H-IMP-3 acceptance for dormant H2 normalizers."""
from __future__ import annotations

import copy
import json
import socket
import urllib.request
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from server.services.phase_h_corporate_action_adapters import (
    DECLARED_EVENT_SUBTYPES, H2NormalizationError, assemble_corporate_action_context,
    failed_source_result,
    normalize_tpex_exright_daily, normalize_tpex_exright_prepost, normalize_twse_twt48u_all,
)
from server.services.phase_h_discontinuity_safety import derive_discontinuity_safety

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = json.loads((ROOT / "tests/fixtures/phase_h_contract_v3/contract_examples.json").read_text(encoding="utf-8"))
SOURCE_ROWS = json.loads((ROOT / "tests/fixtures/phase_h_h2_adapters/source_rows.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "schemas/corporate_action_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
TARGET_TPEX = {"canonical_target_id": "target-tpex-6488", "market": "TPEX", "security_code": "6488"}
TARGET_TWSE = {"canonical_target_id": "target-twse-2330", "market": "TWSE", "security_code": "2330"}
WINDOW = {"start": "2026-08-01", "end": "2026-08-28"}
OBSERVED = "2026-09-22T00:00:00Z"


def pre(code: str = "6488", **extra: object) -> dict:
    return {"SecuritiesCompanyCode": code, "ExRrightsExDividendDate": "2026-08-20", "ExRrightsExDividend": "除息", "CashDividend": "0", "StockDividendRatio": "", "SubscriptionRatioToNewSharesIssued": "0", "SubscriptionPricePerShare": "尚未公告", **extra}


def final(code: str = "6488", **extra: object) -> dict:
    return {"SecuritiesCompanyCode": code, "Date": "2026-08-20", "ClosePriceBeforeExRightsDiviend": "100", "ExRightsDiviendQuote": "95", "CashDividend": "2.5", "StockDividend": "0", "ExRightsDiviend": "0", "OpeningReferencePrice": "95", "SubscriptionPricePerShare": "", **extra}


def twse(code: str = "2330", **extra: object) -> dict:
    return {"Code": code, "Date": "2026-08-20", "Exdividend": "除權", "CashDividend": "0", "StockDividendRatio": "1", "SubscriptionRatio": "", "SubscriptionPricePerShare": "尚未公告", **extra}


def normalize_pair() -> tuple[dict, dict]:
    return (normalize_tpex_exright_prepost(SOURCE_ROWS["tpex_pre"], TARGET_TPEX, observed_at=OBSERVED, citation_id="cite-pre"), normalize_tpex_exright_daily(SOURCE_ROWS["tpex_final"], TARGET_TPEX, observed_at=OBSERVED, citation_id="cite-final"))


def test_source_stages_value_states_and_exact_binding() -> None:
    result_pre, result_final = normalize_pair()
    result_twse = normalize_twse_twt48u_all(SOURCE_ROWS["twse_pre"], TARGET_TWSE, observed_at=OBSERVED, citation_id="cite-twse")
    assert result_pre["events"][0]["source_evidence_stage"] == "preannouncement"
    assert result_final["events"][0]["source_evidence_stage"] == "official_reference_calculated"
    assert result_twse["events"][0]["source_evidence_stage"] == "preannouncement"
    assert result_pre["events"][0]["cash_dividend"] == {"state": "value", "value": 1.0}
    assert result_pre["events"][0]["stock_dividend_ratio"]["state"] == "value"
    assert result_pre["events"][0]["rights_ratio"]["state"] == "value"
    assert result_pre["events"][0]["subscription_price"]["state"] == "blank"
    assert result_pre["events"][0]["official_source_proof"] == "tpex_exright_prepost"
    assert result_pre["events"][0]["revision_relation"]["status"] == "unresolved"
    assert result_final["events"][0]["official_reference_price"] == {"state": "value", "value": 95.0}
    assert result_final["events"][0]["official_source_proof"] == "tpex_exright_daily"
    assert result_twse["events"][0]["cash_dividend"] == {"state": "value", "value": 0.0}
    with pytest.raises(H2NormalizationError, match="wrong_market"):
        normalize_tpex_exright_prepost([pre()], TARGET_TWSE, observed_at=OBSERVED, citation_id="x")
    assert normalize_tpex_exright_prepost([pre("9999")], TARGET_TPEX, observed_at=OBSERVED, citation_id="x")["status"] == "no_evidence_in_covered_scope"
    with pytest.raises(H2NormalizationError, match="ambiguous"):
        normalize_tpex_exright_prepost([pre(), pre()], TARGET_TPEX, observed_at=OBSERVED, citation_id="x")


@pytest.mark.parametrize("rows,error", [
    ([{"ExRrightsExDividendDate": "2026-08-20"}], "SecuritiesCompanyCode"),
    ([{"RenamedCode": "6488", "ExRrightsExDividendDate": "2026-08-20"}], "SecuritiesCompanyCode"),
    ([{"SecuritiesCompanyCode": "6488"}], "ExRrightsExDividendDate"),
    ([pre(CashDividend="not-a-number")], "invalid_numeric_field"),
    ({"not": "rows"}, "invalid_top_level_rows"),
])
def test_source_drift_fails_closed(rows: object, error: str) -> None:
    with pytest.raises(H2NormalizationError, match=error):
        normalize_tpex_exright_prepost(rows, TARGET_TPEX, observed_at=OBSERVED, citation_id="cite")


def test_unknown_classification_fails_closed_and_missing_is_distinct() -> None:
    with pytest.raises(H2NormalizationError, match="event_type_unresolved"):
        normalize_tpex_exright_prepost([pre(StockDividendRatio="", SubscriptionRatioToNewSharesIssued="尚未公告")], TARGET_TPEX, observed_at=OBSERVED, citation_id="cite")
    missing = pre(); missing.pop("ExRrightsExDividend")
    with pytest.raises(H2NormalizationError, match="missing_required_field:ExRrightsExDividend"):
        normalize_tpex_exright_prepost([missing], TARGET_TPEX, observed_at=OBSERVED, citation_id="cite")


def test_explicit_null_differs_from_missing_and_all_classification_paths_exist() -> None:
    null_value = pre(CashDividend="1", StockDividendRatio="0", SubscriptionPricePerShare=None)
    normalized = normalize_tpex_exright_prepost([null_value], TARGET_TPEX, observed_at=OBSERVED, citation_id="null")
    assert normalized["events"][0]["subscription_price"] == {"state": "unavailable", "value": None}
    for cash, stock, rights, expected in (("1", "0", "0", "ex_dividend"), ("0", "1", "0", "ex_right"), ("1", "1", "0", "ex_right_dividend")):
        row = pre(CashDividend=cash, StockDividendRatio=stock, SubscriptionRatioToNewSharesIssued=rights)
        assert normalize_tpex_exright_prepost([row], TARGET_TPEX, observed_at=OBSERVED, citation_id=expected)["events"][0]["event_type"] == expected
    absent = pre(); absent.pop("SubscriptionPricePerShare")
    with pytest.raises(H2NormalizationError, match="missing_required_field:SubscriptionPricePerShare"):
        normalize_tpex_exright_prepost([absent], TARGET_TPEX, observed_at=OBSERVED, citation_id="missing")


def test_complete_value_state_matrix_is_preserved_by_assembly() -> None:
    result = normalize_tpex_exright_prepost([pre(CashDividend="1", StockDividendRatio="0", SubscriptionPricePerShare="")], TARGET_TPEX, observed_at=OBSERVED, citation_id="states")
    event_value = result["events"][0]
    event_value["stock_dividend_ratio"] = {"state": "value", "value": 0}
    event_value["rights_ratio"] = {"state": "blank", "value": None}
    event_value["subscription_price"] = {"state": "not_announced", "value": None}
    assembled = assemble_corporate_action_context([result], TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    event_value = assembled["events"][0]
    event_value["stock_dividend_ratio"] = {"state": "value", "value": 0}
    event_value["rights_ratio"] = {"state": "blank", "value": None}
    event_value["subscription_price"] = {"state": "not_announced", "value": None}
    controlled = copy.deepcopy(result)
    controlled["events"][0]["pre_event_close"] = {"state": "not_applicable", "value": None}
    controlled["events"][0]["official_reference_price"] = {"state": "unavailable", "value": None}
    controlled = assemble_corporate_action_context([controlled], TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    states = [event_value["stock_dividend_ratio"]["state"], event_value["rights_ratio"]["state"], event_value["subscription_price"]["state"], controlled["events"][0]["pre_event_close"]["state"], controlled["events"][0]["official_reference_price"]["state"]]
    assert len(set(states)) == 5


@pytest.mark.parametrize("normalizer,target,row,missing", [
    (normalize_tpex_exright_daily, TARGET_TPEX, final(), "SecuritiesCompanyCode"),
    (normalize_tpex_exright_daily, TARGET_TPEX, final(), "Date"),
    (normalize_tpex_exright_daily, TARGET_TPEX, final(), "ExRightsDiviendQuote"),
    (normalize_twse_twt48u_all, TARGET_TWSE, twse(), "Code"),
    (normalize_twse_twt48u_all, TARGET_TWSE, twse(), "Date"),
    (normalize_twse_twt48u_all, TARGET_TWSE, twse(), "Exdividend"),
])
def test_all_implemented_contracts_fail_closed_on_missing_keys(normalizer, target, row, missing) -> None:
    row.pop(missing)
    with pytest.raises(H2NormalizationError, match=f"missing_required_field:{missing}"):
        normalizer([row], target, observed_at=OBSERVED, citation_id="drift")


def test_assembly_preserves_full_scope_partial_coverage_and_schema() -> None:
    result = assemble_corporate_action_context(normalize_pair(), TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    assert result["status"] == "partial"
    assert result["coverage"]["declared_event_subtypes"] == list(DECLARED_EVENT_SUBTYPES)
    assert "capital_reduction_resume" in result["coverage"]["uncovered_event_subtypes"]
    assert "split" in result["coverage"]["uncovered_event_subtypes"]
    assert not list(Draft7Validator(SCHEMA).iter_errors(result))
    assert [event["source_evidence_stage"] for event in result["events"]] == ["official_reference_calculated", "preannouncement"]


def test_officially_linked_relation_survives_assembly() -> None:
    result = normalize_tpex_exright_daily(SOURCE_ROWS["tpex_final"], TARGET_TPEX, observed_at=OBSERVED, citation_id="linked")
    result["events"][0]["revision_relation"] = {"status": "officially_linked", "relation_type": "supersedes", "related_official_reference": "fixture-official-link"}
    assembled = assemble_corporate_action_context([result], TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    assert assembled["events"][0]["revision_relation"] == result["events"][0]["revision_relation"]


def _complete_for_h4(value: dict) -> dict:
    complete = copy.deepcopy(value)
    coverage = complete["coverage"]
    coverage.update({"status": "complete", "declared_scope_complete": True, "covered_event_subtypes": list(DECLARED_EVENT_SUBTYPES), "uncovered_event_subtypes": []})
    complete["status"] = "available"
    return complete


def test_h2_to_h4_dormant_integration() -> None:
    partial = assemble_corporate_action_context(normalize_pair(), TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    h3 = copy.deepcopy(EXAMPLES["h3_1d"]); h3["target"] = dict(TARGET_TPEX)
    incomplete = derive_discontinuity_safety(h2_evidence=partial, h3_evidence=h3, h2_evidence_reference="h2", h3_evidence_reference="h3", event_evidence_references={0: "final", 1: "pre"}, official_reference_evidence_references={0: "reference"})
    assert incomplete["state"] == "coverage_incomplete"
    complete = _complete_for_h4(partial)
    # This controlled integration fixture isolates the FINAL record; it does
    # not represent production coverage and cannot make the PRE record linked.
    complete["events"] = [complete["events"][0]]
    complete["citation_ids"] = ["cite-final"]
    complete["coverage"]["requested_window"] = {"start": "2026-08-01", "end": "2026-08-31"}
    complete["events"][0]["revision_relation"] = {"status": "officially_linked", "relation_type": "supersedes", "related_official_reference": "fixture-final-link"}
    available = derive_discontinuity_safety(h2_evidence=complete, h3_evidence=h3, h2_evidence_reference="h2", h3_evidence_reference="h3", event_evidence_references={0: "final"}, official_reference_evidence_references={0: "reference"})
    assert available["state"] == "discontinuity_detected_reference_available"
    no_ref = copy.deepcopy(complete); no_ref["events"][0]["official_reference_price"] = {"state": "unavailable", "value": None}
    unavailable = derive_discontinuity_safety(h2_evidence=no_ref, h3_evidence=h3, h2_evidence_reference="h2", h3_evidence_reference="h3", event_evidence_references={0: "final"})
    assert unavailable["state"] == "discontinuity_detected_reference_unavailable"


def test_pre_lifecycle_boundaries_feed_h4_safely() -> None:
    h3 = copy.deepcopy(EXAMPLES["h3_1d"]); h3["target"] = dict(TARGET_TPEX)
    future = normalize_tpex_exright_prepost(SOURCE_ROWS["tpex_pre"], TARGET_TPEX, observed_at=OBSERVED, citation_id="future")
    future["events"][0]["effective_date"] = "2026-09-30"
    future_h2 = assemble_corporate_action_context([future], TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    future_h4 = derive_discontinuity_safety(h2_evidence=future_h2, h3_evidence=h3, h2_evidence_reference="h2", h3_evidence_reference="h3", event_evidence_references={0: "future"})
    assert future_h4["effective_event_evidence_references"] == []
    inside = normalize_tpex_exright_prepost(SOURCE_ROWS["tpex_pre"], TARGET_TPEX, observed_at=OBSERVED, citation_id="inside")
    inside["events"][0]["effective_date"] = "2026-08-20"
    inside_h2 = assemble_corporate_action_context([inside], TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    inside_h4 = derive_discontinuity_safety(h2_evidence=inside_h2, h3_evidence=h3, h2_evidence_reference="h2", h3_evidence_reference="h3", event_evidence_references={0: "inside"})
    assert inside_h4["state"] == "coverage_incomplete"
    assert {failure["failure_type"] for failure in inside_h4["upstream_failures"]} >= {"unresolved_effective_timing"}


def test_failed_or_binding_source_never_fabricates_event_for_h4() -> None:
    h3 = copy.deepcopy(EXAMPLES["h3_1d"]); h3["target"] = dict(TARGET_TPEX)
    for result in (
        failed_source_result("H2-TPEX-EXRIGHT-PRE-OPENAPI", "missing identifier"),
        failed_source_result("H2-TPEX-EXRIGHT-PRE-OPENAPI", "wrong target", binding_failed=True),
    ):
        h2 = assemble_corporate_action_context([result], TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
        h4 = derive_discontinuity_safety(h2_evidence=h2, h3_evidence=h3, h2_evidence_reference="h2", h3_evidence_reference="h3")
        assert h2["events"] == []
        assert h4["state"] == "coverage_incomplete"


def test_source_result_citations_survive_no_target_and_failures() -> None:
    no_target = normalize_tpex_exright_prepost([pre("9999")], TARGET_TPEX, observed_at=OBSERVED, citation_id="source-no-target")
    failed = failed_source_result("H2-TPEX-EXRIGHT-PRE-OPENAPI", "source drift", citation_id="source-failed")
    binding = failed_source_result("H2-TPEX-EXRIGHT-PRE-OPENAPI", "wrong market", binding_failed=True, citation_id="source-binding")
    assembled = assemble_corporate_action_context([no_target, failed, binding], TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    assert assembled["events"] == []
    assert assembled["citation_ids"] == ["source-binding", "source-failed", "source-no-target"]


def test_available_event_citation_is_unioned_once() -> None:
    result = normalize_tpex_exright_prepost(SOURCE_ROWS["tpex_pre"], TARGET_TPEX, observed_at=OBSERVED, citation_id="cite-pre")
    result["citation_ids"].append("cite-extra")
    assembled = assemble_corporate_action_context([result], TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    assert assembled["citation_ids"] == ["cite-extra", "cite-pre"]
    assert assembled["events"][0]["citation_ids"] == ["cite-pre"]


def test_descriptor_states_and_network_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    descriptors = json.loads((ROOT / "config/phase_h_h2_dormant_source_descriptors.json").read_text(encoding="utf-8"))["sources"]
    by_id = {item["source_id"]: item for item in descriptors}
    assert by_id["H2-TWSE-EXRIGHT-FINAL-TWT49U"]["source_role"] == "optional_licensed_provider"
    assert by_id["H2-TWSE-CAPITAL-REDUCTION-WEB"]["source_role"] == "manual_verification"
    assert by_id["H2-TPEX-CAPITAL-REDUCTION-WEB"]["runtime_executable"] is False
    assert by_id["H2-TWSE-PAR-SPLIT-CONSOLIDATION-GAP"]["activation_state"] == "blocked"
    assert by_id["H2-TPEX-PAR-SPLIT-CONSOLIDATION-GAP"]["activation_state"] == "blocked"
    assert by_id["H2-TWSE-EXRIGHT-FINAL-TWT49U"]["runtime_executable"] is False
    assert by_id["H2-TWSE-CAPITAL-REDUCTION-WEB"]["runtime_executable"] is False
    assert by_id["H2-TPEX-CAPITAL-REDUCTION-WEB"]["runtime_executable"] is False
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network attempted"))
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: pytest.fail("network attempted"))
    first = assemble_corporate_action_context(normalize_pair(), TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    second = assemble_corporate_action_context(normalize_pair(), TARGET_TPEX, observed_at=OBSERVED, requested_window=WINDOW)
    assert first == second


def test_fresh_install_without_twt49u() -> None:
    """PRE normalizers and assembly do not initialize optional TWT49U state."""
    assert "TWT49U" not in __import__("server.services.phase_h_corporate_action_adapters", fromlist=["__name__"]).__dict__
    result = normalize_twse_twt48u_all(SOURCE_ROWS["twse_pre"], TARGET_TWSE, observed_at=OBSERVED, citation_id="fresh-twse")
    assembled = assemble_corporate_action_context([result], TARGET_TWSE, observed_at=OBSERVED, requested_window=WINDOW)
    assert assembled["events"]


def test_static_dormant_registry_and_plan_only_boundary() -> None:
    registry = (ROOT / "config/m8r_06_03_executor_registry_metadata.json").read_text(encoding="utf-8")
    assert "corporate_action_context" not in registry
    catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    capability = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == "corporate_action_context")
    assert capability["runtime_executable"] is False
    assert capability["support_status"] == "contract_supported"
    route = next(item for item in json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))["routes"] if item["capability_id"] == "corporate_action_context")
    assert route["runtime_executable"] is False
    assert route["selected_executor_id"] is None
    assert route["routing_status"] == "plan_only"
    assert route["network_required"] is False
