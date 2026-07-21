import pytest
import jsonschema
import json
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master

@pytest.fixture
def test_catalog():
    with open("docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def input_schema():
    with open("schemas/unified_market_evidence_request.v1.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def output_schema():
    with open("schemas/unified_market_evidence_request_validation.v1.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def f3_mini_snapshot():
    return load_f3_verified_security_master(
        "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json",
        "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot_manifest.json",
        allow_fixture_snapshot=True
    )

def test_f3_integration_with_strict_loader(input_schema, output_schema, test_catalog, f3_mini_snapshot):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-real",
        "targets": [
            {"input": "2330", "market_hint": "TWSE"}, # TWSE common_share
            {"input": "5347", "market_hint": "TPEX"}, # TPEX common_share
            {"input": "TW0002330008"}, # ISIN exact match
            {"input": "台積電", "market_hint": "TWSE"}, # Exact name
            {"input": "030000", "market_hint": "TWSE"}, # unsupported instrument
            {"input": "9999", "market_hint": "TWSE"} # quarantined/conflicted
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

    jsonschema.validate(instance=res, schema=output_schema)

    # 2 duplicate TWSE targets in the list makes validation_status invalid, plus the unsupported/quarantined ones.
    assert res["validation_status"] == "invalid"

    # Check 0: 2330 code -> TWSE
    assert res["target_results"][0]["resolution_status"] == "resolved"
    assert res["target_results"][0]["canonical_identity"]["security_code"] == "2330"

    # Check 1: 5347 -> TPEX
    assert res["target_results"][1]["resolution_status"] == "resolved"
    assert res["target_results"][1]["canonical_identity"]["market"] == "TPEX"

    # Check 2: ISIN TW0002330008 -> duplicate of 0
    assert res["target_results"][2]["resolution_status"] == "duplicate"

    # Check 3: name 台積電 -> duplicate of 0
    assert res["target_results"][3]["resolution_status"] == "duplicate"

    # Check 4: 030000 warrant -> execution_eligibility is blocked
    assert res["target_results"][4]["resolution_status"] == "unsupported_security_type"

    # Check 5: 9999 -> quarantined
    assert res["target_results"][5]["resolution_status"] == "quarantined"

def test_f3_integration_ambiguous_case(input_schema, output_schema, test_catalog, f3_mini_snapshot):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-real-ambiguous",
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

    jsonschema.validate(instance=res, schema=output_schema)
    assert res["validation_status"] == "requires_clarification"
    assert res["target_results"][0]["resolution_status"] == "ambiguous"
    assert len(res["target_results"][0]["candidate_matches"]) == 2
