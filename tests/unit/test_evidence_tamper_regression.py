from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.validate_fixture_hash_manifest import validate_manifest
def test_missing_fixture_fails(): assert validate_manifest({'files':[{'path':'missing.json','sha256':'x'}]})[0]['code']=='missing_fixture'
def test_modified_fixture_hash_fails(): assert validate_manifest({'files':[{'path':'tests/fixtures/staging_payloads/valid_single_source_twse_mis.json','sha256':'0'}]})[0]['code']=='hash_mismatch'
