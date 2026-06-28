import json, shutil
from pathlib import Path
from scripts.validate_m5c_promoted_staging_package import validate
from scripts.verify_m5c_staging_manifest import verify
from scripts.run_m5c_controlled_staging_promotion import execute

def test_missing_artifact_blocked(tmp_path):
    (tmp_path/'sha256_manifest.json').write_text(json.dumps({'manifest':{}}))
    assert any(e['code']=='missing_artifact' for e in validate(tmp_path))

def test_untracked_artifact_blocked(tmp_path):
    src=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
    dst=tmp_path/'pkg'; shutil.copytree(src,dst)
    (dst/'extra.json').write_text('{}')
    assert any(e['code']=='untracked_or_missing_artifacts' for e in verify(dst))

def test_consumption_record_mismatch_blocked(tmp_path):
    src=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
    dst=tmp_path/'pkg'; shutil.copytree(src,dst)
    rec=json.loads((dst/'promotion_receipt.json').read_text())
    rec['consumption_record']=str(tmp_path/'missing.json')
    (dst/'promotion_receipt.json').write_text(json.dumps(rec))
    assert any(e['code']=='manifest_hash_mismatch' for e in validate(dst)) or any(e['code']=='consumption_record_missing' for e in validate(dst))

def test_execute_blocks_existing_destination_without_second_promotion():
    out=execute()
    assert out['status']=='blocked'
    assert any(e['code']=='destination_exists' for e in out['errors'])
