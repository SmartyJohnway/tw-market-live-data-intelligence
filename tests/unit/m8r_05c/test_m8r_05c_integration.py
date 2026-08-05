"""Integration tests for M8R-05C projection layer.

These tests prove that the CLI can run end-to-end on a complete set of
valid fixtures, generating a compliant result, audit package, and markdown.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.m8r_05c.cli import main

ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "m8r_05c"


def test_m8r_05c_cli_end_to_end_single_target(tmp_path: Path):
    """Test full projection of a single target identity artifact."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    argv = [
        "--request-input", str(FIXTURES_DIR / "request_single_target.json"),
        "--plan-input", str(FIXTURES_DIR / "plan_single_target.json"),
        "--authorization-input", str(FIXTURES_DIR / "authorization.json"),
        "--consumption-binding-input", str(FIXTURES_DIR / "consumption_binding.json"),
        "--receipt-input", str(FIXTURES_DIR / "receipt.json"),
        "--bundle-input", str(FIXTURES_DIR / "bundle.json"),
        "--artifact-root", str(FIXTURES_DIR / "artifact_root"),
        "--out-dir", str(out_dir),
    ]

    # Run the CLI. It should exit 0.
    exit_code = main(argv)
    assert exit_code == 0

    # Verify output containment.
    result_path = out_dir / "ai_context" / "unified_market_evidence_result.v1.json"
    audit_path = out_dir / "audit" / "unified_market_evidence_audit_package.v1.json"
    md_path = out_dir / "ai_context" / "unified_market_evidence_result.v1.md"

    assert result_path.exists()
    assert audit_path.exists()
    assert md_path.exists()

    # Load result.
    result = json.loads(result_path.read_text(encoding="utf-8"))

    # Assert stable identity mapping.
    assert result["result_id"] == "umeresult-v1-6b748d9f843c86c6ca7d"
    assert result["schema_version"] == "unified_market_evidence_result.v1"
    assert result["status"] == "success_with_partial_coverage"  # identity succeeded, current_observation missing

    # Verify target evidence.
    targets = result.get("targets", [])
    assert len(targets) == 1
    t0 = targets[0]

    assert t0["resolution"]["canonical_target_id"] == "TW.2330"
    assert t0["resolution"]["status"] == "resolved"

    evidence = t0.get("evidence", {})
    identity = evidence.get("identity", {})
    assert identity["status"] == "available"
    assert identity["observed_fields"]["security_name"] == "Taiwan Semiconductor Manufacturing"

    # Verify citations.
    citations = t0.get("citations", [])
    assert len(citations) == 1
    cit = citations[0]
    assert cit["artifact_reference"] == "operations/op_identity/evidence.json"
    assert cit["source_family"] == "twse_mis_v1"

    # Verify audit reference.
    audit_ref = result.get("audit_reference", {})
    assert audit_ref["audit_package_id"] == "umeap-v1-d3ffa34189cacca6ff2c"
    assert audit_ref["relative_path"] == "audit/unified_market_evidence_audit_package.v1.json"

    # Load audit package.
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["audit_package_id"] == "umeap-v1-d3ffa34189cacca6ff2c"
    assert audit["schema_version"] == "unified_market_evidence_audit_package.v1"
    assert audit["integrity_verification"]["all_artifact_hashes_verified"] is True
    assert len(audit["citation_to_operation_map"]) == 1
    assert audit["citation_to_operation_map"][0]["citation_id"] == cit["citation_id"]

    # Verify markdown.
    md_content = md_path.read_text(encoding="utf-8")
    assert "市場證據結果" in md_content
    assert "umeresult-v1-6b748d9f843c86c6ca7d" in md_content
    assert "Taiwan Semiconductor Manufacturing" in md_content
    assert "umeap-v1-d3ffa34189cacca6ff2c" in md_content


def test_m8r_05c_cli_check_only_mode(tmp_path: Path):
    """Test --check-only mode does not write files."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    argv = [
        "--request-input", str(FIXTURES_DIR / "request_single_target.json"),
        "--plan-input", str(FIXTURES_DIR / "plan_single_target.json"),
        "--authorization-input", str(FIXTURES_DIR / "authorization.json"),
        "--consumption-binding-input", str(FIXTURES_DIR / "consumption_binding.json"),
        "--receipt-input", str(FIXTURES_DIR / "receipt.json"),
        "--bundle-input", str(FIXTURES_DIR / "bundle.json"),
        "--artifact-root", str(FIXTURES_DIR / "artifact_root"),
        "--out-dir", str(out_dir),
        "--check-only",
    ]

    exit_code = main(argv)
    assert exit_code == 0

    # Nothing should be written.
    files = list(out_dir.glob("**/*"))
    assert len(files) == 0
