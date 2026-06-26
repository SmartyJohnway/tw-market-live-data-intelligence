from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.build_fixture_hash_manifest import build_manifest
def test_build_manifest_hash():
 m=build_manifest([ROOT/'tests/fixtures/staging_payloads/valid_single_source_twse_mis.json']); assert len(m['files'][0]['sha256'])==64
