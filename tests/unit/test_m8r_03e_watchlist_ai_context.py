import json, subprocess, sys
from pathlib import Path
import pytest
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package, build_context_manifest, render_watchlist_ai_context_preview
from scripts.m8r_03e_conversation_handoff_builder import build_watchlist_conversation_handoff
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package, validate_watchlist_conversation_handoff, validate_watchlist_ai_context_manifest, ptr_get, sha256_json, schema_bundle_sha256
FIX=Path('tests/fixtures/m8r_03e')
def loadcase(name):
    p=FIX/name
    return [json.loads((p/f).read_text()) for f in ['request.json','execution_plan.json','execution_result.json','bundle.json']]
def build(name, ts='2026-07-16T03:00:00Z', policy=None):
    req,plan,res,bundle=loadcase(name)
    pkg=build_watchlist_ai_context_package(validated_request=req,execution_plan=plan,execution_result=res,watchlist_bundle=bundle,generated_at_utc=ts,context_policy=policy)
    hand=build_watchlist_conversation_handoff(context_package=pkg,generated_at_utc=ts)
    man=build_context_manifest(context_package=pkg,conversation_handoff=hand,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle},generated_at_utc=ts)
    return req,plan,res,bundle,pkg,hand,man

def test_package_determinism_and_manifest():
    a=build('complete_snapshot'); b=build('complete_snapshot')
    assert a[4:]==b[4:]
    assert validate_watchlist_ai_context_package(a[4])['valid']
    assert validate_watchlist_conversation_handoff(a[5],context_package=a[4])['valid']
    assert validate_watchlist_ai_context_manifest(a[6],context_package=a[4],handoff=a[5])['valid']
    assert a[6]['schema_bundle_sha256']==schema_bundle_sha256()

def test_identity_lineage_order_and_citations():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    assert [t['target_id'] for t in pkg['targets']]==pkg['request']['enabled_target_order']
    for t in pkg['targets']:
        assert 'snapshot_id' in t['identity'] and 'record_id' in t['identity'] and 'record_hash' in t['identity']
        assert t['citations']
    for c in pkg['citation_index']:
        assert sha256_json(ptr_get(pkg,c['fact_path']))==c['value_hash']

def test_currentness_distinctions_and_stale_disclosure():
    *_,pkg,hand,man=build('stale_currentness_unresolved')
    statuses=[t['current_observation'].get('currentness_status') for t in pkg['targets'] if t['current_observation']]
    assert 'stale' in statuses or any(m['reason_code'] in {'stale_observation','currentness_unresolved'} for m in pkg['missing_evidence'])
    for t in pkg['targets']:
        co=t['current_observation']
        if co:
            assert co.get('source_timestamp') != co.get('retrieved_at_utc')

def test_partial_all_failure_and_blocked_handoff():
    for name,status in [('partial_source_failure','partial'),('all_source_failure','failed'),('blocked_target','blocked')]:
        *_,pkg,hand,man=build(name)
        assert pkg['coverage_summary']['coverage_status']==status
        assert hand['unsupported_questions']
        assert not any(t['current_observation'] for t in pkg['targets']) if name in {'all_source_failure','blocked_target'} else True
        assert validate_watchlist_ai_context_package(pkg)['valid']

def test_performance_uses_upstream_unadjusted_and_insufficient_not_zero():
    *_,pkg,hand,man=build('performance')
    assert any(t['performance'] for t in pkg['targets'])
    assert any(p['code']=='do_not_claim_adjusted_return' for p in pkg['prohibitions'])
    assert not any(t['performance'].get('unadjusted_price_return') == 0 for t in pkg['targets'] if t['coverage']['evidence_states']['performance']=='unavailable')

def test_security_forbidden_recursive_rejected():
    *_,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(pkg)); bad['targets'][0]['current_observation']['raw_payload']={'x':1}; bad['package_hash']='0'*64
    got=validate_watchlist_ai_context_package(bad)
    assert not got['valid'] and 'forbidden_field' in {i['code'] for i in got['issues']}

def test_citation_integrity_failures():
    *_,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(pkg)); bad['citation_index'][0]['value_hash']='0'*64; bad['package_hash']='0'*64
    assert 'citation_value_hash_mismatch' in {i['code'] for i in validate_watchlist_ai_context_package(bad)['issues']}
    bad=json.loads(json.dumps(pkg)); bad['citation_index'].append(bad['citation_index'][0]); bad['package_hash']='0'*64
    assert 'duplicate_citation_id' in {i['code'] for i in validate_watchlist_ai_context_package(bad)['issues']}
    bad=json.loads(json.dumps(pkg)); bad['citation_index'][0]['fact_path']='/bad/path'; bad['package_hash']='0'*64
    assert 'citation_fact_path_mismatch' in {i['code'] for i in validate_watchlist_ai_context_package(bad)['issues']}

def test_manifest_mismatches_rejected():
    *_,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(man)); bad['context_package_sha256']='0'*64
    assert 'package_hash_mismatch' in {i['code'] for i in validate_watchlist_ai_context_manifest(bad,context_package=pkg,handoff=hand)['issues']}
    bad=json.loads(json.dumps(man)); bad['schema_bundle_sha256']='0'*64
    assert 'schema_hash_mismatch' in {i['code'] for i in validate_watchlist_ai_context_manifest(bad,context_package=pkg,handoff=hand)['issues']}

def test_context_budget_truncates_without_target_removal():
    *_,pkg,hand,man=build('context_budget_pressure',policy={'max_caveat_entries':0})
    assert [t['target_id'] for t in pkg['targets']]==pkg['request']['enabled_target_order']
    assert pkg['context_budget']['truncated']
    assert 'context_truncated' in pkg['caveats']

def test_preview_has_only_package_sections():
    *_,pkg,hand,man=build('complete_snapshot')
    md=render_watchlist_ai_context_preview(pkg)
    assert 'Request summary' in md and 'Source lineage' in md and pkg['targets'][0]['target_id'] in md

def test_cli_success_url_rejected_and_write_failure(tmp_path):
    case=FIX/'complete_snapshot'; out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_m8r_03e_watchlist_ai_context_handoff.py','--request',str(case/'request.json'),'--execution-plan',str(case/'execution_plan.json'),'--execution-result',str(case/'execution_result.json'),'--bundle',str(case/'bundle.json'),'--output-root',str(out),'--generated-at-utc','2026-07-16T03:00:00Z']
    r=subprocess.run(cmd,capture_output=True,text=True)
    assert r.returncode==0, r.stderr
    assert list(out.rglob('watchlist_ai_context.json'))
    r=subprocess.run(cmd,capture_output=True,text=True)
    assert r.returncode!=0 and 'output_run_directory_exists' in r.stderr
    bad=cmd.copy(); bad[bad.index('--request')+1]='https://example.invalid/request.json'; bad[bad.index('--output-root')+1]=str(tmp_path/'out2')
    r=subprocess.run(bad,capture_output=True,text=True)
    assert r.returncode!=0 and 'url_input_rejected' in r.stderr
