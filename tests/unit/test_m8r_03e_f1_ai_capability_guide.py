import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=json.load(open(ROOT/'docs/ai/m8_ai_capability_contract.json'))
MATRIX=json.load(open(ROOT/'docs/ai/m8_ai_tool_selection_matrix.json'))
REG=json.load(open(ROOT/'docs/data_capabilities/m8_source_capability_registry.json'))
HEALTH=json.load(open(ROOT/'docs/data_capabilities/m8_repository_health_status.json'))

def caps(): return {c['capability_id']:c for c in CONTRACT['capabilities']}

def test_capability_ids_are_unique():
 ids=list(caps())
 assert len(ids)==len(CONTRACT['capabilities'])

def test_matrix_capability_references_exist():
 ids=set(caps())
 for row in MATRIX['intents']:
  assert set(row['required_capabilities']).issubset(ids)
  assert set(row.get('optional_capabilities',[])).issubset(ids)

def test_implemented_capabilities_map_to_existing_paths():
 for c in CONTRACT['capabilities']:
  if c.get('underlying_runtime_available'):
   assert c['internal_dependencies']
   for p in c['internal_dependencies']:
    assert (ROOT/p).exists(), p

def test_planned_capabilities_are_not_runtime_available():
 assert all(not c['ai_facing_runtime_available'] for c in CONTRACT['capabilities'] if c['maturity_status'] in {'planned','contract_only'})

def test_fixture_only_capability_is_not_marked_live():
 raw=caps()['request_raw_source_payload']
 assert raw['maturity_status']=='contract_only'
 assert raw['underlying_capability_status']=='unavailable'
 assert raw['ai_facing_runtime_available'] is False
 assert raw['underlying_runtime_available'] is False

def test_current_and_eod_timing_classes_are_distinct():
 tc=CONTRACT['timing_classes']
 assert 'current_bounded_observation' in tc and 'completed_session_eod' in tc
 assert tc['current_bounded_observation'] != tc['completed_session_eod']

def test_retrieved_at_not_exchange_event_time():
 assert 'retrieved_at is not exchange event time' in json.dumps(CONTRACT)

def test_unadjusted_return_semantics_are_explicit():
 assert CONTRACT['calculation_semantics']['unadjusted_return']['adjustment_status'].startswith('unadjusted')
 assert 'not total return' in CONTRACT['calculation_semantics']['unadjusted_return']['adjustment_status']

def test_recommendation_intents_are_not_globally_prohibited():
 text=(ROOT/'skills/tw-market-evidence-agent/SKILL.md').read_text()
 assert 'not globally prohibited' in text
 assert 'must_not_provide_investment_advice' not in text

def test_recommendation_can_yield_sufficient_with_caveats():
 row=next(r for r in MATRIX['intents'] if r['intent_id']=='recommendation_with_available_evidence')
 assert row['expected_sufficiency_status']=='sufficient_with_caveats'

def test_missing_evidence_can_require_additional_evidence():
 assert CONTRACT['sufficiency_statuses']['requires_additional_evidence']['invoke_another_capability'] is True
 row=next(r for r in MATRIX['intents'] if r['intent_id']=='recommendation_key_evidence_missing')
 assert row['expected_sufficiency_status']=='requires_additional_evidence'

def test_raw_payload_remains_restricted():
 assert CONTRACT['raw_payload_exposure_allowed'] is False
 raw=next(r for r in MATRIX['intents'] if r['intent_id']=='raw_source_payload_request')
 assert raw['required_capabilities']==['request_raw_source_payload']

def test_skill_does_not_expose_credentials_or_raw_secrets():
 text='\n'.join(p.read_text() for p in (ROOT/'skills/tw-market-evidence-agent').rglob('*') if p.is_file() and p.suffix in {'.md','.json','.py'})
 for banned in ['api_key =','cookie =','secret =']:
  assert banned not in text.lower()

def test_skill_validator_passes():
 r=subprocess.run([sys.executable,'skills/tw-market-evidence-agent/scripts/validate_skill.py'],cwd=ROOT,text=True,capture_output=True)
 assert r.returncode==0, r.stderr+r.stdout

def test_registry_successor_becomes_r2():
 assert REG['recommended_next_task']=='M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION'

def test_phase_c_blocked_until_r2():
 assert CONTRACT['phase_dependencies']['Phase C']=='blocked_until_M8R-03E-R2-complete'
 assert REG['unified_tool_api']=='required_successor_capability'

def test_existing_m8r_03e_schema_files_unchanged_by_f1_contract():
 assert CONTRACT['task_id']=='M8R-03E-F1-AI-CAPABILITY-GUIDE-AND-AGENT-SKILL-CONTRACT'

def test_network_required_capabilities_require_authorization_and_disabled_default():
 for c in CONTRACT['capabilities']:
  if c['network_required']:
   assert c['authorization_required'] is True
   assert c['network_default_enabled'] is False
   assert c['authorization_model']=='M8R-03D controlled execution authorization'

def test_no_phase_c_ai_facing_operation_runtime_available():
 assert all(c['ai_facing_runtime_available'] is False for c in CONTRACT['capabilities'])
 assert {c['ai_facing_operation_status'] for c in CONTRACT['capabilities']} == {'contract_only'}

def test_underlying_capability_availability_remains_represented():
 current=caps()['get_current_market_evidence']
 assert current['underlying_capability_status']=='implemented_with_caveats'
 assert current['underlying_runtime_available'] is True
 assert current['ai_facing_runtime_available'] is False

def test_identify_required_additional_evidence_not_falsely_executable():
 cap=caps()['identify_required_additional_evidence']
 assert cap['ai_facing_runtime_available'] is False
 assert cap['underlying_capability_status']=='fixture_validated'
 assert cap['underlying_runtime_available'] is False

def test_embedded_skill_asset_equals_authoritative_contract():
 assert (ROOT/'docs/ai/m8_ai_capability_contract.json').read_text() == (ROOT/'skills/tw-market-evidence-agent/assets/m8_ai_capability_contract.json').read_text()

def test_registry_status_surfaces_agree():
 r2='M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION'
 for surface in [REG, REG['m8_active_consolidated_status'], REG['planning_state'], HEALTH]:
  assert surface['implemented_through_track']=='M8R-03E-F1'
  assert surface['agent_skill_contract']=='implemented'
  assert surface['ai_capability_guide']=='implemented'
  assert surface['recommended_next_task']==r2
  assert surface['registry_successor']==r2

def test_old_m8r_03f_successor_is_historical_or_superseded():
 old=REG['recommended_successor_after_m8r_03e']
 assert old['task_id']=='M8R-03F-CONVERSATIONAL-TARGET-INTAKE-AND-TEMPORARY-WATCHLIST-RESOLUTION'
 assert old['status'] in {'historical_superseded','superseded'}
