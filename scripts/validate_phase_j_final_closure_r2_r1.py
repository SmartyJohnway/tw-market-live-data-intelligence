"""Acceptance-only semantic alignment and immutable historical evidence checks."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import validate_phase_j_final_closure_r1 as r1
from scripts import validate_phase_j_final_closure_r2 as r2
from scripts.m8r_06_03_production_adapter import _assess_current_observation

ROOT = Path(__file__).resolve().parents[1]
BASE = '62dd88cef8da9c13ffcbd3dec57232e6bfd6678f'
BINDING = ROOT / 'tests/fixtures/phase_j/closure_r2_r1/immutable_authority.json'
DOC = ROOT / 'docs/governance/phase_j'

def require(condition, code):
    if not condition:
        raise ValueError(code)

def baseline():
    binding = json.loads(BINDING.read_text())
    require(binding['starting_head'] == BASE, 'STARTING_AUTHORITY_DRIFT')
    for path, digest in binding['immutable_hashes'].items():
        historical = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
        require(hashlib.sha256(historical).hexdigest() == digest, 'HISTORICAL_BINDING_DRIFT:' + path)
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, 'IMMUTABLE_AUTHORITY_DRIFT:' + path)
    policy = next(s for s in r2.read(ROOT / 'docs/data_capabilities/m8_source_capability_registry.json')['sources'] if s['source_id'] == 'TWSE_MIS')
    p = policy['freshness_evaluator_policy']
    require((p['allow_retrieved_at_only_intraday_freshness'], p['max_intraday_age_seconds'], p['requires_exchange_timestamp_for_fresh']) == (True, 900, False), 'FROZEN_POLICY_DRIFT')
    from server.unified_mcp.tool_contracts import build_tool_specs
    require([t.name for t in build_tool_specs()] == r1.MCP_NAMES, 'MCP_TOOL_SURFACE_DRIFT')
    return policy

def validate_recent(record):
    policy = baseline()
    require(record['scenario_id'] == 'J1-04' and record['request']['request_id'] == record['result']['request_id'] == 'closure-r1-j1-04', 'REQUEST_IDENTITY_DRIFT')
    require(record['executed_layers'] == ['integration', 'service_api'] and record['execution']['consumption_state'] == 'consumed_success', 'NO_PRODUCTION_EXECUTION')
    require(record['initial_execution_count'] == 1 and record['additional_execution_count'] == 0, 'EXECUTION_COUNT_DRIFT')
    require(not any(record['market_network'].values()) and record['execution']['external_market_network_executed'] is False, 'MARKET_NETWORK_NONZERO')
    require(any(c['path'] == '/api/unified/result-package' and c['response_canonical_sha256'] == r1.sha(record['package']) for c in record['server_calls']), 'INDEPENDENT_SERVER_RECEIPT_MISSING')
    require(record['package']['canonical_result'] == record['result'], 'CANONICAL_RESULT_DIVERGENCE')
    require(record['result']['result_id'] == record['audit']['result_id'] == record['handoff']['result_id'], 'RESULT_AUDIT_HANDOFF_LINEAGE')
    require(record['audit']['audit_package_id'] == record['handoff']['audit_package_id'] and record['control_package_id'] == record['handoff']['control_package_id'], 'CONTROL_AUDIT_LINEAGE')
    require(record['case_id'] == 'TWSE_MIS_RETRIEVED_ONLY_RECENT', 'WRONG_CASE')
    native = record['normalized_observation']
    expected = _assess_current_observation(native, policy)
    require(native['source_timestamp'] is None, 'RETRIEVAL_MASQUERADES_AS_EXCHANGE_TIME')
    require(expected['status'] == 'fresh' and expected['freshness_assessment'] == 'fresh_intraday_snapshot', 'RETRIEVED_ONLY_FRESH_REGRESSION')
    require(native['governed_currentness'] == expected, 'PERSISTED_CURRENTNESS_DIVERGENCE')
    ev = record['result']['targets'][0]['evidence']['current_observation']
    require(ev['status'] == 'available', 'FRESHNESS_AVAILABILITY_COLLAPSE')
    require(ev['observed_fields']['freshness_context'] == ev['currentness'], 'RENDERER_OR_PROJECTION_RECLASSIFICATION')
    for key, value in expected.items():
        require(ev['currentness'].get(key) == value, 'RESULT_CURRENTNESS_DIVERGENCE:' + key)
    for key in ('retrieved_time_only', 'exchange_timestamp_absent', 'not_realtime_guaranteed'):
        require(expected[key] is True and ev['observed_fields']['freshness_context'][key] is True, 'SAFETY_FLAG_REMOVED:' + key)
    require(record['handoff']['canonical_result'] == record['result'], 'HANDOFF_CANONICAL_DIVERGENCE')
    # The historical R1 observation helper requires an exchange timestamp for
    # its original fixture. This regression instead proves the accepted M8
    # retrieval-only caveated semantics, without substituting exchange time.
    facts = r1.observe(record)
    facts['facts']['currentness'] = 'observed_not_realtime' if expected['not_realtime_guaranteed'] and expected['retrieved_time_only'] else 'unproven'
    golden = next(s for s in r2.read(DOC / 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json')['scenarios'] if s['scenario_id'] == 'J1-04')
    require(not r2.evaluate_scenario(golden, facts), 'J3_SEMANTIC_FAILURE')
    require('not_realtime_guaranteed' in record['handoff']['ai_ready_markdown'], 'HANDOFF_REALTIME_CAVEAT_MISSING')
    require(not any(token in record['handoff']['ai_ready_markdown'].casefold() for token in ('realtime guaranteed quote', 'realtime price', 'live tick')), 'FALSE_REALTIME_GUARANTEE')
    digest = hashlib.sha256((json.dumps(record['source_artifact'], ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()
    require(digest == record['source_artifact_sha256'], 'SOURCE_HASH_DIVERGENCE')
    require(digest in json.dumps(record['audit']), 'AUDIT_SOURCE_HASH_MISSING')
    require(native in record['source_artifact']['records'], 'NORMALIZED_OBSERVATION_NOT_PERSISTED')
    require(len(record['source_invocations']) == 1 and all(not c['external_dispatch'] for c in record['source_invocations']), 'SOURCE_TRANSPORT_BOUNDARY')
    require(record['real_agent_sessions'] == record['real_agent_tool_calls'] == record['agent_provider_transport'] == 0, 'REAL_AGENT_NOT_AUTHORIZED')
    return True

def validate_stale(record):
    baseline()
    return r2.validate_witness(record)

def validate_terminal():
    ledger = r2.read(DOC / 'PHASE_J_FINAL_CLOSURE_R2_R1_WITNESS_LEDGER_V1.json')
    validate_stale(ledger['j1_21'])
    validate_recent(ledger['retrieved_only_recent'])
    policy = baseline()
    old = ledger['retrieved_only_old']
    require(old['executed_boundary'] == 'production_currentness_helper_replay', 'OLD_RETRIEVAL_BOUNDARY_MISREPRESENTED')
    require(_assess_current_observation(old['observation'], policy, now_utc=old['evaluation_timestamp']) == old['assessment'], 'OLD_RETRIEVAL_ASSESSMENT_DRIFT')
    require(old['assessment']['status'] == 'stale' and old['assessment']['freshness_assessment'] == 'stale_intraday_snapshot', 'OLD_RETRIEVAL_NOT_STALE')
    governance = r2.read(DOC / 'PHASE_J_FINAL_CLOSURE_R2_R1_SEMANTIC_ALIGNMENT_2026-10-11.json')
    require(governance['witness_ledger_sha256'] == hashlib.sha256((DOC / 'PHASE_J_FINAL_CLOSURE_R2_R1_WITNESS_LEDGER_V1.json').read_bytes()).hexdigest(), 'WITNESS_LEDGER_HASH_DRIFT')
    require(governance['coverage_promotions'] == [], 'COVERAGE_LAUNDERING')
    require(governance['remaining_obligations'] == [o['obligation'] for o in r2.derive(ledger['j1_21'])['obligations'] if not o['satisfied']], 'OBLIGATION_LAUNDERING')
    require(governance['remaining_obligations'] == ['real_agent_layer'], 'REMAINING_OBLIGATION_DRIFT')
    require(all(value == 0 for value in governance['external_execution_counts'].values()), 'UNAUTHORIZED_EXTERNAL_EXECUTION')
    require(governance['security_master_selector_before'] == governance['security_master_selector_after'], 'HOST_SECURITY_MASTER_MUTATED')
    require(governance['default_ci']['candidate_only_failure_nodes'] == [], 'CANDIDATE_ONLY_CI_FAILURE')
    require(governance['state']['Phase_K'] == 'NOT_STARTED' and governance['state']['Roadmap_Phase_J'] == 'UNCHECKED', 'PHASE_STATE_EXPANSION')
    return True

if __name__ == '__main__':
    baseline()
    if '--terminal' in sys.argv:
        validate_terminal()
    print('PHASE_J_CLOSURE_R2_R1_IMMUTABLE_AUTHORITY_CHECK_PASS')
