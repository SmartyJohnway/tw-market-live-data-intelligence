from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.validate_source_registry import validate_source_registry
def test_validate_source_registry_ok(): assert validate_source_registry(load('docs/source_registry/source_authority_registry.json'), load('docs/source_registry/source_risk_flag_catalog.json'), load('docs/source_registry/source_contract_schema.json'), load('docs/source_registry/source_family_coverage_matrix.json')) == []
