"""Bounded copied publication snapshots; never mutates repository authorities."""
import copy
import json
import pytest
from scripts import validate_l5_extension_publication_conformance as check
from scripts.generate_portable_catalog import route_publication


@pytest.fixture
def snapshot(tmp_path):
    path = tmp_path / "publication.json"
    path.write_text(json.dumps(check.load_snapshot()), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def codes(snapshot):
    return {e["code"] for e in check.validate_snapshot(snapshot)["errors"]}


def change_cell(s, cid, value):
    lines = s["quick"].splitlines()
    for n, line in enumerate(lines):
        if line.startswith(f"| `{cid}` |"):
            cells = line.split("|")
            cells[4] = value
            lines[n] = "|".join(cells)
    s["quick"] = "\n".join(lines) + "\n"


def test_current_publication_passes_and_validator_is_read_only(snapshot):
    before = copy.deepcopy(snapshot)
    assert check.validate_snapshot(snapshot)["status"] == "PASS"
    assert snapshot == before


def test_portable_field_drift(snapshot):
    snapshot["portable"]["bounds"]["hard_target_limit"] = 9999
    assert "A4_PORTABLE_CATALOG_DRIFT" in codes(snapshot)


@pytest.mark.parametrize("key", ["canonical_sha256", "generated_from_commit", "canonical_git_blob_sha"])
def test_portable_hash_or_git_lineage_drift(snapshot, key):
    snapshot["portable"]["portable_metadata"][key] = "wrong"
    assert "A4_PORTABLE_LINEAGE_DRIFT" in codes(snapshot)


def test_blocked_session_route_cannot_be_published_executable(snapshot):
    change_cell(snapshot, "session_status", "executable subject to authorization/policy")
    assert "A4_BLOCKED_ROUTE_PUBLISHED_EXECUTABLE" in codes(snapshot)


def test_catalog_status_alone_does_not_authorize(snapshot):
    snapshot["quick"] += "Support Status is authoritative for executability.\n"
    assert "A4_GUIDE_CATALOG_ROUTE_DRIFT" in codes(snapshot)


def test_active_route_cannot_be_published_pending(snapshot):
    change_cell(snapshot, "index_futures_context", "Owner activation pending")
    assert "A4_ACTIVE_ROUTE_PUBLISHED_PENDING" in codes(snapshot)


@pytest.mark.parametrize("authority, key", [("catalog", "data_need_capabilities"), ("routing", "routes")])
def test_i2_stale_owner_pending_prose_rejected(snapshot, authority, key):
    row = next(r for r in snapshot[authority][key] if r["capability_id"] == "index_futures_context")
    row["known_limitations"].append("final Owner production activation pending")
    assert "A4_STALE_OWNER_PENDING_PUBLICATION" in codes(snapshot)


@pytest.mark.parametrize("mutation", ["omit", "invent"])
def test_skill_exact_six_tools(snapshot, mutation):
    path = check.GUIDES[0]
    if mutation == "omit":
        snapshot["guides"][path] = snapshot["guides"][path].replace("market_fetch_evidence", "fetch")
    else:
        snapshot["guides"][path] += "\n`market_extension_tool`\n"
    assert "A4_PUBLIC_MCP_SURFACE_DRIFT" in codes(snapshot)


def test_current_limitations_cannot_contradict_blocked_route(snapshot):
    snapshot["guides"][check.GUIDES[2]] += "\nsession_status is executable.\n"
    assert "A4_CURRENT_LIMITATION_DRIFT" in codes(snapshot)


@pytest.mark.parametrize("path", check.HISTORICAL)
def test_historical_guide_not_current_authority(snapshot, path):
    snapshot["guides"][check.GUIDES[0]] += f"Current capability authority: {path}"
    assert "A4_HISTORICAL_GUIDE_PROMOTED_AS_CURRENT" in codes(snapshot)


def test_publication_cannot_become_runtime_input(snapshot):
    snapshot["runtime_inputs"][check.RUNTIME_INPUTS[0]] += '\npublication = "capability_quick_guide.md"\n'
    assert "A4_PUBLICATION_AUTHORITY_INVERSION" in codes(snapshot)


def test_semantic_authority_change_fails_closed(snapshot):
    snapshot["catalog"]["data_need_capabilities"][0]["support_status"] = "runtime_executable"
    assert "A4_CATALOG_SEMANTIC_CHANGE_REQUIRED" in codes(snapshot)


@pytest.mark.parametrize("support, state, selected, provisional, expected", [
    ("runtime_executable", "resolved", "trusted", False, "executable subject to"),
    ("contract_supported", "plan_only", None, False, "NOT currently executable"),
    ("runtime_executable", "blocked", None, False, "NOT currently executable"),
    ("runtime_executable", "resolved", "trusted", True, "NOT currently executable"),
    ("provisional", "resolved", "trusted", False, "NOT currently executable"),
])
def test_effective_publication_is_fail_closed(support, state, selected, provisional, expected):
    cap = {"capability_id": "session_status", "support_status": support}
    route = {"capability_id": "session_status", "supported_markets": ["TWSE"],
             "routing_status": state, "runtime_executable": True,
             "selected_executor_id": selected, "provisional": provisional}
    assert expected in route_publication(cap, [route])[1]


def test_i2_current_activation_uses_accepted_owner_authority():
    phase_i = check.ROOT / "docs/governance/phase_i"
    ledger = json.loads((phase_i / "PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json").read_text(encoding="utf-8"))
    closure = json.loads((phase_i / "PHASE_I_FINAL_CLOSURE_2026-10-05.json").read_text(encoding="utf-8"))
    assert ledger["owner_authority_reference"] == "USER_CHAT_2026-10-01_PHASE_I_I2_A4_FINAL_PRODUCTION_ACTIVATION_ACCEPTANCE_AND_MERGE_CLOSURE"
    assert ledger["closure"]["production_activation_authorized"] is True
    assert closure["accepted_capabilities"]["I2"]["status"] == "ACTIVE / OWNER ACCEPTED"
