"""S1 current authority and historical replay separation; offline only."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from scripts import validate_phase_h_v3_contracts as check
from scripts import validate_phase_j_b04_a3_network_free_implementation as historical

ROOT = Path(__file__).resolve().parents[2]
RESULT = "schemas/unified_market_evidence_result.v3.schema.json"
BASELINE = "344a00689785387f9e6af37dde484b798736ce51"
FROZEN = "acaf726a5b59baee4c5a30521ea5a5d5ec0cec76"


def git_bytes(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def current_schema():
    return json.loads((ROOT / RESULT).read_bytes())


def test_current_authority_matches_frozen_release_and_passes():
    content = (ROOT / RESULT).read_bytes()
    assert content == git_bytes(FROZEN, RESULT)
    check.validate_current_result_v3_authority(content)
    check.main()  # Includes historical V1/V2 identities and selected-route guards.


def test_semantically_equivalent_but_unaccepted_fingerprint_fails():
    content = json.dumps(current_schema(), indent=4).encode()
    with pytest.raises(check.PhaseHV3ContractValidationError, match="current_result_v3_authority_drift"):
        check.validate_current_result_v3_authority(content)


@pytest.mark.parametrize("mutation", [
    "missing_timestamp_required", "allow_null_complete", "allow_timestamp_incomplete",
    "remove_body_condition", "collapse_binding_unavailable", "remove_format", "invalid_structure",
])
def test_semantic_weakening_fails_independently_of_fingerprint(mutation):
    schema = copy.deepcopy(current_schema())
    flow = schema["definitions"]["cash_institutional_flow_context"]
    if mutation == "missing_timestamp_required":
        flow["required"].remove("retrieved_at")
    elif mutation == "allow_null_complete":
        flow["allOf"][-2]["then"]["properties"]["retrieved_at"]["type"] = ["string", "null"]
    elif mutation == "allow_timestamp_incomplete":
        flow["allOf"][-2]["else"]["properties"]["retrieved_at"]["type"] = ["string", "null"]
    elif mutation == "remove_body_condition":
        flow["allOf"].pop(-2)
    elif mutation == "collapse_binding_unavailable":
        flow["allOf"].pop()
    elif mutation == "remove_format":
        flow["properties"]["retrieved_at"].pop("format")
        flow["allOf"][-2]["then"]["properties"]["retrieved_at"].pop("format")
    else:
        flow["required"] = "retrieved_at"
    with pytest.raises(check.PhaseHV3ContractValidationError, match="result_v3_(temporal|schema)"):
        check.validate_result_v3_temporal_provenance(schema)


def test_repinning_weakened_schema_does_not_bypass_semantic_guard(monkeypatch):
    schema = current_schema()
    schema["definitions"]["cash_institutional_flow_context"]["allOf"].pop()
    content = json.dumps(schema).encode()
    monkeypatch.setattr(check, "CURRENT_RESULT_V3_SHA256", hashlib.sha256(content).hexdigest())
    with pytest.raises(check.PhaseHV3ContractValidationError, match="result_v3_temporal_provenance_drift"):
        check.validate_current_result_v3_authority(content)


@pytest.mark.parametrize("content,code", [
    (b'{"definitions":{},"definitions":{}}', "duplicate_json_key:definitions"),
    (b'{', "current_authority_json_invalid"),
    (b'\xff', "current_authority_json_invalid"),
    (b'[]', "result_v3_schema_structure_invalid"),
])
def test_ambiguous_or_malformed_schema_rejected(content, code):
    with pytest.raises(check.PhaseHV3ContractValidationError, match=code):
        check.validate_current_result_v3_authority(content)


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_existing_compatibility_identity_guard_rejects_drift(monkeypatch, version):
    target = ROOT / f"schemas/unified_market_evidence_request.{version}.schema.json"
    original = Path.read_bytes

    def drift(path):
        content = original(path)
        return content + b" " if path == target else content

    monkeypatch.setattr(Path, "read_bytes", drift)
    with pytest.raises(check.PhaseHV3ContractValidationError, match="manifest_integrity_mismatch"):
        check.main()


def test_selected_source_activation_guard_still_rejects_drift(monkeypatch):
    original = check._load_current_authority_json

    def drift(path):
        value = original(path)
        if path.name == "m8r_05b_capability_to_executor_routing_matrix.v3.json":
            record = next(r for r in value["phase_h_source_authority"]["records"]
                          if r["activation_state"] == "active")
            record["activation_state"] = "inactive"
        return value

    monkeypatch.setattr(check, "_load_current_authority_json", drift)
    with pytest.raises(check.PhaseHV3ContractValidationError, match="phase_h_active_source_set_invalid"):
        check.main()


def test_historical_schema_identity_and_gate_artifacts_are_preserved():
    old_hash = historical.FROZEN_SCHEMA_HASHES[RESULT]
    assert old_hash != check.CURRENT_RESULT_V3_SHA256
    assert hashlib.sha256(git_bytes(historical.BASELINE, RESULT)).hexdigest() == old_hash
    for path in (
        "scripts/validate_phase_j_b04_a3_network_free_implementation.py",
        "docs/governance/phase_j/PHASE_J_J_B04_A3_NETWORK_FREE_IMPLEMENTATION_ACCEPTANCE_2026-10-08.json",
        "docs/governance/phase_h/PHASE_H_H0_G_V3_SCHEMA_FREEZE_MANIFEST.json",
        "docs/governance/phase_l/PHASE_L_L7_A5_FINAL_GOVERNANCE_RECONCILIATION_2026-10-26.md",
        "docs/governance/phase_l/PHASE_L_L7_A5_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-27.md",
    ):
        # Git text artifacts may use checkout CRLF; preserve normalized bytes.
        assert (ROOT / path).read_bytes().replace(b"\r\n", b"\n") == git_bytes(BASELINE, path).replace(b"\r\n", b"\n")
