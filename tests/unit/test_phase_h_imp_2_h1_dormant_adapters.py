"""Fixture-only H-IMP-2 acceptance for dormant H1 source normalizers."""
from __future__ import annotations

import copy
import json
import socket
import urllib.request
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from scripts.validate_phase_h_v3_contracts import validate_trading_status_context_semantics
from server.services.phase_h_trading_status_adapters import (
    DECLARED_STATUS_TYPES,
    H1NormalizationError,
    failed_source_result,
    normalize_tpex_attention,
    normalize_tpex_disposition,
    normalize_twse_changed_trading,
)


ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "schemas/trading_status_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
TARGET_TPEX = {"canonical_target_id": "target-tpex-6488", "market": "TPEX", "security_code": "6488"}
TARGET_TWSE = {"canonical_target_id": "target-twse-2330", "market": "TWSE", "security_code": "2330"}
OBSERVED = "2026-09-22T00:00:00Z"
SYNTHETIC_SOURCE = {
    "source_family": "NON_AUTHORITATIVE_TEST_ONLY_COMPLETE_H1_SCOPE",
    "source_contract_id": "controlled_complete_h1_scope_fixture",
    "transport": "fixture",
    "license_authority": None,
    "source_role": "research_only",
    "activation_state": "inactive",
}


def test_fixture_only_source_rows_and_three_dormant_normalizers() -> None:
    assert ROWS["fixture_kind"] == "NON_AUTHORITATIVE_TEST_ONLY"
    attention = normalize_tpex_attention(ROWS["tpex_attention"], TARGET_TPEX, observed_at=OBSERVED, citation_id="attention-source")
    disposition = normalize_tpex_disposition(ROWS["tpex_disposition"], TARGET_TPEX, observed_at=OBSERVED, citation_id="disposition-source")
    changed = normalize_twse_changed_trading(ROWS["twse_changed_trading"], TARGET_TWSE, observed_at=OBSERVED, citation_id="changed-source")
    assert attention["items"][0]["status_type"] == "attention"
    assert attention["items"][0]["official_reason"] is None
    assert attention["items"][0]["source_native_provenance"]["TradingInformation"] == "official attention-list entry"
    assert disposition["items"][0]["status_type"] == "disposition"
    assert disposition["items"][0]["official_conditions"] == "official condition text"
    assert disposition["items"][0]["official_measures"] is None
    assert disposition["items"][0]["source_native_provenance"]["DispositionPeriod"] == "official period text"
    assert disposition["items"][0]["source_native_provenance"]["DispositionReasons"] == "official reason text"
    assert changed["items"][0]["status_type"] == "changed_trading_method"
    assert changed["items"][0]["source_native_provenance"]["PeriodicCallAuctionTrading"] == "official periodic call auction text"
    assert attention["coverage"]["source_snapshot_date"] == "2026-09-21"
    assert changed["coverage"]["source_snapshot_date"] is None
    for result in (attention, disposition, changed):
        assert result["status"] == "partial"
        assert result["coverage"]["declared_status_types"] == list(DECLARED_STATUS_TYPES)
        assert not list(Draft7Validator(SCHEMA).iter_errors(result))


def test_partial_target_absence_keeps_source_citation() -> None:
    rows = copy.deepcopy(ROWS["tpex_attention"])
    rows[0]["SecuritiesCompanyCode"] = "9999"
    result = normalize_tpex_attention(rows, TARGET_TPEX, observed_at=OBSERVED, citation_id="absence-source")
    assert result["status"] == "partial"
    assert result["items"] == []
    assert result["citation_ids"] == ["absence-source"]
    assert result["coverage"]["covered_status_types"] == ["attention"]
    assert result["coverage"]["uncovered_status_types"] == ["changed_trading_method", "disposition", "resumption", "suspension"]


def test_empty_tpex_tables_are_valid_partial_source_slices() -> None:
    for normalizer, subtype in ((normalize_tpex_attention, "attention"), (normalize_tpex_disposition, "disposition")):
        result = normalizer([], TARGET_TPEX, observed_at=OBSERVED, citation_id=f"empty-{subtype}")
        assert result["status"] == "partial"
        assert result["items"] == []
        assert result["coverage"]["covered_status_types"] == [subtype]
        assert result["coverage"]["retrieval_succeeded"] is True
        assert result["coverage"]["source_contract_validated"] is True
        assert result["coverage"]["exact_target_search_succeeded"] is True
        assert result["coverage"]["source_snapshot_date"] is None
        assert result["citation_ids"] == [f"empty-{subtype}"]


def test_present_noncanonical_date_is_preserved_without_source_failure() -> None:
    rows = copy.deepcopy(ROWS["tpex_attention"])
    rows[0]["Date"] = "09/21/2026"
    result = normalize_tpex_attention(rows, TARGET_TPEX, observed_at=OBSERVED, citation_id="raw-date")
    assert result["status"] == "partial"
    assert result["coverage"]["source_snapshot_date"] is None
    assert "source_snapshot_date_unresolved:Date:raw_encoding" in result["caveats"]
    assert result["items"][0]["source_record_date"] is None
    assert result["items"][0]["source_native_provenance"]["Date"] == "09/21/2026"


@pytest.mark.parametrize("raw, diagnostic", [("2026-99-99", "calendar"), ("2026-02-30", "calendar"), ([], "type"), ({}, "type")])
def test_malformed_canonical_date_fails_closed(raw: object, diagnostic: str) -> None:
    rows = copy.deepcopy(ROWS["tpex_attention"])
    rows[0]["Date"] = raw
    with pytest.raises(H1NormalizationError, match=f"invalid_source_snapshot_date_{diagnostic}"):
        normalize_tpex_attention(rows, TARGET_TPEX, observed_at=OBSERVED, citation_id="bad-date")


def test_mixed_source_dates_are_not_source_failure() -> None:
    rows = copy.deepcopy(ROWS["tpex_disposition"])
    rows.append({**rows[0], "SecuritiesCompanyCode": "9999", "Date": "2026-09-22"})
    result = normalize_tpex_disposition(rows, TARGET_TPEX, observed_at=OBSERVED, citation_id="mixed-date")
    assert result["status"] == "partial"
    assert result["coverage"]["source_snapshot_date"] is None
    assert result["coverage"]["retrieval_succeeded"] is True
    assert "source_snapshot_date_unresolved:Date:multiple_values" in result["caveats"]


def test_complete_scope_no_evidence_is_controlled_test_only() -> None:
    fixture = normalize_tpex_attention(ROWS["tpex_attention"], TARGET_TPEX, observed_at=OBSERVED, citation_id="complete-source")
    fixture["source"] = copy.deepcopy(SYNTHETIC_SOURCE)
    fixture["status"] = "no_evidence_in_covered_scope"
    fixture["items"] = []
    fixture["coverage"].update({
        "status": "complete", "declared_scope_complete": True,
        "covered_status_types": list(DECLARED_STATUS_TYPES), "uncovered_status_types": [],
    })
    validate_trading_status_context_semantics(fixture)
    assert not list(Draft7Validator(SCHEMA).iter_errors(fixture))


def test_source_and_binding_failures_remain_distinct_with_citations() -> None:
    source_failed = failed_source_result("H1-TPEX-ATTENTION-OPENAPI", TARGET_TPEX, observed_at=OBSERVED, diagnostic="missing source field", citation_id="failed-source")
    binding_failed = failed_source_result("H1-TPEX-ATTENTION-OPENAPI", TARGET_TPEX, observed_at=OBSERVED, diagnostic="wrong market", citation_id="failed-binding", binding_failed=True)
    assert source_failed["status"] == "source_failed"
    assert source_failed["items"] == []
    assert source_failed["citation_ids"] == ["failed-source"]
    assert binding_failed["status"] == "binding_failed"
    assert binding_failed["items"] == []
    assert binding_failed["citation_ids"] == ["failed-binding"]


def test_lifecycle_states_and_simultaneous_statuses_are_distinguishable() -> None:
    base = normalize_tpex_attention(ROWS["tpex_attention"], TARGET_TPEX, observed_at=OBSERVED, citation_id="lifecycle")
    controlled = copy.deepcopy(base)
    controlled["source"] = copy.deepcopy(SYNTHETIC_SOURCE)
    controlled["coverage"].update({"status": "complete", "declared_scope_complete": True, "covered_status_types": list(DECLARED_STATUS_TYPES), "uncovered_status_types": []})
    controlled["items"] = []
    for lifecycle, status_type in zip(("reported", "effective", "ended", "unresolved"), ("attention", "disposition", "changed_trading_method", "suspension"), strict=True):
        item = copy.deepcopy(base["items"][0])
        item["status_lifecycle"] = lifecycle
        item["status_type"] = status_type
        controlled["items"].append(item)
    item = copy.deepcopy(base["items"][0]); item["status_type"] = "resumption"; controlled["items"].append(item)
    validate_trading_status_context_semantics(controlled)
    assert {item["status_lifecycle"] for item in controlled["items"]} == {"reported", "effective", "ended", "unresolved"}
    assert {item["status_type"] for item in controlled["items"]} == set(DECLARED_STATUS_TYPES)


@pytest.mark.parametrize("normalizer,rows,target,error", [
    (normalize_tpex_attention, [{"Date": "2026-09-21"}], TARGET_TPEX, "SecuritiesCompanyCode"),
    (normalize_tpex_attention, [{"Date": "2026-09-21", "RenamedCode": "6488"}], TARGET_TPEX, "SecuritiesCompanyCode"),
    (normalize_tpex_attention, [{"SecuritiesCompanyCode": "6488"}], TARGET_TPEX, "Date"),
    (normalize_tpex_attention, {"not": "list"}, TARGET_TPEX, "invalid_top_level_rows"),
    (normalize_tpex_disposition, [{"Date": "2026-09-21", "SecuritiesCompanyCode": "6488", "CompanyName": "x", "DisposalCondition": "x"}], TARGET_TPEX, "DispositionPeriod"),
    (normalize_tpex_disposition, [{"Date": "2026-09-21", "SecuritiesCompanyCode": "6488", "CompanyName": "x", "DispositionPeriod": "x", "DisposalCondition": "x"}], TARGET_TPEX, "DispositionReasons"),
    (normalize_twse_changed_trading, [{"Name": "x", "PeriodicCallAuctionTrading": "x"}], TARGET_TWSE, "Code"),
    (normalize_twse_changed_trading, [{"Code": "2330", "Name": "x"}], TARGET_TWSE, "PeriodicCallAuctionTrading"),
])
def test_source_drift_fails_closed(normalizer, rows: object, target: dict, error: str) -> None:
    with pytest.raises(H1NormalizationError, match=error):
        normalizer(rows, target, observed_at=OBSERVED, citation_id="drift")


def test_exact_identity_has_no_name_fallback_or_ambiguous_binding() -> None:
    with pytest.raises(H1NormalizationError, match="wrong_market"):
        normalize_tpex_attention(ROWS["tpex_attention"], TARGET_TWSE, observed_at=OBSERVED, citation_id="wrong-market")
    wrong_code = copy.deepcopy(ROWS["tpex_attention"])
    wrong_code[0]["SecuritiesCompanyCode"] = "9999"
    wrong_code[0]["CompanyName"] = "target name cannot bind"
    result = normalize_tpex_attention(wrong_code, TARGET_TPEX, observed_at=OBSERVED, citation_id="wrong-code")
    assert result["items"] == []
    duplicate = copy.deepcopy(ROWS["tpex_attention"]) * 2
    with pytest.raises(H1NormalizationError, match="ambiguous_exact_target_rows"):
        normalize_tpex_attention(duplicate, TARGET_TPEX, observed_at=OBSERVED, citation_id="ambiguous")


def test_h1_descriptors_exact_selected_activation_and_zero_network_normalizers(monkeypatch: pytest.MonkeyPatch) -> None:
    descriptor_doc = json.loads((ROOT / "config/phase_h_h1_dormant_source_descriptors.json").read_text(encoding="utf-8"))
    descriptors = descriptor_doc["sources"]
    by_id = {item["source_id"]: item for item in descriptors}
    assert len(by_id) == 9
    assert descriptor_doc["status"] == "selected_route_active_v2_preferred"
    assert by_id["H1-TPEX-ATTENTION-OPENAPI"]["activation_state"] == "active"
    assert by_id["H1-TPEX-ATTENTION-OPENAPI"]["runtime_executable"] is True
    assert by_id["H1-TPEX-DISPOSITION-OPENAPI"]["activation_state"] == "eligible"
    assert by_id["H1-TWSE-CHANGED-TRADING-OPENAPI"]["activation_state"] == "eligible"
    assert by_id["H1-TWSE-SUSPEND-RESUME-OPENAPI"]["activation_state"] == "inactive"
    assert by_id["H1-TPEX-SUSPEND-TODAY-OPENAPI"]["activation_state"] == "inactive"
    assert by_id["H1-TPEX-SUSPEND-HISTORY-OPENAPI"]["source_role"] == "governed_fallback"
    assert sum(item["runtime_executable"] is True for item in descriptors) == 1

    registry = json.loads((ROOT / "config/m8r_06_03_executor_registry_metadata.json").read_text(encoding="utf-8"))
    h1_routes = [
        item for item in registry["executors"]
        if item["capability_id"] == "trading_status_context"
    ]
    assert [(item["executor_id"], item["market"]) for item in h1_routes] == [
        ("phase_h_h1_tpex_attention_executor", "TPEX")
    ]

    catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    capability = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == "trading_status_context")
    assert capability["support_status"] == "runtime_executable"
    assert capability["runtime_executable"] is True
    assert capability["phase_h_activation_state"] == "selected_route_active"
    route = next(item for item in json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))["routes"] if item["capability_id"] == "trading_status_context")
    assert route["runtime_executable"] is True
    assert route["selected_executor_id"] == "phase_h_h1_tpex_attention_executor"
    assert route["routing_status"] == "resolved"
    assert route["supported_markets"] == ["TPEX"]
    assert route["network_required"] is True

    source = (ROOT / "server/services/phase_h_trading_status_adapters.py").read_text(encoding="utf-8").lower()
    assert all(term not in source for term in ("threshold", "attention_score", "disposition_score", "risk_score", "surveillance algorithm"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network attempted"))
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: pytest.fail("network attempted"))
    first = normalize_tpex_attention(ROWS["tpex_attention"], TARGET_TPEX, observed_at=OBSERVED, citation_id="repeat")
    second = normalize_tpex_attention(ROWS["tpex_attention"], TARGET_TPEX, observed_at=OBSERVED, citation_id="repeat")
    assert first == second
