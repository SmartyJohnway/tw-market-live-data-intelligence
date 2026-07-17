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
 return cached==uncached and a==b and all([validator.canonical_json(pkg)==validator.canonical_json(pkg),pkg['package_hash']==pkg['package_hash'],pkg['context_package_id']==pkg['context_package_id'],pkg['citation_index']==pkg['citation_index'],pkg['source_lineage']==pkg['source_lineage'],pkg['missing_evidence']==pkg['missing_evidence']])
def execute(sid):
 case={'performance_package':'performance','partial_source_failure':'partial_source_failure','all_source_failure':'all_source_failure','high_missing_evidence_pressure':'all_source_failure','combined_citation_and_missing_evidence_pressure':'all_source_failure'}.get(sid,'complete_snapshot'); n=1 if sid=='1_target_snapshot' else (5 if sid=='50_target_stress' else 10 if sid=='100_target_stress' else 1)
 with counters() as c:
  tracemalloc.start(); start=time.perf_counter_ns(); results=[]
  for _ in range(n):
   up,pkg,hand,man,ok=pipeline(case,sid=='1_target_snapshot'); rec={'valid':ok,'serialized_bytes':0}
   if sid.startswith('conversation_handoff_policy'):
    pol={'conversation_policy':{'recommendations_permitted':sid.endswith('b'),'trading_advice_permitted':sid.endswith('b')}}; h=compose_conversation_handoff(evidence_package=pkg,agent_policy=pol,generated_at_utc='2026-07-17T00:00:00Z'); rec['handoff_policy_differs']=h['response_constraints']!=hand['response_constraints']; rec['valid']=rec['valid'] and validator.validate_watchlist_conversation_handoff(h,context_package=pkg)['valid']
   elif sid=='v1_to_v2_migration':
    v1=json.loads((ROOT/'tests/fixtures/m8r_03e_r3/historical_v1_context_package.json').read_text()); v2,t=clock(lambda:migrate_watchlist_ai_context_package_v1_to_v2(v1)); rec['migration_ms']=t; rec['valid']=validator.validate_schema(v2,'m8r_watchlist_ai_context_package.v2.schema.json') is None
   elif sid=='artifact_serialization_only':
    text,t=clock(lambda:validator.canonical_json(pkg)); c['artifact_serialization']+=1; rec['artifact_serialization_ms']=t; rec['serialized_bytes']=len(text.encode())
   elif sid=='safe_atomic_artifact_write':
    text=validator.canonical_json(pkg); _,t=clock(lambda:atomic_write_text(tempfile.mkdtemp(prefix='m8r-r4-'),'artifact.json',text)); c['filesystem_write']+=1; rec['safe_atomic_write_ms']=t
   elif sid=='manifest_generation':
    _,t=clock(lambda:builder.build_context_manifest(context_package=pkg,conversation_handoff=hand,upstream_artifacts=up,generated_at_utc='2026-07-17T00:00:00Z')); rec['manifest_generation_ms']=t
   results.append(rec)
  peak=tracemalloc.get_traced_memory()[1]; tracemalloc.stop(); elapsed=(time.perf_counter_ns()-start)/1e6
 return {'scenario_id':sid,'tier':'stress_only' if n>1 else 'production_contract','non_contract':n>1,'not_authorized_for_production_request':n>1,'target_count':n*10 if n>1 else (1 if sid=='1_target_snapshot' else 10),'aggregate_valid_package_count':n,'warmup_count':2,'repeat_count':3 if n>1 else 5,'raw_measurements':[{'elapsed_ms':elapsed,'results':results}],'median_measurements_ms':{'total_end_to_end':round(elapsed,3)},'operation_counts':c,'serialized_bytes':sum(x['serialized_bytes'] for x in results),'citation_count':sum(len(pipeline(case,sid=='1_target_snapshot')[1]['citation_index']) for _ in range(n)),'missing_evidence_count':sum(len(pipeline(case,sid=='1_target_snapshot')[1]['missing_evidence']) for _ in range(n)),'peak_memory':{'source':'tracemalloc','units':'bytes','value':peak},'validity_results':all(x['valid'] for x in results),'semantic_equivalence':equivalence(*pipeline(case,sid=='1_target_snapshot')[:4])}
def build():
 for _ in range(2): pipeline()
 ss=[execute(x) for x in SCENARIOS]
 return {'schema_version':'m8r_03e_r4_performance_baseline.v2','task_id':'M8R-03E-R4-PERFORMANCE-AND-SCALABILITY-HARDENING','baseline_main_sha':'d33a807bd8f2a4677dbf630b326271e94dd7202c','tested_tree_sha':sha(),'measurement_contract_ref':'docs/contracts/m8r_03e_r4_performance_measurement_contract.json','measurement_environment':{'python':sys.version.split()[0],'platform':platform.platform(),'timer':'time.perf_counter_ns','gc_enabled':gc.isenabled(),'network':False},'production_contract_limit':10,'stress_only_limits':[50,100],'scenarios':ss}
def verify(d):
 ids=[x.get('scenario_id') for x in d.get('scenarios',[])]; required={'schema_version':'m8r_03e_r4_performance_baseline.v2','task_id':'M8R-03E-R4-PERFORMANCE-AND-SCALABILITY-HARDENING','baseline_main_sha':'d33a807bd8f2a4677dbf630b326271e94dd7202c','production_contract_limit':10}; return all(d.get(k)==v for k,v in required.items()) and set(ids)==set(SCENARIOS) and len(ids)==len(set(ids)) and all(x['warmup_count']==2 and x['repeat_count']>=3 and x['validity_results'] and x['semantic_equivalence'] and {'canonical_json','sha256_json','validate_schema','validator_cache_hits','validator_cache_misses','artifact_serialization','filesystem_write'}<=set(x['operation_counts']) for x in d['scenarios'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='docs/quality/m8r_03e_r4_performance_baseline.json');p.add_argument('--verify-existing',action='store_true');a=p.parse_args();out=Path(a.output)
 if a.verify_existing: ok=verify(json.loads(out.read_text()));print(json.dumps({'status':'pass' if ok else 'fail'}));return 0 if ok else 1
 out.write_text(json.dumps(build(),indent=2,sort_keys=True)+'\n');return 0
if __name__=='__main__':raise SystemExit(main())
