import pytest
import json
import jsonschema
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CATALOG = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json"
PORTABLE_CATALOG = ROOT / "skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json"
REQUEST_SCHEMA_PATH = ROOT / "schemas/unified_market_evidence_request.v1.schema.json"
FIXTURES_DIR = ROOT / "tests/fixtures/m8r_05a_f2"

def test_portable_catalog_matches_canonical():
    assert CANONICAL_CATALOG.exists()
    assert PORTABLE_CATALOG.exists()
    
    with open(CANONICAL_CATALOG, "r", encoding="utf-8") as f:
        canon = json.load(f)
    with open(PORTABLE_CATALOG, "r", encoding="utf-8") as f:
        port = json.load(f)
        
    canon_ids = {c["capability_id"] for c in canon.get("data_need_capabilities", [])}
    port_ids = {c["capability_id"] for c in port.get("data_need_capabilities", [])}
    
    assert canon_ids == port_ids
    assert len(canon_ids) == 7

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
