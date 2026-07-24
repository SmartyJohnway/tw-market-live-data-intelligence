from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from tests.unit.m8r_05b_03_test_helpers import ROOT, build_valid_preflight


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
