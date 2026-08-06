import pytest
import json
import subprocess
from pathlib import Path
import tempfile
import shutil

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "m8r_05c"

def _run_cli_with_overrides(d_out, **kwargs):
    with tempfile.TemporaryDirectory() as tmp_in:
        tmp_in_path = Path(tmp_in)
        
        args = [
            "python", "-m", "scripts.m8r_05c.cli",
            "--artifact-root", str(FIXTURES_DIR / "artifact_root"),
            "--calculated-at", "2026-08-01T10:00:00Z",
            "--out-dir", d_out
        ]
        
        for name in ["request", "f3_validation", "plan", "authorization", "consumption_binding", "claim", "receipt", "bundle"]:
            src_file = FIXTURES_DIR / f"{name}{'_single_target' if name in ('request', 'plan') else ''}.json"
            
            if name in kwargs:
                # Override the json
                obj = json.loads(src_file.read_text(encoding="utf-8"))
                kwargs[name](obj) # mutate
                dst_file = tmp_in_path / f"{name}.json"
                dst_file.write_text(json.dumps(obj), encoding="utf-8")
                args.extend([f"--{name.replace('_', '-')}-input", str(dst_file)])
            else:
                args.extend([f"--{name.replace('_', '-')}-input", str(src_file)])
                
        res = subprocess.run(args, capture_output=True, text=True, cwd=str(FIXTURES_DIR.parents[2]))
        return res

def test_lineage_claim_receipt_id_mismatch():
    if not (FIXTURES_DIR / "claim.json").exists():
        pytest.skip("Fixtures missing")

    def mutate_claim(c):
        c["execution_receipt_id"] = "umerec-v1-00000000000000000000"

    with tempfile.TemporaryDirectory() as d_out:
        res = _run_cli_with_overrides(d_out, claim=mutate_claim)
        assert res.returncode != 0
        assert "predecessor_id_mismatch_receipt" in res.stderr

def test_lineage_claim_receipt_hash_mismatch():
    if not (FIXTURES_DIR / "claim.json").exists():
        pytest.skip("Fixtures missing")

    def mutate_claim(c):
        c["execution_receipt_hash"] = "0" * 64

    with tempfile.TemporaryDirectory() as d_out:
        res = _run_cli_with_overrides(d_out, claim=mutate_claim)
        assert res.returncode != 0
        assert "predecessor_hash_mismatch_receipt" in res.stderr

def test_lineage_claim_binding_id_mismatch():
    if not (FIXTURES_DIR / "claim.json").exists():
        pytest.skip("Fixtures missing")

    def mutate_claim(c):
        c["consumption_binding_id"] = "umeacb-v1-00000000000000000000"

    with tempfile.TemporaryDirectory() as d_out:
        res = _run_cli_with_overrides(d_out, claim=mutate_claim)
        assert res.returncode != 0
        assert "predecessor_id_mismatch_binding" in res.stderr

def test_lineage_claim_binding_hash_mismatch():
    if not (FIXTURES_DIR / "claim.json").exists():
        pytest.skip("Fixtures missing")

    def mutate_claim(c):
        c["consumption_binding_hash"] = "0" * 64

    with tempfile.TemporaryDirectory() as d_out:
        res = _run_cli_with_overrides(d_out, claim=mutate_claim)
        assert res.returncode != 0
        assert "predecessor_hash_mismatch_binding" in res.stderr

def test_inventory_referential_integrity():
    if not (FIXTURES_DIR / "bundle.json").exists():
        pytest.skip("Fixtures missing")

    def mutate_bundle(b):
        # Alter an artifact hash in operation_evidence_entries
        for entry in b.get("operation_evidence_entries", []):
            if entry.get("artifacts"):
                entry["artifacts"][0]["sha256"] = "0" * 64
                break
                
        # Recompute bundle hash
        import copy
        import sys
        sys.path.insert(0, str(FIXTURES_DIR.parents[2]))
        from scripts.m8r_05b_03.canonical import sha256_json
        b_body = copy.deepcopy(b)
        b_body.pop("bundle_hash", None)
        b["bundle_hash"] = sha256_json(b_body)

    with tempfile.TemporaryDirectory() as d_out:
        res = _run_cli_with_overrides(d_out, bundle=mutate_bundle)
        assert res.returncode != 0
        assert "operation_artifact_hash_mismatch" in res.stderr
