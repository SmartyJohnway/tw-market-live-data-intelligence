#!/usr/bin/env python3
"""Acceptance-only deterministic regression scope and receipt verification.

Never executes a candidate, contacts a provider, or grants authorization.
All hashes of semantic objects use sorted compact UTF-8 JSON; file bindings
use exact bytes. Receipts are integrity records, not signatures or permission.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DOC = ROOT / 'docs/governance/phase_j'
AUTHORITY = DOC / 'PHASE_J_J4_REGRESSION_AUTHORITY_V1.json'
MANIFEST_SCHEMA = DOC / 'PHASE_J_J4_REGRESSION_CHANGE_MANIFEST_SCHEMA_V1.json'
RECEIPT_SCHEMA = DOC / 'PHASE_J_J4_REGRESSION_RECEIPT_SCHEMA_V1.json'
CLASSES = ['NEW_SOURCE', 'NEW_EVIDENCE_FAMILY', 'NEW_MCP_VERSION', 'NEW_AGENT_HOST', 'NEW_RELEASE']
DIMENSIONS = ['identity', 'source', 'period', 'currentness', 'missing', 'partial', 'corporate_action', 'authorization', 'bounded_execution', 'citations_lineage', 'no_trading']
LAYERS = ['contract_fixture', 'deterministic_unit', 'integration', 'service_api', 'workbench', 'mcp', 'fresh_install', 'bounded_live', 'real_agent']
SAFETY = ['J1-01', 'J1-08', 'J1-10', 'J1-11', 'J1-12', 'J1-13', 'J1-14', 'J1-16', 'J1-20', 'J1-22', 'J1-23', 'J1-24', 'J1-25', 'J1-26', 'J1-27']
PREEXECUTION = ['J1-10', 'J1-12', 'J1-24', 'J1-25', 'J1-26', 'J1-27']
TOOLS = ['market_describe_capabilities', 'market_validate_request', 'market_preview_request', 'market_read_result', 'market_export_ai_handoff', 'market_fetch_evidence']
COVERED = {'COVERED_EXISTING', 'COVERED_J0_J1'}


BASELINE_HASHES = {'PHASE_J_J2_R1_COVERAGE_DELTA_V1.json': '321e9008ebca8d8a42e77993ae9329b274dd3e05ad5553554890f97e65618539',
 'PHASE_J_J2_R1_EFFECTIVE_COVERAGE_MATRIX_V1.json': '8fe53871a764d66dcca6d3a5531d4801008c58f77e74ace7eede637f15436c3a',
 'PHASE_J_J2_R1_WORKBENCH_HEADLESS_EXECUTION_LEDGER_V1.json': '2c30451e2dc6071191d7d5107149770c4d34767cc45c26b5fa819b68249239fa',
 'PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.json': '74e27776bf9768613cbc25f1f6cf3c81687f29be2551f4f9e31141772ac29487',
 'PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.md': 'eb324584ef03103137eec03a5190ba5bb6c2bd7d6b1d66c16693cae3920975f0',
 'PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json': 'b26712d1389b904ff003b22aa135caac43ab8f6fc7b32dad571b70438248c864',
 'PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json': '5d07ab2618e6bfa6c79f796df28cd69df5c105fb8f60396c293675737febcd45',
 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json': 'b4059b4c1a439e091393daed1887f08c1f6a83e59dfc4095e82e22130e6422fa',
 'PHASE_J_J3_SEMANTIC_TRACEABILITY_V1.json': '8dfd4f256334959142bf81d163546ed0fe485e3d92393fd570fb97ac22d0e247',
 'PHASE_J_J3_R1_GOLDEN_SEMANTIC_FIDELITY_AND_LOSSLESS_PROJECTION_HARDENING_2026-10-11.json': '00ccc7bba67f656fbc3046465a4923c2abf7cc9deeea03411a06cb8df8a402f2',
 'PHASE_J_J3_R1_GOLDEN_SEMANTIC_FIDELITY_AND_LOSSLESS_PROJECTION_HARDENING_2026-10-11.md': '8fda262e5d30f6734cea4679af0ffca7c2284134b2e8d1e2371dddea8ed7e13a'}

REVIEWS = {'J1': '5481271339', 'J2_R1': '5481723267', 'J3_R1': '5482393445', 'J4_authorization': '5482593485'}

STARTING = {'head': '90dc62ea9e6ed3255c065a93910e661f525d483f',
 'tree': '5d19b92a21ced372686b49ff0a1f3871d1c52293',
 'main': '6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a',
 'branch': 'phase-j/j-b04-a5-bounded-live-source-acceptance'}

OWNER_SHA = '5080d30af2efb5c6586ba43d73463ce3d708b5ea8cf3cf0cbd59bc432dd0db5f'

EXPECTED_CORE = [{'scenario_id': 'J1-01',
  'accepted_title': 'normal TWSE',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-01'},
 {'scenario_id': 'J1-08',
  'accepted_title': 'corrected disclosure',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-08'},
 {'scenario_id': 'J1-10',
  'accepted_title': 'financial statements',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-10'},
 {'scenario_id': 'J1-11',
  'accepted_title': 'attention / disposition',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-11'},
 {'scenario_id': 'J1-12',
  'accepted_title': 'suspend / resume',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-12'},
 {'scenario_id': 'J1-13',
  'accepted_title': 'ex-dividend',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-13'},
 {'scenario_id': 'J1-14',
  'accepted_title': 'ex-right',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-14'},
 {'scenario_id': 'J1-16',
  'accepted_title': 'reference-price discontinuity',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-16'},
 {'scenario_id': 'J1-20',
  'accepted_title': 'partial success',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-20'},
 {'scenario_id': 'J1-22',
  'accepted_title': 'missing',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-22'},
 {'scenario_id': 'J1-23',
  'accepted_title': 'source failure',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-23'},
 {'scenario_id': 'J1-24',
  'accepted_title': 'identity ambiguity',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-24'},
 {'scenario_id': 'J1-25',
  'accepted_title': 'unsupported identity',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-25'},
 {'scenario_id': 'J1-26',
  'accepted_title': 'authorization refusal',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-26'},
 {'scenario_id': 'J1-27',
  'accepted_title': 'resource bound',
  'semantic_authority': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-27'}]

CLASS_RULES = {'NEW_SOURCE': {'scenario_scope': 'explicit_or_exact_accepted_domain_match_plus_safety_core',
                'requires_impact_declaration': True,
                'live_gate': 'when_requested'},
 'NEW_EVIDENCE_FAMILY': {'scenario_scope': 'explicit_scenarios_plus_safety_core',
                         'requires_impact_declaration': True,
                         'required_semantic_impact_fields': ['intended_source_authority',
                                                             'timing',
                                                             'missing',
                                                             'partial',
                                                             'citations'],
                         'live_gate': 'when_requested'},
 'NEW_MCP_VERSION': {'scenario_scope': 'safety_core_plus_declared_impact',
                     'mandatory_checks': ['tool_discovery',
                                          'tool_names',
                                          'tool_schemas',
                                          'validate',
                                          'preview',
                                          'authorization',
                                          'execute_once',
                                          'result',
                                          'ai_handoff',
                                          'large_partial_failure',
                                          'no_trading']},
 'NEW_AGENT_HOST': {'scenario_scope': 'all_27',
                    'real_agent_gate': 'always',
                    'mandatory_checks': ['mcp_protocol',
                                         'authorization_sequencing',
                                         'partial_missing_currentness',
                                         'citations',
                                         'no_trading']},
 'NEW_RELEASE': {'scenario_scope': 'all_27',
                 'mandatory_checks': ['all_11_dimensions',
                                      'applicable_deterministic_layers',
                                      'fresh_install',
                                      'six_tool_contract',
                                      'J1_J2_J3_validators']}}

SELECTION_POLICY = {'multiple_classes': 'union',
 'dimensions': 'all_applicable_J3_dimensions_per_selected_scenario',
 'deterministic_layers': 'first_six_except_documented_preexecution_integration; fresh_install_J1_25',
 'preexecution_integration_exemptions': ['J1-10', 'J1-12', 'J1-24', 'J1-25', 'J1-26', 'J1-27'],
 'preexecution_basis': 'Accepted J2-R1 execution ledger: rejection/refusal before legitimate Result/Audit '
                       'construction; no fabricated integration package. Baseline PLANNED cells remain '
                       'unchanged.',
 'fresh_install_scenario_ids': ['J1-25'],
 'changed_paths': 'supporting_only_never_sole_impact_authority',
 'unknown_class': 'CHANGE_CLASS_UNRESOLVED',
 'unknown_impact': 'REGRESSION_IMPACT_UNRESOLVED',
 'no_empty_plan': True}

AUTHORIZATION_POLICY = {'bounded_live': 'NOT_GRANTED',
 'real_agent': 'NOT_GRANTED',
 'manifest_or_receipt_can_self_authorize': False,
 'accepted_future_authorizations': [],
 'grant_acceptance': 'Requires separately independently accepted hash-bound authority entry; current v1 pins '
                     'an empty grant registry.'}

CONTRACTS = ['unified_market_evidence_request.v3',
 'unified_market_evidence_result.v3',
 'unified_market_evidence_audit_package.v3']

PRECEDENCE = ['REGRESSION_SEMANTIC_FAILURE',
 'IMPACT_DECLARATION_REQUIRED',
 'REGRESSION_COVERAGE_GAP',
 'REQUIRES_LIVE_AND_REAL_AGENT_AUTHORIZATION',
 'REQUIRES_SEPARATE_LIVE_AUTHORIZATION',
 'REQUIRES_SEPARATE_REAL_AGENT_AUTHORIZATION',
 'REGRESSION_READY_NETWORK_FREE']

VALIDATORS = ['scripts/validate_phase_j_j0_j1_scenario_registry.py',
 'scripts/validate_phase_j_j2_r1_workbench_headless_completion.py',
 'scripts/validate_phase_j_j3_golden_expected_semantics.py',
 'scripts/validate_phase_j_j4_regression_authority.py']

PROFILES = ['default-ci', 'phase-j-regression-authority']

PHASE_STATE = {'Phase_J': 'STARTED',
 'J0': 'COMPLETE',
 'J1': 'INDEPENDENTLY_ACCEPTED',
 'J2': 'CLOSED_INDEPENDENTLY_ACCEPTED',
 'J3': 'INDEPENDENTLY_ACCEPTED',
 'J4': 'FROZEN_ACCEPTANCE_CANDIDATE_PENDING_REVIEW',
 'Phase_K': 'NOT_STARTED'}

NETWORK_POLICY = {'market_GET': 0, 'market_HEAD': 0, 'market_POST': 0, 'live_executions': 0, 'real_agent_executions': 0}

REGRESSION_INVARIANTS = [{'invariant_id': 'missing_not_zero',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-22/dimensions/missing'},
 {'invariant_id': 'source_failed_not_valid_empty',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-23/dimensions/source'},
 {'invariant_id': 'partial_not_full_success',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-20/dimensions/partial'},
 {'invariant_id': 'authorization_refused_no_execution',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-26/dimensions/authorization'},
 {'invariant_id': 'ambiguous_identity_not_executable',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-24/dimensions/identity'},
 {'invariant_id': 'bounded_H2_not_complete_family',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-14/dimensions/source'},
 {'invariant_id': 'H4_incomplete_blocks_ordinary_return',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-16/dimensions/corporate_action'},
 {'invariant_id': 'result_audit_handoff_lineage',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-01/dimensions/citations_lineage'},
 {'invariant_id': 'no_recommendation_or_trade_order',
  'authority_ref': 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json#J1-01/dimensions/no_trading'}]


ACCEPTANCE_CONTRACT_HASHES = {'docs/governance/phase_j/PHASE_J_J4_REGRESSION_CHANGE_MANIFEST_SCHEMA_V1.json': 'ff0b5d8e0cf22673e234a9241532757f9b37ca5c0bc7d85aeb76c3e4e1e7d7fc',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_RECEIPT_SCHEMA_V1.json': 'c8ac4949aba86a1323ff2305d9835584f664b11b1aa5f911eef1101911dd2ac8'}

EVIDENCE_KINDS = {'bounded_live': ['historical_live_acceptance'],
 'contract_fixture': ['fixture', 'unit_test'],
 'deterministic_unit': ['unit_test'],
 'fresh_install': ['fresh_install_test'],
 'integration': ['integration_test', 'e2e_acceptance'],
 'mcp': ['mcp_test'],
 'real_agent': ['real_agent_acceptance'],
 'service_api': ['service_test'],
 'workbench': ['workbench_test']}
FUTURE_PROFILE_POLICY = {'workbench_required': 'browser-e2e', 'J4_execution': 'browser-e2e is a future local regression prerequisite only; not executed by J4'}

def require(condition, code):
    if not condition:
        raise ValueError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, 'DUPLICATE_JSON_KEY: ' + k)
            result[k] = v
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs)


def baseline():
    return load(DOC / 'PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json'), load(DOC / 'PHASE_J_J2_R1_EFFECTIVE_COVERAGE_MATRIX_V1.json'), load(DOC / 'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json')


def validate_authority(authority=None):
    a = load(AUTHORITY) if authority is None else authority
    # Policy is pinned in code as well as data; a data mutation cannot relax it.
    require(a['schema_version'] == 'phase_j_j4_regression_authority.v1', 'AUTHORITY_VERSION_DRIFT')
    require(a['baseline_hashes'] == BASELINE_HASHES, 'REGRESSION_AUTHORITY_BASELINE_DRIFT')
    for name, expected in BASELINE_HASHES.items():
        require(file_hash(DOC / name) == expected, 'REGRESSION_AUTHORITY_BASELINE_DRIFT: ' + name)
    require(a['reviews'] == REVIEWS, 'REVIEW_AUTHORITY_DRIFT')
    require(a['starting_authority'] == STARTING, 'STARTING_AUTHORITY_DRIFT')
    require(hashlib.sha256(a['owner_authorization_statement'].encode()).hexdigest() == OWNER_SHA == a['owner_authorization_sha256'], 'OWNER_AUTHORIZATION_DRIFT')
    require(a['acceptance_contract_hashes'] == ACCEPTANCE_CONTRACT_HASHES, 'ACCEPTANCE_CONTRACT_DRIFT')
    for path, expected in ACCEPTANCE_CONTRACT_HASHES.items():
        require(file_hash(ROOT / path) == expected, 'ACCEPTANCE_CONTRACT_DRIFT')
    registry, matrix, golden = baseline()
    ids = [s['scenario_id'] for s in registry['scenarios']]
    require(len(ids) == 27 and len(set(ids)) == 27 and a['scenario_ids'] == ids, 'SCENARIO_AUTHORITY_DRIFT')
    require(a['semantic_dimensions'] == DIMENSIONS == golden['dimensions'], 'SEMANTIC_DIMENSION_DRIFT')
    require(a['layers'] == LAYERS == matrix['coverage_dimensions'], 'LAYER_VOCABULARY_DRIFT')
    require(a['layer_evidence_kinds'] == EVIDENCE_KINDS and a['future_profile_policy'] == FUTURE_PROFILE_POLICY, 'LAYER_EVIDENCE_POLICY_DRIFT')
    require(a['change_classes'] == CLASSES, 'CHANGE_CLASS_AUTHORITY_DRIFT')
    require({kind for kinds in EVIDENCE_KINDS.values() for kind in kinds} <= set(matrix['evidence_kinds']), 'UNKNOWN_LAYER_EVIDENCE_KIND')
    require(a['mandatory_safety_core'] == EXPECTED_CORE, 'SAFETY_CORE_DRIFT')
    require(a['class_rules'] == CLASS_RULES, 'CLASS_SELECTION_RULE_DRIFT')
    require(a['selection_policy'] == SELECTION_POLICY, 'SELECTION_POLICY_DRIFT')
    require(a['authorization_policy'] == AUTHORIZATION_POLICY, 'SELF_AUTHORIZATION_FORBIDDEN')
    require(a['mcp_tools'] == TOOLS, 'MCP_TOOL_COUNT_OR_NAME_DRIFT')
    require(a['public_contracts'] == CONTRACTS, 'PUBLIC_CONTRACT_DRIFT')
    require(a['regression_invariants'] == REGRESSION_INVARIANTS, 'REGRESSION_INVARIANT_DRIFT')
    require(a['global_invariants'] == golden['global_boundaries'], 'NO_TRADING_OR_SEMANTIC_INVARIANT_DRIFT')
    require(a['disposition_precedence'] == PRECEDENCE, 'DISPOSITION_PRECEDENCE_DRIFT')
    require(a['required_validators'] == VALIDATORS and a['required_test_profiles'] == PROFILES, 'REGRESSION_CHECKS_DRIFT')
    require(a['phase_state'] == PHASE_STATE and a['network_policy'] == NETWORK_POLICY, 'PHASE_OR_NETWORK_AUTHORITY_DRIFT')
    require(a['authority_status'] == 'FROZEN_ACCEPTANCE_CANDIDATE_PENDING_EXACT_HEAD_REVIEW', 'CANDIDATE_STATE_DRIFT')
    ledger = load(DOC / 'PHASE_J_J2_R1_WORKBENCH_HEADLESS_EXECUTION_LEDGER_V1.json')
    exempt = sorted(r['scenario_id'] for r in ledger['scenarios'] if r['classification'] == 'PREEXECUTION_FAIL_CLOSED' and 'integration' in r['not_applicable_layers'])
    require(exempt == PREEXECUTION, 'PREEXECUTION_EXEMPTION_AUTHORITY_DRIFT')
    for row in a['mandatory_safety_core']:
        source = next(s for s in registry['scenarios'] if s['scenario_id'] == row['scenario_id'])
        require(row['accepted_title'] == source['title'], 'SAFETY_CORE_SEMANTIC_IDENTITY_DRIFT')
        require(any(s['scenario_id'] == row['scenario_id'] for s in golden['scenarios']), 'SAFETY_CORE_WITHOUT_GOLDEN_AUTHORITY')
    return a


def validate_manifest(m):
    require(bool(m.get('change_classes')), 'CHANGE_CLASS_OMITTED')
    require(set(m['change_classes']) <= set(CLASSES), 'CHANGE_CLASS_UNRESOLVED')
    from jsonschema import Draft202012Validator
    errors = sorted(Draft202012Validator(load(MANIFEST_SCHEMA)).iter_errors(m), key=lambda e: str(e.path))
    require(not errors, 'CHANGE_MANIFEST_INVALID: ' + '; '.join(e.message for e in errors))
    flags = [('touches_mcp', 'NEW_MCP_VERSION'), ('touches_agent_host', 'NEW_AGENT_HOST'), ('release_candidate', 'NEW_RELEASE')]
    for flag, cls in flags:
        require(not m[flag] or cls in m['change_classes'], 'CHANGE_CLASS_OMITTED: ' + cls)
    known = set(load(AUTHORITY)['scenario_ids'])
    require(set(m['affected_scenario_ids']) <= known, 'UNKNOWN_SCENARIO_IMPACT')


def gate_disposition(semantic_failures, impact_codes, coverage_gaps, gates):
    if semantic_failures:
        return 'REGRESSION_SEMANTIC_FAILURE'
    if impact_codes:
        return 'IMPACT_DECLARATION_REQUIRED'
    if coverage_gaps:
        return 'REGRESSION_COVERAGE_GAP'
    names = {g['layer'] for g in gates if g['authorization'] == 'NOT_GRANTED'}
    if names == {'bounded_live', 'real_agent'}:
        return 'REQUIRES_LIVE_AND_REAL_AGENT_AUTHORIZATION'
    if 'bounded_live' in names:
        return 'REQUIRES_SEPARATE_LIVE_AUTHORIZATION'
    if 'real_agent' in names:
        return 'REQUIRES_SEPARATE_REAL_AGENT_AUTHORIZATION'
    return 'REGRESSION_READY_NETWORK_FREE'


def select_plan(manifest, authority=None):
    a = validate_authority(authority)
    validate_manifest(manifest)
    registry, matrix, golden = baseline()
    rows = {s['scenario_id']: s for s in registry['scenarios']}
    cov = {s['scenario_id']: s['layers'] for s in matrix['scenarios']}
    semantics = {s['scenario_id']: s for s in golden['scenarios']}
    classes = [c for c in CLASSES if c in manifest['change_classes']]
    selected = set(SAFETY) | set(manifest['affected_scenario_ids'])
    impact_codes = []
    domain_matches = set()
    # Exact accepted domain tokens, never filename guesses or substring ranking.
    for sid, row in rows.items():
        tokens = set(row['required_data_needs']) | set(row['required_evidence_families'])
        tokens.add(row['source_expectation']['source_scope'])
        if tokens & set(manifest['affected_sources'] + manifest['affected_data_needs'] + manifest['affected_evidence_families']):
            domain_matches.add(sid)
    selected |= domain_matches
    if 'NEW_MCP_VERSION' in classes:
        selected.add('J1-03')  # accepted multi-target/large-package contract scenario
    if 'NEW_SOURCE' in classes:
        if not manifest['affected_sources'] or not (manifest['affected_scenario_ids'] or domain_matches):
            impact_codes.append('REGRESSION_IMPACT_UNRESOLVED')
    if 'NEW_EVIDENCE_FAMILY' in classes:
        required = CLASS_RULES['NEW_EVIDENCE_FAMILY']['required_semantic_impact_fields']
        if not manifest['affected_scenario_ids'] or not (manifest['affected_data_needs'] or manifest['affected_evidence_families']) or not all(manifest.get('semantic_impact', {}).get(k) for k in required):
            impact_codes.append('IMPACT_DECLARATION_REQUIRED')
    if manifest['touches_security_master'] and not manifest['affected_scenario_ids']:
        impact_codes.append('IMPACT_DECLARATION_REQUIRED')
    if 'NEW_RELEASE' in classes or 'NEW_AGENT_HOST' in classes:
        selected |= set(rows)
    ids = sorted(selected)
    require(ids, 'ZERO_SCENARIO_REGRESSION_FORBIDDEN')
    dimensions = {sid: [d for d in DIMENSIONS if semantics[sid]['dimensions'][d]['applicability'] == 'APPLICABLE'] for sid in ids}
    cells, covered, gaps, exemptions = [], [], [], []
    for sid in ids:
        for layer in LAYERS[:6]:
            if layer == 'integration' and sid in PREEXECUTION:
                exemptions.append({'scenario_id': sid, 'layer': layer, 'reason': 'accepted_preexecution_refusal_no_result_package'})
                continue
            cell = {'scenario_id': sid, 'layer': layer, 'baseline_status': cov[sid][layer]['status'], 'evidence_refs': copy.deepcopy(cov[sid][layer]['evidence_refs'])}
            cells.append(cell)
            (covered if cell['baseline_status'] in COVERED else gaps).append(cell)
        if sid == 'J1-25':
            cell = {'scenario_id': sid, 'layer': 'fresh_install', 'baseline_status': cov[sid]['fresh_install']['status'], 'evidence_refs': copy.deepcopy(cov[sid]['fresh_install']['evidence_refs'])}
            cells.append(cell)
            (covered if cell['baseline_status'] in COVERED else gaps).append(cell)
    gates = []
    if manifest['requested_live_revalidation']:
        gates.append({'layer': 'bounded_live', 'authorization': 'NOT_GRANTED', 'disposition': 'REQUIRES_SEPARATE_LIVE_AUTHORIZATION', 'scenario_ids': [sid for sid in ids if cov[sid]['bounded_live']['status'] != 'NOT_APPLICABLE']})
    if 'NEW_AGENT_HOST' in classes or manifest['requested_real_agent_revalidation']:
        gates.append({'layer': 'real_agent', 'authorization': 'NOT_GRANTED', 'disposition': 'REQUIRES_SEPARATE_REAL_AGENT_AUTHORIZATION', 'scenario_ids': ids})
    checks = sorted({check for c in classes for check in CLASS_RULES[c].get('mandatory_checks', [])})
    plan = {'authority_version': a['schema_version'], 'regression_authority_hash': file_hash(AUTHORITY), 'baseline_hashes': a['baseline_hashes'], 'baseline_review_ids': a['reviews'], 'change_id': manifest['change_id'], 'change_manifest_sha256': digest(manifest), 'candidate_commit': manifest['candidate_commit'], 'candidate_tree': manifest['candidate_tree'], 'change_classes': classes, 'selected_scenario_ids': ids, 'mandatory_safety_core_ids': SAFETY, 'selected_semantic_dimensions': dimensions, 'required_layers': cells, 'currently_covered_layers': covered, 'planned_or_missing_layers': gaps, 'not_applicable_layers': exemptions, 'authorization_gated_layers': gates, 'historical_live_evidence': {sid: copy.deepcopy(cov[sid]['bounded_live']) for sid in ids if cov[sid]['bounded_live']['status'] == 'COVERED_EXISTING'}, 'required_validators': a['required_validators'], 'required_test_profiles': a['required_test_profiles'] + (['browser-e2e'] if any(c['layer'] == 'workbench' for c in cells) else []), 'required_contract_checks': checks, 'mcp_tool_baseline': TOOLS, 'evidence_requirements': {'per_cell': 'exact_scenario_layer_test_node_and_passing_execution_evidence', 'oracle': 'accepted_J3_typed_semantics_not_prose', 'authorization': 'separate_hash_bound_independently_accepted_authority'}, 'blocking_conditions': sorted(set(impact_codes)), 'gate_disposition': gate_disposition([], impact_codes, gaps, gates)}
    plan['regression_plan_hash'] = digest(plan)
    return copy.deepcopy(plan)


def validate_plan(manifest, plan, authority=None):
    expected = select_plan(manifest, authority)
    # Specific errors precede the complete deep comparison.
    require(plan.get('selected_scenario_ids') == expected['selected_scenario_ids'], 'REGRESSION_SCENARIO_SCOPE_MISMATCH')
    require(plan.get('selected_semantic_dimensions') == expected['selected_semantic_dimensions'], 'REGRESSION_DIMENSION_SCOPE_MISMATCH')
    require(plan.get('authorization_gated_layers') == expected['authorization_gated_layers'], 'REGRESSION_AUTHORIZATION_GATE_MISMATCH')
    require(plan.get('planned_or_missing_layers') == expected['planned_or_missing_layers'], 'REGRESSION_COVERAGE_LAUNDERING')
    require(plan == expected, 'REGRESSION_PLAN_BINDING_OR_POLICY_MISMATCH')
    return True


def make_receipt(manifest, plan, evidence=(), semantic_failures=(), synthetic=True, observations=None, check_evidence=()):
    """Create a conservative receipt; absent per-cell execution evidence stays HOLD."""
    validate_plan(manifest, plan)
    evidence = copy.deepcopy(list(evidence))
    observations = copy.deepcopy(observations or {})
    check_evidence = copy.deepcopy(list(check_evidence))
    failures = list(semantic_failures)
    from scripts.validate_phase_j_j3_golden_expected_semantics import evaluate_scenario
    golden = {r['scenario_id']: r for r in baseline()[2]['scenarios']}
    require(set(observations) <= set(plan['selected_scenario_ids']), 'SEMANTIC_OBSERVATION_SCOPE_MISMATCH')
    for sid, observed in observations.items():
        failures += [sid + ': ' + e for e in evaluate_scenario(golden[sid], observed)]
    failures = sorted(set(failures))
    passed = {(e.get('scenario_id'), e.get('layer')) for e in evidence if e.get('passed') is True}
    gaps = [c for c in plan['required_layers'] if (c['scenario_id'], c['layer']) not in passed]
    gaps += [{'scenario_id': sid, 'layer': 'typed_semantic_evidence', 'reason': 'missing_J3_observation'} for sid in plan['selected_scenario_ids'] if sid not in observations]
    checks = plan['required_validators'] + plan['required_test_profiles'] + ['six_tool_contract'] + plan['required_contract_checks']
    completed = {e['check'] for e in check_evidence if e.get('passed') is True}
    gaps += [{'check': c, 'reason': 'missing_passing_check_evidence'} for c in checks if c not in completed]
    r = {'schema_version': 'phase_j_j4_regression_receipt.v1', 'regression_authority_hash': file_hash(AUTHORITY), 'change_manifest_hash': digest(manifest), 'regression_plan_hash': plan['regression_plan_hash'], 'candidate_commit': manifest['candidate_commit'], 'candidate_tree': manifest['candidate_tree'], 'selected_scenarios': plan['selected_scenario_ids'], 'selected_dimensions': plan['selected_semantic_dimensions'], 'executed_layers': sorted({e['layer'] for e in evidence}), 'test_validator_evidence': evidence, 'authorization_gates': plan['authorization_gated_layers'], 'bounded_live_authorized': False, 'real_agent_authorized': False, 'authorization_refs': [], 'semantic_observations': observations, 'check_evidence': check_evidence, 'semantic_failures': failures, 'coverage_gaps': gaps, 'synthetic': synthetic, 'disposition': gate_disposition(failures, plan['blocking_conditions'], gaps, plan['authorization_gated_layers'])}
    r['receipt_hash'] = digest(r)
    return copy.deepcopy(r)


def explicit_test_node(ref):
    parts = ref.split('::')
    if len(parts) < 2:
        return False
    path = ROOT / parts[0]
    if not path.is_file():
        return False
    name = parts[-1].split('[')[0]
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeError):
        return False
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name for n in ast.walk(tree))


def validate_receipt(manifest, plan, receipt):
    from jsonschema import Draft202012Validator
    validate_plan(manifest, plan)
    errors = list(Draft202012Validator(load(RECEIPT_SCHEMA)).iter_errors(receipt))
    require(not errors, 'REGRESSION_RECEIPT_SCHEMA_INVALID')
    require(not receipt['bounded_live_authorized'] and not receipt['real_agent_authorized'] and not receipt['authorization_refs'], 'RECEIPT_SELF_AUTHORIZATION_FORBIDDEN')
    require(not manifest.get('fixture_metadata', {}).get('synthetic') or receipt['synthetic'], 'SYNTHETIC_MANIFEST_NOT_REAL_CANDIDATE')
    evidence = receipt['test_validator_evidence']
    required = {(c['scenario_id'], c['layer']) for c in plan['required_layers']}
    seen = set()
    for e in evidence:
        require(set(e) == {'scenario_id', 'layer', 'evidence_kind', 'test_node_id', 'passed', 'candidate_commit', 'candidate_tree', 'synthetic'}, 'EXECUTION_EVIDENCE_FIELDS_INVALID')
        pair = (e['scenario_id'], e['layer'])
        require(pair in required and pair not in seen, 'EXECUTION_EVIDENCE_SCOPE_OR_DUPLICATE')
        seen.add(pair)
        require(e['evidence_kind'] in EVIDENCE_KINDS[e['layer']], 'EXECUTION_EVIDENCE_LAYER_LAUNDERING')
        require(type(e['passed']) is bool and type(e['synthetic']) is bool, 'EXECUTION_EVIDENCE_TYPE_INVALID')
        require(e['candidate_commit'] == manifest['candidate_commit'] and e['candidate_tree'] == manifest['candidate_tree'], 'EXECUTION_EVIDENCE_CANDIDATE_MISMATCH')
        require(explicit_test_node(e['test_node_id']), 'EXPLICIT_TEST_NODE_REQUIRED')
        require(not e['synthetic'] or receipt['synthetic'], 'SYNTHETIC_EVIDENCE_NOT_REAL_ACCEPTANCE')
    failures = list(receipt['semantic_failures'])
    for e in evidence:
        if e['passed'] is False:
            require(e['test_node_id'] in failures, 'FAILED_EXECUTION_HIDDEN_FROM_SEMANTIC_FAILURES')
    known_checks = set(plan['required_validators'] + plan['required_test_profiles'] + ['six_tool_contract'] + plan['required_contract_checks'])
    check_names = [e.get('check') for e in receipt['check_evidence']]
    require(len(set(check_names)) == len(check_names) and set(check_names) <= known_checks, 'CHECK_EVIDENCE_SCOPE_OR_DUPLICATE')
    for e in receipt['check_evidence']:
        require(set(e) == {'check', 'passed', 'evidence_ref', 'candidate_commit', 'candidate_tree'}, 'CHECK_EVIDENCE_INVALID')
        require(type(e['passed']) is bool and e['candidate_commit'] == manifest['candidate_commit'] and e['candidate_tree'] == manifest['candidate_tree'], 'CHECK_EVIDENCE_CANDIDATE_MISMATCH')
        require((ROOT / e['evidence_ref'].split('::')[0]).is_file(), 'CHECK_EVIDENCE_REF_UNRESOLVED')
        if e['passed'] is False:
            require(e['check'] in failures, 'FAILED_CHECK_HIDDEN')
    expected = make_receipt(manifest, plan, evidence, failures, receipt['synthetic'], receipt['semantic_observations'], receipt['check_evidence'])
    require(receipt == expected, 'REGRESSION_RECEIPT_BINDING_MISMATCH')
    # Synthetic receipts exercise contracts and can never certify a real candidate.
    require(not receipt['synthetic'] or receipt['disposition'] != 'REGRESSION_READY_NETWORK_FREE', 'SYNTHETIC_RECEIPT_NOT_PRODUCT_ACCEPTANCE')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    print(json.dumps(select_plan(load(args.manifest)), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
