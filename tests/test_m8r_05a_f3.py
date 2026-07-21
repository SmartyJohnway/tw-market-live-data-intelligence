import json
import pytest
import jsonschema
import copy
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
from scripts.m8r_03d_f1_security_master_snapshot_adapter import ValidatedVerifiedSecurityMasterSnapshot, build_verified_security_master_lookup

@pytest.fixture
def input_schema():
    with open("schemas/unified_market_evidence_request.v1.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def output_schema():
    with open("schemas/unified_market_evidence_request_validation.v1.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def test_catalog():
    with open("docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def test_security_master():
    # Use a small controlled fixture for targeted behavior tests
    records = [
        {
            "canonical_target_id": "TWSE:2330",
            "identity": {"security_code": "2330", "security_name_zh": "台積電"},
            "classification": {"market": "TWSE", "instrument_type": "equity"},
            "lifecycle": {}
        },
        {
            "canonical_target_id": "TPEX:5347",
            "identity": {"security_code": "5347", "security_name_zh": "世界"},
            "classification": {"market": "TPEX", "instrument_type": "equity"},
            "lifecycle": {}
        },
        {
            "canonical_target_id": "TWSE:0050",
            "identity": {"security_code": "0050", "security_name_zh": "元大台灣50"},
            "classification": {"market": "TWSE", "instrument_type": "etf"},
            "lifecycle": {}
        },
        {
            "canonical_target_id": "TWSE:030000",
            "identity": {"security_code": "030000", "security_name_zh": "權證A"},
            "classification": {"market": "TWSE", "instrument_type": "warrant"},
            "lifecycle": {}
        }
    ]
    snapshot = {"records": records}
    lookup = build_verified_security_master_lookup(snapshot)
    return ValidatedVerifiedSecurityMasterSnapshot(
        snapshot=snapshot,
        manifest={},
        lookup=lookup,
        validation={}
    )
    
@pytest.fixture
def real_security_master():
    return load_f3_verified_security_master(
        "tests/fixtures/m8r_03e_r5a/security_identity_snapshot.json",
        "tests/fixtures/m8r_03e_r5a/security_identity_snapshot_manifest.json",
        allow_fixture_snapshot=True
    )

def validate_res_against_output_schema(res, schema):
    jsonschema.validate(instance=res, schema=schema)

def test_valid_request(input_schema, output_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-1",
        "targets": [
            {"input": "2330", "market_hint": "TWSE", "resolution_requirement": "exact"}
        ],
        "data_needs": [
            {"type": "official_eod_reference", "priority": "required"}
        ],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=test_security_master, 
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    validate_res_against_output_schema(res, output_schema)
    assert res["validation_status"] == "valid"
    assert res["target_results"][0]["resolution_status"] == "resolved"
    assert res["target_results"][0]["canonical_identity"]["market"] == "TWSE"
    # test capability status properly mapped to catalog status (e.g., runtime_executable)
    assert res["capability_results"][0]["status"] == "runtime_executable"

def test_unsupported_security_type(input_schema, output_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-2",
        "targets": [
            {"input": "030000", "resolution_requirement": "exact"}
        ],
        "data_needs": [{"type": "official_eod_reference", "priority": "required"}],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=test_security_master, 
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    validate_res_against_output_schema(res, output_schema)
    assert res["validation_status"] == "invalid"
    assert res["target_results"][0]["resolution_status"] == "unsupported_security_type"
    assert "canonical_identity" not in res["target_results"][0]

def test_duplicate_targets(input_schema, output_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-3",
        "targets": [
            {"input": "2330"},
            {"input": "台積電"} # Resolves to the exact same target
        ],
        "data_needs": [{"type": "official_eod_reference", "priority": "required"}],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=test_security_master, 
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    validate_res_against_output_schema(res, output_schema)
    assert res["validation_status"] == "invalid"
    assert res["target_results"][0]["resolution_status"] == "resolved"
    assert res["target_results"][1]["resolution_status"] == "duplicate"
    
def test_target_limit_exceeded(input_schema, output_schema, test_catalog, test_security_master):
    # Modify catalog to have a small limit
    catalog = copy.deepcopy(test_catalog)
    catalog["bounds"]["hard_target_limit"] = 1
    
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-limit",
        "targets": [{"input": "2330"}, {"input": "5347"}],
        "data_needs": [{"type": "official_eod_reference", "priority": "required"}],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=test_security_master, 
        capability_catalog=catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    validate_res_against_output_schema(res, output_schema)
    assert res["validation_status"] == "invalid"
    assert any(b["reason_code"] == "TARGET_LIMIT_EXCEEDED" for b in res["blocking_issues"])

def test_invalid_schema(input_schema, output_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-bad-schema",
        "targets": [] # empty array is invalid by schema
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=test_security_master, 
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    validate_res_against_output_schema(res, output_schema)
    assert res["validation_status"] == "invalid"
    assert res["blocking_issues"][0]["reason_code"] == "REQUEST_SCHEMA_INVALID"

def test_ambiguous_resolution_and_stable_ordering(input_schema, output_schema, test_catalog):
    records = [
        {
            "canonical_target_id": "TWSE:2330",
            "identity": {"security_code": "2330", "security_name_zh": "台積電"},
            "classification": {"market": "TWSE", "instrument_type": "equity"},
            "lifecycle": {}
        },
        {
            "canonical_target_id": "TPEX:2330",
            "identity": {"security_code": "2330", "security_name_zh": "台積電"},
            "classification": {"market": "TPEX", "instrument_type": "equity"},
            "lifecycle": {}
        }
    ]
    snapshot = {"records": records}
    lookup = build_verified_security_master_lookup(snapshot)
    ambiguous_master = ValidatedVerifiedSecurityMasterSnapshot(
        snapshot=snapshot, manifest={}, lookup=lookup, validation={}
    )
    
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-amb",
        "targets": [{"input": "2330"}],
        "data_needs": [{"type": "official_eod_reference", "priority": "required"}],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=ambiguous_master, 
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    validate_res_against_output_schema(res, output_schema)
    assert res["validation_status"] == "requires_clarification"
    assert res["target_results"][0]["resolution_status"] == "ambiguous"
    
    # Check stable ordering (TPEX comes before TWSE alphabetically)
    matches = res["target_results"][0]["candidate_matches"]
    assert matches[0]["market"] == "TPEX"
    assert matches[1]["market"] == "TWSE"

def test_requires_target_resolution_blocks_capability(input_schema, output_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-unresolved",
        "targets": [{"input": "9999"}], # Not found
        "data_needs": [{"type": "official_eod_reference", "priority": "required"}],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=test_security_master, 
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    validate_res_against_output_schema(res, output_schema)
    # The required target failed to resolve -> Invalid overall.
    assert res["validation_status"] == "invalid"
    assert res["target_results"][0]["resolution_status"] == "not_found"
    # But specifically, the capability requires resolution and should report so
    assert res["capability_results"][0]["status"] == "requires_target_resolution"

def test_deepcopy_isolation(input_schema, output_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-mut",
        "targets": [{"input": "2330"}],
        "data_needs": [{"type": "official_eod_reference", "priority": "required"}],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=test_security_master, 
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    # Mutate original request
    req["targets"][0]["input"] = "MUTATED"
    
    # The normalized request should remain isolated
    assert res["normalized_request"]["targets"][0]["input"] == "2330"

def test_integration_real_security_master(input_schema, output_schema, test_catalog, real_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-real",
        "targets": [
            {"input": "2330", "market_hint": "TWSE"},
            {"input": "6488", "market_hint": "TPEX"}
        ],
        "data_needs": [
            {"type": "official_eod_reference", "priority": "required"}
        ],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, security_master=real_security_master, 
        capability_catalog=test_catalog, request_schema=input_schema,
        allow_fixture_snapshot=True
    )
    
    validate_res_against_output_schema(res, output_schema)
    assert res["validation_status"] == "valid"
    assert len(res["target_results"]) == 2
    assert res["target_results"][0]["resolution_status"] == "resolved"
    assert res["target_results"][1]["resolution_status"] == "resolved"
