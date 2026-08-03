from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from scripts.m8r_05b_03.consumption_claim import build_claim_record
from tests.unit.m8r_05b_03_test_helpers import CLAIM_TIMESTAMP, ROOT, artifacts, build_valid_preflight, registry_metadata


def test_preflight_schema_accepts_valid_artifact(tmp_path):
    schema = json.loads((ROOT / "schemas/unified_market_evidence_orchestrator_preflight.v1.schema.json").read_text())
    artifact = build_valid_preflight(tmp_path)
    assert not list(Draft202012Validator(schema).iter_errors(artifact))


def test_execution_request_schema_accepts_valid_projection(tmp_path):
    schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_request.v1.schema.json").read_text())
    request = build_valid_preflight(tmp_path)["bounded_execution_requests"][0]
    assert not list(Draft202012Validator(schema).iter_errors(request))


def test_schemas_reject_invalid_payloads(tmp_path):
    preflight_schema = json.loads((ROOT / "schemas/unified_market_evidence_orchestrator_preflight.v1.schema.json").read_text())
    request_schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_request.v1.schema.json").read_text())
    artifact = build_valid_preflight(tmp_path)
    artifact["ready_for_claim"] = False
    request = dict(artifact["bounded_execution_requests"][0])
    request["maximum_records"] = 0
    assert list(Draft202012Validator(preflight_schema).iter_errors(artifact))
    assert list(Draft202012Validator(request_schema).iter_errors(request))


def test_registry_metadata_schema_accepts_valid_and_rejects_string_integer():
    schema = json.loads((ROOT / "schemas/unified_market_evidence_executor_registry_metadata.v1.schema.json").read_text())
    valid = registry_metadata()
    assert not list(Draft202012Validator(schema).iter_errors(valid))
    valid["executors"][0]["timeout_seconds"] = "15"
    assert list(Draft202012Validator(schema).iter_errors(valid))


def test_consumption_record_schema_accepts_claimed_record(tmp_path):
    schema = json.loads((ROOT / "schemas/unified_market_evidence_consumption_record.v1.schema.json").read_text())
    _plan, _authorization, _binding, state = artifacts()
    record = build_claim_record(
        build_valid_preflight(tmp_path),
        state,
        claim_created_at=CLAIM_TIMESTAMP,
    )
    assert not list(Draft202012Validator(schema).iter_errors(record))
    record["state"] = "unknown"
    assert list(Draft202012Validator(schema).iter_errors(record))
