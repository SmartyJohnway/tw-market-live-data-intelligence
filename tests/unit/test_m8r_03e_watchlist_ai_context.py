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
    assert validate_watchlist_ai_context_package(a[4], upstream_artifacts={'validated_request':a[0],'execution_plan':a[1],'execution_result':a[2],'watchlist_bundle':a[3]})['valid']
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
        req,plan,res,bundle=loadcase(name); assert validate_watchlist_ai_context_package(pkg, upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle})['valid']

def test_performance_uses_upstream_unadjusted_and_insufficient_not_zero():
    *_,pkg,hand,man=build('performance')
    assert any(t['performance'] for t in pkg['targets'])
    assert any(p['code']=='unadjusted_completed_eod_price_return' for p in pkg['evidence_limitations'])
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

def test_upstream_mixed_request_plan_result_bundle_rejected():
    req,plan,res,bundle=loadcase('complete_snapshot')
    bad_req=json.loads(json.dumps(req)); bad_req['request_id']='other-request'
    from scripts.m8r_03e_context_validator import validate_m8r_03e_upstream_artifacts
    got=validate_m8r_03e_upstream_artifacts(validated_request=bad_req,execution_plan=plan,execution_result=res,watchlist_bundle=bundle)
    assert not got['valid'] and {'request_id_mismatch','request_hash_mismatch'} & {i['code'] for i in got['issues']}

def test_upstream_plan_id_mismatch_rejected():
    req,plan,res,bundle=loadcase('complete_snapshot')
    bad=json.loads(json.dumps(res)); bad['plan_id']='m8r03d-plan-bad'
    from scripts.m8r_03e_context_validator import validate_m8r_03e_upstream_artifacts
    got=validate_m8r_03e_upstream_artifacts(validated_request=req,execution_plan=plan,execution_result=bad,watchlist_bundle=bundle)
    assert 'plan_id_mismatch' in {i['code'] for i in got['issues']}

def test_upstream_target_order_mismatch_rejected():
    req,plan,res,bundle=loadcase('complete_snapshot')
    bad=json.loads(json.dumps(bundle)); bad['coverage']['requested_target_ids']=list(reversed(bad['coverage']['requested_target_ids']))
    from scripts.m8r_03e_context_validator import validate_m8r_03e_upstream_artifacts
    got=validate_m8r_03e_upstream_artifacts(validated_request=req,execution_plan=plan,execution_result=res,watchlist_bundle=bad)
    assert 'target_order_mismatch' in {i['code'] for i in got['issues']}

def test_missing_source_artifact_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    got=validate_watchlist_ai_context_package(pkg,upstream_artifacts={'execution_plan':plan})
    assert 'citation_source_artifact_missing' in {i['code'] for i in got['issues']}

def test_bad_source_artifact_id_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad_plan=json.loads(json.dumps(plan)); bad_plan['plan_id']='m8r03d-plan-bad'
    got=validate_watchlist_ai_context_package(pkg,upstream_artifacts={'validated_request':req,'execution_plan':bad_plan,'execution_result':res,'watchlist_bundle':bundle})
    assert 'citation_source_artifact_id_mismatch' in {i['code'] for i in got['issues']}

def test_exact_source_value_mismatch_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad_bundle=json.loads(json.dumps(bundle)); bad_bundle['targets'][0]['current_evidence']['facts']['latest_price']=999999
    got=validate_watchlist_ai_context_package(pkg,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bad_bundle})
    assert 'citation_source_value_hash_mismatch' in {i['code'] for i in got['issues']}

def test_uncited_current_fact_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(pkg)); bad['citation_index']=[c for c in bad['citation_index'] if '/current_observation/latest_price' not in c['fact_path']]; bad['targets'][0]['citations']=[c for c in bad['targets'][0]['citations'] if c in {x['citation_id'] for x in bad['citation_index']}]; bad['package_hash']='0'*64
    got=validate_watchlist_ai_context_package(bad,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle})
    assert 'uncited_material_fact' in {i['code'] for i in got['issues']}

def test_uncited_identity_fact_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(pkg)); bad['citation_index']=[c for c in bad['citation_index'] if '/identity/security_code' not in c['fact_path']]; bad['targets'][0]['citations']=[c for c in bad['targets'][0]['citations'] if c in {x['citation_id'] for x in bad['citation_index']}]; bad['package_hash']='0'*64
    got=validate_watchlist_ai_context_package(bad,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle})
    assert 'missing_identity_citation' in {i['code'] for i in got['issues']}

def test_manifest_upstream_hash_mismatch_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(man)); bad['upstream']['request_hash']='0'*64
    got=validate_watchlist_ai_context_manifest(bad,context_package=pkg,handoff=hand,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle})
    assert 'upstream_hash_or_id_mismatch' in {i['code'] for i in got['issues']}

def test_manifest_count_mismatch_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(man)); bad['counts']['citation_count']=-1
    got=validate_watchlist_ai_context_manifest(bad,context_package=pkg,handoff=hand,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle})
    assert 'manifest_count_mismatch' in {i['code'] for i in got['issues']}

def test_citation_limit_deterministic():
    a=build('complete_snapshot',policy={'max_citations_per_target':4})[4]
    b=build('complete_snapshot',policy={'max_citations_per_target':4})[4]
    assert a==b and a['context_budget']['truncated']
    assert all(t['identity'] for t in a['targets'])
    assert all(not t['current_observation'] and not t['eod_reference'] for t in a['targets'])

def test_serialized_byte_limit_deterministic():
    a=build('complete_snapshot',policy={'max_serialized_bytes':5000})[4]
    b=build('complete_snapshot',policy={'max_serialized_bytes':5000})[4]
    assert a==b and a['context_budget']['truncated'] and 'context_truncated' in a['caveats']
    assert [t['target_id'] for t in a['targets']]==a['request']['enabled_target_order']

def test_cli_reread_source_validation_remains_active(tmp_path):
    case=FIX/'complete_snapshot'; out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_m8r_03e_watchlist_ai_context_handoff.py','--request',str(case/'request.json'),'--execution-plan',str(case/'execution_plan.json'),'--execution-result',str(case/'execution_result.json'),'--bundle',str(case/'bundle.json'),'--output-root',str(out),'--generated-at-utc','2026-07-16T03:00:00Z']
    r=subprocess.run(cmd,capture_output=True,text=True)
    assert r.returncode==0, r.stderr
    manifest=json.loads(next(out.rglob('watchlist_ai_context_manifest.json')).read_text())
    assert manifest['validation_status']=='passed'

def test_budget_removes_current_coverage_and_handoff_latest_not_answerable():
    *_,pkg,hand,man=build('complete_snapshot',policy={'max_citations_per_target':4})
    assert pkg['coverage_summary']['target_count_with_current_observation']==0
    assert not any(q['category']=='latest_supplied_observations' for q in hand['answerable_questions'])
    assert any(m['reason_code']=='context_budget_omitted' for m in pkg['missing_evidence'])

def test_uncited_lifecycle_state_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(pkg)); bad['citation_index']=[c for c in bad['citation_index'] if '/lifecycle/lifecycle_state' not in c['fact_path']]; bad['targets'][0]['citations']=[c for c in bad['targets'][0]['citations'] if c in {x['citation_id'] for x in bad['citation_index']}]; bad['package_hash']='0'*64
    got=validate_watchlist_ai_context_package(bad,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle})
    assert 'uncited_material_fact' in {i['code'] for i in got['issues']}

def test_tampered_lifecycle_state_source_hash_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad_plan=json.loads(json.dumps(plan)); bad_plan['targets'][0]['lifecycle_state']='terminated'
    got=validate_watchlist_ai_context_package(pkg,upstream_artifacts={'validated_request':req,'execution_plan':bad_plan,'execution_result':res,'watchlist_bundle':bundle})
    assert 'citation_source_value_hash_mismatch' in {i['code'] for i in got['issues']}

def test_uncited_execution_policy_rejected():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    bad=json.loads(json.dumps(pkg)); bad['citation_index']=[c for c in bad['citation_index'] if '/lifecycle/execution_policy' not in c['fact_path'] and '/execution_eligibility/execution_policy' not in c['fact_path']]; bad['targets'][0]['citations']=[c for c in bad['targets'][0]['citations'] if c in {x['citation_id'] for x in bad['citation_index']}]; bad['package_hash']='0'*64
    got=validate_watchlist_ai_context_package(bad,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle})
    assert 'uncited_material_fact' in {i['code'] for i in got['issues']}

def test_final_serialized_byte_count_and_unsatisfied_budget_reported():
    *_,pkg,hand,man=build('complete_snapshot',policy={'max_serialized_bytes':200})
    assert pkg['context_budget']['final_serialized_bytes']>0
    assert pkg['context_budget']['byte_budget_satisfied'] is False
    assert pkg['context_budget']['minimum_required_context_exceeds_byte_budget'] is True
    assert pkg['context_budget']['overall_budget_status']=='unsatisfied'

def test_normal_bundle_generated_after_execution_start_is_accepted_and_lineage_partial():
    req,plan,res,bundle=loadcase('complete_snapshot')
    later=json.loads(json.dumps(bundle)); later['generated_at_utc']='2026-07-16T09:09:09Z'
    from scripts.m8r_03e_context_validator import validate_m8r_03e_upstream_artifacts
    got=validate_m8r_03e_upstream_artifacts(validated_request=req,execution_plan=plan,execution_result=res,watchlist_bundle=later)
    assert got['valid']
    *_,pkg,hand,man=build('complete_snapshot')
    assert pkg['source_lineage']['lineage_status']=='partial'
    assert pkg['source_lineage']['lineage_missing_fields']==['execution_result_bundle_id','execution_result_bundle_hash']

def test_manifest_fact_count_unique_paths_differs_from_citation_count_when_duplicate():
    req,plan,res,bundle,pkg,hand,man=build('complete_snapshot')
    dup=json.loads(json.dumps(pkg)); dup['citation_index'].append(json.loads(json.dumps(dup['citation_index'][0]))); dup['citation_index'][-1]['citation_id']='cite-1234567890abcdef1234'; dup['targets'][0]['citations'].append('cite-1234567890abcdef1234'); dup['package_hash']='0'*64
    hand2=build_watchlist_conversation_handoff(context_package=pkg,generated_at_utc='2026-07-16T03:00:00Z')
    man2=build_context_manifest(context_package=dup,conversation_handoff=hand2,upstream_artifacts={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle},generated_at_utc='2026-07-16T03:00:00Z')
    assert man2['counts']['fact_count'] < man2['counts']['citation_count']


def test_recorded_serialized_bytes_equal_canonical_size_and_include_final_hash():
    *_,pkg,hand,man=build('complete_snapshot')
    assert pkg['context_budget']['serialized_size_basis']=='canonical_json_utf8_final_package_including_package_hash'
    assert pkg['package_hash'] and len(pkg['package_hash'])==64
    assert pkg['context_package_id']
    from scripts.m8r_03e_context_validator import canonical_json
    assert pkg['context_budget']['final_serialized_bytes']==len(canonical_json(pkg).encode())

def test_mandatory_citations_exceeding_cap_retained_and_reported():
    *_,pkg,hand,man=build('complete_snapshot',policy={'max_citations_per_target':1})
    assert pkg['context_budget']['citation_budget_satisfied'] is False
    assert pkg['context_budget']['targets_exceeding_citation_budget']
    assert pkg['context_budget']['mandatory_citation_count']>0
    assert pkg['context_budget']['final_citation_count']==len(pkg['citation_index'])
    assert pkg['context_budget']['overall_budget_status']=='unsatisfied'
    assert all(t['identity'] for t in pkg['targets'])

def test_unused_lifecycle_event_summary_policy_marked_reserved():
    *_,pkg,hand,man=build('complete_snapshot')
    assert pkg['context_budget']['policy_notes']['max_lifecycle_event_summaries_per_target'].startswith('reserved_not_applicable')
