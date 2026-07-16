import json, subprocess, sys
from pathlib import Path
import pytest
from scripts import m8r_03d_watchlist_controlled_executor as executor
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan, canonical_request_hash, validate_authorization, AUTH_SCHEMA_VERSION, MAX_WATCHLIST_TARGETS
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_watchlist_source_integration import normalize_twse_mis_watchlist_observation, normalize_twse_openapi_watchlist_observation
FIX=Path('tests/fixtures/m8r_03d'); C=Path('tests/fixtures/m8r_03c')
def load(p): return json.loads(Path(p).read_text())
SM={('listed','2330'):{'instrument_type':'equity','name':'台積電','listing_status':'active','lifecycle_state':'active','source':'test'},('listed','2317'):{'instrument_type':'equity','name':'鴻海','listing_status':'active','lifecycle_state':'active','source':'test'},('tpex_otc','6488'):{'instrument_type':'equity','name':'環球晶','listing_status':'active','lifecycle_state':'active','source':'test'},('listed','1111'):{'instrument_type':'equity','listing_status':'delisted','lifecycle_state':'inactive','source':'test'},('listed','1234'):{'instrument_type':'warrant','listing_status':'active','lifecycle_state':'active','source':'test'}}
def auth(req,plan,**kw):
    return {'schema_version':AUTH_SCHEMA_VERSION,'authorization_id':'auth-1','one_shot_nonce':'nonce-1','issued_at_utc':'2026-07-16T00:00:00Z','expires_at_utc':'2026-07-17T00:00:00Z','authorized_request_hash':canonical_request_hash(req),'authorized_bundle_types':['snapshot','performance'],'authorized_source_families':['TWSE_MIS','TWSE_OPENAPI','TPEX_OPENAPI'],'authorized_target_ids':plan['target_order'],'max_target_count':MAX_WATCHLIST_TARGETS,'network_execution_allowed':True,'one_shot_only':True,'polling_allowed':False,'scheduler_allowed':False,'persistent_storage_allowed':False,'raw_payload_retention_allowed':False,'operator_approval':{'approved_by':'test'},**kw}

def test_authorization_accepts_and_rejects_strict_schema():
    req=load(C/'snapshot_request.json'); plan=build_execution_plan(req,bundle_type='snapshot',security_master=SM)
    assert validate_authorization(auth(req,plan),request=req,plan=plan,bundle_type='snapshot',now_utc='2026-07-16T01:00:00Z')['valid']
    cases=[({'expires_at_utc':'2026-07-15T00:00:00Z'},'authorization_expired'),({'expires_at_utc':'2026-07-16T00:00:00Z'},'authorization_expiry_invalid'),({'authorized_request_hash':'x'},'authorization_field_invalid'),({'authorized_target_ids':[]},'authorization_field_invalid'),({'authorized_target_ids':['TWSE:2330','TWSE:2330']},'authorization_duplicate_value'),({'authorized_source_families':[]},'authorization_field_invalid'),({'extra':1},'authorization_unknown_field'),({'authorized_bundle_types':['performance']},'unauthorized_bundle_type'),({'polling_allowed':True},'authorization_flag_rejected'),({'raw_payload_retention_allowed':True},'authorization_flag_rejected')]
    for patch,code in cases:
        got=validate_authorization(auth(req,plan,**patch),request=req,plan=plan,bundle_type='snapshot',now_utc='2026-07-16T01:00:00Z')
        assert code in {i['code'] for i in got['issues']}

def test_plan_security_master_routes_blocking_and_target_limit():
    req=load(FIX/'mixed_snapshot_request.json'); p1=build_execution_plan(req,bundle_type='snapshot',security_master=SM); p2=build_execution_plan(req,bundle_type='snapshot',security_master=SM)
    assert p1['plan_id']==p2['plan_id']; assert p1['target_order']==['TWSE:2330','TPEX:6488']
    by={t['target_id']:t for t in p1['targets']}; assert by['TWSE:2330']['current_source_plan']['route']=='tse_2330.tw'; assert by['TPEX:6488']['current_source_plan']['route']=='otc_6488.tw'; assert by['TPEX:6488']['eod_source_plan']['source_family']=='TPEX_OPENAPI'
    bad=json.loads(json.dumps(req)); bad['persistent_watchlist_reference']['enabled_target_ids']=['TPEX:2330','TWSE:9999','TWSE:1111','TWSE:1234']
    p=build_execution_plan(bad,bundle_type='snapshot',security_master=SM); codes=[t['identity_status'] for t in p['targets']]
    assert codes==['market_mismatch','identity_unresolved','lifecycle_unsupported','unsupported_instrument']
    assert {i['code'] for i in p['issues']} >= {'market_mismatch','lifecycle_unsupported','unsupported_instrument'}
    over=json.loads(json.dumps(req)); over['persistent_watchlist_reference']['enabled_target_ids']=[f'TWSE:{i:04d}' for i in range(11)]
    assert any(i['code']=='target_limit_exceeded' and i.get('blocking') for i in build_execution_plan(over,bundle_type='snapshot',security_master=SM)['issues'])

def test_blocking_plan_stops_fixture_and_execute_before_invocation(tmp_path):
    req=load(FIX/'mixed_snapshot_request.json'); req['persistent_watchlist_reference']['enabled_target_ids']=[f'TWSE:{i:04d}' for i in range(11)]
    calls=[]; out=execute_watchlist(req,mode='fixture',bundle_type='snapshot',fixture_source_data=load(FIX/'mixed_snapshot_source_data.json'),artifact_root=str(tmp_path),security_master=SM)
    assert out['status']=='blocked_preflight' and out['observation_count']==0
    out=execute_watchlist(req,mode='execute',bundle_type='snapshot',authorization={'x':1},artifact_root=str(tmp_path),executors={'TWSE_MIS':lambda *a,**k:calls.append(1)},security_master=SM)
    assert out['status']=='blocked_preflight' and calls==[]

def test_normalization_safe_fields_identity_and_raw_rejected():
    target=build_execution_plan(load(C/'snapshot_request.json'),bundle_type='snapshot',security_master=SM)['targets'][0]
    obs=normalize_twse_mis_watchlist_observation({'symbol':'2330','market':'TWSE','price':1,'change':2,'source_timestamp':'2026-07-16T01:00:00Z','retrieved_at':'2026-07-16T01:00:01Z'},target)
    assert obs['facts']['latest_price']==1 and obs['retrieved_at_utc']!=obs['source_timestamp']
    eod=normalize_twse_openapi_watchlist_observation({'symbol':'2330','market':'listed','trade_date':'2026-07-15','retrieved_at_utc':'2026-07-16T01:00:01Z','price':{'open':'1','high':'2','low':'1','close':'2'},'activity':{'trade_volume':3}},target)
    assert eod['facts']['volume']==3 and eod['trade_date']=='2026-07-15'
    with pytest.raises(ValueError): normalize_twse_mis_watchlist_observation({'raw_payload':{}},target)

def test_fixture_snapshot_performance_and_partial(tmp_path):
    req=load(C/'snapshot_request.json'); out=execute_watchlist(req,mode='fixture',bundle_type='snapshot',fixture_source_data=load(FIX/'snapshot_source_data.json'),artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z',security_master=SM)
    assert out['status']=='success' and out['observation_count']==4
    perf=execute_watchlist(load(C/'performance_request.json'),mode='fixture',bundle_type='performance',fixture_source_data=load(FIX/'performance_source_data.json'),artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z',security_master=SM)
    assert perf['status']=='success' and perf['observation_count']==42
    partial=load(FIX/'snapshot_source_data.json'); del partial['targets']['TWSE:2317']['TWSE_MIS']
    out=execute_watchlist(req,mode='fixture',bundle_type='snapshot',fixture_source_data=partial,artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z',security_master=SM)
    assert out['status']=='success_with_partial_coverage'

def test_successful_injected_execute_and_replay(tmp_path):
    req=load(FIX/'mixed_snapshot_request.json'); plan=build_execution_plan(req,bundle_type='snapshot',security_master=SM); calls=[]
    def fake(fam):
        def run(target_ids, **kw):
            calls.append((fam,tuple(target_ids))); data=load(FIX/'mixed_snapshot_source_data.json'); return {'targets':{tid:{fam:data['targets'][tid][fam]} for tid in target_ids if fam in data['targets'][tid]}}
        return run
    a=auth(req,plan,authorized_source_families=['TWSE_MIS','TWSE_OPENAPI','TPEX_OPENAPI'])
    out=execute_watchlist(req,mode='execute',bundle_type='snapshot',authorization=a,artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z',executors={'TWSE_MIS':fake('TWSE_MIS'),'TWSE_OPENAPI':fake('TWSE_OPENAPI'),'TPEX_OPENAPI':fake('TPEX_OPENAPI')},security_master=SM)
    assert out['status']=='success' and out['observation_count']==4 and len(calls)==3 and out['artifact_paths']['bundle']
    replay=execute_watchlist(req,mode='execute',bundle_type='snapshot',authorization=a,artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:31:05Z',executors={'TWSE_MIS':fake('TWSE_MIS')},security_master=SM)
    assert replay['status']=='authorization_failed' and 'authorization_replayed' in {i['code'] for i in replay['issues']}

def test_source_failure_isolation_all_failure_and_artifact_failure(tmp_path, monkeypatch):
    req=load(FIX/'mixed_snapshot_request.json'); plan=build_execution_plan(req,bundle_type='snapshot',security_master=SM)
    data=load(FIX/'mixed_snapshot_source_data.json')
    a=auth(req,plan,authorization_id='auth-partial',one_shot_nonce='partial')
    out=execute_watchlist(req,mode='execute',bundle_type='snapshot',authorization=a,artifact_root=str(tmp_path),generated_at_utc='2026-07-16T02:00:00Z',executors={'TWSE_MIS':lambda *a,**k: (_ for _ in ()).throw(RuntimeError('mis down')),'TWSE_OPENAPI':lambda tids,**k:{'targets':{'TWSE:2330':{'TWSE_OPENAPI':data['targets']['TWSE:2330']['TWSE_OPENAPI']}}},'TPEX_OPENAPI':lambda tids,**k:{'targets':{'TPEX:6488':{'TPEX_OPENAPI':data['targets']['TPEX:6488']['TPEX_OPENAPI']}}}},security_master=SM)
    assert out['status']=='success_with_partial_coverage' and any(g['status']=='failed' for g in out['source_execution_summary']['group_results'])
    a2=auth(req,plan,authorization_id='auth-allfail',one_shot_nonce='allfail')
    out=execute_watchlist(req,mode='execute',bundle_type='snapshot',authorization=a2,artifact_root=str(tmp_path),generated_at_utc='2026-07-16T02:10:00Z',executors={'TWSE_MIS':lambda *a,**k: (_ for _ in ()).throw(RuntimeError('x')),'TWSE_OPENAPI':lambda *a,**k: (_ for _ in ()).throw(RuntimeError('y')),'TPEX_OPENAPI':lambda *a,**k: (_ for _ in ()).throw(RuntimeError('z'))},security_master=SM)
    assert out['status']=='source_execution_failed'
    a3=auth(req,plan,authorization_id='auth-writefail',one_shot_nonce='writefail')
    monkeypatch.setattr(executor,'_write_json',lambda *a,**k: (_ for _ in ()).throw(OSError('disk full')))
    out=execute_watchlist(req,mode='execute',bundle_type='snapshot',authorization=a3,artifact_root=str(tmp_path),generated_at_utc='2026-07-16T02:20:00Z',executors={'TWSE_MIS':lambda tids,**k:{'targets':{}},'TWSE_OPENAPI':lambda tids,**k:{'targets':{}},'TPEX_OPENAPI':lambda tids,**k:{'targets':{}}},security_master=SM)
    assert out['status']!='success' and any(i['code']=='artifact_write_failed' for i in out['issues'])

def test_execute_authorization_rejections_and_cli(tmp_path):
    req=load(FIX/'mixed_snapshot_request.json'); plan=build_execution_plan(req,bundle_type='snapshot',security_master=SM)
    assert execute_watchlist(req,mode='execute',bundle_type='snapshot',artifact_root=str(tmp_path),security_master=SM)['status']=='authorization_failed'
    assert execute_watchlist(req,mode='execute',bundle_type='snapshot',authorization=auth(req,plan,authorized_request_hash='0'*64),artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z',security_master=SM)['status']=='authorization_failed'
    out=tmp_path/'out'; cmd=[sys.executable,'scripts/run_m8r_03d_watchlist_controlled_execution.py','--request',str(FIX/'mixed_snapshot_request.json'),'--mode','fixture','--bundle-type','snapshot','--fixture-source-data',str(FIX/'mixed_snapshot_source_data.json'),'--artifact-root',str(out),'--generated-at-utc','2026-07-16T01:30:05Z']
    assert subprocess.run(cmd,capture_output=True,text=True).returncode==0
    texts='\n'.join(p.read_text() for p in out.rglob('*.json'))
    assert not any(x in texts.lower() for x in ['"raw_payload"','cookies','session_id','access_token'])
