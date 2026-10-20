"""Fail-closed tests for the exact A4 I2 publication compatibility projection."""
import copy
import json
import subprocess
from pathlib import Path

import pytest
from scripts import phase_i_i3_a4_compat as compat


@pytest.fixture(params=[compat.A4_CATALOG_PATH, compat.A4_ROUTING_PATH])
def authority(request):
    path = request.param
    entry = json.loads(subprocess.check_output(
        ["git", "show", f"{compat.L5_A4_ENTRY}:{path}"], cwd=compat.ROOT
    ).decode("utf-8"))
    current = copy.deepcopy(entry)
    key = "data_need_capabilities" if path == compat.A4_CATALOG_PATH else "routes"
    row = next(x for x in current[key] if x["capability_id"] == compat.A4_I2_CAPABILITY)
    if path == compat.A4_CATALOG_PATH:
        row["description"] = compat.A4_CATALOG_DESCRIPTION
        row["known_limitations"] = compat._replace_one(
            row["known_limitations"], compat.A4_CATALOG_LIMITATION_OLD,
            compat.A4_CATALOG_LIMITATION_NEW, "test.catalog")
    else:
        row["capability_status_source"] = compat.A4_ROUTING_STATUS_SOURCE
        row["known_limitations"] = compat._replace_one(
            row["known_limitations"], compat.A4_ROUTING_LIMITATION_OLD,
            compat.A4_ROUTING_LIMITATION_NEW, "test.routing")
    return path, entry, current



def row_for(doc, path, capability=compat.A4_I2_CAPABILITY):
    key = "data_need_capabilities" if path == compat.A4_CATALOG_PATH else "routes"
    return next(x for x in doc[key] if x["capability_id"] == capability)


def catalog_authority_data():
    path = compat.A4_CATALOG_PATH
    entry = json.loads(subprocess.check_output(["git", "show", f"{compat.L5_A4_ENTRY}:{path}"], cwd=compat.ROOT).decode())
    current = copy.deepcopy(entry); row = row_for(current, path)
    row["description"] = compat.A4_CATALOG_DESCRIPTION
    row["known_limitations"] = compat._replace_one(row["known_limitations"], compat.A4_CATALOG_LIMITATION_OLD, compat.A4_CATALOG_LIMITATION_NEW, "test.catalog")
    return path, entry, current


def routing_authority_data():
    path = compat.A4_ROUTING_PATH
    entry = json.loads(subprocess.check_output(["git", "show", f"{compat.L5_A4_ENTRY}:{path}"], cwd=compat.ROOT).decode())
    current = copy.deepcopy(entry); row = row_for(current, path)
    row["capability_status_source"] = compat.A4_ROUTING_STATUS_SOURCE
    row["known_limitations"] = compat._replace_one(row["known_limitations"], compat.A4_ROUTING_LIMITATION_OLD, compat.A4_ROUTING_LIMITATION_NEW, "test.routing")
    return path, entry, current


@pytest.fixture
def catalog_authority(): return catalog_authority_data()


@pytest.fixture
def routing_authority(): return routing_authority_data()

def test_exact_authorized_delta_projects_only_for_historical_comparison(authority):
    path, entry, current = authority
    projected = compat.project_l5_a4_publication_reconciliation(path, current, entry)
    assert projected == entry
    assert current != projected  # current publication remains untouched


@pytest.mark.parametrize("field,value", [
    ("support_status", "contract_supported"),
    ("runtime_executable", False),
    ("supported_markets", ["TPEX"]),
])
def test_catalog_functional_drift_fails_closed(catalog_authority, field, value):
    path, entry, current = catalog_authority
    row_for(current, path)[field] = value
    with pytest.raises(AssertionError, match="l5_a4_publication_delta_out_of_scope"):
        compat.project_l5_a4_publication_reconciliation(path, current, entry)


@pytest.mark.parametrize("field,value", [
    ("routing_status", "blocked"),
    ("runtime_executable", False),
    ("selected_executor_id", None),
    ("output_evidence_contract", "other.v1"),
    ("candidate_executor_ids", []),
    ("network_required", False),
    ("parameter_mapping", {"unexpected": "value"}),
])
def test_routing_functional_drift_fails_closed(routing_authority, field, value):
    path, entry, current = routing_authority
    row_for(current, path)[field] = value
    with pytest.raises(AssertionError, match="l5_a4_publication_delta_out_of_scope"):
        compat.project_l5_a4_publication_reconciliation(path, current, entry)


@pytest.mark.parametrize("authority", ["catalog", "routing"])
def test_unapproved_i2_prose_fails_closed(authority):
    path, entry, current = (catalog_authority_data() if authority == "catalog" else routing_authority_data())
    row = row_for(current, path)
    if authority == "catalog":
        row["description"] += " Extra unapproved prose."
    else:
        row["known_limitations"].append("unexpected prose")
    with pytest.raises(AssertionError, match="l5_a4_publication_delta_out_of_scope"):
        compat.project_l5_a4_publication_reconciliation(path, current, entry)


def test_other_capability_is_not_projected_and_historical_comparison_rejects(authority):
    path, entry, current = authority
    key = "data_need_capabilities" if path == compat.A4_CATALOG_PATH else "routes"
    other = next(x for x in current[key] if x["capability_id"] != compat.A4_I2_CAPABILITY)
    other["known_limitations"] = list(other.get("known_limitations", [])) + ["unauthorized change"]
    projected = compat.project_l5_a4_publication_reconciliation(path, current, entry)
    projected_other = next(x for x in projected[key] if x["capability_id"] == other["capability_id"])
    assert "unauthorized change" in projected_other["known_limitations"]
    with pytest.raises(AssertionError, match="non_i3_production_authority_drift"):
        compat.assert_projected_authority_matches_historical(projected, entry, path)


def test_unrelated_authority_is_never_projected():
    sentinel = {"arbitrary": "mutation"}
    assert compat.project_l5_a4_publication_reconciliation("other.json", sentinel, {}) is sentinel


def test_a4_entry_is_pinned_not_remote_main():
    assert compat.L5_A4_ENTRY == "91458d203ac28fe4ab00c89229ed1320bcb64753"
