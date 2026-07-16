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
    lookup=load_verified_security_master_snapshot(FIX/'snapshot.json', FIX/'manifest.json', allow_fixture_snapshot=True).lookup
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
    lookup=load_verified_security_master_snapshot(FIX/'snapshot.json', FIX/'manifest.json', allow_fixture_snapshot=True).lookup
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
    validated=load_verified_security_master_snapshot(FIX/'snapshot.json', FIX/'manifest.json', allow_fixture_snapshot=True); snap=validated.snapshot; lookup=validated
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

def test_trust_gap_tampered_direct_snapshot_and_lookup_rejected():
    snap=load('snapshot.json')
    tampered=copy.deepcopy(snap); tampered['records'][0]['execution_eligibility']['status']='allowed'
    with pytest.raises(VerifiedSecurityMasterSnapshotError): build_execution_plan(_req(['TWSE:2330']),bundle_type='snapshot',security_master=tampered)
    validated=load_verified_security_master_snapshot(FIX/'snapshot.json', FIX/'manifest.json', allow_fixture_snapshot=True)
    bad_lookup=copy.deepcopy(validated.lookup); bad_lookup['by_canonical']['TWSE:2330']['record_hash']='fabricated'
    with pytest.raises(VerifiedSecurityMasterSnapshotError): build_execution_plan(_req(['TWSE:2330']),bundle_type='snapshot',security_master=bad_lookup)

def test_lifecycle_join_cross_market_ambiguous_event_quarantined():
    rec=load('classification_records.json'); ctx=load('source_context.json')
    ambiguous={"source_family":"twse_company_delisted","source_url":"https://www.twse.com.tw/zh/listed/suspend-listing.html","security_code":"3333","event_type":"twse_delisted","effective_date":"2026-01-01","evidence_status":"official_table"}
    snap,man=export_verified_security_master_snapshot(classification_records=rec,lifecycle_events=[ambiguous],source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    assert snap['coverage']['quarantined_lifecycle_event_count']==1
    assert snap['quarantined_lifecycle_events'][0]['quarantine_reason']=='lifecycle_identity_ambiguous'
    assert all(not (e.get('security_code')=='3333') for r in snap['records'] for e in r['lifecycle']['events'])
    precise={**ambiguous,'market':'tpex'}
    snap2,_=export_verified_security_master_snapshot(classification_records=rec,lifecycle_events=[precise],source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    tpex=[r for r in snap2['records'] if r['canonical_target_id']=='TPEX:3333'][0]
    twse=[r for r in snap2['records'] if r['canonical_target_id']=='TWSE:3333'][0]
    assert tpex['lifecycle']['events'] and not twse['lifecycle']['events']

def test_invalid_skill_inputs_rejected():
    rec=load('classification_records.json'); ctx=load('source_context.json')
    bad=copy.deepcopy(rec); bad[0]['classification']['classification_status']='bogus'
    with pytest.raises(Exception): export_verified_security_master_snapshot(classification_records=bad,lifecycle_events=[],source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    event={"source_family":"x","source_url":"not-url","security_code":"2330","event_type":"bad","effective_date":"bad","evidence_status":"bad"}
    with pytest.raises(Exception): export_verified_security_master_snapshot(classification_records=rec,lifecycle_events=[event],source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')

def test_manifest_strengthened_rejections_and_duplicate_isin_order_independent():
    snap=load('snapshot.json'); man=load('manifest.json')
    cases=[]
    for field, code in [('schema_sha256','schema_hash_mismatch'),('skill_contract_hash','skill_contract_hash_mismatch'),('lifecycle_event_count','lifecycle_event_count_mismatch'),('generated_at_utc','generated_at_mismatch')]:
        m=copy.deepcopy(man); m[field]='bad' if not isinstance(m[field],int) else m[field]+1; cases.append((snap,m,code))
    for s,m,code in cases:
        with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(s,m,allow_fixture_snapshot=True)
        assert code in str(e.value)
    dup=copy.deepcopy(snap); dup['records'][0]['identity']['isin']=dup['records'][1]['identity']['isin']; dup['records'][0]['record_hash']=sha256_json({k:v for k,v in dup['records'][0].items() if k!='record_hash'})
    m=copy.deepcopy(man); m['snapshot_sha256']=sha256_json(dup)
    with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(dup,m,allow_fixture_snapshot=True)
    assert 'duplicate_unresolved_isin_identity' in str(e.value)
    dup['records']=list(reversed(dup['records'])); m['snapshot_sha256']=sha256_json(dup)
    with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(dup,m,allow_fixture_snapshot=True)
    assert 'duplicate_unresolved_isin_identity' in str(e.value)

def test_fabricated_validated_wrapper_revalidated_and_rejected():
    validated=load_verified_security_master_snapshot(FIX/'snapshot.json', FIX/'manifest.json', allow_fixture_snapshot=True)
    tampered=copy.deepcopy(validated.snapshot); tampered['records'][0]['record_hash']='0'*64
    forged=ValidatedVerifiedSecurityMasterSnapshot(snapshot=tampered, manifest=validated.manifest, lookup=validated.lookup, validation={'valid':True})
    with pytest.raises(VerifiedSecurityMasterSnapshotError): build_execution_plan(_req(['TWSE:2330']),bundle_type='snapshot',security_master=forged)

def test_snapshot_and_manifest_json_schema_rejections():
    snap=load('snapshot.json'); man=load('manifest.json')
    s=copy.deepcopy(snap); del s['records'][0]['identity']
    m=copy.deepcopy(man); m['snapshot_sha256']=sha256_json(s)
    with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(s,m,allow_fixture_snapshot=True)
    assert 'snapshot_schema_invalid' in str(e.value)
    m2=copy.deepcopy(man); m2['record_count']='14'
    with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(snap,m2,allow_fixture_snapshot=True)
    assert 'manifest_schema_invalid' in str(e.value)

def test_duplicate_isin_policy_explicit_quarantine_only():
    snap=load('snapshot.json'); man=load('manifest.json')
    dup=copy.deepcopy(snap); dup['records'][0]['identity']['isin']=dup['records'][1]['identity']['isin']; dup['records'][0]['execution_eligibility']={'status':'blocked','reason_codes':['unsupported_instrument_type']}; dup['records'][0]['record_hash']=sha256_json({k:v for k,v in dup['records'][0].items() if k!='record_hash'})
    m=copy.deepcopy(man); m['snapshot_sha256']=sha256_json(dup)
    with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(dup,m,allow_fixture_snapshot=True)
    assert 'duplicate_unresolved_isin_identity' in str(e.value)
    for idx in (0,1):
        dup['records'][idx]['classification']['classification_status']='quarantine_conflict'; dup['records'][idx]['conflicts']=['identity_conflict']; dup['records'][idx]['execution_eligibility']={'status':'blocked','reason_codes':['classification_quarantine_or_conflict']}; dup['records'][idx]['record_hash']=sha256_json({k:v for k,v in dup['records'][idx].items() if k!='record_hash'})
    m['snapshot_sha256']=sha256_json(dup)
    assert validate_verified_security_master_snapshot(dup,m,allow_fixture_snapshot=True)['valid']

def test_conflicting_lifecycle_identity_keys_quarantined():
    rec=load('classification_records.json'); ctx=load('source_context.json')
    event={"source_family":"twse_company_delisted","source_url":"https://www.twse.com.tw/zh/listed/suspend-listing.html","security_code":"2330","canonical_target_id":"TPEX:6488","event_type":"twse_delisted","effective_date":"2026-01-01","evidence_status":"official_table"}
    snap,_=export_verified_security_master_snapshot(classification_records=rec,lifecycle_events=[event],source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    assert snap['quarantined_lifecycle_events'][0]['quarantine_reason']=='lifecycle_identity_conflict'
    assert all(not r['lifecycle']['events'] for r in snap['records'] if r['canonical_target_id'] in {'TWSE:2330','TPEX:6488'})

def test_isin_only_record_rejected_before_invalid_canonical_target():
    rec=load('classification_records.json'); ctx=load('source_context.json')
    bad=copy.deepcopy(rec[:1]); bad[0]['identity']['security_code']=None
    with pytest.raises(Exception) as e: export_verified_security_master_snapshot(classification_records=bad,lifecycle_events=[],source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    assert 'missing_runtime_identity' in str(e.value) or 'invalid_canonical_target_identity' in str(e.value)

def test_canonical_identity_mismatch_rejected():
    snap=load('snapshot.json'); man=load('manifest.json')
    for patch in [('canonical_target_id','TPEX:2330'),('canonical_target_id','TWSE:9999')]:
        s=copy.deepcopy(snap); s['records'][0][patch[0]]=patch[1]; s['records'][0]['record_hash']=sha256_json({k:v for k,v in s['records'][0].items() if k!='record_hash'})
        m=copy.deepcopy(man); m['snapshot_sha256']=sha256_json(s)
        with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(s,m,allow_fixture_snapshot=True)
        assert 'canonical_identity_mismatch' in str(e.value)

def test_quarantined_lifecycle_required_counts_and_duplicate_disposition():
    snap=load('snapshot.json'); man=load('manifest.json')
    s=copy.deepcopy(snap); del s['quarantined_lifecycle_events']; m=copy.deepcopy(man); m['snapshot_sha256']=sha256_json(s)
    with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(s,m,allow_fixture_snapshot=True)
    assert 'snapshot_schema_invalid' in str(e.value)
    s=copy.deepcopy(snap); s['coverage']['quarantined_lifecycle_event_count']=99; m=copy.deepcopy(man); m['coverage']=s['coverage']; m['snapshot_sha256']=sha256_json(s)
    with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(s,m,allow_fixture_snapshot=True)
    assert 'quarantined_lifecycle_event_count_mismatch' in str(e.value)
    rec=load('classification_records.json'); ctx=load('source_context.json')
    ev={"source_family":"twse_company_delisted","source_url":"https://www.twse.com.tw/zh/listed/suspend-listing.html","security_code":"2330","event_type":"twse_delisted","effective_date":"2026-01-01","evidence_status":"official_table","event_key":"dup-event"}
    s,m=export_verified_security_master_snapshot(classification_records=rec,lifecycle_events=[ev],source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    s['quarantined_lifecycle_events'].append({**ev,'event_id':'dup-event','quarantine_reason':'forced'}); s['coverage']['quarantined_lifecycle_event_count']=1; s['coverage']['total_lifecycle_event_count']=2; m['coverage']=s['coverage']; m['snapshot_sha256']=sha256_json(s)
    with pytest.raises(VerifiedSecurityMasterSnapshotError) as e: validate_verified_security_master_snapshot(s,m,allow_fixture_snapshot=True)
    assert 'duplicate_lifecycle_event_disposition' in str(e.value)

def test_lifecycle_total_count_and_dict_conflict_duplicate_isin():
    rec=load('classification_records.json'); ctx=load('source_context.json')
    ambiguous={"source_family":"twse_company_delisted","source_url":"https://www.twse.com.tw/zh/listed/suspend-listing.html","security_code":"3333","event_type":"twse_delisted","effective_date":"2026-01-01","evidence_status":"official_table"}
    s,m=export_verified_security_master_snapshot(classification_records=rec,lifecycle_events=load('lifecycle_events.json')+[ambiguous],source_context=ctx,generated_at_utc='2026-07-16T00:00:00Z',effective_observation_date='2026-07-16')
    assert s['coverage']['total_lifecycle_event_count']==s['coverage']['lifecycle_event_count']+s['coverage']['quarantined_lifecycle_event_count']
    assert m['coverage']['total_lifecycle_event_count']==m['coverage']['lifecycle_event_count']+m['coverage']['quarantined_lifecycle_event_count']
    snap=load('snapshot.json'); man=load('manifest.json')
    dup=copy.deepcopy(snap); dup['records'][0]['identity']['isin']=dup['records'][1]['identity']['isin']
    for idx in (0,1):
        dup['records'][idx]['classification']['classification_status']='confirmed_dual_lane'; dup['records'][idx]['conflicts']=[{'category':'identity_conflict','severity':'hard','field':'isin'}]; dup['records'][idx]['record_hash']=sha256_json({k:v for k,v in dup['records'][idx].items() if k!='record_hash'})
    mm=copy.deepcopy(man); mm['snapshot_sha256']=sha256_json(dup)
    assert validate_verified_security_master_snapshot(dup,mm,allow_fixture_snapshot=True)['valid']
