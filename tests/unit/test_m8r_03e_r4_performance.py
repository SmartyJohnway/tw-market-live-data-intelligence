import copy,json
from pathlib import Path
from scripts.run_m8r_03e_r4_performance import verify
ROOT=Path(__file__).resolve().parents[2]
def load(): return json.loads((ROOT/'docs/quality/m8r_03e_r4_performance_baseline.json').read_text())
def test_baseline_verifies_and_scaling_is_explicitly_unsupported():
 b=load(); assert verify(b)
 s={x['scenario_id']:x for x in b['scenarios']}
 assert s['10_target_snapshot']['measurement_executed'] is False
 assert s['50_target_stress']['tier']=='stress_only'
def test_verify_rejects_unsupported_fake_metrics_and_missing_reason():
 b=load(); x=next(x for x in b['scenarios'] if x.get('measurement_executed') is False)
 a=copy.deepcopy(b); next(y for y in a['scenarios'] if y['scenario_id']==x['scenario_id'])['raw_measurements']=[]; assert not verify(a)
 a=copy.deepcopy(b); next(y for y in a['scenarios'] if y['scenario_id']==x['scenario_id'])['reason_code']=''; assert not verify(a)
def test_verify_rejects_duplicate_scenario():
 b=load(); b['scenarios'].append(copy.deepcopy(b['scenarios'][0])); assert not verify(b)
def test_verify_rejects_wrong_unsupported_contract_and_median():
 b=load(); a=copy.deepcopy(b); x=next(x for x in a['scenarios'] if x['scenario_id']=='50_target_stress'); x['tier']='production_contract'; assert not verify(a)
 a=copy.deepcopy(b); x=next(x for x in a['scenarios'] if x.get('measurement_executed',True)); x['median_measurements_ms']['total_end_to_end']+=1; assert not verify(a)
def test_verify_rejects_later_invalid_and_fake_summary():
 b=load(); m=next(x for x in b['scenarios'] if x.get('measurement_executed',True)); a=copy.deepcopy(b); next(x for x in a['scenarios'] if x['scenario_id']==m['scenario_id'])['raw_measurements'][2]['records'][0]['valid']=False; assert not verify(a)
 a=copy.deepcopy(b); next(x for x in a['scenarios'] if x.get('measurement_executed') is False)['operation_counts_scope']='x'; assert not verify(a)

def measured(doc): return next(x for x in doc['scenarios'] if x.get('measurement_executed',True))
def unsupported(doc): return next(x for x in doc['scenarios'] if x.get('measurement_executed') is False)
def test_verify_rejects_false_validity_summaries():
 for field in ('validity_results','all_repetitions_valid'):
  b=load(); measured(b)[field]=False; assert not verify(b)
def test_verify_rejects_measurement_target_count_mismatch():
 b=load(); measured(b)['raw_measurements'][1]['actual_target_count']+=1; assert not verify(b)
def test_verify_rejects_malformed_or_negative_record_fields():
 for field,value in [('citation_count',-1),('missing_evidence_count',True),('actual_target_count','2')]:
  b=load(); measured(b)['raw_measurements'][1]['records'][0][field]=value; assert not verify(b)
def test_verify_rejects_wrong_warmup_and_operation_scope():
 for field,value in [('warmup_count',1),('operation_counts_scope','per_repetition')]:
  b=load(); measured(b)[field]=value; assert not verify(b)
def test_verify_rejects_missing_or_invalid_operation_counter():
 b=load(); del measured(b)['operation_counts']['canonical_json']; assert not verify(b)
 b=load(); measured(b)['operation_counts']['canonical_json']=True; assert not verify(b)
def test_verify_rejects_parameterized_unsupported_summary_fields():
 for field,value in [('all_repetitions_valid',True),('raw_measurement_count',5),('operation_counts_scope','x'),('serialized_bytes',1),('repeat_count',5)]:
  b=load(); unsupported(b)[field]=value; assert not verify(b)
