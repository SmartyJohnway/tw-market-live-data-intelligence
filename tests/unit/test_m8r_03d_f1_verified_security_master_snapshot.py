import copy, json, subprocess, sys
from pathlib import Path
import pytest
from scripts.m8r_03d_f1_security_master_snapshot_exporter import export_verified_security_master_snapshot, sha256_json
from scripts.m8r_03d_f1_security_master_snapshot_adapter import *
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan

FIX=Path('tests/fixtures/m8r_03d_f1')
def load(n): return json.loads((FIX/n).read_text(encoding='utf-8'))

def test_snapshot_export_deterministic_manifest_and_hashes():
    rec=load('classification_records.json'); ev=load('lifecycle_events.json'); ctx=load('source_context.json')
    a,b=export_verified_security_master_snapshot(classification_records=rec,lifecycle_events=ev,source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    a2,b2=export_verified_security_master_snapshot(classification_records=rec,lifecycle_events=ev,source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    assert a==a2 and b==b2 and b['snapshot_sha256']==sha256_json(a)
    assert a['coverage']['record_count']==14 and a['coverage']['lifecycle_event_count']==2
    assert all(r['record_hash']==sha256_json({k:v for k,v in r.items() if k!='record_hash'}) for r in a['records'])
    assert {e['event_id'] for r in a['records'] for e in r['lifecycle']['events']} >= {'delist-7777','suspend-6666'}

def test_loader_rejects_drift_and_raw_fields():
    snap=load('snapshot.json'); man=load('manifest.json')
    assert validate_verified_security_master_snapshot(snap,man)['valid']
    cases=[]
    s=copy.deepcopy(snap); s['schema_version']='bad'; cases.append((s,man,'unsupported_snapshot_schema'))
    m=copy.deepcopy(man); m['snapshot_sha256']='0'; cases.append((snap,m,'snapshot_hash_mismatch'))
    s=copy.deepcopy(snap); s['records'][0]['record_hash']='0'; m=copy.deepcopy(man); m['snapshot_sha256']=sha256_json(s); cases.append((s,m,'record_hash_mismatch'))
    s=copy.deepcopy(snap); s['records'][1]['canonical_target_id']=s['records'][0]['canonical_target_id']; m=copy.deepcopy(man); m['snapshot_sha256']=sha256_json(s); cases.append((s,m,'duplicate_canonical_target_id'))
    s=copy.deepcopy(snap); s['records'][0]['raw_html']='<table>'; m=copy.deepcopy(man); m['snapshot_sha256']=sha256_json(s); cases.append((s,m,'forbidden_raw_field'))
    m=copy.deepcopy(man); m['validation_status']='failed'; cases.append((snap,m,'manifest_validation_not_passed'))
    for s,m,code in cases:
        with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(s,m)
        assert code in str(e.value)

def test_classification_lifecycle_and_observation_policy():
    lookup=build_verified_security_master_lookup(load('snapshot.json'))
    def sel(q, **kw): return resolve_verified_security_identity(q, lookup, allow_fixture_snapshot=kw.get('allow',False))['selected']
    assert sel('TWSE:2330')['classification']['instrument_type']=='common_share'
    assert sel('TWSE:0050')['classification']['instrument_type']=='etf'
    assert sel('TWSE:2881A')['execution_eligibility']['status']=='blocked'
    assert sel('TWSE:1234')['execution_eligibility']['status']=='blocked'
    assert resolve_verified_security_identity('TWSE:9999',lookup)['resolution_status']=='quarantined'
    assert sel('TWSE:7777')['lifecycle']['state']=='terminated'
    assert sel('TWSE:6666')['lifecycle']['state']=='suspended'
    assert sel('TWSE:2222')['lifecycle']['state']=='unknown'
    assert resolve_verified_security_identity('TWSE:8888',lookup)['resolution_status']=='quarantined'
    assert resolve_verified_security_identity('TWSE:8888',lookup,allow_fixture_snapshot=True)['resolution_status']=='resolved'

def test_resolution_exact_and_ambiguous():
    lookup=build_verified_security_master_lookup(load('snapshot.json'))
    assert resolve_verified_security_identity('TW0002330008',lookup)['selected']['canonical_target_id']=='TWSE:2330'
    assert resolve_verified_security_identity('2330',lookup,market_context='TWSE')['selected']['canonical_target_id']=='TWSE:2330'
    assert resolve_verified_security_identity('台積電',lookup)['selected']['canonical_target_id']=='TWSE:2330'
    assert resolve_verified_security_identity('TSMC',lookup)['selected']['canonical_target_id']=='TWSE:2330'
    assert resolve_verified_security_identity('重名股',lookup)['resolution_status']=='ambiguous'
    assert resolve_verified_security_identity('NOPE',lookup)['resolution_status']=='not_found'
    assert resolve_verified_security_identity('3333',lookup)['resolution_status']=='ambiguous'
    assert resolve_verified_security_identity('3333',lookup,market_context='TWSE')['selected']['canonical_target_id']=='TWSE:3333'

def _req(ids):
    req=json.loads(Path('tests/fixtures/m8r_03d/mixed_snapshot_request.json').read_text())
    req['request_id']='req-f1'
    req['persistent_watchlist_reference']['enabled_target_ids']=ids
    return req

def test_m8r03d_planner_consumes_verified_snapshot_and_fails_closed(tmp_path):
    snap=load('snapshot.json'); lookup=build_verified_security_master_lookup(snap)
    plan=build_execution_plan(_req(['TWSE:2330','TPEX:6488','TWSE:0050']),bundle_type='snapshot',security_master=lookup)
    by={t['target_id']:t for t in plan['targets']}
    assert by['TWSE:2330']['current_source_plan']['route']=='tse_2330.tw' and by['TWSE:2330']['snapshot_id']=='fixture-m8r03d-f1'
    assert by['TPEX:6488']['current_source_plan']['route']=='otc_6488.tw' and by['TPEX:6488']['eod_source_plan']['source_family']=='TPEX_OPENAPI'
    assert by['TWSE:0050']['identity_status']=='resolved' and by['TWSE:0050']['record_hash']
    blocked=build_execution_plan(_req(['TWSE:7777','TWSE:9999','TWSE:1234','TWSE:8888']),bundle_type='snapshot',security_master=lookup)
    assert not blocked['source_call_groups']
    assert {t['identity_status'] for t in blocked['targets']} >= {'lifecycle_unsupported','identity_conflict','unsupported_instrument'}
    bad=tmp_path/'bad.json'; man=tmp_path/'man.json'; bad.write_text(json.dumps(snap),encoding='utf-8'); m=load('manifest.json'); m['snapshot_sha256']='bad'; man.write_text(json.dumps(m),encoding='utf-8')
    with pytest.raises(VerifiedSecurityMasterSnapshotError): build_execution_plan(_req(['TWSE:2330']),bundle_type='snapshot',verified_snapshot_path=str(bad),verified_snapshot_manifest_path=str(man))

def test_non_network_clis():
    export_cmd=[sys.executable,'scripts/export_m8r_03d_f1_verified_security_master_snapshot.py','--classification-input',str(FIX/'classification_records.json'),'--lifecycle-events',str(FIX/'lifecycle_events.json'),'--source-context',str(FIX/'source_context.json'),'--output','/tmp/f1_snapshot.json','--manifest-output','/tmp/f1_manifest.json','--generated-at-utc','2026-07-16T00:00:00Z','--effective-observation-date','2026-07-16']
    assert subprocess.run(export_cmd,capture_output=True,text=True).returncode==0
    for q in ['2330','台積電','重名股','TWSE:7777']:
        r=subprocess.run([sys.executable,'scripts/resolve_m8r_03d_f1_security_identity.py','--snapshot','/tmp/f1_snapshot.json','--manifest','/tmp/f1_manifest.json','--query',q,'--allow-fixture-snapshot'],capture_output=True,text=True)
        assert r.returncode==0 and 'm8r_03d_f1_security_identity_resolution.v1' in r.stdout
