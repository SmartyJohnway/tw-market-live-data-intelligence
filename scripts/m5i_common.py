from __future__ import annotations
import json, hashlib, math, os, tempfile, shutil
from datetime import datetime, timezone
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
ALLOWED_BOUNDED={"0050","00929","2330"}
ACTION="m5i_explicit_bounded_market_refresh"
SOURCE="TWSE_OpenAPI"
MAX_TARGETS=5
FORBIDDEN_KEYS={'buy','sell','hold','target_price','target price','ranking','rank','recommendation','raw_payload','raw_full_response','full_raw_payload','response_body','raw_endpoint_payload'}
REQ_CAVEATS=['not_realtime_guaranteed','not_trading_signal','not_production_current_state','source_risk_present','freshness_must_be_displayed']

def dump(o): return json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n"
def write_lf(p,t): Path(p).write_bytes(t.encode('utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def now(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def configured_targets():
    d=load(REPO/'config/market_targets.json'); out=set()
    for g in d.values():
        for s in (g.get('symbols',{}) if isinstance(g,dict) else {}).get('standard',[]): out.add(s)
    return out

def reject_forbidden(o,path='<root>'):
    if isinstance(o,dict):
        for k,v in o.items():
            if str(k).lower() in FORBIDDEN_KEYS: raise ValueError(f'forbidden field {path}.{k}')
            reject_forbidden(v,f'{path}.{k}')
    elif isinstance(o,list):
        for i,v in enumerate(o): reject_forbidden(v,f'{path}[{i}]')

def validate_authorization(auth, targets, source=SOURCE):
    errs=[]
    if auth.get('allowed_action')!=ACTION: errs.append('wrong_action')
    if auth.get('source')!=source or source!=SOURCE: errs.append('wrong_source')
    if auth.get('single_use') is not True: errs.append('single_use_required')
    if not auth.get('single_use_id'): errs.append('missing_single_use_id')
    if auth.get('operator_acknowledged') is not True: errs.append('missing_operator_acknowledgement')
    exp=auth.get('expires_at_utc')
    if exp:
        try:
            e=datetime.fromisoformat(exp.replace('Z','+00:00'))
            if e <= datetime.now(timezone.utc): errs.append('expired_authorization')
        except Exception: errs.append('bad_expiry')
    auth_targets=auth.get('targets')
    if auth_targets != targets: errs.append('targets_mismatch')
    if not isinstance(targets,list) or not targets: errs.append('targets_required')
    elif len(set(targets))!=len(targets): errs.append('duplicate_targets')
    max_targets=auth.get('max_targets')
    if not isinstance(max_targets,int) or max_targets<1 or max_targets>MAX_TARGETS: errs.append('bad_max_targets')
    elif len(targets)>max_targets or len(targets)>MAX_TARGETS: errs.append('targets_exceed_bound')
    bad_indicators={'*','ALL','all','FULL_MARKET','full_market','全市場'}
    if any(t in bad_indicators or '*' in str(t) for t in targets): errs.append('full_market_or_wildcard_target')
    cfg=configured_targets()
    if any(t not in cfg for t in targets): errs.append('target_outside_config')
    if any(t not in ALLOWED_BOUNDED for t in targets): errs.append('target_outside_m5f_bounded_scope')
    required_true=['no_frontend_publication','no_production_refresh','no_generated_refresh','no_trading_output','no_full_market_scan','no_polling']
    for k in required_true:
        if auth.get(k) is not True: errs.append(f'{k}_must_be_true')
    return errs

def claim_authorization(auth):
    claims=REPO/'research/live_probe_runs/m5i/claims'; claims.mkdir(parents=True,exist_ok=True)
    aid=auth.get('authorization_id'); sid=auth.get('single_use_id')
    if not aid or not sid: raise ValueError('missing claim ids')
    path=claims/f'{aid}__{sid}.json'
    fd=os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:
        f.write(dump({'authorization_id':aid,'single_use_id':sid,'claimed_at_utc':now(),'runner_started':True,'network_calls_may_have_occurred':True}))
    return path

def promote_m5i_candidate_to_m5f(candidate_dir: Path):
    c_path = candidate_dir / 'market-context.json'
    if c_path.exists():
        c_data = load(c_path)
        if c_data.get('failed_targets'):
            return {
                'status': 'blocked',
                'stage': 'pre_promotion_policy',
                'reason': 'failed_targets_present',
                'promotion_performed': False
            }

    import sys
    scripts_dir = str(Path(__file__).resolve().parents[0])
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import build_m5f_canonical_market_context_package as bld
    import validate_m5f_canonical_market_context_package as val
    write_package = getattr(bld, 'write_package')
    validate_package = getattr(val, 'validate_package')
    canonical_dir = REPO/'research/staging/m5f/m5f_canonical_market_context_01'

    # 1. Build and validate temp package
    temp_dir = Path(tempfile.mkdtemp(prefix='m5i_promote_'))
    try:
        write_package(str(candidate_dir), temp_dir)
        validate_package(temp_dir)
    except Exception as e:
        shutil.rmtree(temp_dir)
        return {'status': 'failed', 'stage': 'temp_package_build_or_validate', 'error': str(e)}

    # 2. Preserve last known good
    backup_dir = Path(tempfile.mkdtemp(prefix='m5i_backup_'))
    try:
        if canonical_dir.exists():
            shutil.copytree(canonical_dir, backup_dir, dirs_exist_ok=True)
    except Exception as e:
        shutil.rmtree(temp_dir)
        shutil.rmtree(backup_dir)
        return {'status': 'failed', 'stage': 'backup_creation', 'error': str(e)}

    # 3. Final replace
    try:
        if canonical_dir.exists():
            shutil.rmtree(canonical_dir)
        shutil.copytree(temp_dir, canonical_dir)
    except Exception as e:
        # Rollback on replace failure
        if canonical_dir.exists():
            shutil.rmtree(canonical_dir)
        if backup_dir.exists() and any(backup_dir.iterdir()):
            shutil.copytree(backup_dir, canonical_dir)
        shutil.rmtree(temp_dir)
        shutil.rmtree(backup_dir)
        return {'status': 'failed', 'stage': 'final_replace', 'error': str(e), 'rollback': 'successful'}

    # 4. Post-promotion validation
    try:
        res = validate_package(canonical_dir)
    except Exception as e:
        # Rollback on post-promotion failure
        shutil.rmtree(canonical_dir)
        shutil.copytree(backup_dir, canonical_dir)
        shutil.rmtree(temp_dir)
        shutil.rmtree(backup_dir)
        return {'status': 'failed', 'stage': 'post_promotion_validation', 'error': str(e), 'rollback': 'successful'}

    shutil.rmtree(temp_dir)
    shutil.rmtree(backup_dir)
    res['status'] = 'promoted'
    res['promotion_mode'] = 'rollback_protected_non_atomic_directory_replace'
    return res
