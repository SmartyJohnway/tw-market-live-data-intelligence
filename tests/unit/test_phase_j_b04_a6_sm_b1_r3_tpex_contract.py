"""Network-denied structural contract tests; synthetic shell only, no live body."""
from __future__ import annotations

import copy
import importlib.util
import json
import socket
import sys
from pathlib import Path

import jsonschema
import pytest

from scripts.phase_j_b04_a6_sm_b1_r3_tpex_contract import (
    CANDIDATE_CLASSES, CAPTURE_SHA256, LANDING_URL,
    analyze_landing, discovery_proposal, verified_capture,
)

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/tw-security-master-classifier"
sys.path.insert(0, str(SKILL / "scripts"))
from lifecycle_common import LifecycleSchemaDrift  # noqa: E402
from parse_tpex_delisted import parse  # noqa: E402

SHELL = b'''<!doctype html><html><body><form></form>
<script src="/rsrc/asset/js/global.js"></script>
<script src="/rsrc/js/tables.js"></script>
<script>tables.init({pattern:API_PATTERN,action:"company/deListed"});</script>
</body></html>'''


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*_args, **_kwargs):
        pytest.fail("R3 test attempted a socket/network operation")
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)


def materializer():
    spec = importlib.util.spec_from_file_location(
        "r3_contract_materializer", ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_manifest():
    manifest = json.loads((SKILL / "references/source-manifest.json").read_text())
    source = next(s for s in manifest["lifecycle_sources"] if s["id"] == "tpex_company_delisted")
    return manifest, source


def test_shell_is_contract_metadata_not_a_valid_empty_lifecycle_dataset():
    inventory = analyze_landing(SHELL)
    assert inventory["doctype_present"] and inventory["html_element_present"]
    assert inventory["table_element_count"] == 0
    assert inventory["script_element_count"] == 3
    assert inventory["inline_script_count"] == 1
    assert inventory["form_count"] == 1
    assert inventory["embedded_json_script_blocks"]["count"] == 0
    assert inventory["lifecycle_events_generated"] == 0
    assert inventory["lifecycle_dataset_validated"] is False
    with pytest.raises(LifecycleSchemaDrift, match="no_html_tables"):
        parse(SHELL, LANDING_URL)


def test_action_token_is_not_promoted_to_endpoint():
    inventory = analyze_landing(SHELL)
    action = inventory["company/deListed"]
    assert action["exact_literal_occurrence_count"] == 1
    assert action["classification"] == "SYMBOLIC_ACTION_TOKEN"
    assert action["syntactic_context"] == "tables.init action property"
    assert action["executable_endpoint"] is False
    assert inventory["executable_lifecycle_data_endpoint"] is None
    assert inventory["API_PATTERN"]["symbolic_reference_only"] is True
    assert inventory["API_PATTERN"]["declaration_absent"] is True
    assert inventory["API_PATTERN"]["literal_value_present"] is False
    assert all(c["classification"] in CANDIDATE_CLASSES for c in inventory["literal_path_action_candidates"])


def test_uncaptured_script_dependencies_need_bounded_discovery_not_evaluation():
    inventory = analyze_landing(SHELL)
    scripts = [c for c in inventory["literal_path_action_candidates"] if c["origin"] == "script.src"]
    assert all(c["classification"] == "EXTERNAL_SCRIPT_DEPENDENCY" for c in scripts)
    proposal = discovery_proposal(inventory)
    assert proposal["authorization_status"] == "NOT_AUTHORIZED"
    assert proposal["max_logical_requests"] == 2
    assert proposal["max_dispatches_total"] == 4
    assert proposal["retry"] == 0
    assert proposal["data_endpoint_requests"] == 0
    assert proposal["execute_imported_assets_or_javascript"] is False
    assert [t["url"] for t in proposal["targets"]] == [
        "https://www.tpex.org.tw/rsrc/asset/js/global.js",
        "https://www.tpex.org.tw/rsrc/js/tables.js",
    ]
    assert all(t["maximum_followed_redirects"] == 1 and t["maximum_dispatches"] == 2 for t in proposal["targets"])
    assert "company/deListed" not in json.dumps(proposal["targets"])


def test_missing_direct_script_reference_makes_discovery_targets_not_ready():
    inventory = analyze_landing(b'<html><script>tables.init({pattern:API_PATTERN,action:"company/deListed"})</script></html>')
    assert discovery_proposal(inventory)["authorization_readiness"] == "NOT_READY"
    assert discovery_proposal(inventory)["targets"] == []


def test_inventory_excludes_credentials_queries_beacon_and_script_bodies():
    data = b'''<html><script src="https://user:password@www.tpex.org.tw/x.js?key=secret#part"></script>
    <script data-cf-beacon='{"token":"beacon-secret"}'>var unrelated="unrelated-body";</script></html>'''
    inventory = analyze_landing(data)
    text = json.dumps(inventory)
    for secret in ("password", "key=secret", "beacon-secret", "unrelated-body"):
        assert secret not in text
    ref = inventory["external_script_src_values"][0]["src"]
    assert ref["userinfo_omitted"] and ref["query_omitted"] and ref["fragment_omitted"]
    assert ref["host"] == "www.tpex.org.tw" and ref["path"] == "/x.js"


def test_json_scripts_report_type_count_only():
    inventory = analyze_landing(b'<html><script type="application/json">{"private":"dont-copy"}</script></html>')
    assert inventory["embedded_json_script_blocks"] == {"count": 1, "types": {"application/json": 1}}
    assert "dont-copy" not in json.dumps(inventory)
    assert inventory["lifecycle_dataset_validated"] is False


def test_even_literal_api_pattern_does_not_prove_event_or_response_contract():
    inventory = analyze_landing(b'<html><script>const API_PATTERN="https://www.tpex.org.tw/example"; tables.init({pattern:API_PATTERN,action:"company/deListed"});</script></html>')
    assert inventory["API_PATTERN"]["declaration_present"]
    assert inventory["API_PATTERN"]["literal_value_present"]
    assert not inventory["API_PATTERN"]["symbolic_reference_only"]
    assert inventory["executable_lifecycle_data_endpoint"] is None


def test_legacy_supplied_html_table_preserves_lifecycle_semantics():
    events = parse((SKILL / "references/fixtures/tpex_delisted_excerpt.html").read_bytes(), LANDING_URL)
    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "tpex_delisted"
    assert event["security_code"] == "9999"
    assert event["effective_date"] == "2026-06-01"
    assert event["date_raw"] == "115/06/01"
    assert event["calendar"] == "ROC"
    assert event["source_url"] == LANDING_URL
    assert event["evidence_status"] == "official_table"


def test_manifest_is_truthful_and_schema_valid_without_guessed_endpoint():
    manifest, source = source_manifest()
    jsonschema.validate(manifest, json.loads((SKILL / "references/schemas/source-manifest.schema.json").read_text()))
    assert source["id"] == "tpex_company_delisted"
    assert source["url"] == LANDING_URL
    assert source["format"] == "client_rendered_shell"
    assert source["verification"] == "landing_capture_verified_data_contract_unresolved"
    assert source["contract_state"] == "blocked_pending_data_endpoint_qualification"
    assert source["production_automatic_acquisition"] is False
    assert source["landing_page_contract"]["capture_sha256"] == CAPTURE_SHA256
    assert source["lifecycle_data_contract"]["endpoint"] is None
    assert source["lifecycle_data_contract"]["state"] == "unresolved"
    assert source["events"] == ["tpex_delisted"]


def test_unresolved_contract_blocks_real_materializer_before_any_probe(monkeypatch, tmp_path):
    module = materializer()
    calls = []
    monkeypatch.setattr(module, "BUNDLE_BASE", tmp_path / "bundles")
    monkeypatch.setattr(module, "probe", lambda *_args, **_kwargs: calls.append("probe"))
    monkeypatch.setattr(module, "export_verified_security_master_snapshot", lambda *_args, **_kwargs: calls.append("export"))
    with pytest.raises(RuntimeError, match="BOOTSTRAP_TPEX_LIFECYCLE_DATA_CONTRACT_UNRESOLVED"):
        module.main()
    assert calls == []
    assert not (tmp_path / "bundles").exists()


@pytest.mark.parametrize("change", [
    {"production_automatic_acquisition": True},
    {"contract_state": "qualified_data_contract"},
    {"verification": "payload_verified"},
])
def test_partial_manifest_promotion_cannot_unlock_acquisition(change):
    manifest, _ = source_manifest()
    manifest = copy.deepcopy(manifest)
    next(s for s in manifest["lifecycle_sources"] if s["id"] == "tpex_company_delisted").update(change)
    with pytest.raises(RuntimeError, match="BOOTSTRAP_TPEX_LIFECYCLE_DATA_CONTRACT_UNRESOLVED"):
        materializer()._require_tpex_lifecycle_data_contract(manifest)


def test_capture_unavailable_or_wrong_hash_is_not_reacquired(tmp_path):
    with pytest.raises(ValueError, match="BLOCKED_LOCAL_CAPTURE_UNAVAILABLE"):
        verified_capture(tmp_path / "missing.html")
    file = tmp_path / "supplied.html"
    file.write_bytes(SHELL)
    with pytest.raises(ValueError, match="BLOCKED_LOCAL_CAPTURE_HASH_MISMATCH"):
        verified_capture(file)
