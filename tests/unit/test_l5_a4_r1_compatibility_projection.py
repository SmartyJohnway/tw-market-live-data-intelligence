"""Fail-closed tests for the exact A4 I2 publication compatibility projection."""
import copy
import json
import subprocess
from pathlib import Path

import pytest
from scripts import phase_i_i3_a4_compat as compat
from scripts import s4_catalog_compat as s4


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


# S4-R1 micro-tests remain compatibility-only focused coverage. Current profiles
# already exercise both integration guards through the five formerly failing nodes.
def session(document):
    return next(row for row in document["data_need_capabilities"]
                if row["capability_id"] == "session_status")


@pytest.fixture
def s4_pair():
    current = json.loads((compat.ROOT / s4.CATALOG).read_text(encoding="utf-8"))
    entry = json.loads(subprocess.check_output(
        ["git", "show", f"{compat.L5_A4_ENTRY}:{s4.CATALOG}"], cwd=compat.ROOT))
    historical = copy.deepcopy(current)
    historical["known_limitations"][4:6] = entry["known_limitations"][4:6]
    session(historical)["description"] = session(entry)["description"]
    return current, historical


def test_s4_exact_three_leaves_restore_historical_form_without_mutating_inputs(s4_pair):
    current, historical = s4_pair
    saved = copy.deepcopy(s4_pair)
    projected = s4.project_s4_catalog(s4.CATALOG, current, historical)
    assert projected == historical and projected is not current
    assert s4_pair == saved
    # Reversing the exact historical view also reproduces the actual candidate.
    assert s4.s4_expected_catalog(historical) == current
    assert sum(a != b for a, b in zip(current["known_limitations"],
                                     projected["known_limitations"])) == 2
    assert session(projected)["description"] != session(current)["description"]


@pytest.mark.parametrize("field,value", [
    ("support_status", "contract_supported"),
    ("supported_markets", ["TWSE"]),
    ("known_limitations", ["unauthorized adjacent limitation"]),
])
def test_s4_adjacent_session_drift_survives_projection_and_fails_i2_guard(s4_pair, monkeypatch, field, value):
    from scripts import phase_i_i2_a4_proof as proof
    current, historical = s4_pair
    session(current)[field] = value
    projected = s4.project_s4_catalog(s4.CATALOG, current, historical)
    assert session(projected)[field] == value
    with pytest.raises(AssertionError, match="non_i3_production_authority_drift"):
        compat.assert_projected_authority_matches_historical(projected, historical, s4.CATALOG)
    read_current = proof.current_json
    monkeypatch.setattr(proof, "current_json", lambda path: current if path == s4.CATALOG else read_current(path))
    with pytest.raises(AssertionError, match=s4.CATALOG):
        proof.verify_candidate_authority()


def test_s4_other_top_level_limitation_survives_and_fails_historical_comparison(s4_pair):
    current, historical = s4_pair
    current["known_limitations"][6] += " unauthorized"
    projected = s4.project_s4_catalog(s4.CATALOG, current, historical)
    assert projected["known_limitations"][6] == current["known_limitations"][6]
    with pytest.raises(AssertionError, match="non_i3_production_authority_drift"):
        compat.assert_projected_authority_matches_historical(projected, historical, s4.CATALOG)


@pytest.mark.parametrize("leaf", ["h1", "h2", "session"])
def test_s4_modified_successor_fails_closed(s4_pair, leaf):
    current, historical = s4_pair
    if leaf == "session":
        session(current)["description"] += " unauthorized"
    else:
        current["known_limitations"][4 if leaf == "h1" else 5] += " unauthorized"
    with pytest.raises(ValueError, match="S4 successor mismatch"):
        s4.project_s4_catalog(s4.CATALOG, current, historical)


@pytest.mark.parametrize("side", ["current", "historical"])
@pytest.mark.parametrize("mutation", [
    "missing_session", "duplicate_session", "missing_description", "missing_limitations",
    "short_limitations", "duplicate_limit", "wrong_position", "wrong_value", "mixed_old_new",
])
def test_s4_malformed_or_ambiguous_targets_fail_closed(s4_pair, side, mutation):
    current, historical = s4_pair
    document = current if side == "current" else historical
    if mutation == "missing_session":
        document["data_need_capabilities"] = [r for r in document["data_need_capabilities"]
                                              if r["capability_id"] != "session_status"]
    elif mutation == "duplicate_session":
        document["data_need_capabilities"].append(copy.deepcopy(session(document)))
    elif mutation == "missing_description":
        session(document).pop("description")
    elif mutation == "missing_limitations":
        document.pop("known_limitations")
    elif mutation == "short_limitations":
        document["known_limitations"] = document["known_limitations"][:5]
    elif mutation == "duplicate_limit":
        document["known_limitations"].append(document["known_limitations"][4])
    elif mutation == "wrong_position":
        values = document["known_limitations"]
        values[4], values[5] = values[5], values[4]
    elif mutation == "wrong_value":
        document["known_limitations"][5] = "unexpected"
    else:
        document["known_limitations"].append(s4.S4_TOP_LIMITATION_DELTAS[0][1 if side == "current" else 2])
    with pytest.raises(ValueError, match="S4 (successor|predecessor) mismatch"):
        s4.project_s4_catalog(s4.CATALOG, current, historical)
    if side == "historical":
        with pytest.raises(ValueError, match="S4 predecessor mismatch"):
            s4.s4_expected_catalog(historical)


def test_s4_routing_is_unchanged_and_mutation_still_fails():
    path = compat.A4_ROUTING_PATH
    historical = json.loads((compat.ROOT / path).read_text(encoding="utf-8"))
    current = copy.deepcopy(historical)
    current["routes"][0]["network_required"] = not current["routes"][0]["network_required"]
    assert s4.project_s4_catalog(path, current, historical) is current
    with pytest.raises(AssertionError, match="non_i3_production_authority_drift"):
        compat.assert_projected_authority_matches_historical(current, historical, path)


def test_s4_unrelated_documents_are_never_projected():
    sentinel = {"arbitrary": "mutation"}
    assert s4.project_s4_catalog("other.json", sentinel, {}) is sentinel
