import pytest
import json
import jsonschema
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CATALOG = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json"
PORTABLE_CATALOG = ROOT / "skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json"
PORTABLE_MD = ROOT / "skills/tw-market-evidence-agent/references/capability_quick_guide.md"
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
    from scripts.generate_portable_catalog import generate_portable_catalog

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    generate_portable_catalog(
        canonical_path=CANONICAL_CATALOG,
        portable_json_path=first_dir / "portable.json",
        portable_guide_path=first_dir / "guide.md",
    )
    generate_portable_catalog(
        canonical_path=CANONICAL_CATALOG,
        portable_json_path=second_dir / "portable.json",
        portable_guide_path=second_dir / "guide.md",
    )
    first_json = (first_dir / "portable.json").read_bytes()
    first_md = (first_dir / "guide.md").read_bytes()
    second_json = (second_dir / "portable.json").read_bytes()
    second_md = (second_dir / "guide.md").read_bytes()

    assert first_json == second_json, "Generator JSON output is not deterministic between runs"
    assert first_md == second_md, "Generator Markdown output is not deterministic between runs"


def test_portable_catalog_hash_and_projections_are_newline_stable(tmp_path):
    from scripts.generate_portable_catalog import (
        generate_portable_catalog,
        get_file_sha256,
    )

    canonical_text = CANONICAL_CATALOG.read_text(encoding="utf-8")
    lf_catalog = tmp_path / "catalog_lf.json"
    crlf_catalog = tmp_path / "catalog_crlf.json"
    lf_catalog.write_text(canonical_text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\n")
    crlf_catalog.write_text(canonical_text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\r\n")

    lf_hash = get_file_sha256(lf_catalog)
    crlf_hash = get_file_sha256(crlf_catalog)
    assert lf_hash == crlf_hash

    lf_dir = tmp_path / "lf"
    crlf_dir = tmp_path / "crlf"
    generate_portable_catalog(
        canonical_path=lf_catalog,
        portable_json_path=lf_dir / "portable.json",
        portable_guide_path=lf_dir / "guide.md",
    )
    generate_portable_catalog(
        canonical_path=crlf_catalog,
        portable_json_path=crlf_dir / "portable.json",
        portable_guide_path=crlf_dir / "guide.md",
    )

    assert (lf_dir / "portable.json").read_bytes() == (crlf_dir / "portable.json").read_bytes()
    assert (lf_dir / "guide.md").read_bytes() == (crlf_dir / "guide.md").read_bytes()
    assert b"\r\n" in (lf_dir / "portable.json").read_bytes()
    assert b"\r\n" in (lf_dir / "guide.md").read_bytes()

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
