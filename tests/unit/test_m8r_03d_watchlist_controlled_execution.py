import json, subprocess, sys
from pathlib import Path
import pytest
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan, canonical_request_hash, validate_authorization, AUTH_SCHEMA_VERSION, MAX_WATCHLIST_TARGETS
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_watchlist_source_integration import normalize_twse_mis_watchlist_observation, normalize_twse_openapi_watchlist_observation
FIX=Path('tests/fixtures/m8r_03d'); C=Path('tests/fixtures/m8r_03c')
def load(p): return json.loads(Path(p).read_text())
def auth(req,plan,**kw):
    return {'schema_version':AUTH_SCHEMA_VERSION,'authorization_id':'auth-1','issued_at_utc':'2026-07-16T00:00:00Z','expires_at_utc':'2026-07-17T00:00:00Z','authorized_request_hash':canonical_request_hash(req),'authorized_bundle_types':['snapshot','performance'],'authorized_source_families':['TWSE_MIS','TWSE_OPENAPI','TPEX_OPENAPI'],'authorized_target_ids':plan['target_order'],'max_target_count':MAX_WATCHLIST_TARGETS,'network_execution_allowed':True,'one_shot_only':True,'polling_allowed':False,'scheduler_allowed':False,'persistent_storage_allowed':False,'raw_payload_retention_allowed':False,'operator_approval':{},**kw}

def test_authorization_accepts_and_rejects_bounds():
    req=load(C/'snapshot_request.json'); plan=build_execution_plan(req,bundle_type='snapshot')
    assert validate_authorization(auth(req,plan),request=req,plan=plan,bundle_type='snapshot',now_utc='2026-07-16T01:00:00Z')['valid']
    cases=[({'expires_at_utc':'2026-07-15T00:00:00Z'},'authorization_expired'),({'authorized_request_hash':'x'},'request_hash_mismatch'),({'authorized_target_ids':['TWSE:2330']},'unauthorized_target'),({'authorized_source_families':['TWSE_MIS']},'unauthorized_source_family'),({'authorized_bundle_types':['performance']},'unauthorized_bundle_type'),({'polling_allowed':True},'authorization_flag_rejected'),({'raw_payload_retention_allowed':True},'authorization_flag_rejected')]
    for patch,code in cases:
        got=validate_authorization(auth(req,plan,**patch),request=req,plan=plan,bundle_type='snapshot',now_utc='2026-07-16T01:00:00Z')
        assert code in {i['code'] for i in got['issues']}

def test_plan_deterministic_routes_identity_and_limit():
    req=load(FIX/'mixed_snapshot_request.json'); p1=build_execution_plan(req,bundle_type='snapshot'); p2=build_execution_plan(req,bundle_type='snapshot')
    assert p1['plan_id']==p2['plan_id']; assert p1['target_order']==['TWSE:2330','TPEX:6488']
    by={t['target_id']:t for t in p1['targets']}; assert by['TWSE:2330']['current_source_plan']['route']=='tse_2330.tw'; assert by['TPEX:6488']['current_source_plan']['route']=='otc_6488.tw'; assert by['TPEX:6488']['eod_source_plan']['source_family']=='TPEX_OPENAPI'
    bad=json.loads(json.dumps(req)); bad['persistent_watchlist_reference']['enabled_target_ids']=['BAD']
    p=build_execution_plan(bad,bundle_type='snapshot'); assert p['targets'][0]['identity_status']=='unresolved'; assert p['source_call_groups']==[]
    over=json.loads(json.dumps(req)); over['persistent_watchlist_reference']['enabled_target_ids']=[f'TWSE:{i:04d}' for i in range(11)]
    assert any(i['code']=='target_limit_exceeded' for i in build_execution_plan(over,bundle_type='snapshot')['issues'])

def test_normalization_safe_fields_and_raw_rejected():
    target=build_execution_plan(load(C/'snapshot_request.json'),bundle_type='snapshot')['targets'][0]
    obs=normalize_twse_mis_watchlist_observation({'price':1,'change':2,'source_timestamp':'2026-07-16T01:00:00Z','retrieved_at':'2026-07-16T01:00:01Z'},target)
    assert obs['facts']['latest_price']==1 and obs['retrieved_at_utc']!=obs['source_timestamp']
    eod=normalize_twse_openapi_watchlist_observation({'trade_date':'2026-07-15','retrieved_at_utc':'2026-07-16T01:00:01Z','price':{'open':'1','high':'2','low':'1','close':'2'},'activity':{'trade_volume':3}},target)
    assert eod['facts']['volume']==3 and eod['trade_date']=='2026-07-15'
    with pytest.raises(ValueError): normalize_twse_mis_watchlist_observation({'raw_payload':{}},target)

def test_fixture_snapshot_performance_and_partial(tmp_path):
    req=load(C/'snapshot_request.json'); out=execute_watchlist(req,mode='fixture',bundle_type='snapshot',fixture_source_data=load(FIX/'snapshot_source_data.json'),artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z')
    assert out['status']=='success' and out['observation_count']==4
    perf=execute_watchlist(load(C/'performance_request.json'),mode='fixture',bundle_type='performance',fixture_source_data=load(FIX/'performance_source_data.json'),artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z')
    assert perf['status']=='success' and perf['observation_count']==42
    partial=load(FIX/'snapshot_source_data.json'); del partial['targets']['TWSE:2317']['TWSE_MIS']
    out=execute_watchlist(req,mode='fixture',bundle_type='snapshot',fixture_source_data=partial,artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z')
    assert out['status']=='success_with_partial_coverage'

def test_execute_authorization_rejections_and_cli(tmp_path):
    req=load(C/'snapshot_request.json'); plan=build_execution_plan(req,bundle_type='snapshot')
    assert execute_watchlist(req,mode='execute',bundle_type='snapshot',artifact_root=str(tmp_path))['status']=='authorization_failed'
    assert execute_watchlist(req,mode='execute',bundle_type='snapshot',authorization=auth(req,plan,authorized_request_hash='bad'),artifact_root=str(tmp_path),generated_at_utc='2026-07-16T01:30:05Z')['status']=='authorization_failed'
    out=tmp_path/'out'; cmd=[sys.executable,'scripts/run_m8r_03d_watchlist_controlled_execution.py','--request',str(C/'snapshot_request.json'),'--mode','fixture','--bundle-type','snapshot','--fixture-source-data',str(FIX/'snapshot_source_data.json'),'--artifact-root',str(out),'--generated-at-utc','2026-07-16T01:30:05Z']
    assert subprocess.run(cmd,capture_output=True,text=True).returncode==0
    texts='\n'.join(p.read_text() for p in out.rglob('*.json'))
    assert not any(x in texts.lower() for x in ['"raw_payload"','cookies','session_id','access_token'])
