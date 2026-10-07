from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker

from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_05c.phase_h_semantics import validate_trading_status_context_semantics
from scripts.m8r_05c.trading_status_composer import (
    COMPONENT_ORDER,
    build_component_record,
    compose_trading_status_context,
    validate_trading_status_context_composite,
)
from server.services.phase_h_trading_status_adapters import (
    H1NormalizationError,
    failed_source_result,
    normalize_representative_tpex_h1_component,
    normalize_tpex_attention,
    normalize_tpex_cmode_native,
    normalize_tpex_disposition,
)

ROOT = Path(__file__).resolve().parents[2]
TARGET = {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}
OBSERVED = "2026-10-07T00:00:00Z"
CITATION = "a25-citation"


def _cmode_row(**changes):
    row = {
        "Date": "1151007",
        "SecuritiesCompanyCode": TARGET["security_code"],
        "CompanyName": "fixture company",
        "AlteredTrading": "",
        "PeriodicTrading": "",
        "ManagedStock": "",
        "MatchingFrequency": "",
        "SuspensionOfTrading": "Ｙ",
        " FinancialAnnouncements": "",
    }
    row.update(changes)
    return row


def _attention():
    source_rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))
    return normalize_tpex_attention(source_rows["tpex_attention"], TARGET, observed_at=OBSERVED, citation_id=CITATION)


def _disposition(rows=None):
    if rows is None:
        source_rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))
        rows = source_rows["tpex_disposition"]
    return normalize_tpex_disposition(rows, TARGET, observed_at=OBSERVED, citation_id=CITATION)


def _cmode(rows=None):
    return normalize_tpex_cmode_native([_cmode_row()] if rows is None else rows, TARGET, observed_at=OBSERVED, citation_id=CITATION)


def _component(source_id, evidence):
    source_contract = next(row[1] for row in COMPONENT_ORDER if row[0] == source_id)
    canonical_bytes = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    return build_component_record(
        TARGET,
        source_id,
        evidence,
        {"relative_path": f"artifacts/{source_contract}.json", "sha256": digest},
    )


def _three_components(cmode_evidence=None, disposition=None):
    return [
        _component("H1-TPEX-ATTENTION-OPENAPI", _attention()),
        _component("H1-TPEX-DISPOSITION-OPENAPI", disposition or _disposition()),
        _component("H1-TPEX-CHANGED-TRADING-OPENAPI", cmode_evidence or _cmode()),
    ]


def _validate_v2(value):
    schema = json.loads((ROOT / "schemas/trading_status_context_evidence.v2.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(value))
    validate_trading_status_context_semantics(value)


def test_a25_c1_attention_adapter_remains_h1_v1_and_deterministic():
    first = _attention()
    second = _attention()
    assert first == second
    assert first["schema_version"] == "trading_status_context_evidence.v1"
    assert first["items"][0]["status_type"] == "attention"


def test_a25_c2_c3_disposition_single_and_multiple_rows_remain_h1_v1():
    one = _disposition()
    source_rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))
    original = source_rows["tpex_disposition"][0]
    multi = _disposition([
        {**original},
        {**original, "DispositionReasons": "second row"},
    ])
    assert one["schema_version"] == multi["schema_version"] == "trading_status_context_evidence.v1"
    assert len(one["items"]) == 1 and len(multi["items"]) == 2
    assert all(item["status_type"] == "disposition" for item in multi["items"])
    assert all(item["status_lifecycle"] == "reported" for item in multi["items"])
    assert all(item["effective_from"] is None and item["effective_to"] is None for item in multi["items"])
    assert multi["items"][0]["source_native_provenance"] == original
    assert multi["items"][1]["source_native_provenance"]["DispositionReasons"] == "second row"


def test_a25_c4_c5_c16_cmode_y_is_exact_native_evidence_with_zero_coverage():
    value = _cmode()
    observation = value["native_observations"][0]
    _validate_v2(value)
    assert value["schema_version"] == "trading_status_context_evidence.v2"
    assert value["items"] == [] and value["native_observation_count"] == 1
    assert value["coverage"]["covered_status_types"] == []
    assert observation["source_native_value"] == "Ｙ"
    assert [f"U+{ord(char):04X}" for char in observation["source_native_value"]] == ["U+FF39"]
    assert observation["source_native_value"].encode("utf-8").hex() == "efbcb9"
    assert observation["semantic_status"] == "unresolved"
    assert observation["source_native_field"] == "SuspensionOfTrading"
    assert "suspension" not in value["coverage"]["covered_status_types"]
    assert any("source_native_provenance:Date=1151007" == caveat for caveat in value["caveats"])


def test_a25_c6_blank_marker_is_preserved_as_unresolved_not_negative():
    value = _cmode([_cmode_row(SuspensionOfTrading="")])
    observation = value["native_observations"][0]
    _validate_v2(value)
    assert observation["source_native_value"] == ""
    assert observation["source_native_value_type"] == "string"
    assert observation["semantic_status"] == "unresolved"
    assert "do not infer not suspended, normal trading, or tradeability" in observation["semantic_caveat"]


def test_a25_c7_c15_cmode_exact_no_match_is_successful_partial_and_composable():
    value = _cmode([_cmode_row(SecuritiesCompanyCode="9999")])
    _validate_v2(value)
    assert value["status"] == "partial"
    assert value["items"] == [] and value["native_observations"] == []
    assert value["native_observation_count"] == 0
    assert value["coverage"]["retrieval_succeeded"] is True
    assert value["coverage"]["source_contract_validated"] is True
    assert value["coverage"]["exact_target_search_succeeded"] is True
    assert value["coverage"]["covered_status_types"] == []
    assert any(caveat.startswith("cmode_exact_no_match:") for caveat in value["caveats"])
    composite = compose_trading_status_context(TARGET, _three_components(cmode_evidence=value))
    validate_trading_status_context_composite(composite)
    assert composite["status"] == "partial"
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention", "disposition"]


def test_cmode_accepts_calendar_valid_canonical_iso_date_without_changing_generic_parser():
    value = _cmode([_cmode_row(Date="2026-10-07")])
    observation = value["native_observations"][0]
    _validate_v2(value)
    assert observation["source_record_date"] == "2026-10-07"
    assert "source_native_provenance:Date=2026-10-07" in value["caveats"]


def test_a25_c8_cmode_duplicate_exact_rows_fail_closed():
    with pytest.raises(H1NormalizationError, match="ambiguous_exact_target_rows"):
        _cmode([_cmode_row(), _cmode_row(PeriodicTrading="different")])


def test_a25_c9_invalid_roc_calendar_date_fails_closed():
    with pytest.raises(H1NormalizationError, match="invalid_source_snapshot_date_calendar"):
        _cmode([_cmode_row(Date="1150230")])


@pytest.mark.parametrize("field,value", [("MatchingFrequency", []), ("SuspensionOfTrading", True), (" FinancialAnnouncements", 1)])
def test_a25_c10_unsafe_required_field_type_fails_closed(field, value):
    with pytest.raises(H1NormalizationError, match="invalid_required_field_type"):
        _cmode([_cmode_row(**{field: value})])


def test_a25_c11_unknown_marker_is_preserved_exactly_and_unresolved():
    marker = "?未定"
    value = _cmode([_cmode_row(SuspensionOfTrading=marker)])
    observation = value["native_observations"][0]
    _validate_v2(value)
    assert observation["source_native_value"] == marker
    assert observation["semantic_status"] == "unresolved"


def test_a25_c12_unknown_representative_source_fails_closed():
    with pytest.raises(H1NormalizationError, match="unapproved_representative_source"):
        normalize_representative_tpex_h1_component("H1-TPEX-UNKNOWN-OPENAPI", [], TARGET, observed_at=OBSERVED, citation_id=CITATION)


def test_a25_c13_component_records_have_deterministic_identities():
    first = _three_components()
    second = _three_components()
    assert [item["component_id"] for item in first] == [item["component_id"] for item in second]
    assert [item["source_id"] for item in first] == [
        "H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI"
    ]
    assert [item["evidence_schema_version"] for item in first] == [
        "trading_status_context_evidence.v1", "trading_status_context_evidence.v1", "trading_status_context_evidence.v2"
    ]


def test_a25_c14_representative_composite_keeps_cmode_native_only():
    composite = compose_trading_status_context(TARGET, _three_components())
    validate_trading_status_context_composite(composite)
    assert composite["schema_version"] == "trading_status_context_composite.v1"
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention", "disposition"]
    assert {"changed_trading_method", "suspension", "resumption"}.issubset(composite["aggregate_coverage"]["uncovered_status_types"])
    assert composite["status"] == "partial"
    assert composite["native_observation_count"] == 1


def test_a25_c17_embedded_source_identity_mismatch_fails_closed():
    evidence = _attention()
    evidence["source"]["source_family"] = "TPEX_WRONG_OPEN_DATA"
    with pytest.raises(ProjectionError, match="composite_component_source_identity_mismatch"):
        _component("H1-TPEX-ATTENTION-OPENAPI", evidence)


def _failed_cmode():
    value = _cmode()
    value["status"] = "source_failed"
    value["coverage"].update({
        "status": "source_failed", "retrieval_succeeded": False,
        "source_contract_validated": False, "exact_target_search_succeeded": False,
        "failed_source_families": ["TPEX_CHANGED_TRADING_OPEN_DATA"],
    })
    value["native_observation_count"] = 0
    value["native_observations"] = []
    value["caveats"] = ["fixture_source_failed"]
    _validate_v2(value)
    return value


def test_a25_c18_failure_independence_preserves_all_component_outcomes():
    components = _three_components(cmode_evidence=_failed_cmode())
    composite = compose_trading_status_context(TARGET, components)
    assert [item["component_status"] for item in composite["components"]] == ["partial", "partial", "source_failed"]
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention", "disposition"]
    assert composite["status"] == "partial"

    disposition_failed = failed_source_result(
        "H1-TPEX-DISPOSITION-OPENAPI", TARGET, observed_at=OBSERVED,
        diagnostic="fixture source failure", citation_id=CITATION,
    )
    components = _three_components(disposition=disposition_failed)
    composite = compose_trading_status_context(TARGET, components)
    assert [item["component_status"] for item in composite["components"]] == ["partial", "source_failed", "partial"]
    assert composite["canonical_item_count"] == 1
    assert composite["native_observation_count"] == 1


def test_representative_dispatch_maps_each_frozen_source_explicitly():
    attention_rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))["tpex_attention"]
    disposition_rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))["tpex_disposition"]
    outputs = [
        normalize_representative_tpex_h1_component("H1-TPEX-ATTENTION-OPENAPI", attention_rows, TARGET, observed_at=OBSERVED, citation_id=CITATION),
        normalize_representative_tpex_h1_component("H1-TPEX-DISPOSITION-OPENAPI", disposition_rows, TARGET, observed_at=OBSERVED, citation_id=CITATION),
        normalize_representative_tpex_h1_component("H1-TPEX-CHANGED-TRADING-OPENAPI", [_cmode_row()], TARGET, observed_at=OBSERVED, citation_id=CITATION),
    ]
    assert [item["schema_version"] for item in outputs] == [
        "trading_status_context_evidence.v1", "trading_status_context_evidence.v1", "trading_status_context_evidence.v2"
    ]
    assert all(item["target"] == TARGET for item in outputs)
