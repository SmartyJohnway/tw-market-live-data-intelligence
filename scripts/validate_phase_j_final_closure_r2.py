#!/usr/bin/env python3
"""Network-free Closure-R2 verification; cannot execute a source or agent."""
from __future__ import annotations
import argparse, copy, hashlib, json, subprocess, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import validate_phase_j_final_closure_r1 as r1
from scripts.m8r_06_03_production_adapter import _assess_current_observation
from scripts.validate_phase_j_j3_golden_expected_semantics import evaluate_scenario
from server.unified_mcp.tool_contracts import build_tool_specs
DOC = ROOT / 'docs/governance/phase_j'
BASE = '09b8c16f0aced84cf85c10b0da1c09d95e7f09c5'
TREE = '6e0e7124d7bfbd2504c15027c447d981f9d5bfb0'
AUTH = 'db926b01ad5fb103d3bb71f8122855a9ba51b29566a95526e059712c0447464e'
PASS = 'PHASE_J_FINAL_CLOSURE_R2_J1_21_STALE_CURRENTNESS_REACCEPTANCE_PASS'
PRODUCTION = ['scripts/m8r_06_03_production_adapter.py', 'scripts/m8r_05c/evidence_projector.py', 'scripts/m8r_05c/markdown_renderer.py']
require, read, sha, file_sha = r1.require, r1.read, r1.sha, r1.file_sha

def baseline(check_git=True):
    binding = read(ROOT / 'tests/fixtures/phase_j/closure_r2/authority_binding.json')
    require(binding['starting_head'] == BASE and binding['starting_tree'] == TREE, 'STARTING_AUTHORITY_DRIFT')
    require(binding['review'] == '5483192952' and binding['authorization_review'] == '5483396347', 'REVIEW_DRIFT')
    require(hashlib.sha256(binding['owner_statement'].encode()).hexdigest() == binding['owner_authorization_sha256'] == AUTH, 'OWNER_AUTHORIZATION_HASH')
    for path, expected in binding['immutable_hashes'].items():
        require(file_sha(ROOT / path) == expected, 'IMMUTABLE_AUTHORITY_DRIFT:' + path)
        original = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
        require(hashlib.sha256(original).hexdigest() == expected, 'BASELINE_BINDING_LAUNDERING:' + path)
    expected_paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, 'docs/governance/phase_j', 'ROADMAP.md', 'docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json'], cwd=ROOT, text=True).splitlines()
    require(set(binding['immutable_hashes']) == set(expected_paths), 'IMMUTABLE_BINDING_INCOMPLETE')
    require(file_sha(ROOT / 'docs/data_capabilities/m8_source_capability_registry.json') == binding['source_policy_registry_sha256'], 'SOURCE_POLICY_DRIFT')
    require(hashlib.sha256(subprocess.check_output(['git', 'show', BASE + ':docs/data_capabilities/m8_source_capability_registry.json'], cwd=ROOT)).hexdigest() == binding['source_policy_registry_sha256'], 'SOURCE_POLICY_BINDING_LAUNDERING')
    require(r1.validate(check_git=False, terminal=True)['remaining_obligations'] == 2, 'HISTORICAL_CLOSURE_R1_REWRITTEN')
    require([tool.name for tool in build_tool_specs()] == r1.MCP_NAMES, 'MCP_COUNT_OR_NAME_DRIFT')
    if check_git:
        git = lambda *args: subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
        require(git('rev-parse', BASE + '^{tree}') == TREE and git('rev-parse', 'origin/main') == binding['origin_main'], 'BASELINE_DRIFT')
        require(git('branch', '--show-current') == 'phase-j/j-b04-a5-bounded-live-source-acceptance', 'BRANCH_DRIFT')
        allowed = tuple(PRODUCTION + ['tests/unit/test_m8r_06_03_production_adapter.py', 'scripts/validate_phase_j_final_closure_r2.py', 'tests/acceptance/test_phase_j_final_closure_r2.py', 'tests/fixtures/phase_j/closure_r2/', 'tests/helpers/phase_j_closure_r2.py', 'docs/governance/phase_j/PHASE_J_FINAL_CLOSURE_R2_'])
        require(all(p.startswith(allowed) for p in git('diff', '--name-only', BASE, 'HEAD').splitlines()), 'UNRELATED_PRODUCTION_DIFF')
    return binding

def validate_boundary(evidence):
    require(evidence['MCP_tools'] == r1.MCP_NAMES, 'MCP_COUNT_OR_NAME_DRIFT')
    require(not any(evidence['network'].values()), 'NETWORK_OR_AGENT_EXECUTION')
    require(evidence['state']['Phase_K'] == 'NOT_STARTED' and evidence['state']['Roadmap_checkbox'] == 'UNCHECKED', 'UNAUTHORIZED_PHASE_ADVANCE')
    require(evidence['host_selector_before'] == evidence['host_selector_after'], 'HOST_SELECTOR_MUTATION')
    return True

def validate_witness(record):
    require(record['scenario_id'] == 'J1-21', 'SCENARIO_OUT_OF_SCOPE')
    require(record['executed_layers'] == ['integration', 'service_api'], 'UNEXECUTED_LAYER_PROMOTION')
    r1.validate_scenario(record)
    require(record.get('real_agent_sessions') == 0 and record.get('real_agent_tool_calls') == 0 and record.get('agent_provider_transport') == 0, 'REAL_AGENT_NOT_AUTHORIZED')
    calls = record.get('source_invocations', [])
    require(len(calls) == record['initial_execution_count'] == 1 and all(c['source_boundary'] == 'raw_http_fixture' and c['external_dispatch'] is False and c['method'] == 'GET' and c['url'].startswith('https://mis.twse.com.tw/stock/api/getStockInfo.jsp?') for c in calls), 'SOURCE_TRANSPORT_RECEIPT_INVALID')
    native = record['normalized_observation']
    require(native['source'] == 'TWSE_MIS' and native['source_timestamp'] == '2026-09-01T05:30:00Z', 'SOURCE_TIMESTAMP_REWRITTEN')
    require((native.get('retrieved_at_utc') or native.get('retrieved_at')) == '2026-10-08T06:00:00Z', 'RETRIEVAL_TIMESTAMP_REWRITTEN')
    policy = next(s for s in read(ROOT / 'docs/data_capabilities/m8_source_capability_registry.json')['sources'] if s['source_id'] == 'TWSE_MIS')
    expected = _assess_current_observation(native, policy)
    require(native['governed_currentness'] == expected, 'EVALUATOR_OR_POLICY_DIVERGENCE')
    require(expected['status'] == 'stale' and expected['freshness_assessment'] == 'stale_intraday_snapshot', 'CANONICAL_TYPED_STALE_MISSING')
    envelope = record['result']['targets'][0]['evidence']['current_observation']
    currentness = envelope['currentness']
    require(all(currentness.get(k) == v for k, v in expected.items()), 'RESULT_CURRENTNESS_DIVERGENCE')
    require(envelope['observed_fields']['freshness_context'] == currentness, 'OBSERVED_CURRENTNESS_DIVERGENCE')
    require(envelope['status'] == 'available' and currentness['currentness_policy'] == 'family_specific', 'STALE_AVAILABILITY_COLLAPSE')
    require('stale_intraday_snapshot' in record['handoff']['ai_ready_markdown'] and 'Current Market Snapshot' not in record['handoff']['ai_ready_markdown'], 'HANDOFF_STALE_MISREPRESENTED')
    require(record['source_artifact_sha256'] == file_sha_from_object(record['source_artifact']), 'SOURCE_ARTIFACT_HASH_MISMATCH')
    require(native in record['source_artifact']['records'], 'SOURCE_ARTIFACT_LINEAGE_MISSING')
    # Verify the same source bytes are present in Audit's artifact inventory.
    require(record['source_artifact_sha256'] in json.dumps(record['audit']), 'AUDIT_SOURCE_HASH_LINEAGE_MISSING')
    require(any('stale_intraday_snapshot' in operation.get('warnings', []) for operation in record['audit']['operation_lineage']), 'AUDIT_TYPED_STALE_MISSING')
    text = record['handoff']['ai_ready_markdown'].casefold()
    require(not any(marker in text for marker in ('current market price', 'currently trading at', 'realtime price', 'live price', 'fresh current observation')), 'HANDOFF_FALSE_CURRENT_CLAIM')
    g = next(s for s in read(DOC / 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json')['scenarios'] if s['scenario_id'] == 'J1-21')
    require(not evaluate_scenario(g, r1.observe(record)), 'J3_SEMANTIC_FAILURE')
    return True

def file_sha_from_object(value):
    return hashlib.sha256((json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()

def derive(record):
    validate_witness(record)
    matrix = copy.deepcopy(read(DOC / 'PHASE_J_FINAL_CLOSURE_R1_EFFECTIVE_COVERAGE_V1.json'))
    row = next(r for r in matrix['scenarios'] if r['scenario_id'] == 'J1-21')
    promotions = []
    for layer in record['executed_layers']:
        cell = row['layers'][layer]
        require(cell['status'] == 'PLANNED', 'PROMOTION_BASELINE_DRIFT')
        refs = [{'kind': 'integration_test' if layer == 'integration' else 'service_test', 'ref': 'tests/acceptance/test_phase_j_final_closure_r2.py::test_j1_21_production_path'}, {'kind': 'integration_test' if layer == 'integration' else 'service_test', 'ref': 'docs/governance/phase_j/PHASE_J_FINAL_CLOSURE_R2_J1_21_WITNESS_LEDGER_V1.json#J1-21'}]
        promotions.append({'scenario_id': 'J1-21', 'layer': layer, 'baseline_status': cell['status'], 'new_overlay_status': 'COVERED_EXISTING', 'witness_kind': 'fixture_backed_production_path', 'evidence_refs': refs, 'scenario_match': 'J3 typed stale and family-specific policy', 'introduced_by_tranche': 'PHASE_J_FINAL_CLOSURE_R2', 'result_id': record['result']['result_id'], 'audit_package_id': record['audit']['audit_package_id']})
        cell.update(status='COVERED_EXISTING', evidence_refs=refs, introduced_by_tranche='PHASE_J_FINAL_CLOSURE_R2')
    matrix.update(schema_version='phase_j_final_closure_r2_effective_coverage.v1', authority_status='R2_FROZEN_ACCEPTANCE_CANDIDATE_PENDING_REVIEW', introduced_by_tranche='PHASE_J_FINAL_CLOSURE_R2', baseline_binding={'path': 'docs/governance/phase_j/PHASE_J_FINAL_CLOSURE_R1_EFFECTIVE_COVERAGE_V1.json', 'sha256': file_sha(DOC / 'PHASE_J_FINAL_CLOSURE_R1_EFFECTIVE_COVERAGE_V1.json')}, coverage_summary={'status_counts': dict(sorted(Counter(c['status'] for r in matrix['scenarios'] for c in r['layers'].values()).items())), 'promoted_cell_count': len(promotions)})
    historic = read(DOC / 'PHASE_J_FINAL_CLOSURE_R1_2026-10-11.json')
    obligations = copy.deepcopy(historic['obligations'])
    for obligation in obligations:
        if obligation['obligation'] == 'J1-21':
            require(not obligation['satisfied'], 'J1_21_ALREADY_SATISFIED')
            obligation['satisfied'] = True
    return {'disposition': PASS, 'promotions': promotions, 'effective_matrix': matrix, 'obligations': obligations, 'remaining_obligations': sum(not o['satisfied'] for o in obligations)}

def validate(terminal=False, check_git=True):
    baseline(check_git)
    if not terminal:
        return {'validator_status': 'PASS', 'baseline_immutable': True, 'witness_not_yet_adjudicated': True}
    ledger = read(DOC / 'PHASE_J_FINAL_CLOSURE_R2_J1_21_WITNESS_LEDGER_V1.json')
    expected = derive(ledger['scenario_record'])
    require(read(DOC / 'PHASE_J_FINAL_CLOSURE_R2_WITNESS_DELTA_V1.json')['promotions'] == expected['promotions'], 'COVERAGE_LAUNDERING')
    require(read(DOC / 'PHASE_J_FINAL_CLOSURE_R2_EFFECTIVE_COVERAGE_V1.json') == expected['effective_matrix'], 'EFFECTIVE_OVERLAY_DIVERGENCE')
    evidence = read(DOC / 'PHASE_J_FINAL_CLOSURE_R2_2026-10-11.json')
    require(evidence['disposition'] == expected['disposition'] and evidence['obligations'] == expected['obligations'] and evidence['remaining_obligations'] == expected['remaining_obligations'], 'FALSE_CLOSURE')
    validate_boundary(evidence)
    require(not evidence['default_ci']['candidate_only_failure_nodes'], 'CANDIDATE_ONLY_CI_FAILURE')
    return {'validator_status': 'PASS', 'disposition': expected['disposition'], 'remaining_obligations': expected['remaining_obligations']}

def validate_overlay(proposed, record):
    require(proposed == derive(record), 'COVERAGE_OR_OBLIGATION_LAUNDERING')
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--terminal', action='store_true')
    args = parser.parse_args()
    print(json.dumps(validate(args.terminal), indent=2))
