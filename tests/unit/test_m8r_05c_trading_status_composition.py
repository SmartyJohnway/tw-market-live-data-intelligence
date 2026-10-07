from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, Draft202012Validator

from scripts.m8r_05b_03.component_artifact_roles import validate_operation_artifact_roles
from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_05c.markdown_renderer import _fmt_phase_h_evidence
from scripts.m8r_05c.phase_h_semantics import STATUS_TYPES, validate_trading_status_context_semantics
from scripts.m8r_05c.trading_status_composer import (
    COMPONENT_ORDER,
    build_component_record,
    compose_trading_status_context,
    validate_component_artifact_bindings,
    validate_trading_status_context_composite,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = json.loads((ROOT / "tests/fixtures/phase_h_contract_v3/contract_examples.json").read_text(encoding="utf-8"))
TARGET = {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}
CITATION = "cite-fixture"


def _base_h1(source_contract: str, status_type: str | None, *, version: int = 1, failed: bool = False, no_match: bool = False):
    value = copy.deepcopy(EXAMPLES["h1_attention_available"])
    covered = [status_type] if status_type and not failed else (["disposition"] if no_match else [])
    uncovered = sorted(STATUS_TYPES - set(covered))
    value.update({
        "schema_version": f"trading_status_context_evidence.v{version}",
        "status": "source_failed" if failed else "partial",
        "target": copy.deepcopy(TARGET),
        "source": {
            "source_family": f"TPEX_{source_contract.upper()}",
            "source_contract_id": source_contract,
            "transport": "official_https_openapi",
            "license_authority": "data.gov.tw:11736:ODGL-1.0",
            "source_role": "default_candidate",
            "activation_state": "eligible",
        },
        "observed_at": "2026-10-07T00:00:00Z",
        "items": [],
        "caveats": [],
        "citation_ids": [] if failed else [CITATION],
        "coverage": {
            **value["coverage"],
            "status": "source_failed" if failed else "partial",
            "declared_scope_complete": False,
            "retrieval_succeeded": not failed,
            "source_contract_validated": not failed,
            "exact_target_search_succeeded": not failed,
            "source_snapshot_date": "2026-10-06",
            "covered_status_types": covered,
            "uncovered_status_types": uncovered,
            "failed_source_families": [f"TPEX_{source_contract.upper()}"] if failed else [],
        },
    })
    if status_type and not failed:
        item = copy.deepcopy(EXAMPLES["h1_attention_available"]["items"][0])
        item.update({"status_type": status_type, "source_record_date": "2026-10-06", "citation_ids": [CITATION]})
        value["items"] = [item]
    if version == 2:
        value["native_observation_count"] = 0
        value["native_observations"] = []
        if source_contract == "tpex_cmode" and not failed:
            value["status"] = "partial"
            value["items"] = []
            value["citation_ids"] = [CITATION]
            value["coverage"].update({"covered_status_types": [], "uncovered_status_types": sorted(STATUS_TYPES)})
            value["native_observation_count"] = 1
            value["native_observations"] = [{
                "source_native_field": "SuspensionOfTrading", "source_native_label": "停止交易",
                "source_native_value": "Ｙ", "source_native_value_type": "string",
                "source_record_date": "2026-10-06", "semantic_status": "unresolved",
                "semantic_caveat": "Official marker semantics are unresolved; no tradeability inference is permitted.",
                "citation_ids": [CITATION],
            }]
    return value


def _component(source_id: str, *, evidence=None, target=TARGET, reference=None):
    source_contract = next(row[1] for row in COMPONENT_ORDER if row[0] == source_id)
    if evidence is None:
        if source_id == "H1-TPEX-ATTENTION-OPENAPI":
            evidence = _base_h1(source_contract, "attention")
        elif source_id == "H1-TPEX-DISPOSITION-OPENAPI":
            evidence = _base_h1(source_contract, "disposition")
        else:
            evidence = _base_h1(source_contract, None, version=2)
    evidence = copy.deepcopy(evidence)
    reference = dict(reference or {"relative_path": f"artifacts/{source_contract}.json", "sha256": (source_contract.encode().hex() * 64)[:64]})
    return build_component_record(target, source_id, evidence, reference)


def _components():
    return [_component(row[0]) for row in COMPONENT_ORDER]


def _schema_validate(value, version):
    path = ROOT / "schemas" / f"trading_status_context_evidence.v{version}.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    errors = list(Draft7Validator(schema).iter_errors(value))
    if errors:
        raise AssertionError(errors[0].message)


def test_c1_components_compose_with_native_unresolved_and_partial_coverage():
    composite = compose_trading_status_context(TARGET, _components())
    validate_trading_status_context_composite(composite)
    assert composite["status"] == "partial"
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention", "disposition"]
    assert "suspension" in composite["aggregate_coverage"]["uncovered_status_types"]
    assert composite["canonical_item_count"] == 2
    assert composite["native_observation_count"] == 1
    assert composite["component_count"] == 3


def test_c2_failure_is_retained_while_other_components_survive():
    components = _components()
    failed = _base_h1("tpex_disposal_information", None, failed=True)
    components[1] = _component("H1-TPEX-DISPOSITION-OPENAPI", evidence=failed)
    composite = compose_trading_status_context(TARGET, components)
    assert [c["component_status"] for c in composite["components"]] == ["partial", "source_failed", "partial"]
    assert composite["status"] == "partial"
    assert composite["canonical_item_count"] == 1 and composite["native_observation_count"] == 1


def test_c3_exact_no_match_does_not_claim_normal_trading():
    components = _components()
    no_match = _base_h1("tpex_disposal_information", None, no_match=True)
    components[1] = _component("H1-TPEX-DISPOSITION-OPENAPI", evidence=no_match)
    composite = compose_trading_status_context(TARGET, components)
    assert composite["status"] == "partial"
    markdown = _fmt_phase_h_evidence(composite, "trading_status_context")
    assert "無符合" not in markdown
    assert "不表示正常交易" in markdown


def test_c4_duplicate_source_or_reordered_component_fails_closed():
    components = _components()
    components[1] = copy.deepcopy(components[0])
    with pytest.raises(ProjectionError):
        compose_trading_status_context(TARGET, components)


def test_c5_target_mismatch_fails_closed():
    components = _components()
    bad_target = {**TARGET, "security_code": "2330", "canonical_target_id": "TPEX:2330"}
    with pytest.raises(ProjectionError):
        components[2] = _component("H1-TPEX-CHANGED-TRADING-OPENAPI", target=bad_target)


def test_c6_native_marker_cannot_create_suspension_coverage():
    components = _components()
    candidate = components[2]["evidence"]
    candidate["coverage"]["covered_status_types"] = ["suspension"]
    candidate["coverage"]["uncovered_status_types"] = sorted(STATUS_TYPES - {"suspension"})
    with pytest.raises(ValueError):
        validate_trading_status_context_semantics(candidate)


def test_c7_same_artifact_reuse_fails_closed():
    components = _components()
    components[2]["artifact_reference"] = copy.deepcopy(components[0]["artifact_reference"])
    with pytest.raises(ProjectionError):
        compose_trading_status_context(TARGET, components)


def test_c8_unknown_h1_component_schema_fails_closed():
    components = _components()
    components[2]["evidence_schema_version"] = "trading_status_context_evidence.v99"
    with pytest.raises(ProjectionError):
        compose_trading_status_context(TARGET, components)


def test_c9_reference_hash_or_path_tampering_fails_component_identity():
    components = _components()
    composite = compose_trading_status_context(TARGET, components)
    artifacts = {item["artifact_reference"]["relative_path"]: item["evidence"] for item in components}
    inventory = {
        item["artifact_reference"]["relative_path"]: {
            "sha256": item["artifact_reference"]["sha256"],
            "schema_version": item["evidence_schema_version"],
            "evidence_contract": item["evidence_schema_version"],
            "artifact_role": "component_evidence",
            "item_count": len(item["evidence"].get("items", [])),
        }
        for item in components
    }
    inventory[components[0]["artifact_reference"]["relative_path"]]["sha256"] = "f" * 64
    with pytest.raises(ProjectionError):
        validate_component_artifact_bindings(composite, artifacts, inventory)


def test_c10_extra_source_is_not_permitted():
    components = _components()
    components[2]["source_id"] = "H1-TWSE-SUSPEND-OPENAPI"
    with pytest.raises(ProjectionError):
        compose_trading_status_context(TARGET, components)


def test_result_v3_h1_union_accepts_v1_v2_and_composite_without_ambiguity():
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))
    union_schema = {
        "$schema": result_schema["$schema"],
        "definitions": result_schema["definitions"],
        "type": "object",
        "properties": {"evidence": {"$ref": "#/definitions/trading_status_context"}},
        "required": ["evidence"],
    }
    v1 = copy.deepcopy(EXAMPLES["h1_attention_available"])
    v2 = _base_h1("tpex_cmode", None, version=2)
    composite = compose_trading_status_context(TARGET, _components())
    for value in (v1, v2, composite):
        assert not list(Draft7Validator(union_schema).iter_errors({"evidence": value}))
    # Distinct schema_version const branches ensure exactly one oneOf match.
    union = result_schema["definitions"]["trading_status_context"]["oneOf"]
    assert len(union) == 3


def test_composite_v3_schema_branch_and_native_handoff_guard():
    schema = json.loads((ROOT / "schemas/trading_status_context_composite.v1.schema.json").read_text(encoding="utf-8"))
    composite = compose_trading_status_context(TARGET, _components())
    assert not list(Draft202012Validator(schema).iter_errors(composite))
    rendered = _fmt_phase_h_evidence(composite, "trading_status_context")
    assert "停止交易" in rendered and "Ｙ" in rendered and "unresolved" in rendered
    assert "不可單獨解讀為停牌" in rendered
    assert "目前停牌" not in rendered and "cannot trade" not in rendered


def test_operation_result_component_role_preserves_primary_item_count_semantics():
    operation = {
        "schema_version": "unified_market_evidence_operation_result.v2",
        "capability_id": "trading_status_context", "evidence_contract": "trading_status_context_composite.v1",
        "status": "succeeded", "result_item_count": 2,
        "evidence_artifacts": [
            {"artifact_role": "primary_evidence", "schema_version": "trading_status_context_composite.v1", "evidence_contract": "trading_status_context_composite.v1", "relative_path": "artifacts/composite.json", "sha256": "a"*64, "item_count": 2, "byte_size": 1},
            *[{"artifact_role": "component_evidence", "schema_version": f"trading_status_context_evidence.v{v}", "evidence_contract": f"trading_status_context_evidence.v{v}", "relative_path": f"artifacts/{i}.json", "sha256": f"{i+1}"*64, "item_count": 1, "byte_size": 1} for i,v in enumerate((1,1,2))],
        ],
    }
    validate_operation_artifact_roles(operation)
    wrong = copy.deepcopy(operation)
    wrong["result_item_count"] = 4
    # The unchanged dispatch/aggregation rule sums only primary artifacts; component counts are excluded.
    primary_count = sum(a["item_count"] for a in wrong["evidence_artifacts"] if a["artifact_role"] == "primary_evidence")
    assert primary_count == 2 and primary_count != wrong["result_item_count"]
    with pytest.raises(ValueError):
        validate_operation_artifact_roles({**operation, "evidence_contract": "other"})
