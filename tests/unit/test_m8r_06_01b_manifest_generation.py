import json
from pathlib import Path
import pytest
from scripts.m8r_06_01b_materialize_production_inputs import build_immutable_manifest

def test_build_immutable_manifest_deterministic_hashes(tmp_path: Path):
    """
    Test that build_immutable_manifest properly hashes all expected files
    and produces non-null dryrun and raw_payloads SHA256 hashes.
    """
    bundle_id = "test-bundle-123"
    bundle_dir = tmp_path / bundle_id
    bundle_dir.mkdir()

    # Create dummy files
    (bundle_dir / "classification_records.json").write_text("[]", encoding="utf-8")
    (bundle_dir / "lifecycle_events.json").write_text("[]", encoding="utf-8")
    (bundle_dir / "source_evidence_manifest.json").write_text("{}", encoding="utf-8")
    (bundle_dir / "qualification_report.json").write_text("{}", encoding="utf-8")
    (bundle_dir / "dryrun_snapshot.json").write_text("{}", encoding="utf-8")
    (bundle_dir / "dryrun_manifest.json").write_text("{}", encoding="utf-8")

    raw_dir = bundle_dir / "raw_payloads"
    raw_dir.mkdir()
    (raw_dir / "test_source.html").write_text("<html></html>", encoding="utf-8")

    source_probes = [
        {
            "transport_success": True,
            "source_id": "test_source",
            "observed_at": "2026-08-07T05:35:40Z"
        }
    ]

    # Change ROOT so it writes the manifest in our tmp_path instead of the real repo
    import scripts.m8r_06_01b_materialize_production_inputs as m8r
    original_root = m8r.ROOT
    m8r.ROOT = tmp_path

    try:
        build_immutable_manifest(bundle_id, bundle_dir, [], [], source_probes)
    finally:
        m8r.ROOT = original_root

    manifest_file = tmp_path / "docs" / "reviews" / "m8r06-01b-bundle-manifest" / "immutable_manifest.json"
    assert manifest_file.exists()
    
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    
    # Check that it's deterministic and not null
    assert manifest["classification_records"]["sha256"] is not None
    assert manifest["lifecycle_events"]["sha256"] is not None
    assert manifest["dryrun_snapshot"]["sha256"] is not None
    assert manifest["dryrun_manifest"]["sha256"] is not None
    
    assert len(manifest["raw_payloads"]) == 1
    assert manifest["raw_payloads"][0]["sha256"] is not None
    assert manifest["raw_payloads"][0]["source_id"] == "test_source"
    
    assert manifest["skill_contract_hash"] is not None
