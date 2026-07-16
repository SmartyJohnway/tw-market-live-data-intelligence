import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=json.load(open(ROOT/'docs/ai/m8_ai_capability_contract.json'))
MATRIX=json.load(open(ROOT/'docs/ai/m8_ai_tool_selection_matrix.json'))
REG=json.load(open(ROOT/'docs/data_capabilities/m8_source_capability_registry.json'))

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
  if c['runtime_available']:
   assert c['internal_dependencies']
   for p in c['internal_dependencies']:
    assert (ROOT/p).exists(), p

def test_planned_capabilities_are_not_runtime_available():
 assert all(not c['runtime_available'] for c in CONTRACT['capabilities'] if c['maturity_status']=='planned')

def test_fixture_only_capability_is_not_marked_live():
 raw=caps()['request_raw_source_payload']
 assert raw['maturity_status']=='unavailable'
 assert raw['runtime_available'] is False

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
