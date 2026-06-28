import json, shutil
from pathlib import Path
from scripts.validate_m5c_promoted_staging_package import validate
from scripts.verify_m5c_staging_manifest import verify

def test_committed_package_valid_if_present():
    p=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
    if p.exists(): assert validate(p)==[]

def test_manifest_verifier_is_independent_and_detects_tamper(tmp_path):
    src=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
    dst=tmp_path/'pkg'; shutil.copytree(src,dst)
    data=json.loads((dst/'run_summary.json').read_text()); data['status']='tampered'
    (dst/'run_summary.json').write_text(json.dumps(data))
    assert any(e['code']=='manifest_hash_mismatch' for e in verify(dst))
