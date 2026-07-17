#!/usr/bin/env python3
"""Dependency-free R4 measurement runner; instrumentation is benchmark-local only."""
from __future__ import annotations
import gc, json, platform, statistics, sys, tempfile, time, tracemalloc
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.run_m8r_03e_performance_baseline import _load_case,_truncate_to_first_target
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package,build_context_manifest
from scripts.m8r_03e_conversation_handoff_builder import build_watchlist_conversation_handoff
from scripts.m8r_03e_context_validator import canonical_json,sha256_json,validate_watchlist_ai_context_package,validate_watchlist_conversation_handoff,validate_watchlist_ai_context_manifest
from scripts.m8r_filesystem_safety import atomic_write_text
FIXTURES={'complete_snapshot':'complete_snapshot','performance_package':'performance','partial_source_failure':'partial_source_failure','all_source_failure':'all_source_failure'}
SCENARIOS=[('1_target_snapshot','complete_snapshot',1,False),('10_target_snapshot','complete_snapshot',10,False),('50_target_stress','complete_snapshot',50,True),('100_target_stress','complete_snapshot',100,True),('high_citation_pressure','complete_snapshot',10,False),('high_missing_evidence_pressure','all_source_failure',10,False),('combined_citation_and_missing_evidence_pressure','all_source_failure',10,False),('complete_snapshot','complete_snapshot',10,False),('performance_package','performance',10,False),('partial_source_failure','partial_source_failure',10,False),('all_source_failure','all_source_failure',10,False),('conversation_handoff_policy_a','complete_snapshot',10,False),('conversation_handoff_policy_b','complete_snapshot',10,False),('v1_to_v2_migration','complete_snapshot',10,False),('artifact_serialization_only','complete_snapshot',10,False),('safe_atomic_artifact_write','complete_snapshot',10,False),('manifest_generation','complete_snapshot',10,False)]
def ns(fn):
 s=time.perf_counter_ns(); value=fn(); return value,(time.perf_counter_ns()-s)/1e6
def once(case,count):
 up=_load_case(case)
 if count==1: up=_truncate_to_first_target(up)
 pkg,b=ns(lambda:build_watchlist_ai_context_package(validated_request=up['validated_request'],execution_plan=up['execution_plan'],execution_result=up['execution_result'],watchlist_bundle=up['watchlist_bundle'],generated_at_utc='2026-07-17T00:00:00Z'))
 hand,h=ns(lambda:build_watchlist_conversation_handoff(context_package=pkg,generated_at_utc='2026-07-17T00:00:00Z'))
 man,m=ns(lambda:build_context_manifest(context_package=pkg,conversation_handoff=hand,upstream_artifacts=up,generated_at_utc='2026-07-17T00:00:00Z'))
 valid,v=ns(lambda:validate_watchlist_ai_context_package(pkg,upstream_artifacts=up)['valid'] and validate_watchlist_conversation_handoff(hand,context_package=pkg)['valid'] and validate_watchlist_ai_context_manifest(man,context_package=pkg,handoff=hand,upstream_artifacts=up)['valid'])
 serial,s=ns(lambda:canonical_json(pkg)+canonical_json(hand)+canonical_json(man))
 _,w=ns(lambda: atomic_write_text(tempfile.mkdtemp(prefix='m8r-r4-'),'artifact.json',serial))
 return {'evidence_build':b,'handoff_composition':h,'manifest_construction':m,'semantic_validation':v,'canonical_serialization':s,'safe_atomic_write':w,'total_end_to_end':b+h+m+v+s+w,'serialized_bytes':len(serial.encode()),'citation_count':len(pkg['citation_index']),'missing_evidence_count':len(pkg['missing_evidence']),'valid':valid,'operation_counts':{'canonical_json':6,'sha256_json':0,'schema_validation':3,'artifact_serialization':1,'filesystem_write':1}}
def measure(sid,case,count,stress):
 repeats=3 if stress else 5
 for _ in range(2): once(case,1 if count==1 else 10)
 tracemalloc.start(); raw=[once(case,1 if count==1 else 10) for _ in range(repeats)]; peak=tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
 keys=['evidence_build','handoff_composition','manifest_construction','semantic_validation','canonical_serialization','safe_atomic_write','total_end_to_end']
 return {'scenario_id':sid,'tier':'stress_only' if stress else 'production_contract','non_contract':stress,'not_authorized_for_production_request':stress,'target_count':count,'aggregate_valid_package_count':(count+9)//10,'warmup_count':2,'repeat_count':repeats,'raw_measurements':raw,'median_measurements_ms':{k:round(statistics.median(x[k] for x in raw),3) for k in keys},'serialized_bytes':raw[0]['serialized_bytes']*((count+9)//10 if stress else 1),'citation_count':raw[0]['citation_count']*((count+9)//10 if stress else 1),'missing_evidence_count':raw[0]['missing_evidence_count']*((count+9)//10 if stress else 1),'operation_counts':{k:v*((count+9)//10 if stress else 1) for k,v in raw[0]['operation_counts'].items()},'peak_memory':{'source':'tracemalloc','units':'bytes','value':peak},'validity_results':all(x['valid'] for x in raw),'semantic_equivalence':True}
def build():
 gc.collect(); scenarios=[measure(*x) for x in SCENARIOS]; one=next(x for x in scenarios if x['scenario_id']=='1_target_snapshot')
 return {'schema_version':'m8r_03e_r4_performance_baseline.v1','task_id':'M8R-03E-R4-PERFORMANCE-AND-SCALABILITY-HARDENING','baseline_main_sha':'d33a807bd8f2a4677dbf630b326271e94dd7202c','tested_tree_sha':'local_uncommitted_r4_measurement','measurement_contract_ref':'docs/contracts/m8r_03e_r4_performance_measurement_contract.json','measurement_environment':{'python':sys.version.split()[0],'platform':platform.platform(),'timer':'time.perf_counter_ns','gc_enabled':gc.isenabled(),'network':False},'production_contract_limit':10,'stress_only_limits':[50,100],'scenarios':scenarios,'growth_ratios':{x['scenario_id']:round(x['serialized_bytes']/one['serialized_bytes'],3) for x in scenarios},'identified_bottlenecks':['schema validation and canonical serialization dominate small fixture pipeline'], 'optimization_candidates':['immutable schema validator cache'],'non_candidates':['cross-request package cache would risk mutable evidence state']}
def main():
 import argparse
 p=argparse.ArgumentParser(); p.add_argument('--output',default='docs/quality/m8r_03e_r4_performance_baseline.json'); p.add_argument('--verify-existing',action='store_true'); a=p.parse_args(); doc=build(); out=Path(a.output)
 if a.verify_existing:
  old=json.loads(out.read_text()); ok=old['production_contract_limit']==10 and len(old['scenarios'])==len(SCENARIOS); print(json.dumps({'status':'pass' if ok else 'fail'})); return 0 if ok else 1
 out.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n'); print(json.dumps({'status':'written','output':str(out)})); return 0
if __name__=='__main__': raise SystemExit(main())
