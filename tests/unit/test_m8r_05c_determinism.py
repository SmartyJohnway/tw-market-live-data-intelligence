import pytest
import json
import subprocess
from pathlib import Path
import tempfile
import sys
import shutil

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "m8r_05c"
CLI_PATH = Path(__file__).resolve().parents[2] / "scripts" / "m8r_05c" / "cli.py"

def test_m8r_05c_determinism():
    if not (FIXTURES_DIR / "claim.json").exists():
        pytest.skip("Fixtures missing")

    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        cmd = [
            sys.executable, "-m", "scripts.m8r_05c.cli",
            "--request-input", str(FIXTURES_DIR / "request_single_target.json"),
            "--f3-validation-input", str(FIXTURES_DIR / "f3_validation.json"),
            "--plan-input", str(FIXTURES_DIR / "plan_single_target.json"),
            "--authorization-input", str(FIXTURES_DIR / "authorization.json"),
            "--consumption-binding-input", str(FIXTURES_DIR / "consumption_binding.json"),
            "--claim-input", str(FIXTURES_DIR / "claim.json"),
            "--receipt-input", str(FIXTURES_DIR / "receipt.json"),
            "--bundle-input", str(FIXTURES_DIR / "bundle.json"),
            "--artifact-root", str(FIXTURES_DIR / "artifact_root"),
            "--calculated-at", "2026-08-01T10:00:00Z"
        ]
        
        # Run 1
        cmd1 = cmd + ["--out-dir", d1]
        res1 = subprocess.run(cmd1, capture_output=True, text=True, cwd=str(FIXTURES_DIR.parents[2]))
        assert res1.returncode == 0, res1.stderr
        
        # Run 2
        cmd2 = cmd + ["--out-dir", d2]
        res2 = subprocess.run(cmd2, capture_output=True, text=True, cwd=str(FIXTURES_DIR.parents[2]))
        assert res2.returncode == 0, res2.stderr
        
        # Verify result determinism
        res1_json = json.loads((Path(d1) / "ai_context" / "unified_market_evidence_result.v1.json").read_text(encoding="utf-8"))
        res2_json = json.loads((Path(d2) / "ai_context" / "unified_market_evidence_result.v1.json").read_text(encoding="utf-8"))
        
        assert res1_json == res2_json
        
        # Verify audit determinism
        audit1_json = json.loads((Path(d1) / "audit" / "unified_market_evidence_audit_package.v1.json").read_text(encoding="utf-8"))
        audit2_json = json.loads((Path(d2) / "audit" / "unified_market_evidence_audit_package.v1.json").read_text(encoding="utf-8"))
        
        assert audit1_json == audit2_json

def test_m8r_05c_check_only():
    if not (FIXTURES_DIR / "claim.json").exists():
        pytest.skip("Fixtures missing")

    with tempfile.TemporaryDirectory() as d:
        cmd = [
            sys.executable, "-m", "scripts.m8r_05c.cli",
            "--request-input", str(FIXTURES_DIR / "request_single_target.json"),
            "--f3-validation-input", str(FIXTURES_DIR / "f3_validation.json"),
            "--plan-input", str(FIXTURES_DIR / "plan_single_target.json"),
            "--authorization-input", str(FIXTURES_DIR / "authorization.json"),
            "--consumption-binding-input", str(FIXTURES_DIR / "consumption_binding.json"),
            "--claim-input", str(FIXTURES_DIR / "claim.json"),
            "--receipt-input", str(FIXTURES_DIR / "receipt.json"),
            "--bundle-input", str(FIXTURES_DIR / "bundle.json"),
            "--artifact-root", str(FIXTURES_DIR / "artifact_root"),
            "--out-dir", d,
            "--check-only"
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(FIXTURES_DIR.parents[2]))
        assert res.returncode == 0, res.stderr
        
        assert not (Path(d) / "ai_context").exists()
        assert not (Path(d) / "audit").exists()
