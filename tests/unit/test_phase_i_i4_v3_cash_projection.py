"""Offline Unified V3 projection coverage for the I3 cash-flow contract."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, Draft7Validator

from scripts.m8r_05c.artifact_loader import _RESEARCH_EVIDENCE_CONTRACTS
from scripts.m8r_05c.evidence_projector import project_typed_research_evidence
from scripts.m8r_05c.lineage_resolver import OperationBinding, _CAPABILITY_TO_DATA_NEED, _PHASE_I_TYPED_CONTRACT_BY_DATA_NEED

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "cash_institutional_flow_context_evidence.v2"
SCHEMA_VERSION = CONTRACT


def _artifact():
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "complete",
        "market": "TWSE",
        "security_code": "1101",
        "canonical_target_id": "TWSE:1101",
        "trade_date": "2026-10-02",
        "resolved_source_trade_date": "2026-10-02",
        "source_reported_trade_date": "2026-10-02",
        "retrieved_at": "2026-10-04T12:00:00Z",
        "unit": "share",
        "citation_ids": ["cite-i3"],
    }


def _binding(artifact):
    return OperationBinding(
        operation_id="op-i3",
        capability_id="cash_institutional_flow_context",
        executor_id="phase_i_i3_cash_institutional_flow_context_executor",
        canonical_target_id="TWSE:1101",
        requested_data_need="cash_institutional_flow_context",
        market="TWSE",
        status="succeeded",
        error_code=None,
        artifact_objects={"evidence/i3.json": artifact},
        evidence_artifacts=[{"relative_path": "evidence/i3.json", "schema_version": SCHEMA_VERSION}],
    )


def test_i3_v2_contract_is_registered_and_projection_preserves_provenance():
    assert _CAPABILITY_TO_DATA_NEED["cash_institutional_flow_context"] == "cash_institutional_flow_context"
    assert _PHASE_I_TYPED_CONTRACT_BY_DATA_NEED["cash_institutional_flow_context"] == SCHEMA_VERSION
    assert _RESEARCH_EVIDENCE_CONTRACTS[SCHEMA_VERSION] == "cash_institutional_flow_context_evidence.v2.schema.json"
    projected = project_typed_research_evidence(_binding(_artifact()), ["cite-i3"], SCHEMA_VERSION)
    assert projected["resolved_source_trade_date"] == "2026-10-02"
    assert projected["source_reported_trade_date"] == "2026-10-02"
    assert projected["retrieved_at"] == "2026-10-04T12:00:00Z"


def test_i3_v2_projection_rejects_unrelated_citation_lineage():
    try:
        project_typed_research_evidence(_binding(_artifact()), ["other"], SCHEMA_VERSION)
    except Exception as exc:
        assert "citation" in str(exc)
    else:
        raise AssertionError("projection accepted citation outside operation lineage")


def test_i3_v3_result_and_audit_schemas_admit_v2_artifact_reference():
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))
    audit_schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(result_schema)
    Draft7Validator.check_schema(audit_schema)
    ref = {"capability_id": "cash_institutional_flow_context", "schema_version": SCHEMA_VERSION, "relative_path": "evidence/i3.json", "sha256": "a" * 64}
    item_schema = audit_schema["properties"]["phase_i_evidence"]["properties"]["evidence_artifact_references"]["items"]
    assert Draft7Validator(item_schema).is_valid(ref)
    assert "string" in result_schema["definitions"]["cash_institutional_flow_context"]["properties"]["resolved_source_trade_date"]["type"]
