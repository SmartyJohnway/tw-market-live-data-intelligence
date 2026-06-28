import json, hashlib, shutil
from pathlib import Path
import scripts.run_m5c_controlled_staging_promotion as runner
from scripts.validate_m5c_promoted_staging_package import validate
from scripts.verify_m5c_staging_manifest import verify
from scripts.validate_m5c_supplemental_audit import validate as validate_audit, AUDIT

def _rehash_manifest(pkg: Path):
    man=json.loads((pkg/'sha256_manifest.json').read_text())
    for p in pkg.iterdir():
        if p.is_file() and p.name!='sha256_manifest.json':
            man['manifest'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (pkg/'sha256_manifest.json').write_text(json.dumps(man,indent=2,sort_keys=True)+'\n')

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
    out=runner.execute()
    assert out['status']=='blocked'
    assert any(e['code']=='destination_exists' for e in out['errors'])

def test_build_failure_persists_failed_consumption_outcome(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'DEST', str(tmp_path/'dest'))
    monkeypatch.setattr(runner, 'CONSUME_DIR', tmp_path/'consumption')
    monkeypatch.setattr(runner, 'validate_auth', lambda: [])
    monkeypatch.setattr(runner, 'preflight_run', lambda: {'ok': True})
    monkeypatch.setattr(runner, 'is_success', lambda _: True)
    monkeypatch.setattr(runner, '_build', lambda *_: (_ for _ in ()).throw(RuntimeError('boom-build')))
    out=runner.execute()
    record=next((tmp_path/'consumption').glob('*.json'))
    data=json.loads(record.read_text())
    assert out['status']=='blocked'
    assert data['status']=='failed'
    assert data['stage']=='build'
    assert data['failure_receipt_persisted'] is True
    assert data['temporary_directory_cleanup_result']=='removed'
    assert data['destination_state']['exists'] is False

def test_rename_failure_persists_failed_consumption_outcome(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'DEST', str(tmp_path/'dest'))
    monkeypatch.setattr(runner, 'CONSUME_DIR', tmp_path/'consumption')
    monkeypatch.setattr(runner, 'validate_auth', lambda: [])
    monkeypatch.setattr(runner, 'preflight_run', lambda: {'ok': True})
    monkeypatch.setattr(runner, 'is_success', lambda _: True)
    monkeypatch.setattr(runner, '_build', lambda dst, _: (dst/'artifact.json').write_text('{}'))
    monkeypatch.setattr(runner.os, 'rename', lambda *_: (_ for _ in ()).throw(RuntimeError('boom-rename')))
    out=runner.execute()
    record=next((tmp_path/'consumption').glob('*.json'))
    data=json.loads(record.read_text())
    assert out['status']=='blocked'
    assert data['status']=='failed'
    assert data['stage']=='atomic_rename'
    assert data['failure_receipt_persisted'] is True
    assert data['temporary_directory_cleanup_result']=='removed'

def test_existing_consumption_without_destination_blocks_reuse(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'DEST', str(tmp_path/'dest'))
    monkeypatch.setattr(runner, 'CONSUME_DIR', tmp_path/'consumption')
    monkeypatch.setattr(runner, 'validate_auth', lambda: [])
    monkeypatch.setattr(runner, 'preflight_run', lambda: {'ok': True})
    monkeypatch.setattr(runner, 'is_success', lambda _: True)
    (tmp_path/'consumption').mkdir()
    auth=json.loads(Path('docs/authorization/decisions/M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZATION.json').read_text())
    ((tmp_path/'consumption')/(auth['authorization_id']+'.json')).write_text('{}')
    out=runner.execute()
    assert out['status']=='blocked'
    assert any(e['code']=='authorization_already_consumed' for e in out['errors'])

def test_deleted_binding_field_after_rehash_is_blocked(tmp_path):
    src=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
    dst=tmp_path/'pkg'; shutil.copytree(src,dst)
    binding=json.loads((dst/'source_binding.json').read_text())
    del binding['source_manifest_sha256']
    (dst/'source_binding.json').write_text(json.dumps(binding,indent=2,sort_keys=True)+'\n')
    _rehash_manifest(dst)
    assert any(e['code']=='required_binding_missing' and e.get('object')=='source_binding' for e in validate(dst))

def test_supplemental_audit_missing_or_tampered_blocked(tmp_path):
    audit=json.loads(AUDIT.read_text())
    audit['artifacts']=audit['artifacts'][:-1]
    p=tmp_path/'audit.json'; p.write_text(json.dumps(audit))
    assert validate_audit(p)
    audit=json.loads(AUDIT.read_text())
    audit['artifacts'][0]['sha256']='0'*64
    p.write_text(json.dumps(audit))
    assert any(e['code']=='audit_artifact_hash_mismatch' for e in validate_audit(p))

def test_success_outcome_persistence_failure_does_not_retry_or_delete_destination(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'DEST', str(tmp_path/'dest'))
    monkeypatch.setattr(runner, 'CONSUME_DIR', tmp_path/'consumption')
    monkeypatch.setattr(runner, 'validate_auth', lambda: [])
    monkeypatch.setattr(runner, 'preflight_run', lambda: {'ok': True})
    monkeypatch.setattr(runner, 'is_success', lambda _: True)
    monkeypatch.setattr(runner, '_build', lambda dst, _: (dst/'artifact.json').write_text('{}'))
    real_try=runner._try_record_outcome
    def flaky(path, status, stage, detail=None, tmp=None, cleanup_result=None):
        if status == 'succeeded':
            return {'code':'outcome_persistence_failed','status':status,'stage':stage,'detail':'disk full','destination_state':runner._destination_state()}
        return real_try(path,status,stage,detail,tmp,cleanup_result)
    monkeypatch.setattr(runner, '_try_record_outcome', flaky)
    out=runner.execute()
    assert out['status']=='pass'
    assert out['outcome_persistence_warning']['code']=='outcome_persistence_failed'
    assert (tmp_path/'dest').exists()
    assert (tmp_path/'dest'/'artifact.json').exists()

def test_failed_outcome_persistence_failure_is_reported(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'DEST', str(tmp_path/'dest'))
    monkeypatch.setattr(runner, 'CONSUME_DIR', tmp_path/'consumption')
    monkeypatch.setattr(runner, 'validate_auth', lambda: [])
    monkeypatch.setattr(runner, 'preflight_run', lambda: {'ok': True})
    monkeypatch.setattr(runner, 'is_success', lambda _: True)
    monkeypatch.setattr(runner, '_build', lambda *_: (_ for _ in ()).throw(RuntimeError('boom-build')))
    real_try=runner._try_record_outcome
    def flaky(path, status, stage, detail=None, tmp=None, cleanup_result=None):
        if status == 'failed':
            return {'code':'outcome_persistence_failed','status':status,'stage':stage,'detail':'disk full','destination_state':runner._destination_state()}
        return real_try(path,status,stage,detail,tmp,cleanup_result)
    monkeypatch.setattr(runner, '_try_record_outcome', flaky)
    out=runner.execute()
    assert out['status']=='blocked'
    assert any(e['code']=='outcome_persistence_failed' for e in out['errors'])

def test_consumed_at_is_preserved_across_outcome_updates(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'DEST', str(tmp_path/'dest'))
    monkeypatch.setattr(runner, 'CONSUME_DIR', tmp_path/'consumption')
    monkeypatch.setattr(runner, 'validate_auth', lambda: [])
    monkeypatch.setattr(runner, 'preflight_run', lambda: {'ok': True})
    monkeypatch.setattr(runner, 'is_success', lambda _: True)
    monkeypatch.setattr(runner, '_build', lambda dst, _: (dst/'artifact.json').write_text('{}'))
    out=runner.execute()
    record=Path(out['consumption_record'])
    data=json.loads(record.read_text())
    assert data['status']=='succeeded'
    assert data['consumed_at_utc'] <= data['updated_at_utc']
    assert data['completed_at_utc'] == data['updated_at_utc']
