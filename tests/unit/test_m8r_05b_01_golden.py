import copy,json
from pathlib import Path
import jsonschema,pytest
from scripts.m8r_05b_01.canonical import canonical_json,sha256_json
from tests.unit.test_m8r_05b_01_planner import validation,plan,ROUTE,bindings
SCHEMA=json.load(open('schemas/unified_market_evidence_orchestration_plan.v1.schema.json'));G=Path('tests/fixtures/m8r_05b_01/golden')
def scenario(name):
 if name=='single_executable_plan': return validation(),{}
 if name=='multi_target_same_source_batch': return validation(targets=['TWSE:2330','TWSE:6488']),{}
 if name=='batching_none_two_unique_batches':
  v=validation(targets=['TWSE:2330','TWSE:6488']);r=copy.deepcopy(ROUTE);next(x for x in r['routes'] if x['capability_id']=='current_observation')['batching_scope']='none';b=bindings(v);b['routing_matrix_hash']=sha256_json(r);return v,{'routing':r,'bindings':b}
 if name=='mixed_executable_optional_omission':
  v=validation();v['normalized_request']['data_needs'].append({'type':'session_status','priority':'optional','parameters':{}});v['capability_results'].append({'data_need_index':1,'capability_id':'session_status','priority':'optional','status':'runtime_executable'});return v,{}
 if name=='required_plan_only_recent_performance': return validation('recent_performance',status='contract_supported'),{}
 if name=='required_blocked_session_status': return validation('session_status'),{}
 if name=='taifex_provisional_plan': return validation('official_eod_reference',market='TAIFEX',targets=['TAIFEX:TX']),{}
 if name=='derived_source_currentness_dependency':
  v=validation();v['normalized_request']['data_needs'].append({'type':'source_currentness','priority':'required','parameters':{}});v['capability_results'].append({'data_need_index':1,'capability_id':'source_currentness','priority':'required','status':'contract_supported'});return v,{}
 if name=='derived_missing_upstream_warning': return validation('source_currentness',status='contract_supported'),{}
 raise AssertionError(name)
@pytest.mark.parametrize('path',sorted(G.glob('*.json')))
def test_committed_golden_is_exact_projection(path):
 v,kw=scenario(path.stem);actual=plan(v,**kw);expected=json.load(open(path));assert canonical_json(actual)==canonical_json(expected);jsonschema.Draft7Validator(SCHEMA,format_checker=jsonschema.FormatChecker()).validate(actual);assert actual['execution_authorized'] is False
def test_none_scope_membership():
 actual=plan(*[scenario('batching_none_two_unique_batches')[0]],**scenario('batching_none_two_unique_batches')[1]);groups=actual['batch_groups'];assert len(groups)==2==actual['accounting']['batch_group_count'];assert len({g['batch_group_id'] for g in groups})==2 and all(len(g['operation_ids'])==1 for g in groups);assert len({o['batch_group_id'] for o in actual['operations']})==2
def test_timestamp_identity_unchanged():
 a=plan(validation(),timestamp='2026-07-23T00:00:00Z');b=plan(validation(),timestamp='2026-07-24T00:00:00Z');assert (a['plan_hash'],a['plan_id'],[x['operation_id'] for x in a['operations']])==(b['plan_hash'],b['plan_id'],[x['operation_id'] for x in b['operations']])
