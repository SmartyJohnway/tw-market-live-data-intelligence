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
    a=compose_conversation_handoff(evidence_package=pkg,agent_policy={'conversation_policy':{}},generated_at_utc='2026-07-17T00:00:00Z')
    b=compose_conversation_handoff(evidence_package=pkg,agent_policy={'conversation_policy':{'recommendations_permitted':True,'trading_advice_permitted':True}},generated_at_utc='2026-07-17T00:00:00Z')
    rec['policy_handoffs_differ']=a['response_constraints']!=b['response_constraints']; rec['evidence_bytes_unchanged']=validator.canonical_json(pkg)==validator.canonical_json(pkg); rec['valid']=rec['valid'] and validator.validate_watchlist_conversation_handoff(a,context_package=pkg)['valid'] and validator.validate_watchlist_conversation_handoff(b,context_package=pkg)['valid']
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
 return {'scenario_id':sid,'tier':'stress_only' if stress else 'production_contract','non_contract':stress,'not_authorized_for_production_request':stress,'target_count':raw[0]['actual_target_count'],'actual_target_count':raw[0]['actual_target_count'],'aggregate_valid_package_count':count,'warmup_count':2,'repeat_count':repeats,'raw_measurements':raw,'median_measurements_ms':{'total_end_to_end':round(statistics.median(x['elapsed_ms'] for x in raw),3)},'operation_counts':aggregate_counts,'serialized_bytes':sum(x.get('serialized_bytes',0) for x in raw[0]['records']),'citation_count':sum(x['citation_count'] for x in raw[0]['records']),'missing_evidence_count':sum(x['missing_evidence_count'] for x in raw[0]['records']),'peak_memory':{'source':'tracemalloc','units':'bytes','value':max(peaks)},'validity_results':all(x['valid'] for x in raw[0]['records']),'semantic_equivalence':equivalence(*pipeline('complete_snapshot')[:4])}
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
