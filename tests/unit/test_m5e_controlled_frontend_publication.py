import json, time
from pathlib import Path
import pytest
from scripts import run_m5e_controlled_frontend_publication as m5e


def test_check_only_fail_closed():
    r=m5e.check_only()
    assert r['ready_for_explicit_user_authorization_review'] is True
    assert r['frontend_publication_authorized'] is False
    assert r['publication_performed'] is False
    assert r['execute_mode_available'] is False
    assert r['production_ready'] is False


def test_repository_execute_without_auth_fails(capsys):
    assert m5e.main(['--execute-publication']) == 2
    assert 'authorization_decision_and_token_required' in capsys.readouterr().out


def make_auth(tmp_path, **over):
    base={
      'authorization_id':'auth-1','allowed_action':m5e.ACTION,'candidate_dir':str(m5e.CAND),'candidate_manifest_sha256':m5e.manifest_sha(),
      'm5c_lineage_hashes':{'m5c_manifest_sha256':m5e.M5C_MANIFEST_SHA,'m5c_frontend_readonly_context_package_sha256':m5e.M5C_FRONTEND_PACKAGE_SHA,'m5c_supplemental_audit_sha256':m5e.M5C_AUDIT_SHA,'m5c_run_summary_destination_correction_sha256':m5e.M5C_CORRECTION_SHA},
      'destination':str(m5e.DEST),'frontend_baseline_sha256':m5e.fsha(m5e.ROOT/m5e.CAND/'frontend_public_baseline.json'),'expires_at_epoch':int(time.time())+9999,
      'single_use_id':'once','acknowledgement_required':True,'operator_acknowledged':True,
      'forbidden_behaviors':{'production_ready':False,'generated_write':False,'network_market_data_call':False,'trading_output':False,'recommendation_output':False,'realtime_claim':False,'publication_performed':False}}
    base.update(over)
    tok={'authorization_id':base['authorization_id'],'allowed_action':base.get('allowed_action'),'single_use':True,'single_use_id':base.get('single_use_id','once'),'candidate_dir':base.get('candidate_dir'),'candidate_manifest_sha256':base.get('candidate_manifest_sha256'),'destination':base.get('destination'),'frontend_baseline_sha256':base.get('frontend_baseline_sha256'),'m5c_lineage_hashes':base.get('m5c_lineage_hashes'),'expires_at_epoch':base['expires_at_epoch']}
    tok['token_sha256']=m5e.canonical_hash(tok)
    base['token_sha256']=tok['token_sha256']
    dec=tmp_path/'decision.json'; dec.write_text(json.dumps(base))
    token=tmp_path/'token.json'; token.write_text(json.dumps(tok)); return dec,token


def tx_kwargs(tmp_path, src, auth_id='auth-tx'):
    return {'auth_id': auth_id, 'claim_dir': tmp_path / ('claims-' + auth_id), 'expected_src_sha256': m5e.fsha(src), 'candidate_manifest_sha256': m5e.fsha(src), 'simulation_mode': True}

@pytest.mark.parametrize('field,value,code',[('candidate_manifest_sha256','0'*64,'wrong_candidate_hash'),('destination','frontend/public/evil.json','wrong_destination'),('allowed_action','bad','wrong_action'),('operator_acknowledged',False,'acknowledgement_missing'),('expires_at_epoch',1,'expired_token')])
def test_authorization_failures(tmp_path,field,value,code):
    d,t=make_auth(tmp_path, **{field:value})
    errs=m5e.validate_auth(d,t)
    assert code in errs or any(e.startswith('decision_schema:') or e.startswith('token_schema:') for e in errs)

def test_schema_invalid_auth_returns_structured_errors(tmp_path):
    d,t=make_auth(tmp_path, expires_at_epoch=[])
    errs=m5e.validate_auth(d,t)
    assert any(e.startswith('decision_schema:') for e in errs)

def test_token_hash_integrity(tmp_path):
    d,t=make_auth(tmp_path)
    token=json.loads(t.read_text()); token['token_sha256']='0'*64; t.write_text(json.dumps(token))
    errs=m5e.validate_auth(d,t)
    assert 'token_sha256_mismatch' in errs
    decision=json.loads(d.read_text()); decision['token_sha256']='0'*64; d.write_text(json.dumps(decision))
    errs=m5e.validate_auth(d,t)
    assert 'decision_token_sha256_binding_mismatch' in errs

def test_lineage_drift_and_forbidden_flag(tmp_path):
    d,t=make_auth(tmp_path, m5c_lineage_hashes={'m5c_manifest_sha256':'bad'}, forbidden_behaviors={'production_ready':True})
    errs=m5e.validate_auth(d,t)
    assert any(e.startswith('m5c_lineage_drift') for e in errs) or any(e.startswith('decision_schema:') for e in errs)
    assert any(e.startswith('forbidden_flag') for e in errs) or any(e.startswith('decision_schema:') for e in errs)

def test_single_use_duplicate(tmp_path):
    m5e.claim_once(tmp_path,'a')
    with pytest.raises(FileExistsError): m5e.claim_once(tmp_path,'a')
    with pytest.raises(ValueError): m5e.claim_once(tmp_path,'../escape')

def test_transaction_claims_single_use(tmp_path):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; journal=tmp_path/'j'; claims=tmp_path/'claims'
    m5e.publish_transaction(src,dest,journal,auth_id='auth-claim',claim_dir=claims,expected_src_sha256=m5e.fsha(src),candidate_manifest_sha256=m5e.fsha(src),simulation_mode=True)
    assert (claims/'auth-claim.used').exists()
    with pytest.raises(FileExistsError): m5e.publish_transaction(src,tmp_path/'dest2',tmp_path/'j2',auth_id='auth-claim',claim_dir=claims,expected_src_sha256=m5e.fsha(src),candidate_manifest_sha256=m5e.fsha(src),simulation_mode=True)

def test_transaction_new_target_rollback_and_recovery(tmp_path):
    src=tmp_path/'src.json'; src.write_text('{"ok":true}\n'); dest=tmp_path/'out.json'; journal=tmp_path/'j'
    r=m5e.publish_transaction(src,dest,journal,**tx_kwargs(tmp_path, src))
    assert r['status']=='simulated' and r['publication_performed'] is False and dest.read_bytes()==src.read_bytes()
    rb=m5e.rollback(dest,journal)
    assert rb['status']=='rolled_back_new_target' and not dest.exists()
    assert (journal/'rollback_receipt.json').exists()

def test_transaction_replace_rollback(tmp_path):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; dest.write_text('old'); journal=tmp_path/'j'
    m5e.publish_transaction(src,dest,journal,**tx_kwargs(tmp_path, src))
    assert dest.read_text()=='new'
    assert m5e.rollback(dest,journal)['status']=='rolled_back_replacement'
    assert dest.read_text()=='old'

def test_rollback_refuses_to_overwrite_newer_content(tmp_path):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; dest.write_text('old'); journal=tmp_path/'j'
    m5e.publish_transaction(src,dest,journal,**tx_kwargs(tmp_path, src))
    dest.write_text('operator-newer-content')
    rb=m5e.rollback(dest,journal)
    assert rb['status']=='manual_recovery_required'
    assert dest.read_text()=='operator-newer-content'

@pytest.mark.parametrize('phase,expected', [('before_temp_write','safe_no_publication_or_temp_only'),('after_temp_write','safe_no_publication_or_temp_only'),('after_backup','safe_no_publication_or_temp_only'),('after_replace','manual_recovery_required'),('before_receipt','manual_recovery_required'),('after_receipt','simulation_completed')])
def test_crash_recovery_matrix(tmp_path, phase, expected):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; dest.write_text('old'); journal=tmp_path/'j'
    with pytest.raises(RuntimeError): m5e.publish_transaction(src,dest,journal,crash_at=phase,**tx_kwargs(tmp_path, src, 'crash-'+phase.replace('_','-')))
    rec=m5e.recover(dest,journal)
    assert rec['status'] == expected
    assert (journal/'recovery_state.json').exists()
    if expected == 'safe_no_publication_or_temp_only':
        assert dest.read_text() == 'old'

def test_path_traversal_and_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(m5e, 'ROOT', tmp_path)
    public=tmp_path/'frontend'/'public'; public.mkdir(parents=True)
    with pytest.raises(ValueError): m5e.safe_dest('../bad')
    outside=tmp_path/'outside'; outside.write_text('x')
    link=public/'market-context.json'; link.symlink_to(outside)
    with pytest.raises(ValueError): m5e.safe_dest('frontend/public/market-context.json')

def test_frontend_public_unchanged():
    before=m5e.frontend_inventory(); m5e.check_only(); after=m5e.frontend_inventory(); assert before==after

def test_reproducibility_materialize_candidate(tmp_path):
    from scripts.m5d_publication_common import _materialize_candidate
    _materialize_candidate(tmp_path)
    committed=json.loads((m5e.ROOT/m5e.CAND/'sha256_manifest.json').read_text())['files']
    generated=json.loads((tmp_path/'sha256_manifest.json').read_text())['files']
    assert generated==committed

def test_preview_static_dom_contract():
    html=(m5e.ROOT/'frontend/readonly-preview/M5EMarketContextPreview.html').read_text()
    js=(m5e.ROOT/'frontend/readonly-preview/m5e-market-context-adapter.js').read_text()
    assert 'Loading M5D readonly candidate' in html
    assert '<script type="module"' in html
    for text in ['TWSE_OpenAPI','historical/stale','Mandatory caveats','tabindex="0"','<main>']:
        assert text in js
    for forbidden in ['buy','sell','hold','target price','ranking']:
        assert forbidden not in (html + js).lower()

def test_transaction_requires_claim_dir_and_candidate_hash(tmp_path):
    src=tmp_path/'src'; src.write_text('not-candidate'); dest=tmp_path/'dest'; journal=tmp_path/'j'
    with pytest.raises(ValueError, match='claim_dir_required'):
        m5e.publish_transaction(src,dest,journal,auth_id='no-claim')
    with pytest.raises(ValueError, match='simulation_destination_in_repo_forbidden'):
        m5e.publish_transaction(src,m5e.ROOT/'frontend/public/market-context.json',journal,auth_id='repo-sim',claim_dir=tmp_path/'claims-repo',expected_src_sha256=m5e.fsha(src),candidate_manifest_sha256=m5e.fsha(src),simulation_mode=True)
    with pytest.raises(ValueError, match='candidate_lineage_override_forbidden'):
        m5e.publish_transaction(src,dest,journal,auth_id='override',claim_dir=tmp_path/'claims0',expected_src_sha256=m5e.fsha(src),candidate_manifest_sha256=m5e.fsha(src))
    with pytest.raises(ValueError, match='source_hash_mismatch'):
        m5e.publish_transaction(src,dest,journal,auth_id='bad-source',claim_dir=tmp_path/'claims',simulation_mode=True)

def test_transaction_outputs_validate_against_schemas(tmp_path):
    src=m5e.ROOT/m5e.CAND/'market-context.json'; dest=tmp_path/'dest'; journal=tmp_path/'j'; claims=tmp_path/'claims'
    receipt=m5e.publish_transaction(src,dest,journal,auth_id='schema-output',claim_dir=claims,simulation_mode=True,expected_src_sha256=m5e.candidate_market_context_sha(),candidate_manifest_sha256=m5e.manifest_sha())
    assert not m5e._schema_errors('publication_receipt', receipt)
    assert not m5e._schema_errors('journal', m5e.load(journal/'journal.json'))
    rb=m5e.rollback(dest,journal)
    assert not m5e._schema_errors('rollback_receipt', rb)

def test_after_receipt_recovery_rejects_wrong_authorization_binding(tmp_path):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; dest.write_text('old'); journal=tmp_path/'j'
    with pytest.raises(RuntimeError):
        m5e.publish_transaction(src,dest,journal,crash_at='after_receipt',**tx_kwargs(tmp_path, src, 'after-receipt-bind'))
    receipt_path=journal/'publication_receipt.json'
    receipt=json.loads(receipt_path.read_text()); receipt['authorization_id']='other-auth'; receipt_path.write_text(json.dumps(receipt))
    rec=m5e.recover(dest,journal)
    assert rec['status']=='manual_recovery_required'

def test_simulation_journal_and_receipt_do_not_claim_publication(tmp_path):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; journal=tmp_path/'j'
    receipt=m5e.publish_transaction(src,dest,journal,**tx_kwargs(tmp_path, src, 'sim-governance'))
    journal_payload=m5e.load(journal/'journal.json')
    assert receipt['status']=='simulated'
    assert receipt['publication_performed'] is False
    assert journal_payload['simulation_mode'] is True
    assert journal_payload['publication_performed'] is False
    assert journal_payload['destination_write_simulated'] is True
    bad={**receipt, 'status':'published', 'publication_performed':False}
    assert m5e._schema_errors('publication_receipt', bad)

def test_production_rejects_symlink_alias_destination(tmp_path, monkeypatch):
    monkeypatch.setattr(m5e, 'ROOT', tmp_path)
    public=tmp_path/'frontend'/'public'; public.mkdir(parents=True)
    target=public/'market-context.json'; target.write_text('old')
    alias=tmp_path/'alias.json'; alias.symlink_to(target)
    src=tmp_path/'src'; src.write_text('new')
    with pytest.raises(ValueError, match='production_destination_mismatch'):
        m5e.publish_transaction(src,alias,tmp_path/'j',auth_id='prod-alias',claim_dir=tmp_path/'claims')

def test_io_failure_injection_for_write_fsync_replace_and_backup(tmp_path, monkeypatch):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; journal=tmp_path/'j'
    def fail_write(fd, data): raise OSError('short_write')
    monkeypatch.setattr(m5e, '_write_all', fail_write)
    with pytest.raises(OSError, match='short_write'):
        m5e.publish_transaction(src,dest,journal,**tx_kwargs(tmp_path, src, 'fail-write'))
    monkeypatch.setattr(m5e, '_write_all', lambda fd, data: None)
    def fail_fsync(fd): raise OSError('fsync_failed')
    monkeypatch.setattr(m5e.os, 'fsync', fail_fsync)
    with pytest.raises(OSError, match='fsync_failed'):
        m5e.publish_transaction(src,tmp_path/'dest2',tmp_path/'j2',**tx_kwargs(tmp_path, src, 'fail-fsync'))
    monkeypatch.undo()
    def fail_replace(a,b): raise OSError('replace_failed')
    monkeypatch.setattr(m5e.os, 'replace', fail_replace)
    with pytest.raises(OSError, match='replace_failed'):
        m5e.publish_transaction(src,tmp_path/'dest3',tmp_path/'j3',**tx_kwargs(tmp_path, src, 'fail-replace'))

def test_duplicate_single_use_same_journal_preserves_existing_evidence(tmp_path):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; dest.write_text('old'); journal=tmp_path/'j'; claims=tmp_path/'claims'
    m5e.publish_transaction(src,dest,journal,auth_id='same-journal',claim_dir=claims,expected_src_sha256=m5e.fsha(src),candidate_manifest_sha256=m5e.fsha(src),simulation_mode=True)
    before={p.name:p.read_bytes() for p in journal.iterdir() if p.is_file()}
    dest_before=dest.read_bytes()
    with pytest.raises(FileExistsError):
        m5e.publish_transaction(src,dest,journal,auth_id='same-journal',claim_dir=claims,expected_src_sha256=m5e.fsha(src),candidate_manifest_sha256=m5e.fsha(src),simulation_mode=True)
    after={p.name:p.read_bytes() for p in journal.iterdir() if p.is_file()}
    assert after == before
    assert dest.read_bytes() == dest_before


def test_failure_injection_late_transaction_and_receipt_stages(tmp_path, monkeypatch):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; dest.write_text('old')
    # Backup copy failure after temp write but before replace.
    def fail_copy(a,b): raise OSError('backup_failed')
    monkeypatch.setattr(m5e, 'durable_copy', fail_copy)
    with pytest.raises(OSError, match='backup_failed'):
        m5e.publish_transaction(src,dest,tmp_path/'j-backup',**tx_kwargs(tmp_path, src, 'fail-backup'))
    monkeypatch.undo()
    # Destination replace failure: allow journal/temp replaces, fail specifically for final dest path.
    real_replace=m5e.os.replace
    def fail_dest_replace(a,b):
        if str(b) == str(tmp_path/'dest-replace'):
            raise OSError('destination_replace_failed')
        return real_replace(a,b)
    monkeypatch.setattr(m5e.os, 'replace', fail_dest_replace)
    with pytest.raises(OSError, match='destination_replace_failed'):
        m5e.publish_transaction(src,tmp_path/'dest-replace',tmp_path/'j-dest-replace',**tx_kwargs(tmp_path, src, 'fail-dest-replace'))
    monkeypatch.undo()
    # Journal after-replace failure.
    real_durable=m5e.durable_json_replace
    def fail_after_replace(path,obj):
        if obj.get('state') == 'after_replace':
            raise OSError('journal_after_replace_failed')
        return real_durable(path,obj)
    monkeypatch.setattr(m5e, 'durable_json_replace', fail_after_replace)
    with pytest.raises(OSError, match='journal_after_replace_failed'):
        m5e.publish_transaction(src,tmp_path/'dest-after-replace',tmp_path/'j-after-replace',**tx_kwargs(tmp_path, src, 'fail-after-replace'))
    monkeypatch.undo()
    # Publication receipt write failure.
    def fail_receipt(path,obj):
        if obj.get('schema_version') == 'm5e_publication_receipt.v1':
            raise OSError('receipt_write_failed')
        return real_durable(path,obj)
    monkeypatch.setattr(m5e, 'durable_json_replace', fail_receipt)
    with pytest.raises(OSError, match='receipt_write_failed'):
        m5e.publish_transaction(src,tmp_path/'dest-receipt',tmp_path/'j-receipt',**tx_kwargs(tmp_path, src, 'fail-receipt'))
    monkeypatch.undo()


def test_failure_injection_rollback_receipt_and_directory_fsync(tmp_path, monkeypatch):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; journal=tmp_path/'j'
    m5e.publish_transaction(src,dest,journal,**tx_kwargs(tmp_path, src, 'rollback-fail'))
    real_durable=m5e.durable_json_replace
    def fail_rollback_receipt(path,obj):
        if obj.get('schema_version') == 'm5e_rollback_receipt.v1':
            raise OSError('rollback_receipt_failed')
        return real_durable(path,obj)
    monkeypatch.setattr(m5e, 'durable_json_replace', fail_rollback_receipt)
    with pytest.raises(OSError, match='rollback_receipt_failed'):
        m5e.rollback(dest,journal)
    monkeypatch.undo()
    def fail_dir(path): raise OSError('dir_fsync_failed')
    monkeypatch.setattr(m5e, '_fsync_dir', fail_dir)
    with pytest.raises(OSError, match='dir_fsync_failed'):
        m5e.publish_transaction(src,tmp_path/'dest-dir-fsync',tmp_path/'j-dir-fsync',**tx_kwargs(tmp_path, src, 'fail-dir-fsync'))
