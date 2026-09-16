"""A1 frozen-contract installation and dormant resolution acceptance."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from server.services.unified_contract_versions import (
    UnsupportedRequestSchemaVersion,
    resolve_request_schema,
)
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master


ROOT = Path(__file__).resolve().parents[2]
FROZEN = Path(r"D:\Codex-Workspace\docs\tw-market-live-data-intelligence\10_Phase_G_Authority\Phase_G_V2_Exact_Schema_Contract_FROZEN")
SCHEMAS = (
    "unified_market_evidence_request.v2.schema.json",
    "unified_market_evidence_result.v2.schema.json",
    "unified_market_evidence_audit_package.v2.schema.json",
    "material_disclosure_evidence.v1.schema.json",
    "monthly_revenue_evidence.v1.schema.json",
    "unified_market_evidence_capability_catalog.v2.schema.json",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def v2_request() -> dict:
    return load_json(FROZEN / "example_unified_market_evidence_request.v2.json")


def v2_catalog() -> dict:
    return load_json(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v2.json")


def fixture_security_master():
    fixture = ROOT / "tests/fixtures/m8r_05a_f3"
    return load_f3_verified_security_master(
        fixture / "verified_security_master_snapshot.json",
        fixture / "verified_security_master_snapshot_manifest.json",
        allow_fixture_snapshot=True,
    )


def test_a1_frozen_assets_are_exact_bytes_and_meta_valid():
    manifest = load_json(FROZEN / "SCHEMA_FREEZE_MANIFEST.json")
    for name in SCHEMAS:
        installed = ROOT / "schemas" / name
        assert hashlib.sha256(installed.read_bytes()).hexdigest() == manifest["files"][name]["sha256"]
        jsonschema.Draft7Validator.check_schema(load_json(installed))
    catalog = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v2.json"
    assert hashlib.sha256(catalog.read_bytes()).hexdigest() == manifest["files"][catalog.name]["sha256"]
    catalog_schema = load_json(ROOT / "schemas/unified_market_evidence_capability_catalog.v2.schema.json")
    jsonschema.validate(v2_catalog(), catalog_schema)


def test_a1_frozen_examples_validate():
    examples = {
        "example_unified_market_evidence_request.v2.json": "unified_market_evidence_request.v2.schema.json",
        "example_material_disclosure_evidence.v1.json": "material_disclosure_evidence.v1.schema.json",
        "example_monthly_revenue_evidence.v1.json": "monthly_revenue_evidence.v1.schema.json",
        "example_unified_market_evidence_result.v2.json": "unified_market_evidence_result.v2.schema.json",
    }
    for example, schema in examples.items():
        jsonschema.validate(load_json(FROZEN / example), load_json(ROOT / "schemas" / schema))


def test_a01_a02_a05_version_resolution_is_deterministic_and_v1_remains_valid():
    v1 = {
        "schema_version": "unified_market_evidence_request.v1", "request_id": "v1",
        "execution_mode": "preview", "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": [{"type": "identity", "priority": "required"}],
    }
    assert resolve_request_schema(v1)["properties"]["schema_version"]["const"].endswith("v1")
    assert resolve_request_schema(v2_request())["properties"]["schema_version"]["const"].endswith("v2")
    jsonschema.validate(v1, resolve_request_schema(v1))
    jsonschema.validate(v2_request(), resolve_request_schema(v2_request()))
    with pytest.raises(UnsupportedRequestSchemaVersion, match="unsupported_request_schema_version"):
        resolve_request_schema({"schema_version": "unified_market_evidence_request.v999"})


@pytest.mark.parametrize("capability, parameter", [
    ("material_disclosures", "lookback_days"),
    ("material_disclosures", "date_range"),
    ("material_disclosures", "history"),
    ("monthly_revenue", "months"),
    ("monthly_revenue", "start_date"),
    ("monthly_revenue", "end_date"),
    ("monthly_revenue", "history"),
])
def test_a03_a04_research_parameters_fail_closed(capability, parameter):
    request = v2_request()
    request["data_needs"] = [{"type": capability, "priority": "required", "parameters": {parameter: 1}}]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(request, resolve_request_schema(request))


def test_a12_financial_summary_is_not_initial_v2_vocabulary():
    request = v2_request()
    request["data_needs"] = [{"type": "financial_summary", "priority": "optional"}]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(request, resolve_request_schema(request))


def test_v2_catalog_validation_accepts_empty_research_parameters_without_runtime_activation():
    request = v2_request()
    result = validate_unified_market_evidence_request(
        request, security_master=fixture_security_master(), capability_catalog=v2_catalog(),
        request_schema=resolve_request_schema(request), allow_fixture_snapshot=True,
    )
    assert result["validation_status"] == "valid"
    assert [item["capability_id"] for item in result["capability_results"]] == ["current_observation", "material_disclosures", "monthly_revenue"]


def test_frozen_negative_evidence_invariants():
    material = load_json(FROZEN / "example_material_disclosure_evidence.v1.json")
    material["status"] = "no_evidence_in_covered_scope"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(material, load_json(ROOT / "schemas/material_disclosure_evidence.v1.schema.json"))
    revenue = load_json(FROZEN / "example_monthly_revenue_evidence.v1.json")
    revenue["value"]["currency"] = "USD"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(revenue, load_json(ROOT / "schemas/monthly_revenue_evidence.v1.schema.json"))
    result = load_json(FROZEN / "example_unified_market_evidence_result.v2.json")
    result["targets"][0]["resolution"]["resolution_status"] = "not_found"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, load_json(ROOT / "schemas/unified_market_evidence_result.v2.schema.json"))
