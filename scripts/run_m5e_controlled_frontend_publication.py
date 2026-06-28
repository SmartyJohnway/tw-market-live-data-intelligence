from __future__ import annotations
import argparse, hashlib, json, os, shutil, sys, tempfile, time
from pathlib import Path
try:
    from scripts.m5d_publication_common import ROOT, CAND, DEST, REQ, M5C, validate_candidate, sha, frontend_inventory, M5C_MANIFEST_SHA, M5C_FRONTEND_PACKAGE_SHA, M5C_AUDIT_SHA, M5C_CORRECTION_SHA
except ModuleNotFoundError:
    from m5d_publication_common import ROOT, CAND, DEST, REQ, M5C, validate_candidate, sha, frontend_inventory, M5C_MANIFEST_SHA, M5C_FRONTEND_PACKAGE_SHA, M5C_AUDIT_SHA, M5C_CORRECTION_SHA

FALSE_FLAGS={"production_ready","generated_write","network_market_data_call","trading_output","recommendation_output","realtime_claim","publication_performed"}
ACTION="publish_frontend_market_context"

def jdump(p,obj):
    p.parent.mkdir(parents=True, exist_ok=True); data=json.dumps(obj,indent=2,sort_keys=True).encode()+b"\n"; p.write_bytes(data); return hashlib.sha256(data).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def manifest_sha(cdir=CAND): return fsha(ROOT/cdir/'sha256_manifest.json')
def validate_auth(decision, token, *, now=None):
    now=now or int(time.time()); errs=[]
    try: d=load(decision); t=load(token)
    except Exception as e: return [f"malformed_json:{e}"]
    if d.get('authorization_id')!=t.get('authorization_id'): errs.append('authorization_token_binding_mismatch')
    if d.get('allowed_action')!=ACTION or t.get('allowed_action')!=ACTION: errs.append('wrong_action')
    if d.get('acknowledgement_required') is not True or d.get('operator_acknowledged') is not True: errs.append('acknowledgement_missing')
    if t.get('single_use') is not True or not t.get('single_use_id'): errs.append('single_use_token_required')
    if int(d.get('expires_at_epoch',0)) <= now or int(t.get('expires_at_epoch',0)) <= now: errs.append('expired_token')
    if d.get('candidate_dir')!=str(CAND): errs.append('candidate_dir_mismatch')
    if d.get('candidate_manifest_sha256')!=manifest_sha(): errs.append('wrong_candidate_hash')
    if d.get('destination')!=str(DEST): errs.append('wrong_destination')
    if d.get('frontend_baseline_sha256')!=fsha(ROOT/CAND/'frontend_public_baseline.json'): errs.append('frontend_baseline_drift')
    lineage=d.get('m5c_lineage_hashes',{})
    for k,v in {'m5c_manifest_sha256':M5C_MANIFEST_SHA,'m5c_frontend_readonly_context_package_sha256':M5C_FRONTEND_PACKAGE_SHA,'m5c_supplemental_audit_sha256':M5C_AUDIT_SHA,'m5c_run_summary_destination_correction_sha256':M5C_CORRECTION_SHA}.items():
        if lineage.get(k)!=v: errs.append('m5c_lineage_drift:'+k)
    def scan(o,p='$'):
        if isinstance(o,dict):
            for k,v in o.items():
                if k in FALSE_FLAGS and v is not False: errs.append('forbidden_flag:'+p+'/'+k)
                scan(v,p+'/'+k)
        elif isinstance(o,list):
            for i,v in enumerate(o): scan(v,p+'/'+str(i))
    scan(d); scan(t)
    return errs

def safe_dest(dest):
    p=(ROOT/dest).resolve(); base=(ROOT/'frontend/public').resolve()
    if not str(p).startswith(str(base)+os.sep): raise ValueError('path_traversal_or_wrong_root')
    if p.exists() and p.is_symlink(): raise ValueError('symlink_target_forbidden')
    return p

def claim_once(claim_dir, auth_id):
    claim_dir.mkdir(parents=True,exist_ok=True); fd=os.open(claim_dir/(auth_id+'.used'), os.O_CREAT|os.O_EXCL|os.O_WRONLY); os.write(fd,b'claimed\n'); os.close(fd)

def publish_transaction(src, dest, journal_dir, auth_id='tmp-auth', crash_at=None):
    dest=Path(dest); journal_dir=Path(journal_dir); journal_dir.mkdir(parents=True,exist_ok=True); receipt=journal_dir/'publication_receipt.json'; state={'state':'started','auth_id':auth_id,'publication_performed':False}
    jdump(journal_dir/'journal.json',state)
    if crash_at=='before_temp_write': raise RuntimeError('crash:before_temp_write')
    tmp=dest.with_name('.'+dest.name+'.tmp'); data=Path(src).read_bytes(); fd=os.open(tmp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    try: os.write(fd,data); os.fsync(fd)
    finally: os.close(fd)
    state.update(state='after_temp_write',temp=str(tmp),new_sha256=hashlib.sha256(data).hexdigest()); jdump(journal_dir/'journal.json',state)
    if crash_at=='after_temp_write': raise RuntimeError('crash:after_temp_write')
    backup=None
    if dest.exists():
        backup=journal_dir/'previous.bin'; shutil.copy2(dest,backup); state.update(state='after_backup',backup=str(backup),previous_sha256=fsha(backup)); jdump(journal_dir/'journal.json',state)
    if crash_at=='after_backup': raise RuntimeError('crash:after_backup')
    os.replace(tmp,dest); state.update(state='after_replace',publication_performed=True); jdump(journal_dir/'journal.json',state)
    if crash_at=='after_replace' or crash_at=='before_receipt': raise RuntimeError('crash:'+crash_at)
    out={'status':'published','destination':str(dest),'sha256':fsha(dest),'previous_sha256':state.get('previous_sha256'),'publication_performed':True}
    jdump(receipt,out)
    state.update(state='after_receipt',receipt=str(receipt)); jdump(journal_dir/'journal.json',state)
    if crash_at=='after_receipt': raise RuntimeError('crash:after_receipt')
    return out

def rollback(dest,journal_dir):
    dest=Path(dest); st=load(Path(journal_dir)/'journal.json');
    if st.get('backup') and Path(st['backup']).exists(): shutil.copy2(st['backup'],dest); return {'status':'rolled_back_replacement','rollback_performed':True,'sha256':fsha(dest)}
    if st.get('publication_performed') and dest.exists() and fsha(dest)==st.get('new_sha256'):
        dest.unlink(); return {'status':'rolled_back_new_target','rollback_performed':True}
    return {'status':'manual_recovery_required','state':st}

def recover(dest,journal_dir):
    st=load(Path(journal_dir)/'journal.json')
    if st.get('state') in ('started','after_temp_write','after_backup'): return rollback(dest,journal_dir) if st.get('backup') else {'status':'safe_no_publication_or_temp_only','state':st}
    if st.get('state') in ('after_replace','after_receipt'): return {'status':'manual_recovery_required','state':st}
    return {'status':'manual_recovery_required','state':st}

def check_only():
    return {'ready_for_explicit_user_authorization_review': not validate_candidate(CAND), 'frontend_publication_authorized':False,'publication_performed':False,'execute_mode_available':False,'production_ready':False,'candidate_manifest_sha256':manifest_sha(),'runtime_consumer_compatible':True,'authorization_absent':True}

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--execute-publication',action='store_true'); ap.add_argument('--authorization-decision'); ap.add_argument('--token'); ap.add_argument('--json',action='store_true'); ns=ap.parse_args(argv)
    if not ns.execute_publication:
        print(json.dumps(check_only(),indent=2,sort_keys=True)); return 0
    if not (ns.authorization_decision and ns.token): print(json.dumps({'status':'blocked','errors':['authorization_decision_and_token_required'],'publication_performed':False})); return 2
    errs=validate_candidate(CAND)+validate_auth(ns.authorization_decision,ns.token)
    try: dest=safe_dest(DEST)
    except Exception as e: errs.append(str(e))
    if errs: print(json.dumps({'status':'blocked','errors':errs,'publication_performed':False},indent=2)); return 2
    print(json.dumps({'status':'blocked','errors':['repository_level_execution_disabled_without_real_authorization_ceremony'],'publication_performed':False},indent=2)); return 2
if __name__=='__main__': raise SystemExit(main())
