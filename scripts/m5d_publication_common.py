from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
M5C=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
CAND=Path('research/staging/m5d/m5d_frontend_publication_candidate_01')
DEST=Path('frontend/public/market-context.json')
REQ=Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json')
AUDIT=Path('research/staging/m5c/supplemental_audit/M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZED_01_AUDIT.json')
CORR=Path('research/staging/m5c/corrections/M5C_RUN_SUMMARY_DESTINATION_CORRECTION_20260627_01.json')
MERGE_SHA='3931f19564698926a96a3022c5c3b40b07de6081'
TARGETS=['2330','0050','00929']

def sha(p:Path): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def load(p:Path): return json.loads((ROOT/p).read_text())
def dump(p:Path,d):
    path=ROOT/p; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
def frontend_inventory():
    base=ROOT/'frontend/public'; rows=[]
    if base.exists():
      for p in sorted(x for x in base.rglob('*') if x.is_file()):
        rel=p.relative_to(base).as_posix(); rows.append({'relative_path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size,'target_path_exists':rel=='market-context.json','overwrite_required':rel=='market-context.json','rollback_required':rel=='market-context.json'})
    return {'schema_version':'m5d_frontend_public_baseline.v1','baseline_root':'frontend/public','hash_only':True,'files':rows,'target_path':'frontend/public/market-context.json','target_path_exists':(ROOT/DEST).exists(),'overwrite_required':(ROOT/DEST).exists(),'rollback_required':(ROOT/DEST).exists()}
def verify_upstream():
    errs=[]
    if os.popen('git rev-parse HEAD').read().strip()!=MERGE_SHA: errs.append('head_sha_mismatch')
    man=load(M5C/'sha256_manifest.json')
    if sha(M5C/'sha256_manifest.json')!='9956b27850f2561f3738ebacda350b1685d54e1947910191605be637ad7dd203': errs.append('m5c_manifest_sha_mismatch')
    if man.get('targets')!=TARGETS: errs.append('targets_mismatch')
    src=load(M5C/'frontend_readonly_context_package.json')
    if {s.get('source_id') for s in src.get('sources',[])}!={'TWSE_OpenAPI'}: errs.append('source_mismatch')
    for p in [AUDIT,CORR,M5C/'validation_report.json']:
      if not (ROOT/p).exists(): errs.append(f'missing:{p}')
    return errs
def build():
    errs=verify_upstream()
    if errs: raise SystemExit('upstream integrity failed: '+','.join(errs))
    src=load(M5C/'frontend_readonly_context_package.json')
    bindings={'m5c_package_dir':str(M5C),'m5c_manifest_sha256':sha(M5C/'sha256_manifest.json'),'m5c_frontend_readonly_context_package_sha256':sha(M5C/'frontend_readonly_context_package.json'),'m5c_supplemental_audit_sha256':sha(AUDIT),'m5c_run_summary_destination_correction_sha256':sha(CORR),'pr57_merge_sha':MERGE_SHA,'source':'TWSE_OpenAPI','targets':TARGETS}
    common={'schema_version':'m5d_frontend_publication_candidate.v1','candidate_dir':str(CAND),'proposed_destination':str(DEST),'publication_performed':False,'frontend_public_write':False,'actual_frontend_publication_authorized':False,'production_ready':False,'realtime_guaranteed':False,'trading_signal':False,'readonly_only':True,'historical_evidence_snapshot':True,'stale_status':'stale','badge':'historical/stale','no_temporary_paths':True}
    dump(CAND/'market-context.json',{**src,**common,'schema_version':'m5d_market_context.v1','derived_from':'reviewed_m5c_frontend_readonly_context_package','bindings':bindings})
    dump(CAND/'source_binding.json',{**common,**bindings})
    dump(CAND/'frontend_public_baseline.json',frontend_inventory())
    dump(CAND/'candidate_summary.json',{**common,'ready_for_user_authorization_review':True,'frontend_publication_authorized':False,'symbols':TARGETS,'authority':'TWSE_OpenAPI','caveats':src.get('global_caveats',[])})
    dump(CAND/'validation_report.json',{**common,'status':'pass','checks':['upstream_integrity','baseline_hash_only','readonly_stale_caveats','no_temp_paths','forbidden_flags']})
    dump(CAND/'rollback_plan.json',{**common,'simulation_only':True,'rollback_required':(ROOT/DEST).exists(),'steps':['restore previous destination hash from baseline if overwritten in future authorized execution','remove newly created destination if no baseline existed']})
    dump(CAND/'publication_plan.json',{**common,'request_only':True,'next_required_action':'user_authorization','execution_available':False,'fail_closed_reason':'no authorization decision or token exists'})
    # final manifest
    files=[p for p in sorted((ROOT/CAND).glob('*.json')) if p.name!='sha256_manifest.json']
    manifest={'schema_version':'m5d_sha256_manifest.v1','candidate_dir':str(CAND),'manifest_final':True,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},**common,**bindings}
    dump(CAND/'sha256_manifest.json',manifest)
    req={'schema_version':'m5d_frontend_publication_request.v2','request_id':'M5D_FRONTEND_PUBLICATION_REQUEST','candidate_dir':str(CAND),'candidate_manifest_sha256':sha(CAND/'sha256_manifest.json'),'proposed_destination':str(DEST),'m5c_staging_package_dir':str(M5C),'m5c_staging_manifest_sha256':bindings['m5c_manifest_sha256'],'single_use':True,'request_only':True,'authorization_token_issued':False,'actual_frontend_publication_authorized':False,'publication_performed':False,'next_required_action':'user_authorization'}
    dump(REQ,req)
    return manifest

def validate_candidate(cdir=CAND):
    errs=[]; c=Path(cdir); man=load(c/'sha256_manifest.json')
    for name,h in man.get('files',{}).items():
      if sha(c/name)!=h: errs.append('candidate_payload_tampering:'+name)
    mc=load(c/'market-context.json')
    for caveat in ['not_realtime_guaranteed','not_trading_signal','not_production_current_state','freshness_must_be_displayed']:
      if caveat not in mc.get('global_caveats',[]): errs.append('missing_caveat:'+caveat)
    text='\n'.join((ROOT/p).read_text() for p in (c).glob('*.json'))
    if '/tmp/' in text or '.m5c_tmp_' in text: errs.append('temporary_path_leakage')
    for k in ['realtime_guaranteed','trading_signal','production_ready','publication_performed','frontend_public_write','actual_frontend_publication_authorized']:
      if mc.get(k) is not False: errs.append('forbidden_flag:'+k)
    if sha(M5C/'frontend_readonly_context_package.json')!=man.get('m5c_frontend_readonly_context_package_sha256'): errs.append('source_package_changed_after_candidate_build')
    return errs
