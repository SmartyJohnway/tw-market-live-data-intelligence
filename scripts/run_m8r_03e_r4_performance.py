#!/usr/bin/env python3
"""R4 non-network benchmark. Counters exist only while this runner is executing."""
from __future__ import annotations
import argparse, copy, gc, hashlib, json, platform, statistics, subprocess, sys, tempfile, time, tracemalloc
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.run_m8r_03e_performance_baseline import _load_case,_truncate_to_first_target
import scripts.m8r_03e_context_validator as validator
import scripts.m8r_03e_watchlist_ai_context_builder as builder
from scripts.m8r_03e_conversation_handoff_builder import compose_conversation_handoff,build_watchlist_conversation_handoff
from scripts.m8r_03e_v1_to_v2_migration import migrate_watchlist_ai_context_package_v1_to_v2
from scripts.m8r_filesystem_safety import atomic_write_text
UNSUPPORTED_EXPECTATIONS={'10_target_snapshot':{'expected_target_count':10,'tier':'production_contract','non_contract':False,'not_authorized_for_production_request':False,'reason_code':'schema_valid_10_target_upstream_fixture_unavailable'},'50_target_stress':{'expected_target_count':50,'tier':'stress_only','non_contract':True,'not_authorized_for_production_request':True,'reason_code':'schema_valid_10_target_upstream_fixture_unavailable'},'100_target_stress':{'expected_target_count':100,'tier':'stress_only','non_contract':True,'not_authorized_for_production_request':True,'reason_code':'schema_valid_10_target_upstream_fixture_unavailable'},'high_citation_pressure':{'expected_target_count':None,'tier':'production_contract','non_contract':False,'not_authorized_for_production_request':False,'reason_code':'pressure_fixture_unavailable'},'combined_citation_and_missing_evidence_pressure':{'expected_target_count':None,'tier':'production_contract','non_contract':False,'not_authorized_for_production_request':False,'reason_code':'pressure_fixture_unavailable'}}
SCENARIOS=['1_target_snapshot','10_target_snapshot','50_target_stress','100_target_stress','high_citation_pressure','high_missing_evidence_pressure','combined_citation_and_missing_evidence_pressure','complete_snapshot','performance_package','partial_source_failure','all_source_failure','conversation_handoff_policy_a','conversation_handoff_policy_b','v1_to_v2_migration','artifact_serialization_only','safe_atomic_artifact_write','manifest_generation']
def clock(fn):
 s=time.perf_counter_ns(); x=fn(); return x,(time.perf_counter_ns()-s)/1e6
def sha(): return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
@contextmanager
def counters():
 c={'canonical_json':0,'sha256_json':0,'validate_schema':0,'artifact_serialization':0,'filesystem_write':0}; before=validator._validator.cache_info()
 canon=validator.canonical_json; hashfn=validator.sha256_json; schema=validator.validate_schema
 def cj(v): c['canonical_json']+=1; return canon(v)
 def sj(v): c['sha256_json']+=1; return hashfn(v)
 def vs(o,n): c['validate_schema']+=1; return schema(o,n)
 with patch.object(validator,'canonical_json',cj),patch.object(validator,'sha256_json',sj),patch.object(validator,'validate_schema',vs),patch.object(builder,'canonical_json',cj),patch.object(builder,'sha256_json',sj): yield c
 after=validator._validator.cache_info(); c['validator_cache_hits']=after.hits-before.hits; c['validator_cache_misses']=after.misses-before.misses
def build_experimental_target_workload(*, fixture_case: str, target_count: int):
 """Benchmark-only experimental constructor; not schema-valid for production measurement and not authoritative."""
 base=_load_case(fixture_case)
 originals=base['validated_request']['persistent_watchlist_reference']['enabled_target_ids']
 out=copy.deepcopy(base); ids=[f"TWSE:R4T{i:03d}" for i in range(1,target_count+1)]
 def clone_list(values, key):
  return [dict(copy.deepcopy(values[i % len(values)]), **{key: ids[i]}) for i in range(target_count)]
 out['validated_request']['persistent_watchlist_reference']['enabled_target_ids']=ids
 out['execution_plan']['target_order']=ids
 out['execution_plan']['targets']=clone_list(base['execution_plan']['targets'],'target_id')
 for g in out['execution_plan']['source_call_groups']: g['target_ids']=ids
 out['execution_result']['target_results']=clone_list(base['execution_result']['target_results'],'target_id');out['execution_result']['observation_count']=len(out['execution_result']['target_results'])
 for g in out['execution_result']['source_execution_summary'].get('group_results',[]): g['target_ids']=ids
 out['watchlist_bundle']['targets']=clone_list(base['watchlist_bundle']['targets'],'target_id')
 out['watchlist_bundle']['facts']=[dict(copy.deepcopy(base['watchlist_bundle']['facts'][i % len(base['watchlist_bundle']['facts'])]),target_id=ids[i % target_count]) for i in range(target_count*2)]
 out['watchlist_bundle']['coverage']['requested_target_ids']=ids;out['watchlist_bundle']['coverage']['targets']=clone_list(base['watchlist_bundle']['coverage']['targets'],'target_id')
 rh=validator.sha256_json(out['validated_request']);out['execution_plan']['request_hash']=rh;out['execution_result']['request_hash']=rh
 return out

def pipeline(case='complete_snapshot',one=False):
 up=_load_case(case)
 if one: up=_truncate_to_first_target(up)
 pkg=builder.build_watchlist_ai_context_package(validated_request=up['validated_request'],execution_plan=up['execution_plan'],execution_result=up['execution_result'],watchlist_bundle=up['watchlist_bundle'],generated_at_utc='2026-07-17T00:00:00Z')
 hand=build_watchlist_conversation_handoff(context_package=pkg,generated_at_utc='2026-07-17T00:00:00Z')
 man=builder.build_context_manifest(context_package=pkg,conversation_handoff=hand,upstream_artifacts=up,generated_at_utc='2026-07-17T00:00:00Z')
 ok=validator.validate_watchlist_ai_context_package(pkg,upstream_artifacts=up)['valid'] and validator.validate_watchlist_conversation_handoff(hand,context_package=pkg)['valid'] and validator.validate_watchlist_ai_context_manifest(man,context_package=pkg,handoff=hand,upstream_artifacts=up)['valid']
 return up,pkg,hand,man,ok
def equivalence(up,pkg,hand,man):
 # cached and uncached validators must return identical results for valid and invalid inputs.
 cached=[validator.validate_watchlist_ai_context_package(pkg,upstream_artifacts=up),validator.validate_watchlist_conversation_handoff(hand,context_package=pkg),validator.validate_watchlist_ai_context_manifest(man,context_package=pkg,handoff=hand,upstream_artifacts=up)]
 validator._validator.cache_clear(); uncached=[validator.validate_watchlist_ai_context_package(pkg,upstream_artifacts=up),validator.validate_watchlist_conversation_handoff(hand,context_package=pkg),validator.validate_watchlist_ai_context_manifest(man,context_package=pkg,handoff=hand,upstream_artifacts=up)]
 bad=copy.deepcopy(pkg); bad['package_hash']='bad'; a=validator.validate_watchlist_ai_context_package(bad,upstream_artifacts=up); validator._validator.cache_clear(); b=validator.validate_watchlist_ai_context_package(bad,upstream_artifacts=up)
 return cached==uncached and a==b
def _run_once(sid):
 case={'performance_package':'performance','partial_source_failure':'partial_source_failure','all_source_failure':'all_source_failure','high_missing_evidence_pressure':'all_source_failure','combined_citation_and_missing_evidence_pressure':'all_source_failure'}.get(sid,'complete_snapshot')
 package_count=5 if sid=='50_target_stress' else 10 if sid=='100_target_stress' else 1
 prepared=[]
 # Stage-only scenarios deliberately prepare valid inputs outside their timed stage.
 if sid in {'artifact_serialization_only','safe_atomic_artifact_write','manifest_generation'}: prepared=[pipeline(case,sid=='1_target_snapshot')]
 def work():
  records=[]
  for _ in range(package_count):
   up,pkg,hand,man,ok=prepared.pop() if prepared else pipeline(case,sid=='1_target_snapshot')
   
   rec={'valid':ok,'actual_target_count':len(pkg['targets']),'citation_count':len(pkg['citation_index']),'missing_evidence_count':len(pkg['missing_evidence'])}
   if sid.startswith('conversation_handoff_policy'):
    before=validator.canonical_json(pkg); a=compose_conversation_handoff(evidence_package=pkg,agent_policy={'conversation_policy':{}},generated_at_utc='2026-07-17T00:00:00Z'); after_a=validator.canonical_json(pkg); b=compose_conversation_handoff(evidence_package=pkg,agent_policy={'conversation_policy':{'recommendations_permitted':True,'trading_advice_permitted':True}},generated_at_utc='2026-07-17T00:00:00Z'); after_b=validator.canonical_json(pkg); rec['policy_handoffs_differ']=a['response_constraints']!=b['response_constraints']; rec['evidence_bytes_unchanged']=before==after_a==after_b; rec['valid']=rec['valid'] and rec['policy_handoffs_differ'] and rec['evidence_bytes_unchanged'] and validator.validate_watchlist_conversation_handoff(a,context_package=pkg)['valid'] and validator.validate_watchlist_conversation_handoff(b,context_package=pkg)['valid']
   elif sid=='v1_to_v2_migration':
    v1=json.loads((ROOT/'tests/fixtures/m8r_03e_r3/historical_v1_context_package.json').read_text()); v2,ms=clock(lambda:migrate_watchlist_ai_context_package_v1_to_v2(v1)); rec['migration_ms']=ms; rec['valid']=validator.validate_schema(v2,'m8r_watchlist_ai_context_package.v2.schema.json') is None
   elif sid=='artifact_serialization_only':
    text,ms=clock(lambda:validator.canonical_json(pkg)); rec['artifact_serialization_ms']=ms; rec['serialized_bytes']=len(text.encode())
   elif sid=='safe_atomic_artifact_write':
    text=validator.canonical_json(pkg); _,ms=clock(lambda:atomic_write_text(tempfile.mkdtemp(prefix='m8r-r4-'),'artifact.json',text)); rec['safe_atomic_write_ms']=ms
   elif sid=='manifest_generation':
    _,ms=clock(lambda:builder.build_context_manifest(context_package=pkg,conversation_handoff=hand,upstream_artifacts=up,generated_at_utc='2026-07-17T00:00:00Z')); rec['manifest_generation_ms']=ms
   records.append(rec)
  return records
 return package_count,work
def execute(sid):
 if sid in {'10_target_snapshot','50_target_stress','100_target_stress','high_citation_pressure','combined_citation_and_missing_evidence_pressure'}:
  stress=sid in {'50_target_stress','100_target_stress'}
  return {'scenario_id':sid,'status':'unsupported_pending_cross_layer_fixture' if not stress else 'unsupported_pending_valid_10_target_package','supported':False,'measurement_executed':False,'expected_target_count':{'10_target_snapshot':10,'50_target_stress':50,'100_target_stress':100}.get(sid,None),'actual_target_count':None,'reason_code':'schema_valid_10_target_upstream_fixture_unavailable' if 'target' in sid else 'pressure_fixture_unavailable','blocking_dependency':'R5A-PHASE-C-ENABLING-CROSS-LAYER-FIXTURE-INFRASTRUCTURE','tier':'stress_only' if stress else 'production_contract','non_contract':stress,'not_authorized_for_production_request':stress}
 repeats=3 if sid in {'50_target_stress','100_target_stress'} else 5
 # two scenario-specific warmups execute the real named workload.
 for _ in range(2):
  count,work=_run_once(sid)
  with counters(): work()
 raw=[]; peaks=[]; aggregate_counts={}
 for _ in range(repeats):
  count,work=_run_once(sid)
  with counters() as c:
   tracemalloc.start(); records,ms=clock(work); peak=tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
  raw.append({'elapsed_ms':ms,'records':records,'actual_target_count':sum(x['actual_target_count'] for x in records)}); peaks.append(peak)
  for k,v in c.items(): aggregate_counts[k]=aggregate_counts.get(k,0)+v
 stress=sid in {'50_target_stress','100_target_stress'}
 cache_equivalent=equivalence(*pipeline('complete_snapshot')[:4])
 return {'scenario_id':sid,'tier':'stress_only' if stress else 'production_contract','non_contract':stress,'not_authorized_for_production_request':stress,'target_count':raw[0]['actual_target_count'],'actual_target_count':raw[0]['actual_target_count'],'aggregate_valid_package_count':count,'warmup_count':2,'repeat_count':repeats,'raw_measurements':raw,'median_measurements_ms':{'total_end_to_end':round(statistics.median(x['elapsed_ms'] for x in raw),3)},'operation_counts':aggregate_counts,'serialized_bytes':sum(x.get('serialized_bytes',0) for x in raw[0]['records']),'citation_count':sum(x['citation_count'] for x in raw[0]['records']),'missing_evidence_count':sum(x['missing_evidence_count'] for x in raw[0]['records']),'peak_memory':{'source':'tracemalloc','units':'bytes','value':max(peaks)},'validity_results':all(record['valid'] for measurement in raw for record in measurement['records']),'all_repetitions_valid':all(record['valid'] for measurement in raw for record in measurement['records']),'raw_measurement_count':len(raw),'operation_counts_scope':'aggregate_across_all_measured_repetitions','validator_cache_result_equivalence':cache_equivalent,'semantic_equivalence':cache_equivalent}
def build():
 for _ in range(2): pipeline()
 ss=[execute(x) for x in SCENARIOS]
 return {'schema_version':'m8r_03e_r4_performance_baseline.v2','task_id':'M8R-03E-R4-PERFORMANCE-AND-SCALABILITY-HARDENING','baseline_main_sha':'d33a807bd8f2a4677dbf630b326271e94dd7202c','tested_tree_sha':sha(),'measurement_contract_ref':'docs/contracts/m8r_03e_r4_performance_measurement_contract.json','measurement_environment':{'python':sys.version.split()[0],'platform':platform.platform(),'timer':'time.perf_counter_ns','gc_enabled':gc.isenabled(),'network':False},'production_contract_limit':10,'stress_only_limits':[50,100],'scenarios':ss}
def verify(d):
 required={'schema_version':'m8r_03e_r4_performance_baseline.v2','task_id':'M8R-03E-R4-PERFORMANCE-AND-SCALABILITY-HARDENING','baseline_main_sha':'d33a807bd8f2a4677dbf630b326271e94dd7202c','measurement_contract_ref':'docs/contracts/m8r_03e_r4_performance_measurement_contract.json','production_contract_limit':10}
 if any(d.get(k)!=v for k,v in required.items()) or d.get('stress_only_limits') != [50,100] or not isinstance(d.get('scenarios'),list): return False
 ids=[x.get('scenario_id') for x in d['scenarios']]
 if set(ids)!=set(SCENARIOS) or len(ids)!=len(set(ids)): return False
 forbidden={'raw_measurements','median_measurements_ms','peak_memory','validity_results','all_repetitions_valid','raw_measurement_count','operation_counts','operation_counts_scope','validator_cache_result_equivalence','semantic_equivalence','serialized_bytes','target_count','citation_count','missing_evidence_count','aggregate_valid_package_count','warmup_count','repeat_count'}
 counters={'canonical_json','sha256_json','validate_schema','validator_cache_hits','validator_cache_misses','artifact_serialization','filesystem_write'}
 for x in d['scenarios']:
  if x['scenario_id'] in UNSUPPORTED_EXPECTATIONS:
   e=UNSUPPORTED_EXPECTATIONS[x['scenario_id']]
   if any(x.get(k)!=v for k,v in e.items()) or x.get('supported') is not False or x.get('measurement_executed') is not False or x.get('actual_target_count') is not None or not isinstance(x.get('blocking_dependency'),str) or not x['blocking_dependency'].strip() or forbidden.intersection(x): return False
   continue
  raw=x.get('raw_measurements')
  if x.get('warmup_count')!=2 or x.get('repeat_count')!=5 or x.get('raw_measurement_count')!=5 or not isinstance(raw,list) or len(raw)!=5 or x.get('validity_results') is not True or x.get('all_repetitions_valid') is not True or x.get('validator_cache_result_equivalence') is not True or x.get('semantic_equivalence') is not True or x.get('operation_counts_scope')!='aggregate_across_all_measured_repetitions': return False
  ops=x.get('operation_counts');
  if not isinstance(ops,dict) or any(not isinstance(ops.get(k),int) or isinstance(ops.get(k),bool) or ops[k]<0 for k in counters): return False
  for m in raw:
   if not isinstance(m,dict) or not isinstance(m.get('elapsed_ms'),(int,float)) or isinstance(m.get('elapsed_ms'),bool) or m['elapsed_ms']<0 or not isinstance(m.get('records'),list) or not m['records'] or not isinstance(m.get('actual_target_count'),int) or isinstance(m['actual_target_count'],bool): return False
   total=0
   for r in m['records']:
    if not isinstance(r,dict) or r.get('valid') is not True: return False
    for k in ('actual_target_count','citation_count','missing_evidence_count'):
     if not isinstance(r.get(k),int) or isinstance(r[k],bool) or r[k]<0:return False
    total+=r['actual_target_count']
   if total!=m['actual_target_count']:return False
  med=x.get('median_measurements_ms',{}).get('total_end_to_end')
  if not isinstance(med,(int,float)) or isinstance(med,bool) or abs(med-round(statistics.median(m['elapsed_ms'] for m in raw),3))>.001:return False
 return True
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='docs/quality/m8r_03e_r4_performance_baseline.json');p.add_argument('--verify-existing',action='store_true');a=p.parse_args();out=Path(a.output)
 if a.verify_existing: ok=verify(json.loads(out.read_text()));print(json.dumps({'status':'pass' if ok else 'fail'}));return 0 if ok else 1
 out.write_text(json.dumps(build(),indent=2,sort_keys=True)+'\n');return 0
if __name__=='__main__':raise SystemExit(main())
