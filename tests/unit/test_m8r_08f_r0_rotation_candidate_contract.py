from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.m8r_06_01c1b_compact_runtime_identity_index import (
    CompactArtifactValidationError,
    sha256_file,
    verify_bundle_integrity,
)
from scripts.m8r_06_security_master_candidate_paths import (
    input_bundle_dir,
    runtime_immutable_seal_path,
    runtime_index_dir,
    source_immutable_seal_path,
    validate_candidate_id,
)


CANDIDATE_B = "m8r06-01b-20990101T000000Z"
SKILL_HASH = "b" * 64


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _sealed_bundle(root: Path) -> Path:
    bundle = input_bundle_dir(root, CANDIDATE_B)
    _write_json(bundle / "classification_records.json", [])
    _write_json(bundle / "lifecycle_events.json", [])
    _write_json(bundle / "source_evidence_manifest.json", {})
    _write_json(bundle / "qualification_report.json", {})
    snapshot = {
        "snapshot_id": f"dryrun-{CANDIDATE_B}",
        "generated_at_utc": "2099-01-01T00:00:00+00:00",
        "source_skill": {"skill_contract_hash": SKILL_HASH},
        "records": [],
    }
    _write_json(bundle / "dryrun_snapshot.json", snapshot)
    _write_json(bundle / "dryrun_manifest.json", {})
    _write_json(bundle / "immutable_manifest.json", {"producer_stage": True})
    raw = bundle / "raw_payloads" / "identity.html"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text("identity", encoding="utf-8")
    seal = {
        "bundle_id": CANDIDATE_B,
        "bundle_persisted_in_git": False,
        "skill_contract_hash": SKILL_HASH,
        "classification_records": {"count": 0, "sha256": sha256_file(bundle / "classification_records.json")},
        "lifecycle_events": {"count": 0, "sha256": sha256_file(bundle / "lifecycle_events.json")},
        "source_evidence_manifest": {"sha256": sha256_file(bundle / "source_evidence_manifest.json")},
        "qualification_report": {"sha256": sha256_file(bundle / "qualification_report.json")},
        "dryrun_snapshot": {"record_count": 0, "sha256": sha256_file(bundle / "dryrun_snapshot.json")},
        "dryrun_manifest": {"sha256": sha256_file(bundle / "dryrun_manifest.json")},
        "raw_payloads": [{"source_id": "identity", "file_name": "identity.html", "sha256": sha256_file(raw)}],
    }
    _write_json(source_immutable_seal_path(root, CANDIDATE_B), seal)
    return bundle


def test_candidate_id_contract_and_paths_are_strict_and_deterministic(tmp_path: Path) -> None:
    assert validate_candidate_id(CANDIDATE_B) == CANDIDATE_B
    assert input_bundle_dir(tmp_path, CANDIDATE_B).name == CANDIDATE_B
    assert runtime_index_dir(tmp_path, CANDIDATE_B).name == CANDIDATE_B
    assert source_immutable_seal_path(tmp_path, CANDIDATE_B).name == "source_immutable_manifest.json"
    assert runtime_immutable_seal_path(tmp_path, CANDIDATE_B).name == "runtime_identity_immutable_manifest.json"
    for invalid in ("", "../m8r06-01b-20990101T000000Z", "C:/x", "m8r06-01b-20990101T000000Z/x", "m8r06-01b-20990101T000000", "m8r06-01b-20261301T000000Z"):
        with pytest.raises(ValueError, match="invalid_governed_candidate_id"):
            validate_candidate_id(invalid)


def test_rotatable_candidate_source_seal_verifies_exact_bundle(tmp_path: Path) -> None:
    _sealed_bundle(tmp_path)
    snapshot, seal, _ = verify_bundle_integrity(CANDIDATE_B, repo_root=tmp_path)
    assert snapshot["snapshot_id"] == f"dryrun-{CANDIDATE_B}"
    assert seal["bundle_id"] == CANDIDATE_B


@pytest.mark.parametrize("mutation", ["missing_raw", "raw_hash", "raw_filename", "extra_file", "skill_hash", "snapshot_id", "fixture"])
def test_rotatable_candidate_source_seal_fails_closed(tmp_path: Path, mutation: str) -> None:
    bundle = _sealed_bundle(tmp_path)
    seal_path = source_immutable_seal_path(tmp_path, CANDIDATE_B)
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if mutation == "missing_raw":
        (bundle / "raw_payloads" / "identity.html").unlink()
    elif mutation == "raw_hash":
        seal["raw_payloads"][0]["sha256"] = "f" * 64
        _write_json(seal_path, seal)
    elif mutation == "raw_filename":
        seal["raw_payloads"][0]["file_name"] = "other.html"
        _write_json(seal_path, seal)
    elif mutation == "extra_file":
        (bundle / "unexpected.json").write_text("{}", encoding="utf-8")
    elif mutation == "skill_hash":
        seal["skill_contract_hash"] = "f" * 64
        _write_json(seal_path, seal)
    elif mutation == "snapshot_id":
        snapshot_path = bundle / "dryrun_snapshot.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["snapshot_id"] = "dryrun_snapshot.json"
        _write_json(snapshot_path, snapshot)
        seal["dryrun_snapshot"]["sha256"] = sha256_file(snapshot_path)
        _write_json(seal_path, seal)
    elif mutation == "fixture":
        snapshot_path = bundle / "dryrun_snapshot.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["records"] = [{"observation": {"status": "fixture_observation_only"}}]
        _write_json(snapshot_path, snapshot)
        seal["dryrun_snapshot"] = {"record_count": 1, "sha256": sha256_file(snapshot_path)}
        _write_json(seal_path, seal)
    with pytest.raises(CompactArtifactValidationError):
        verify_bundle_integrity(CANDIDATE_B, repo_root=tmp_path)
