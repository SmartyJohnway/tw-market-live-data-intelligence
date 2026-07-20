import pytest
import json
import jsonschema
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CATALOG = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json"
PORTABLE_CATALOG = ROOT / "skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json"
REQUEST_SCHEMA_PATH = ROOT / "schemas/unified_market_evidence_request.v1.schema.json"
FIXTURES_DIR = ROOT / "tests/fixtures/m8r_05a_f2"
VALIDATOR_SCRIPT = ROOT / "scripts/validate_portable_catalog_sync.py"

def test_portable_catalog_matches_canonical_via_deep_equality():
    assert CANONICAL_CATALOG.exists()
    assert PORTABLE_CATALOG.exists()
    assert VALIDATOR_SCRIPT.exists()
    
    # Run the actual sync validator which performs deep equality
    result = subprocess.run(
        ["python", str(VALIDATOR_SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Sync validation failed:\n{result.stdout}\n{result.stderr}"
    assert "PASS:" in result.stdout
    assert "Deep Equality Verified" in result.stdout

def test_portable_catalog_generator_is_strictly_deterministic(tmp_path):
    # This tests that running the generator twice on the same canonical input produces
    # the exact same byte arrays (Double-Generation Determinism test)
    import subprocess
    import shutil
    
    gen_script = ROOT / "scripts/generate_portable_catalog.py"
    assert gen_script.exists()
    
    # Run first time in temp directory, we will copy the output
    subprocess.run(["python", str(gen_script)], cwd=str(ROOT), check=True, capture_output=True)
    first_json = PORTABLE_CATALOG.read_bytes()
    first_md = PORTABLE_MD.read_bytes()
    
    # Run second time
    subprocess.run(["python", str(gen_script)], cwd=str(ROOT), check=True, capture_output=True)
    second_json = PORTABLE_CATALOG.read_bytes()
    second_md = PORTABLE_MD.read_bytes()
    
    assert first_json == second_json, "Generator JSON output is not deterministic between runs"
    assert first_md == second_md, "Generator Markdown output is not deterministic between runs"

def test_fixtures_validate_against_schema():
    assert REQUEST_SCHEMA_PATH.exists()
    with open(REQUEST_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    fixtures = list(FIXTURES_DIR.glob("*.json"))
    assert len(fixtures) == 8
    
    for fpath in fixtures:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Validate schema
        jsonschema.validate(instance=data, schema=schema)
