import pytest
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_03d_f1_security_master_snapshot_exporter import canonical_json, sha256_json
import json

@pytest.fixture
def f3_mini_snapshot():
    return load_f3_verified_security_master(
        "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json",
        "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot_manifest.json",
        allow_fixture_snapshot=True
    )

@pytest.fixture
def test_catalog():
    with open("docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def input_schema():
    with open("schemas/unified_market_evidence_request.v1.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_snapshot_immutability(input_schema, test_catalog, f3_mini_snapshot):
    before_json = canonical_json(f3_mini_snapshot.snapshot)
    before_sha = sha256_json(f3_mini_snapshot.snapshot)

    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-real",
        "targets": [
            {"input": "2330", "market_hint": "TWSE"},
            {"input": "030000", "market_hint": "TWSE"},
            {"input": "9999", "market_hint": "TWSE"}
        ],
        "data_needs": [
            {"type": "official_eod_reference", "priority": "required"}
        ],
        "execution_mode": "preview"
    }

    res = validate_unified_market_evidence_request(
        req, security_master=f3_mini_snapshot,
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )

    after_json = canonical_json(f3_mini_snapshot.snapshot)
    after_sha = sha256_json(f3_mini_snapshot.snapshot)

    assert before_json == after_json
    assert before_sha == after_sha


def test_fixture_production_rejection(input_schema, test_catalog, f3_mini_snapshot):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-real",
        "targets": [
            {"input": "2330", "market_hint": "TWSE"}
        ],
        "data_needs": [
            {"type": "official_eod_reference", "priority": "required"}
        ],
        "execution_mode": "preview"
    }

    # Try resolving WITHOUT allow_fixture_snapshot
    res_rejected = validate_unified_market_evidence_request(
        req, security_master=f3_mini_snapshot,
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=False
    )

    assert res_rejected["target_results"][0]["resolution_status"] == "quarantined"

    # Try resolving WITH allow_fixture_snapshot
    res_allowed = validate_unified_market_evidence_request(
        req, security_master=f3_mini_snapshot,
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )

    assert res_allowed["target_results"][0]["resolution_status"] == "resolved"


def test_capability_status_consistency_ambiguous(input_schema, test_catalog, f3_mini_snapshot):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-amb",
        "targets": [
            {"input": "富邦特"}
        ],
        "data_needs": [
            {"type": "official_eod_reference", "priority": "required"}
        ],
        "execution_mode": "preview"
    }

    res = validate_unified_market_evidence_request(
        req, security_master=f3_mini_snapshot,
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )

    assert res["validation_status"] == "requires_clarification"
    assert res["target_validation_status"] == "requires_clarification"
    assert res["capability_results"][0]["status"] == "requires_target_resolution"
    assert res["capability_validation_status"] != "unsupported"

    for issue in res.get("blocking_issues", []):
        assert issue["reason_code"] != "REQUIRED_CAPABILITY_UNAVAILABLE"
