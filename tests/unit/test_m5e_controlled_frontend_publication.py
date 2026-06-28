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
    base.update(over); dec=tmp_path/'decision.json'; dec.write_text(json.dumps(base))
    tok={'authorization_id':base['authorization_id'],'allowed_action':base.get('allowed_action'),'single_use':True,'single_use_id':'once','expires_at_epoch':base['expires_at_epoch']}
    token=tmp_path/'token.json'; token.write_text(json.dumps(tok)); return dec,token

@pytest.mark.parametrize('field,value,code',[('candidate_manifest_sha256','0'*64,'wrong_candidate_hash'),('destination','frontend/public/evil.json','wrong_destination'),('allowed_action','bad','wrong_action'),('operator_acknowledged',False,'acknowledgement_missing'),('expires_at_epoch',1,'expired_token')])
def test_authorization_failures(tmp_path,field,value,code):
    d,t=make_auth(tmp_path, **{field:value})
    assert code in m5e.validate_auth(d,t)

def test_lineage_drift_and_forbidden_flag(tmp_path):
    d,t=make_auth(tmp_path, m5c_lineage_hashes={'m5c_manifest_sha256':'bad'}, forbidden_behaviors={'production_ready':True})
    errs=m5e.validate_auth(d,t)
    assert any(e.startswith('m5c_lineage_drift') for e in errs)
    assert any(e.startswith('forbidden_flag') for e in errs)

def test_single_use_duplicate(tmp_path):
    m5e.claim_once(tmp_path,'a')
    with pytest.raises(FileExistsError): m5e.claim_once(tmp_path,'a')

def test_transaction_new_target_rollback_and_recovery(tmp_path):
    src=tmp_path/'src.json'; src.write_text('{"ok":true}\n'); dest=tmp_path/'out.json'; journal=tmp_path/'j'
    r=m5e.publish_transaction(src,dest,journal)
    assert r['publication_performed'] and dest.read_bytes()==src.read_bytes()
    rb=m5e.rollback(dest,journal)
    assert rb['status']=='rolled_back_new_target' and not dest.exists()

def test_transaction_replace_rollback(tmp_path):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; dest.write_text('old'); journal=tmp_path/'j'
    m5e.publish_transaction(src,dest,journal)
    assert dest.read_text()=='new'
    assert m5e.rollback(dest,journal)['status']=='rolled_back_replacement'
    assert dest.read_text()=='old'

@pytest.mark.parametrize('phase',['before_temp_write','after_temp_write','after_backup','after_replace','before_receipt','after_receipt'])
def test_crash_recovery_matrix(tmp_path, phase):
    src=tmp_path/'src'; src.write_text('new'); dest=tmp_path/'dest'; dest.write_text('old'); journal=tmp_path/'j'
    with pytest.raises(RuntimeError): m5e.publish_transaction(src,dest,journal,crash_at=phase)
    rec=m5e.recover(dest,journal)
    assert rec['status'] in {'rolled_back_replacement','safe_no_publication_or_temp_only','manual_recovery_required'}

def test_path_traversal_and_symlink(tmp_path):
    with pytest.raises(ValueError): m5e.safe_dest('../bad')
    link=m5e.ROOT/m5e.DEST
    assert not link.is_symlink()

def test_frontend_public_unchanged():
    before=m5e.frontend_inventory(); m5e.check_only(); after=m5e.frontend_inventory(); assert before==after

def test_reproducibility_materialize_candidate(tmp_path):
    from scripts.m5d_publication_common import _materialize_candidate
    _materialize_candidate(tmp_path)
    committed=json.loads((m5e.ROOT/m5e.CAND/'sha256_manifest.json').read_text())['files']
    generated=json.loads((tmp_path/'sha256_manifest.json').read_text())['files']
    assert generated==committed
