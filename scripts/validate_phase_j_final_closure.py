#!/usr/bin/env python3
"""Conservative network-free Phase-J exit adjudication over immutable evidence.

Validator PASS means the exit decision is internally valid, not Phase-J closure.
No acceptance subject, source, browser, agent, or runtime is executed here.
"""
from __future__ import annotations
import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import phase_j_j4_regression_authority as j4

DOC = ROOT / 'docs/governance/phase_j'
CONTRACT = DOC / 'PHASE_J_FINAL_CLOSURE_EXIT_CRITERIA_V1.json'
EVIDENCE = DOC / 'PHASE_J_FINAL_CLOSURE_2026-10-11.json'
GAPS = DOC / 'PHASE_J_FINAL_CLOSURE_GAP_ADJUDICATION_V1.json'
REGISTRY = 'docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json'
MATRIX = 'docs/governance/phase_j/PHASE_J_J2_R1_EFFECTIVE_COVERAGE_MATRIX_V1.json'
LEDGER = 'docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_EXECUTION_LEDGER_V1.json'
GOLDEN = 'docs/governance/phase_j/PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json'
REGRESSION = 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_AUTHORITY_V1.json'
START = 'docs/governance/phase_j/PHASE_J_J0_START_AND_J1_ACCEPTANCE_ARCHITECTURE_2026-10-11.json'
B03 = 'docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json'
B04 = 'docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json'
PHASE_I = 'docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json'
COVERED = {'COVERED_EXISTING', 'COVERED_J0_J1'}
UNSUPPORTED = {'UNSUPPORTED_FAIL_CLOSED', 'UNSUPPORTED_FAMILIES_EXPLICIT', 'H2_SUBTYPE_UNSUPPORTED_FAIL_CLOSED', 'UNRESOLVED_FAIL_CLOSED'}


OWNER_SHA = 'e24a723cf464c29a765fa42d69bf16e518bd5a471f35c7f7b790d7485fd61377'

EXPECTED_HASHES = {'docs/governance/phase_j/PHASE_J_J0_START_AND_J1_ACCEPTANCE_ARCHITECTURE_2026-10-11.json': 'ddc259dff051d012a9186e8b127c3ce9940ed6f31099b4da9d64f371e28ead61',
 'docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json': '68d3bc28f03683e015349fc5b0fa9d352660e648cd803846e39a83aea9c7d65e',
 'docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json': '050a94438a6ca907fb02bfafcc0ba17e3019d994a5bb5be63fb79b9c65975e86',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_AUTHORITY_V1.json': '848a28faa4b130260339cf86fba90d3304bd6a83d48107caac6007a36299360a',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_CHANGE_MANIFEST_SCHEMA_V1.json': 'ff0b5d8e0cf22673e234a9241532757f9b37ca5c0bc7d85aeb76c3e4e1e7d7fc',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_RECEIPT_SCHEMA_V1.json': 'c8ac4949aba86a1323ff2305d9835584f664b11b1aa5f911eef1101911dd2ac8',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_AUTHORITY_2026-10-11.json': '148cf87b485d4aaab27ad11532067962ad937daa0c6afa81081921fc6af245f6',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_AUTHORITY_2026-10-11.md': 'ba92947b6af5bc66f340d10ee99a462610e7c31f177cdcd19d682aa14dc91218',
 'docs/governance/phase_j/PHASE_J_J2_R1_COVERAGE_DELTA_V1.json': '321e9008ebca8d8a42e77993ae9329b274dd3e05ad5553554890f97e65618539',
 'docs/governance/phase_j/PHASE_J_J2_R1_EFFECTIVE_COVERAGE_MATRIX_V1.json': '8fe53871a764d66dcca6d3a5531d4801008c58f77e74ace7eede637f15436c3a',
 'docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_EXECUTION_LEDGER_V1.json': '2c30451e2dc6071191d7d5107149770c4d34767cc45c26b5fa819b68249239fa',
 'docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.json': '74e27776bf9768613cbc25f1f6cf3c81687f29be2551f4f9e31141772ac29487',
 'docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.md': 'eb324584ef03103137eec03a5190ba5bb6c2bd7d6b1d66c16693cae3920975f0',
 'docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json': 'b26712d1389b904ff003b22aa135caac43ab8f6fc7b32dad571b70438248c864',
 'docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json': '5d07ab2618e6bfa6c79f796df28cd69df5c105fb8f60396c293675737febcd45',
 'docs/governance/phase_j/PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json': 'b4059b4c1a439e091393daed1887f08c1f6a83e59dfc4095e82e22130e6422fa',
 'docs/governance/phase_j/PHASE_J_J3_SEMANTIC_TRACEABILITY_V1.json': '8dfd4f256334959142bf81d163546ed0fe485e3d92393fd570fb97ac22d0e247',
 'docs/governance/phase_j/PHASE_J_J3_R1_GOLDEN_SEMANTIC_FIDELITY_AND_LOSSLESS_PROJECTION_HARDENING_2026-10-11.json': '00ccc7bba67f656fbc3046465a4923c2abf7cc9deeea03411a06cb8df8a402f2',
 'docs/governance/phase_j/PHASE_J_J3_R1_GOLDEN_SEMANTIC_FIDELITY_AND_LOSSLESS_PROJECTION_HARDENING_2026-10-11.md': '8fda262e5d30f6734cea4679af0ffca7c2284134b2e8d1e2371dddea8ed7e13a',
 'ROADMAP.md': '8b258d327b16e96a4904cf55f12f76129faff703569fb7f6169767585eb4e789',
 'docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json': 'f0379356dc5a5e51f6889266de8571b70fb286afbab05aa1408e13fde897d98b'}

EXPECTED_REVIEWS = {'entry': {'review_id': '5479545125',
           'reviewed_commit': '2455fd0875bc09d6bc5926a6267351aadb38beb1',
           'GitHub_review_state': 'COMMENTED',
           'review_body_sha256': 'a2a080f7aec8f195a725caeeb6055b8bf006fb806ae4749d862c869fd150448a',
           'authority_kind': 'GitHub_owner_authorization_review'},
 'J1': {'review_id': '5481271339',
        'reviewed_commit': '230606eb0b51b2004dbeac72f8c2908abe0372d3',
        'GitHub_review_state': 'COMMENTED',
        'review_body_sha256': '1671a6efd3970750c2c74f76ae1dc22719da6cb26c5effd8675112eb79dcfcb6',
        'authority_kind': 'GitHub_independent_review'},
 'J2': {'review_id': '5481723267',
        'reviewed_commit': '7454c4613e50759265ebf4c96ec6571117b2c1a4',
        'GitHub_review_state': 'COMMENTED',
        'review_body_sha256': '08ce121ed794c439b6c5cdbbc6f23d4964e231d1ad51ea21182e8cd57407665b',
        'authority_kind': 'GitHub_independent_review'},
 'J3': {'review_id': '5482393445',
        'reviewed_commit': '90dc62ea9e6ed3255c065a93910e661f525d483f',
        'GitHub_review_state': 'COMMENTED',
        'review_body_sha256': '7b5f5cc0a4629ac6016bf79a101d84345f83ae0ce7d27705a58c83ad68c94ead',
        'authority_kind': 'GitHub_independent_review'},
 'J4': {'review_id': '5482700449',
        'reviewed_commit': '2d217936464659073c1aa75ad2383b5ecebc47da',
        'GitHub_review_state': 'COMMENTED',
        'review_body_sha256': '628cc1ceeec3eb93b956c691c2e68f3ba50b2ef64d28bd71ca4c718bae624e16',
        'authority_kind': 'GitHub_independent_review'},
 'J_B04': {'review_id': '5479527453',
           'reviewed_commit': '2455fd0875bc09d6bc5926a6267351aadb38beb1',
           'GitHub_review_state': 'COMMENTED',
           'review_body_sha256': '8985a86d1525a5c6fb9e0d4e216c3da2c7376ca148f2090930a029287ffb1743',
           'authority_kind': 'GitHub_independent_review'},
 'closure_authorization': {'review_id': '5482764686',
                           'reviewed_commit': '2d217936464659073c1aa75ad2383b5ecebc47da',
                           'GitHub_review_state': 'COMMENTED',
                           'review_body_sha256': '4922343252252a4bfaaf12ac74bac4ad27c07f6d6c8a5a61493ac5964f104fe5',
                           'authority_kind': 'GitHub_owner_authorization_review'}}

EXPECTED_B03_ROLE = {'ref': 'docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json',
 'authority_kind': 'governance_record',
 'review_id': None}

EXPECTED_LAYER_POLICY = {'roadmap_requires_all_nine_layers': True,
 'every_scenario_every_layer_required': False,
 'required_phase_level_minimum': 'at_least_one_accepted_semantically_relevant_witness_per_layer_or_explicit_reviewed_Roadmap_compatible_deferral',
 'real_agent_accepted_witnesses': [],
 'real_agent_accepted_deferrals': [],
 'Phase_K_substitutes_for_Phase_J_real_agent': False,
 'authorization_not_granted_is_deferral': False,
 'bounded_live_witness': 'docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json'}

CONTRACT_CONTENT_HASH = '99cd198fa56abd836374a89a885ba6b976cc04277b8368e6ce51887bfa8412a8'

EXPECTED_CONTENT_HASHES = {'docs/governance/phase_j/PHASE_J_J0_START_AND_J1_ACCEPTANCE_ARCHITECTURE_2026-10-11.json': 'ec6408ee4898406272177d962378144f0be5588f72e16cb2b2c094641fa3b5b2',
 'docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json': '5d5b33a6a9bff1c4609357d83434f015c5e29c10fccbf806c3bf57afcb33ace4',
 'docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json': 'cf1e53148b82c6ac619779f2884a2231291ced739426ace86752dccae4c9e578',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_AUTHORITY_V1.json': '6cfd3e31d9013f0661a5f3436d036fdbaa57c8c13ba445e7034f4f4b3ca5ae61',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_CHANGE_MANIFEST_SCHEMA_V1.json': '7195a9586962a1c58d6a2a17a92722e90d38c623ffa10546a9b25b98869f8793',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_RECEIPT_SCHEMA_V1.json': '0fe5e38d038e464401b2c621a6bec2929a5342b396e6171ef13c3c6d19900c8a',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_AUTHORITY_2026-10-11.json': 'a62a5b7e28756603983d971aba6201e3b1e6b5b95d98593586ce6904cabed2f5',
 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_AUTHORITY_2026-10-11.md': '4c42c9ee71deaa07bebc63128fa79954aea225ec2efc5ae4317c500dd58a4268',
 'docs/governance/phase_j/PHASE_J_J2_R1_COVERAGE_DELTA_V1.json': 'd3e0a2439bb58b095d99cd090eb2b58514592bca24a5393c8ad38c54313a8374',
 'docs/governance/phase_j/PHASE_J_J2_R1_EFFECTIVE_COVERAGE_MATRIX_V1.json': '6e8b44648aa44dc74955292eeb941fdd04025933a78f574c9f71b0e0f156c22c',
 'docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_EXECUTION_LEDGER_V1.json': 'a9447488544286f9243d41d254de393f1866ac03951ee41ffa9a9b62a1c841b0',
 'docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.json': 'ed1eab69eb8a27a01b8a7c48e9d27c7696f8583bd339ca44e6f494d292be4533',
 'docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.md': '2ffe219c804161a8c705e79a97e87edd3fd2e16cc204f76f0507ae4fac82b0a1',
 'docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json': '467483b3cb541cf7120ce5cda3b01ed9d4f542ade6b0d13e3dc1e8ec239c947d',
 'docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json': '24b3e33cab581cdd168345de9a94971f52e6de8164f3a2dbb9c89c0c917324c6',
 'docs/governance/phase_j/PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json': '780094837f7d629628343cf3a208b0d9f4eafd128f259641142bf6c14c221c59',
 'docs/governance/phase_j/PHASE_J_J3_SEMANTIC_TRACEABILITY_V1.json': '18956be0d84414589f53f017833300aac9cce716c0d664428202901b713a5cff',
 'docs/governance/phase_j/PHASE_J_J3_R1_GOLDEN_SEMANTIC_FIDELITY_AND_LOSSLESS_PROJECTION_HARDENING_2026-10-11.json': '1d2bb111d8b9d5090826dcd75695721d82efca405904e53fe1e6e639b59ccdf3',
 'docs/governance/phase_j/PHASE_J_J3_R1_GOLDEN_SEMANTIC_FIDELITY_AND_LOSSLESS_PROJECTION_HARDENING_2026-10-11.md': '3cbc3d7551eb927ad1b10efecb87bcd15857de96fb20ebe1cd22b48249b414e0',
 'ROADMAP.md': 'd80ea37b21921c49c1439cea6eac0fea307ecca0205079e7bdccc973166030f3',
 'docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json': 'fe216e589d83f91d08e153f6b6a82da13d35a07295f94dae2423f8f3a5d0e398'}

EXPECTED_GOLDEN_CONTRACTS = {'request': 'unified_market_evidence_request.v3',
 'result': 'unified_market_evidence_result.v3',
 'audit': 'unified_market_evidence_audit_package.v3',
 'mcp_tool_count': 6,
 'mcp_tools': ['market_describe_capabilities',
               'market_validate_request',
               'market_preview_request',
               'market_read_result',
               'market_export_ai_handoff',
               'market_fetch_evidence']}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def validate_contract(contract=None):
    c = j4.load(CONTRACT) if contract is None else contract
    require(c.get('J_B03_authority') == EXPECTED_B03_ROLE, 'J_B03_AUTHORITY_ROLE_INVALID')
    require(c.get('accepted_reviews') == EXPECTED_REVIEWS, 'INDEPENDENT_REVIEW_ROLE_DRIFT')
    require(c.get('immutable_artifact_hashes') == EXPECTED_HASHES, 'ACCEPTED_ARTIFACT_HASH_DRIFT')
    require(c.get('MCP_tools') == j4.TOOLS, 'MCP_TOOL_COUNT_OR_NAME_DRIFT')
    require(c.get('Phase_K') == 'NOT_STARTED', 'PHASE_K_UNAUTHORIZED_START')
    require(c.get('layer_exit_policy') == EXPECTED_LAYER_POLICY, 'INVENTED_LAYER_DEFERRAL_OR_WITNESS')
    require(j4.digest(c) == CONTRACT_CONTENT_HASH, 'EXIT_CRITERIA_CONTRACT_DRIFT')
    require(hashlib.sha256(c['owner_authorization_statement'].encode()).hexdigest() == c['owner_authorization_sha256'] == OWNER_SHA, 'OWNER_AUTHORIZATION_DRIFT')
    return c


def validate_authorities(contract, documents=None):
    docs = {} if documents is None else copy.deepcopy(documents)
    if documents is None:
        for path, sha in contract['immutable_artifact_hashes'].items():
            require(j4.file_hash(ROOT / path) == sha, 'ACCEPTED_AUTHORITY_BYTE_DRIFT: ' + path)
            if path.endswith('.json'):
                docs[path] = j4.load(ROOT / path)
            else:
                docs[path] = (ROOT / path).read_text(encoding='utf-8')
    require(set(docs) == set(EXPECTED_HASHES), 'ACCEPTED_AUTHORITY_MISSING')
    require(docs[B03].get('decision') == 'J_B03_CLOSED_BOUNDED_CONVERSATIONAL_CORRECTNESS_SATISFIED', 'J_B03_NOT_CLOSED')
    require(docs[B04].get('terminal_disposition') == 'J_B04_A6_R2_INTEGRATED_LIVE_REACCEPTANCE_PASS', 'J_B04_NOT_CLOSED')
    require(docs[PHASE_I].get('status') == 'PHASE_I_COMPLETED_INDEPENDENT_EXIT_REVIEW_PASS', 'PHASE_I_NOT_CLOSED')
    require('# [ ] Phase J — Integrated Research Acceptance' in docs['ROADMAP.md'], 'ROADMAP_PHASE_J_CHECKBOX_CHANGED')
    for path, data in docs.items():
        require(j4.digest(data) == EXPECTED_CONTENT_HASHES[path], 'ACCEPTED_AUTHORITY_CONTENT_DRIFT: ' + path)
    rows = docs[REGISTRY]['scenarios']
    require([r['scenario_id'] for r in rows] == contract['scenario_ids'] and len(rows) == 27, 'SCENARIO_ID_DRIFT')
    require(docs[MATRIX]['coverage_dimensions'] == contract['layers'] == j4.LAYERS, 'ACCEPTANCE_LAYER_DRIFT')
    require(docs[GOLDEN]['dimensions'] == contract['semantic_dimensions'] == j4.DIMENSIONS, 'GOLDEN_DIMENSION_DRIFT')
    require(docs[REGISTRY]['entry_disposition'] == {'J-B01': 'NON_BLOCKING', 'J-B02': 'NON_BLOCKING', 'J-B03': 'CLOSED', 'J-B04': 'CLOSED / CLEARED'}, 'ENTRY_BLOCKER_STATUS_DRIFT')
    i = docs[PHASE_I]
    require([i['accepted_capabilities'][k]['status'] for k in ['I1', 'I2', 'I3']] == ['ACTIVE / OWNER ACCEPTED', 'ACTIVE / OWNER ACCEPTED', 'ACTIVE / OWNER ACCEPTED / MERGED'], 'PHASE_I_CAPABILITY_AUTHORITY_DRIFT')
    require(i['unified_public_surface']['MCP_tool_count'] == 6, 'PHASE_I_MCP_DRIFT')
    require(docs[GOLDEN]['contracts'] == EXPECTED_GOLDEN_CONTRACTS, 'PUBLIC_V3_CONTRACT_DRIFT')
    return docs


def artifact_ref(path, contract, role=None, pointer=None):
    ref = {'ref': path + (('#' + pointer) if pointer else ''), 'sha256': contract['immutable_artifact_hashes'][path], 'authority_kind': 'governance_record' if path != 'ROADMAP.md' else 'Roadmap_V3.2'}
    if role:
        ref['review'] = contract['accepted_reviews'][role]
    return ref


def layer_witnesses(contract, docs):
    matrix = docs[MATRIX]
    result = []
    for layer in j4.LAYERS:
        cells = [r for r in matrix['scenarios'] if r['layers'][layer]['status'] in COVERED]
        witnesses = [{'scenario_id': r['scenario_id'], 'evidence_refs': r['layers'][layer]['evidence_refs'], 'accepted_matrix_status': r['layers'][layer]['status'], 'authority': artifact_ref(MATRIX, contract, 'J2', r['scenario_id'] + '/layers/' + layer)} for r in cells]
        if layer == 'bounded_live':
            a6 = docs[B04]
            s = a6['stage_2']
            require(s['transport']['actual_market_get_dispatches'] == 3 and s['transport']['pair_validation'] == 'PASS', 'BOUNDED_LIVE_TRANSPORT_WITNESS_INVALID')
            require(s['h3']['result'] == 'succeeded' and s['h4']['ordinary_return_interpretation'] == 'blocked' and s['h4']['state'] == 'coverage_incomplete', 'BOUNDED_LIVE_SEMANTIC_WITNESS_INVALID')
            witnesses.append({'scenario_ids': ['J1-14', 'J1-16', 'J1-17'], 'authority': artifact_ref(B04, contract, 'J_B04', 'stage_2'), 'scope': 'one bounded integrated TWSE:2330 H3/H2/H4 production execution, Result/Audit V3 and stored-result reuse; H2 current-slice no-evidence; no complete corporate-action/history claim', 'GET_dispatches_historical': 3, 'new_GET_dispatches': 0})
        deferrals = []  # No accepted closure-compatible layer waiver in the authority chain.
        accepted = bool(witnesses)
        result.append({'layer': layer, 'roadmap_required': True, 'accepted_witnesses': witnesses, 'scenario_ids': sorted({s for w in witnesses for s in ([w['scenario_id']] if 'scenario_id' in w else w['scenario_ids'])}), 'authority_refs': [artifact_ref('ROADMAP.md', contract, pointer='J.2'), artifact_ref(MATRIX, contract, 'J2')], 'coverage_status': 'ACCEPTED_REPRESENTATIVE_WITNESS' if accepted else 'WITNESS_MISSING', 'deferral_authority_if_any': deferrals, 'closure_disposition': 'PASS' if accepted or deferrals else 'FAIL', 'reason_code': 'ACCEPTED_LAYER_WITNESS' if accepted else 'ROADMAP_LAYER_WITNESS_MISSING'})
    return result


def supported_scenarios_without_witness(docs):
    rows = {r['scenario_id']: r for r in docs[REGISTRY]['scenarios']}
    return [r['scenario_id'] for r in docs[MATRIX]['scenarios'] if rows[r['scenario_id']]['product_relevance_class'] == 'MUST_HAVE_FOR_CONVERSATIONAL_J' and rows[r['scenario_id']]['current_readiness_status'].startswith('SUPPORTED') and not any(cell['status'] in COVERED for layer, cell in r['layers'].items() if layer != 'fresh_install')]


def gap_adjudication(contract, docs, witnesses):
    registry = {r['scenario_id']: r for r in docs[REGISTRY]['scenarios']}
    golden = {r['scenario_id']: r for r in docs[GOLDEN]['scenarios']}
    preexecution = {r['scenario_id'] for r in docs[LEDGER]['scenarios'] if 'integration' in r['not_applicable_layers']}
    # J4 already pins exact accepted sources. Pure selector execution is local governance,
    # not any execution of candidate/source/browser/agent acceptance.
    manifest = j4.load(ROOT / 'tests/fixtures/phase_j/j4/new_release.json')
    plan = j4.select_plan(manifest)
    future_cells = {(c['scenario_id'], c['layer']) for c in plan['planned_or_missing_layers']}
    satisfied = {r['layer']: r['closure_disposition'] == 'PASS' for r in witnesses}
    missing_scenarios = supported_scenarios_without_witness(docs)
    rows = []
    for scenario in docs[MATRIX]['scenarios']:
        sid = scenario['scenario_id']
        for layer, cell in scenario['layers'].items():
            status = cell['status']
            if status in COVERED | {'NOT_APPLICABLE'}:
                continue
            refs = [artifact_ref(REGISTRY, contract, 'J1', sid), artifact_ref(GOLDEN, contract, 'J3', sid), artifact_ref('ROADMAP.md', contract, pointer='J.2')]
            scope = 'EXACT_SCENARIO_SEMANTICS'
            if not satisfied[layer]:
                cls, reason = 'CURRENT_PHASE_J_BLOCKER', 'ROADMAP_LAYER_WITNESS_MISSING'
                refs += [artifact_ref(REGRESSION, contract, 'J4', 'authorization_policy')]
            elif layer == 'integration' and sid in preexecution:
                cls, reason = 'NOT_APPLICABLE', 'PREEXECUTION_REFUSAL_NO_INTEGRATION_RESULT'
                refs += [artifact_ref(LEDGER, contract, 'J2', sid + '/not_applicable_layers')]
            elif layer == 'fresh_install':
                # Legal empty installation is a different authority context, not an
                # unsupported label applied to a supported initialized product path.
                fresh = docs[LEDGER]['fresh_install']
                require(fresh['scenario_id'] == 'J1-25' and fresh['classification'] == 'PREEXECUTION_FAIL_CLOSED' and fresh['initial_execution_count'] == 0, 'FRESH_INSTALL_FAIL_CLOSED_WITNESS_MISSING')
                require('SECURITY_MASTER_NOT_INITIALIZED' in fresh['dom_observations']['#validation-summary'], 'FRESH_INSTALL_EMPTY_AUTHORITY_INVALID')
                cls, reason = 'ACCEPTED_FAIL_CLOSED_OR_UNSUPPORTED', 'GOLDEN_OUTCOME_IS_FAIL_CLOSED'
                scope = 'EMPTY_INSTALLATION_IDENTITY_AUTHORITY_BOUNDARY_NOT_POSITIVE_SCENARIO_EXECUTION'
                refs += [artifact_ref(LEDGER, contract, 'J2', 'fresh_install'), artifact_ref(GOLDEN, contract, 'J3', 'J1-25/identity')]
            elif sid in missing_scenarios:
                cls, reason = 'CURRENT_PHASE_J_BLOCKER', 'SUPPORTED_SCENARIO_WITNESS_MISSING'
                scope = 'SUPPORTED_MUST_HAVE_SCENARIO_LACKS_ANY_ACCEPTED_EXECUTION_WITNESS; ONE_WITNESS_REQUIRED_NOT_ALL_LAYERS'
                refs += [artifact_ref(MATRIX, contract, 'J2', sid + '/layers')]
            elif layer == 'bounded_live':
                if sid in preexecution or registry[sid]['current_readiness_status'] in UNSUPPORTED:
                    cls, reason = 'ACCEPTED_FAIL_CLOSED_OR_UNSUPPORTED', 'GOLDEN_OUTCOME_IS_FAIL_CLOSED'
                    refs += [artifact_ref(LEDGER, contract, 'J2'), artifact_ref(GOLDEN, contract, 'J3', sid + '/accepted_fail_closed_outcomes')]
                else:
                    cls, reason = 'AUTHORIZATION_GATED_FUTURE_LAYER', 'SEPARATE_LIVE_AUTHORIZATION_REQUIRED'
                    refs += [artifact_ref(B04, contract, 'J_B04', 'stage_2'), artifact_ref(REGRESSION, contract, 'J4', 'class_rules/NEW_SOURCE/live_gate')]
            elif registry[sid]['current_readiness_status'] in UNSUPPORTED:
                require(golden[sid]['readiness_status'] == registry[sid]['current_readiness_status'], 'UNSUPPORTED_SEMANTIC_MISMATCH')
                cls, reason = 'ACCEPTED_FAIL_CLOSED_OR_UNSUPPORTED', 'SCENARIO_UNSUPPORTED_BY_ACCEPTED_CONTRACT'
            elif (sid, layer) in future_cells:
                # Each exact cell must be selected by J4, AND the phase-level layer
                # has accepted witnesses, AND J1/J3 retain this scenario's semantics.
                cls, reason = 'FUTURE_REGRESSION_COVERAGE_GAP', 'FUTURE_CHANGED_CANDIDATE_REGRESSION_SCOPE'
                refs += [artifact_ref(REGRESSION, contract, 'J4', 'class_rules/NEW_RELEASE'), artifact_ref(MATRIX, contract, 'J2', 'layer_baselines')]
            else:
                cls, reason = 'CURRENT_PHASE_J_BLOCKER', 'ROADMAP_LAYER_WITNESS_MISSING'
            rows.append({'cell_id': sid + '/' + layer, 'scenario_id': sid, 'layer': layer, 'accepted_matrix_status': status, 'accepted_evidence_refs': copy.deepcopy(cell['evidence_refs']), 'accepted_readiness_status': registry[sid]['current_readiness_status'], 'accepted_fail_closed_outcomes': golden[sid]['accepted_fail_closed_outcomes'], 'closure_classification': cls, 'closure_reason_code': reason, 'classification_scope': scope, 'authority_refs': refs, 'is_phase_j_blocker': cls == 'CURRENT_PHASE_J_BLOCKER'})
    return {'schema_version': 'phase_j_final_closure_gap_adjudication.v1', 'accepted_matrix_sha256': contract['immutable_artifact_hashes'][MATRIX], 'accepted_matrix_unchanged': True, 'classification_vocabulary': contract['gap_classifications'], 'cells': rows}


def derive_decision(contract=None, documents=None):
    c = validate_contract(contract)
    docs = validate_authorities(c, documents)
    witnesses = layer_witnesses(c, docs)
    gaps = gap_adjudication(c, docs, witnesses)
    counts = Counter(r['closure_classification'] for r in gaps['cells'])
    matrix_counts = Counter(cell['status'] for row in docs[MATRIX]['scenarios'] for cell in row['layers'].values())
    results = []
    for e in c['exit_criteria']:
        id = e['criterion_id']
        passed = True
        refs = [artifact_ref('ROADMAP.md', c, pointer='J.0-J.4')]
        paths = {'E1': START, 'E2': START, 'E3': REGISTRY, 'E4': MATRIX, 'E5': LEDGER, 'E6': GOLDEN, 'E7': REGRESSION, 'E8': REGISTRY, 'E9': B03, 'E10': B04, 'E11': PHASE_I, 'E12': GOLDEN, 'E13': REGRESSION, 'E14': GOLDEN, 'E15': MATRIX, 'E16': MATRIX, 'E17': MATRIX, 'E18': REGRESSION}
        refs.append(artifact_ref(paths[id], c, e['review_role']))
        if id == 'E2':
            passed = docs[START]['phase_j_state']['j0'] == 'COMPLETE'
        elif id == 'E16':
            passed = counts['CURRENT_PHASE_J_BLOCKER'] == 0
        elif id == 'E17':
            passed = all(w['closure_disposition'] == 'PASS' for w in witnesses)
        elif id == 'E18':
            passed = docs[REGRESSION]['phase_state']['Phase_K'] == 'NOT_STARTED'
        results.append({'criterion_id': id, 'requirement': e['requirement'], 'status': 'PASS' if passed else 'FAIL', 'authority_refs': refs})
    blockers = [r['cell_id'] for r in gaps['cells'] if r['is_phase_j_blocker']]
    disposition = 'PHASE_J_FINAL_CLOSURE_PASS_CANDIDATE' if all(e['status'] == 'PASS' for e in results) and not blockers else 'PHASE_J_FINAL_CLOSURE_HARD_BLOCK'
    return {'schema_version': 'phase_j_final_closure_decision.v1', 'disposition': disposition, 'exit_criteria_results': results, 'layer_exit_witnesses': witnesses, 'gap_adjudication': gaps,
        'summary': {'total_matrix_cells': sum(matrix_counts.values()), 'covered_cells': sum(matrix_counts[s] for s in COVERED), 'not_applicable_matrix_cells': matrix_counts['NOT_APPLICABLE'], 'remaining_gap_count': len(gaps['cells']), 'classification_counts': {k: counts[k] for k in c['gap_classifications']}, 'layer_witness_count': sum(bool(w['accepted_witnesses']) for w in witnesses), 'layer_deferral_count': sum(bool(w['deferral_authority_if_any']) for w in witnesses), 'unsatisfied_layer_count': sum(w['closure_disposition'] == 'FAIL' for w in witnesses)},
        'blocker_cells': blockers,
        'blocker_obligations': [{'code': 'ROADMAP_J2_' + w['layer'].upper() + '_LAYER_UNSATISFIED', 'layer': w['layer'], 'minimum_missing_witnesses': 1, 'affected_cell_ids': [r['cell_id'] for r in gaps['cells'] if r['layer'] == w['layer'] and r['is_phase_j_blocker']], 'not_every_scenario_every_layer_required': True, 'authority_refs': w['authority_refs']} for w in witnesses if w['closure_disposition'] == 'FAIL'] + [{'code': 'SUPPORTED_GOLDEN_SCENARIO_WITNESS_MISSING', 'scenario_id': sid, 'minimum_missing_witnesses': 1, 'affected_cell_ids': [r['cell_id'] for r in gaps['cells'] if r['scenario_id'] == sid and r['closure_reason_code'] == 'SUPPORTED_SCENARIO_WITNESS_MISSING'], 'authority_refs': [artifact_ref(REGISTRY, c, 'J1', sid), artifact_ref(MATRIX, c, 'J2', sid), artifact_ref('ROADMAP.md', c, pointer='J.1')]} for sid in supported_scenarios_without_witness(docs)],
        'phase_state': {'Phase_J': 'STARTED_CLOSURE_HARD_BLOCK' if blockers else 'CLOSURE_PASS_CANDIDATE_PENDING_EXACT_HEAD_REVIEW', 'J0': 'COMPLETE', 'J1': 'INDEPENDENTLY_ACCEPTED', 'J2': 'CLOSED_INDEPENDENTLY_ACCEPTED', 'J3': 'INDEPENDENTLY_ACCEPTED', 'J4': 'INDEPENDENTLY_ACCEPTED', 'Phase_K': 'NOT_STARTED'},
        'Roadmap_Phase_J_checkbox': 'UNCHECKED',
        'authorization_state': {'bounded_live': 'NOT_GRANTED', 'real_agent': 'NOT_GRANTED'},
        'MCP_tools': j4.TOOLS,
        'phase_level_evidence_map': [{'roadmap_requirement': key, 'authority_refs': [artifact_ref(path, c, role)], 'conclusion': conclusion} for key,path,role,conclusion in [('J.1',REGISTRY,'J1','PASS: 27 governed scenarios'),('J.2',MATRIX,'J2','FAIL: real-agent witness and accepted deferral absent'),('J.3',GOLDEN,'J3','PASS: 11 dimensions and lossless semantic authority'),('J.4',REGRESSION,'J4','PASS: five regression change classes and gated receipts'),('Phase_J_expected_outcome',GOLDEN,'J3','NOT_YET_ESTABLISHED_FOR_CLOSURE: real-agent layer and supported MUST_HAVE scenario witnesses unsatisfied')]]}


def require_pass_eligibility(criteria, gaps, witnesses):
    """Independent gate: no blocker or missing required phase-level layer."""
    require(not any(r['is_phase_j_blocker'] for r in gaps), 'PASS_FORBIDDEN_CURRENT_BLOCKER')
    require(all(e['status'] == 'PASS' for e in criteria), 'PASS_FORBIDDEN_EXIT_CRITERION_FAIL')
    require([w['layer'] for w in witnesses] == j4.LAYERS, 'PASS_FORBIDDEN_LAYER_UNIVERSE_MISSING')
    require(all(w['accepted_witnesses'] or w['deferral_authority_if_any'] for w in witnesses), 'PASS_FORBIDDEN_LAYER_WITNESS_MISSING')


def validate_decision(decision):
    expected = derive_decision()
    gaps = decision['gap_adjudication']['cells']
    ids = [r['cell_id'] for r in gaps]
    require(len(set(ids)) == len(ids), 'DUPLICATE_GAP_ADJUDICATION')
    require(set(ids) == {r['cell_id'] for r in expected['gap_adjudication']['cells']}, 'GAP_UNIVERSE_INCOMPLETE')
    for r in gaps:
        require(r['closure_classification'] in j4.load(CONTRACT)['gap_classifications'], 'UNKNOWN_CLOSURE_CLASSIFICATION')
        require(r['is_phase_j_blocker'] == (r['closure_classification'] == 'CURRENT_PHASE_J_BLOCKER'), 'BLOCKER_FLAG_INCONSISTENT')
        original = next(e for e in expected['gap_adjudication']['cells'] if e['cell_id'] == r['cell_id'])
        require(r['accepted_matrix_status'] == original['accepted_matrix_status'], 'ACCEPTED_MATRIX_STATUS_LAUNDERED')
        require(r == original, 'GAP_CLASSIFICATION_OR_AUTHORITY_UNPROVEN: ' + r['cell_id'])
    if decision['disposition'] == 'PHASE_J_FINAL_CLOSURE_PASS_CANDIDATE':
        require_pass_eligibility(decision['exit_criteria_results'], gaps, decision['layer_exit_witnesses'])
    require(decision['layer_exit_witnesses'] == expected['layer_exit_witnesses'], 'LAYER_WITNESS_OR_DEFERRAL_UNPROVEN')
    require(decision == expected, 'CLOSURE_DECISION_NOT_MACHINE_DERIVED')
    return True


def validate(check_git=True, terminal=False):
    c = validate_contract()
    if check_git:
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
        require(git('rev-parse', c['starting_authority']['head'] + '^{tree}') == c['starting_authority']['tree'], 'PHASE_J_FINAL_CLOSURE_BASELINE_DRIFT')
        require(git('rev-parse','origin/main') == c['starting_authority']['main'] and git('branch','--show-current') == c['starting_authority']['branch'], 'PHASE_J_FINAL_CLOSURE_BASELINE_DRIFT')
        subprocess.run(['git','merge-base','--is-ancestor',c['starting_authority']['head'],'HEAD'],cwd=ROOT,check=True)
        paths=git('diff','--name-only',c['starting_authority']['head'],'HEAD').splitlines()
        allowed=('scripts/validate_phase_j_final_closure.py','tests/acceptance/test_phase_j_final_closure.py','docs/governance/phase_j/PHASE_J_FINAL_CLOSURE_')
        require(all(path.startswith(allowed) for path in paths), 'UNAUTHORIZED_CLOSURE_IMPLEMENTATION_DIFF')
    decision = derive_decision(c)
    validate_decision(decision)
    if terminal:
        e = j4.load(EVIDENCE)
        require(e['decision'] == decision and j4.load(GAPS) == decision['gap_adjudication'], 'TERMINAL_EXIT_EVIDENCE_DIVERGENCE')
        require(e['owner_authorization_sha256'] == OWNER_SHA, 'TERMINAL_AUTHORIZATION_DRIFT')
        require(e['default_ci']['candidate_only_failure_nodes'] == [], 'CANDIDATE_ONLY_CI_FAILURE')
        require(e['Security_Master']['host_selector_before'] == e['Security_Master']['host_selector_after'], 'HOST_SELECTOR_MUTATION')
    return {'validator_status': 'PASS', 'derived_closure_disposition': decision['disposition'],
        'summary': decision['summary'], 'failed_exit_criteria': [e['criterion_id'] for e in decision['exit_criteria_results'] if e['status']=='FAIL'],
        'blocker_obligations': decision['blocker_obligations']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal',action='store_true')
    parser.add_argument('--decision-json',action='store_true')
    args=parser.parse_args()
    print(json.dumps(derive_decision() if args.decision_json else validate(terminal=args.terminal),ensure_ascii=False,indent=2))
