from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
from scripts.run_m4_local_validation import run_local_validation
def test_local_validation_no_network(): assert run_local_validation(ROOT)['network_used'] is False
def test_local_validation_fails_bad_manifest(tmp_path):
 bad=tmp_path/'bad_manifest.json'; bad.write_text('{}')
 r=run_local_validation(ROOT, bad)
 assert not r['ok']; assert any(c['name']=='governance_policy_manifest' and not c['ok'] for c in r['checks'])
