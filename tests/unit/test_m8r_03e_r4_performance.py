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
