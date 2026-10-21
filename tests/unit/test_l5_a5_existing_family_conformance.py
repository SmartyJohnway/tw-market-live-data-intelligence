"""A5 acceptance-only mutations; no production authority/fixture is modified."""
from copy import deepcopy
import socket

import pytest

from scripts.validate_l5_existing_family_conformance import (
    build_case, build_evidence, dimension_matrix, load_snapshot, read, request_probe,
    schema_errors, validate_case, validate_snapshot,
)


@pytest.fixture(scope="module")
def cases():
    return {(f, m): build_case(f, m) for f in ("monthly_revenue", "material_disclosures") for m in ("TWSE", "TPEX")}


@pytest.fixture(scope="module")
def snapshot():
    return load_snapshot()


@pytest.mark.parametrize("family,market", [
    ("monthly_revenue", "TWSE"), ("monthly_revenue", "TPEX"),
    ("material_disclosures", "TWSE"), ("material_disclosures", "TPEX"),
])
def test_existing_family_cross_market_conformance(cases, family, market):
    assert validate_case(cases[family, market]) == []


def test_owner_clarified_request_namespace_and_closed_wire_representation():
    probes = request_probe()
    assert len(probes) == 6
    assert all(p["valid"] == (p["mode"] == "type") for p in probes)
    for p in probes:
        if p["mode"] != "type":
            assert any("capability_id" in message and "Additional properties" in message for message in p["errors"])


@pytest.mark.parametrize("family", ["monthly_revenue", "material_disclosures"])
@pytest.mark.parametrize("mutation,expected", [
    ("typed_contract", "A5_TYPED_CONTRACT_DRIFT"),
    ("operation_contract", "A5_OPERATION_CONTRACT_DRIFT"),
    ("source_contract", "A5_SOURCE_CONTRACT_DRIFT"),
    ("source_authority", "A5_SOURCE_AUTHORITY_DRIFT"),
    ("capability", "A5_CAPABILITY_IDENTITY_DRIFT"),
    ("executor", "A5_EXECUTOR_IDENTITY_DRIFT"),
    ("market", "A5_ROUTE_IDENTITY_DRIFT"),
    ("target", "A5_LINEAGE_DRIFT"),
    ("operation", "A5_CITATION_DRIFT"),
    ("citation_target", "A5_CITATION_DRIFT"),
    ("citation_operation", "A5_CITATION_DRIFT"),
    ("audit_result", "A5_AUDIT_PROJECTION_DRIFT"),
    ("audit_hash", "A5_AUDIT_PROJECTION_DRIFT"),
    ("audit_lineage", "A5_LINEAGE_DRIFT"),
    ("artifact_hash", "A5_LINEAGE_DRIFT"),
    ("result_value", "A5_RESULT_PROJECTION_DRIFT"),
    ("handoff", "A5_HANDOFF_DRIFT"),
])
def test_family_identity_lineage_output_mutations_fail_closed(cases, family, mutation, expected):
    c = deepcopy(cases[family, "TWSE"])
    other = "material_disclosures" if family == "monthly_revenue" else "monthly_revenue"
    typed = c["result"]["targets"][0]["evidence"][family]
    other_case = cases[other, "TWSE"]
    if mutation == "typed_contract":
        typed["schema_version"] = other_case["result"]["targets"][0]["evidence"][other]["schema_version"]
    elif mutation == "operation_contract":
        c["operation_evidence"]["schema_version"] = other_case["operation_evidence"]["schema_version"]
    elif mutation == "source_contract":
        c["operation_evidence"]["source"]["source_contract_id"] = other_case["operation_evidence"]["source"]["source_contract_id"]
    elif mutation == "source_authority":
        c["operation_evidence"]["source"]["source_family"] = "unknown_source"
    elif mutation == "capability":
        c["operation_evidence"]["capability_id"] = other
    elif mutation == "executor":
        c["plan_operation"]["executor_id"] = "unknown_executor"
    elif mutation == "market":
        c["plan_operation"]["market"] = "TPEX"
    elif mutation == "target":
        c["operation_evidence"]["target"]["canonical_target_id"] = "TWSE:2317"
    elif mutation == "operation":
        c["plan_operation"]["operation_id"] = "other-operation"
    elif mutation == "citation_target":
        c["audit"]["citation_to_operation_map"][0]["canonical_target_id"] = "TWSE:2317"
    elif mutation == "citation_operation":
        c["audit"]["citation_to_operation_map"][0]["operation_id"] = "other-operation"
    elif mutation == "audit_result":
        c["audit"]["result_id"] = "umeresult-v3-" + "f" * 20
    elif mutation == "audit_hash":
        c["audit"]["result_hash"] = "f" * 64
    elif mutation == "audit_lineage":
        c["audit"]["operation_lineage"][0]["operation_id"] = "other-operation"
    elif mutation == "artifact_hash":
        c["artifact_reference"]["sha256"] = "f" * 64
    elif mutation == "result_value":
        if family == "monthly_revenue":
            typed["value"]["current_month_revenue"] = 999
        else:
            typed["items"][0]["subject"] = "invented"
    elif mutation == "handoff":
        c["handoff"] += "\nInvented citation and investment conclusion."
    assert expected in {e["code"] for e in validate_case(c)}


@pytest.mark.parametrize("mutation,code", [
    ("dimension", "A5_DIMENSION_UNACCOUNTED"),
    ("classification", "A5_DIMENSION_UNACCOUNTED"),
    ("dimension_proof", "A5_DIMENSION_UNACCOUNTED"),
    ("family_registry", "A5_NEW_FAMILY_DETECTED"),
    ("new_family", "A5_NEW_FAMILY_DETECTED"),
    ("seventh_tool", "A5_NEW_CAPABILITY_DETECTED"),
    ("new_capability", "A5_NEW_CAPABILITY_DETECTED"),
    ("publication", "A5_PUBLICATION_DRIFT"),
    ("retention", "A5_PLATFORM_INHERITANCE_DRIFT"),
    ("security", "A5_PLATFORM_INHERITANCE_DRIFT"),
    ("resource", "A5_PLATFORM_INHERITANCE_DRIFT"),
    ("source_contract", "A5_SOURCE_CONTRACT_DRIFT"),
    ("route", "A5_ROUTE_IDENTITY_DRIFT"),
    ("executor", "A5_EXECUTOR_IDENTITY_DRIFT"),
])
def test_acceptance_snapshot_negative_controls(snapshot, mutation, code):
    s = deepcopy(snapshot)
    if mutation == "dimension":
        s["dimensions"].pop()
    elif mutation == "classification":
        s["dimensions"][0]["A1_classification"] = "DECISION_REQUIRED"
    elif mutation == "dimension_proof":
        s["dimensions"][0].pop("exact_evidence_path_symbol")
    elif mutation == "family_registry":
        s["family_registry"] = {"fake_family_id": "runtime-owner"}
    elif mutation == "new_family":
        s["examples"].append({"capability_id": "fake-family"})
    elif mutation == "seventh_tool":
        s["tools"].append("market_extension_tool")
    elif mutation == "new_capability":
        s["catalog"]["data_need_capabilities"].append({"capability_id": "fake-capability"})
    elif mutation == "publication":
        s["publication"]["quick"] = s["publication"]["quick"].replace("| `monthly_revenue` |", "| `unknown` |")
    elif mutation in {"retention", "security", "resource"}:
        s["family_owned_policies"] = [{"family": "monthly_revenue", "owns": mutation}]
    elif mutation == "source_contract":
        s["source_routes"][0]["contract"] = "other-family-source"
    elif mutation == "route":
        next(r for r in s["routing"]["routes"] if r["capability_id"] == "monthly_revenue")["supported_markets"] = ["TWSE"]
    elif mutation == "executor":
        next(r for r in s["executor_metadata"] if r["capability_id"] == "monthly_revenue")["executor_id"] = "other"
    assert code in {e["code"] for e in validate_snapshot(s)}


def test_72_dimension_cells_keep_exact_frozen_classifications(snapshot):
    assert len(dimension_matrix()) == 72
    assert validate_snapshot(snapshot) == []
    assert {r["applicability"] for r in dimension_matrix()} == {"APPLICABLE"}


@pytest.mark.parametrize("family", ["monthly_revenue", "material_disclosures"])
def test_actual_missing_and_failure_states_remain_distinct(family):
    available = build_case(family, "TWSE")
    missing = build_case(family, "TWSE", "missing")
    failed = build_case(family, "TWSE", "source_failed")
    assert all(validate_case(c) == [] for c in (available, missing, failed))
    statuses = [c["result"]["targets"][0]["evidence"][family]["status"] for c in (available, missing, failed)]
    assert len(set(statuses)) == 3 and statuses[-1] == "source_failed"
    if family == "monthly_revenue":
        value = available["result"]["targets"][0]["evidence"][family]["value"]
        assert value["previous_month_revenue"] == -2 and value["mom_pct"] is None
        assert value["currency"] == "TWD" and value["unit"] == "thousand"
        assert missing["result"]["targets"][0]["evidence"][family]["value"] is None


def test_partial_disclosure_does_not_become_complete():
    case = build_case("material_disclosures", "TWSE", "partial")
    assert validate_case(case) == []
    typed = case["result"]["targets"][0]["evidence"]["material_disclosures"]
    assert typed["status"] == "partial" and typed["coverage"]["truncated"] is True
    assert len(typed["items"]) == 50 and "partial" in case["handoff"]


def test_stale_currentness_and_unsupported_are_distinct_existing_schema_axes(cases):
    for family, case in ((f, cases[f, "TWSE"]) for f in ("monthly_revenue", "material_disclosures")):
        typed = deepcopy(case["result"]["targets"][0]["evidence"][family])
        typed["currentness"]["status"] = "stale"
        assert typed["status"] == "available"
        assert schema_errors(typed, "schemas/" + typed["schema_version"] + ".schema.json") == []
        schema = read("schemas/" + typed["schema_version"] + ".schema.json")
        assert {"unsupported", "source_failed", "not_yet_available"} <= set(schema["properties"]["status"]["enum"])


def test_entire_validator_is_offline_and_does_not_write(monkeypatch):
    from pathlib import Path
    def forbidden(*args, **kwargs):
        raise AssertionError("provider/socket or write forbidden in acceptance validator")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    assert build_evidence()["status"] == "PASS"
