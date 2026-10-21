#!/usr/bin/env python3
"""TEST / ACCEPTANCE AUTHORITY ONLY: bounded, offline integrated proof.

No runtime registry, discovery, activation or provider access. Temporary test
installations are the only execution writes. All actual product boundaries run.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.helpers.l5_a6_integrated import FAMILIES, run_trace

A1 = 'docs/governance/phase_l/PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT.v1.json'
TOOLS = ['market_describe_capabilities', 'market_validate_request', 'market_preview_request',
         'market_read_result', 'market_export_ai_handoff', 'market_fetch_evidence']
EXECUTOR = 'phase_g_official_research_executor'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def parts(t):
    calls, artifacts = t['calls'], t['artifacts']
    result = calls['market_read_result']['canonical_result']
    audit = artifacts['audit/unified_market_evidence_audit_package.v3.json']
    return calls, artifacts, result, audit


def publication():
    from scripts.validate_l5_extension_publication_conformance import load_snapshot, validate_snapshot
    s = load_snapshot()
    return {'errors': validate_snapshot(s)['errors'], 'catalog': s['catalog'], 'routing': s['routing'],
            'portable': s['portable'], 'guides': list(s['guides']),
            'family_registry': None, 'family_owned_policies': []}


def validate_trace(t):
    from jsonschema import Draft7Validator
    from scripts.m8r_05c.markdown_renderer import render_result_markdown
    errors = []
    def check(ok, code, detail=''):
        if not ok:
            errors.append({'code': code, 'detail': detail})
    calls, artifacts, result, audit = parts(t)
    target = t['request']['targets'][0]['input']
    check(t['tool_names'] == TOOLS and set(calls) == set(TOOLS), 'A6_TOOL_SURFACE')
    check(not list(Draft7Validator(read('schemas/unified_market_evidence_request.v3.schema.json')).iter_errors(t['request'])), 'A6_REQUEST_SCHEMA')
    check([n['type'] for n in t['request']['data_needs']] == list(FAMILIES), 'A6_REQUEST_CAPABILITIES')
    check(t['request'] == artifacts['control/request.json'], 'A6_REQUEST_AFTER_PREVIEW')
    check(result['request_id'] == t['request']['request_id'] == audit['request_identity']['request_id'], 'A6_REQUEST_ID')
    check(calls['market_validate_request']['validation_status'] == 'valid', 'A6_VALIDATION')
    preview = calls['market_preview_request']
    plan = artifacts['control/plan.json']
    check(digest(t['request']) == plan['input_bindings']['original_request_hash'] == audit['request_identity']['request_hash'], 'A6_REQUEST_HASH_BINDING')
    check(audit['plan_identity']['plan_id'] == plan['plan_id'] and audit['plan_identity']['plan_hash'] == plan['plan_hash'], 'A6_PLAN_AUDIT_BINDING')
    authorization = artifacts['control/authorization.json']
    check(set(authorization['approved_operation_ids']) == {op['operation_id'] for op in plan['operations']} and authorization['single_use'] is True, 'A6_AUTHORIZATION_SCOPE')
    check(authorization['authorization_id'] == calls['market_fetch_evidence']['control_package_id'], 'A6_AUTHORIZATION_ID')
    for name, expected_hash in artifacts['control/manifest.json']['artifact_hashes'].items():
        check(t['retained_bytes']['control/'+name+'.json']['sha256'] == expected_hash, 'A6_CONTROL_ARTIFACT_HASH', name)
    check(preview['orchestration_plan']['operations'] == plan['operations'], 'A6_PREVIEW_OPERATIONS')
    check(preview['execution_performed'] is False and preview['authorization_created'] is False, 'A6_PREVIEW_NOT_AUTHORIZATION')
    check(result['targets'][0]['canonical_identity']['canonical_target_id'] == target, 'A6_RESULT_TARGET')
    check(digest({k: v for k, v in result.items() if k != 'result_hash'}) == result['result_hash'], 'A6_RESULT_HASH')
    check(digest({k: v for k, v in audit.items() if k != 'audit_package_hash'}) == audit['audit_package_hash'], 'A6_AUDIT_HASH')
    check(audit['result_hash'] == result['result_hash'] and audit['result_id'] == result['result_id'], 'A6_AUDIT_RESULT')
    render_input = deepcopy(result)
    # Renderer iterates this builder-owned map. Persisted canonical JSON sorts
    # map keys; restore only the documented builder display order for re-render.
    for target_row in render_input['targets']:
        for e in target_row['evidence'].values():
            currentness = e['currentness']
            e['currentness'] = {k:currentness[k] for k in ('status','observed_at') if k in currentness}
    fields = ('citation_id','canonical_target_id','capability_id','executor_id','artifact_relative_path','artifact_hash')
    expected_handoff_citations = sorted([{k:c[k] for k in fields} for c in audit['citation_to_operation_map']],
                                       key=lambda row:tuple(str(row[k]) for k in fields))
    for name in ('market_fetch_evidence', 'market_export_ai_handoff'):
        payload = calls[name]
        check(payload['canonical_result'] == result and payload['result_id'] == result['result_id'] and payload['result_hash'] == result['result_hash'], 'A6_HANDOFF_RESULT', name)
        check(payload['ai_ready_markdown'] == calls['market_read_result']['ai_ready_markdown'] == render_result_markdown(render_input), 'A6_HANDOFF_CONTENT', name)
        check(payload['citation_references'] == expected_handoff_citations, 'A6_HANDOFF_CITATIONS', name)
    check(calls['market_fetch_evidence']['market_network_attempted'] is False and calls['market_fetch_evidence']['market_network_executed'] is False, 'A6_FIXTURE_NETWORK')
    check(not t['socket_attempts'] and all(x['external_dispatch'] is False for x in t['transport_calls']), 'A6_SOCKET_BOUNDARY')
    events = t['operational_events']
    source_events = [e for e in events if e['event_code']=='source.acquisition.completed']
    execution_events = [e for e in events if e['event_code'] in ('execution.child.completed','adapter.execution.completed')]
    check(len(source_events)==len(t['transport_calls']) and len(execution_events)==3, 'A6_OPERATIONAL_ACCOUNTING')
    check(len({e['trace_id'] for e in source_events+execution_events})==1 and all(e['metrics']['duration_ms']>=0 for e in source_events+execution_events), 'A6_OPERATIONAL_CORRELATION')
    desc = calls['market_describe_capabilities']
    check(desc['preferred_request_schema_version'] == 'unified_market_evidence_request.v3' and desc['emitted_result_schema_version'] == 'unified_market_evidence_result.v3', 'A6_PREFERRED_VERSION')
    check(next(x for x in desc['capabilities'] if x['capability_id'] == 'identity')['selected_executor_id'] is None, 'A6_CONTRACT_NOT_EXECUTABLE')
    evidence = result['targets'][0]['evidence']
    check(set(evidence) == set(FAMILIES), 'A6_RESULT_FAMILY_SET')
    for family in FAMILIES:
        op = next(x for x in plan['operations'] if x['capability_id'] == family)
        lineage = next(x for x in audit['operation_lineage'] if x['capability_id'] == family)
        ref = lineage['artifact_references'][0]
        operation = artifacts[ref['relative_path']]
        typed = evidence[family]
        contract = ('t187ap05_' if family == 'monthly_revenue' else 't187ap04_') + ('L' if t['market'] == 'TWSE' else 'O')
        operation_schema = 'phase_g_' + ('monthly_revenue' if family == 'monthly_revenue' else 'material_disclosure') + '_operation_evidence.v1'
        typed_schema = ('monthly_revenue' if family == 'monthly_revenue' else 'material_disclosure') + '_evidence.v1'
        check(op['executor_id'] == lineage['executor_id'] == operation['executor_id'] == EXECUTOR, 'A6_EXECUTOR', family)
        check(op['operation_id'] == lineage['operation_id'] and ref['relative_path'] == 'evidence/'+op['operation_id']+'.json', 'A6_OPERATION_ID', family)
        check(op['network_required'] is True and op['capability_requires_execution_approval'] is True, 'A6_EXECUTION_BOUNDARY', family)
        check(op['market'] == lineage['market'] == operation['target']['market'] == typed['source']['market'] == t['market'], 'A6_MARKET', family)
        check(op['canonical_target_ids'] == lineage['canonical_target_ids'] == [target] and operation['target']['canonical_target_id'] == target, 'A6_TARGET', family)
        check(op['expected_evidence_contract'] == lineage['evidence_contract'] == operation['schema_version'] == operation_schema, 'A6_OPERATION_CONTRACT', family)
        check(operation['capability_id'] == family, 'A6_OPERATION_CAPABILITY', family)
        check(typed['schema_version'] == typed_schema, 'A6_TYPED_CONTRACT', family)
        check(operation['source']['source_contract_id'] == typed['source']['source_contract_id'] == contract, 'A6_SOURCE_CONTRACT', family)
        check(any(x['contract'] == contract for x in t['transport_calls']), 'A6_SOURCE_TRANSPORT', family)
        check(operation['status'] == typed['status'], 'A6_STATUS_PRESERVATION', family)
        check(operation['observed_at'] == typed['currentness']['observed_at'], 'A6_OBSERVED_AT', family)
        check(all(typed['coverage'].get(k) == v for k,v in operation['coverage'].items()), 'A6_SOURCE_TIME_COVERAGE', family)
        for obj, schema in ((operation, operation_schema), (typed, typed_schema)):
            check(not list(Draft7Validator(read('schemas/' + schema + '.schema.json')).iter_errors(obj)), 'A6_EVIDENCE_SCHEMA', family)
        actual_hash = hashlib.sha256((json.dumps(operation, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()
        check(actual_hash == ref['sha256'] == t['retained_bytes'][ref['relative_path']]['sha256'], 'A6_ARTIFACT_HASH', family)
        check(ref['byte_size'] == t['retained_bytes'][ref['relative_path']]['bytes'], 'A6_ARTIFACT_SIZE', family)
        published = next(x for x in desc['capabilities'] if x['capability_id'] == family)
        check(published['semantic_support_status'] == 'runtime_executable' and published['selected_executor_id'] == op['executor_id'], 'A6_DESCRIBE_ROUTE', family)
        for citation_id in typed['citation_ids']:
            citation = next(x for x in result['targets'][0]['citations'] if x['citation_id'] == citation_id)
            mapping = next(x for x in audit['citation_to_operation_map'] if x['citation_id'] == citation_id)
            check(mapping['operation_id'] == op['operation_id'] and mapping['canonical_target_id'] == target and mapping['capability_id'] == family, 'A6_CITATION_BINDING', family)
            check(citation['artifact_reference'] == mapping['artifact_relative_path'] == ref['relative_path'], 'A6_CITATION_PATH', family)
            check(citation['normalized_evidence_hash'] == mapping['artifact_hash'] == ref['sha256'], 'A6_CITATION_HASH', family)
            check(citation['source_contract_id'] == contract, 'A6_CITATION_SOURCE', family)
        if operation['status'] == 'available':
            check(bool(typed['citation_ids']), 'A6_AVAILABLE_CITATION', family)
            if family == 'monthly_revenue':
                check(operation['value'] == typed['value'] and typed['value']['current_month_revenue'] == 100 and typed['value']['mom_pct'] is None, 'A6_NORMALIZED_VALUE')
    if t['scenario'] == 'mixed':
        check(evidence['monthly_revenue']['status'] == 'available' and evidence['material_disclosures']['status'] == 'source_failed', 'A6_FAILURE_ISOLATION')
        check(result['status'] == 'partially_failed' and evidence['material_disclosures']['citation_ids'] == [] and 'all_governed_transports_failed' in evidence['material_disclosures']['caveats'], 'A6_MIXED_AGGREGATE')
    else:
        check(result['status'] == 'full_success', 'A6_POSITIVE_AGGREGATE')
    return errors


def validate_context(s):
    from scripts.validate_l5_extension_publication_conformance import validate_snapshot, load_snapshot
    errors = []
    if s.get('family_registry') is not None: errors.append({'code': 'A6_SECOND_REGISTRY'})
    if s.get('family_owned_policies'): errors.append({'code': 'A6_FAMILY_PLATFORM_POLICY'})
    if s.get('dimensions') != [d['dimension_id'] for d in read(A1)['dimensions']]: errors.append({'code': 'A6_DIMENSION_COVERAGE'})
    actual = load_snapshot()
    for key in ('catalog', 'routing', 'portable'):
        actual[key] = s[key]
    try:
        errors.extend(validate_snapshot(actual)['errors'])
    except (KeyError, ValueError, TypeError) as exc:
        errors.append({'code':'A6_PUBLICATION_SHAPE_INVALID','detail':type(exc).__name__})
    return errors


def dimension_coverage():
    from scripts.validate_l5_existing_family_conformance import platform_proof
    platform = platform_proof()
    # Fixed proof roles, never capability/source/dispatch registration values.
    stage_groups = {
        'S02,S05': [4, 5, 13], 'S03,S14': [3, 27, 35], 'S04,S08,S23': [2, 7, 8],
        'S09,S10,S11': [6, 25], 'S13,S14,S15': [1, 9, 10, 11, 12, 14, 26],
        'S16,S17,S19': [15, 16, 21], 'S18': [28], 'S19': [23], 'S20,S22': [24],
        'S23,S24': [18, 19], 'S25': [17, 20, 22, 29, 30, 31, 32, 33, 34, 36]}
    rows = []
    for d in read(A1)['dimensions']:
        number = int(d['dimension_id'][-2:])
        stages = next(k.split(',') for k, ids in stage_groups.items() if number in ids)
        cls = ('DERIVED_PUBLICATION_GATE' if number in (18, 19) else
               'PLATFORM_INHERITED_ACCEPTED_GATE' if number in (20, 22, 29, 30, 31, 32, 33, 34, 36) else
               'TRACE_PLUS_ACCEPTED_GATE' if number in (12, 13, 17, 21) else 'TRACE_PROVEN')
        rows.append({'dimension_id': d['dimension_id'], 'dimension': d['name'], 'frozen_a1_classification': d['classification'],
                     'proof_class': cls, 'trace_stages': stages, 'current_authority': d['canonical_owner'],
                     'delegated_tests': platform['behavioral_gates'] if cls == 'PLATFORM_INHERITED_ACCEPTED_GATE' else
                     ['tests/unit/test_l5_a5_existing_family_conformance.py'] if cls == 'TRACE_PLUS_ACCEPTED_GATE' else
                     ['scripts/validate_l5_extension_publication_conformance.py'] if cls == 'DERIVED_PUBLICATION_GATE' else [],
                     'proof_artifacts': ['edge_invariant_verification.json', 'existing_integration_test_result.json', 'required_validator_result.json'],
                     'result': 'PASS_CONDITIONAL_ON_RECORDED_TRACE_AND_DELEGATED_GATES'})
    return rows


STAGES = ['surface', 'Request', 'target/SecurityMaster', 'capability', 'validation', 'preview', 'authorization',
          'executor', 'source authority', 'source contract', 'transport fixture', 'normalization', 'operation evidence',
          'typed evidence', 'timing/status', 'retained hash', 'citations', 'Result', 'Audit', 'handoff', 'MCP read',
          'MCP export', 'Catalog/Routing', 'portable/guide/Skill/use', 'L1-L4']


def graph(t):
    calls, a, result, audit = parts(t)
    ops = a['control/plan.json']['operations']
    values = [t['tool_names'], t['request'], result['targets'][0]['canonical_identity'],
              [x['capability_id'] for x in ops], calls['market_validate_request']['validation_status'],
              calls['market_preview_request']['orchestration_plan']['operations'], a['control/authorization.json'],
              [x['executor_id'] for x in ops], [x['source']['source_family'] for k,x in a.items() if k.startswith('evidence/')],
              [x['contract'] for x in t['transport_calls']], t['transport_calls'],
              {f: result['targets'][0]['evidence'][f].get('value', result['targets'][0]['evidence'][f].get('items')) for f in FAMILIES},
              {k:v for k,v in a.items() if k.startswith('evidence/')}, result['targets'][0]['evidence'],
              {f: {'status': e['status'], 'currentness': e['currentness']} for f,e in result['targets'][0]['evidence'].items()},
              audit['artifact_inventory'], audit['citation_to_operation_map'], {'result_id':result['result_id'], 'result_hash':result['result_hash']},
              audit, calls['market_export_ai_handoff'], calls['market_read_result']['result_id'],
              calls['market_export_ai_handoff']['result_id'], calls['market_describe_capabilities'],
              {'gate': 'validate_l5_extension_publication_conformance', 'artifact': 'publication_join.json'},
              {'gates': 'platform_inheritance.json + existing_integration_test_result.json'}]
    errors = validate_trace(t)
    nodes = [{'stage':f'S{i+1:02}', 'role':role, 'observed':v} for i,(role,v) in enumerate(zip(STAGES, values))]
    edges = [{'from':nodes[i]['stage'], 'to':nodes[i+1]['stage'], 'carried_identity':
              {'request_id': t['request']['request_id'], 'target':t['request']['targets'][0]['input'],
               'operation_ids':[x['operation_id'] for x in ops], 'capabilities':list(FAMILIES)},
              'evidence_source': f'integrated_trace_{t["market"].lower()}.json / calls + artifacts; publication_join.json; platform_inheritance.json',
              'verification_rule':'validate_trace identity/hash/schema joins; S23-S25 delegated current publication/platform gates',
              'result':'FAIL' if errors else 'PASS'} for i in range(24)]
    return {'nodes':nodes, 'edges':edges, 'errors':errors}


def semantic_view(t):
    """Explicit semantic projection, retaining all family values/state/caveats.

    Exactly observed_at is removed from each operation/typed currentness. Source
    reporting/publication dates remain. IDs/hashes are independently verified
    before equivalence; they depend on execution clocks and are mapped to stable
    operation IDs, NOT ignored during integrity verification.
    """
    calls, a, result, audit = parts(t)
    operations = {k:deepcopy(v) for k,v in a.items() if k.startswith('evidence/')}
    for v in operations.values(): v.pop('observed_at')
    typed = deepcopy(result['targets'][0]['evidence'])
    for v in typed.values(): v['currentness'].pop('observed_at')
    # Handoff text is compared in full after replacing only known run-local
    # timestamps and Result/Audit IDs already verified above.
    text = calls['market_export_ai_handoff']['ai_ready_markdown']
    replacements = {result['generated_at']:'<execution-time>', result['result_id']:'<result-id>',
                    audit['audit_package_id']:'<audit-id>'}
    for v in result['targets'][0]['evidence'].values(): replacements[v['currentness']['observed_at']] = '<execution-time>'
    for old,new in replacements.items(): text = text.replace(old,new)
    # Preserve the complete Result body, including every citation, caveat and
    # additional field. Replace only individually known execution identities,
    # timestamps and their artifact-hash consequences after integrity checks.
    result_tokens = dict(replacements)
    result_tokens[result['result_hash']] = '<verified-result-hash>'
    for lineage in audit['operation_lineage']:
        for ref in lineage['artifact_references']:
            result_tokens[ref['sha256']] = digest(operations[ref['relative_path']])
    def tokens(value):
        if isinstance(value,dict): return {k:tokens(v) for k,v in value.items()}
        if isinstance(value,list): return [tokens(v) for v in value]
        return result_tokens.get(value,value) if isinstance(value,str) else value
    full_result_semantics = tokens(result)
    return {'plan_operations': a['control/plan.json']['operations'], 'source_selection': t['transport_calls'],
            'operation_semantic_hashes':{k:digest(v) for k,v in operations.items()}, 'typed_semantics':typed,
            'result_semantic_body':full_result_semantics,
            'result_semantic_body_sha256':digest(full_result_semantics),
            'audit_lineage':[{k:v for k,v in row.items() if k != 'artifact_references'} for row in audit['operation_lineage']],
            'handoff_content':text}


def build_evidence(root):
    traces = {'twse':run_trace(root/'twse'), 'tpex':run_trace(root/'tpex','TPEX'),
              'mixed_outcome':run_trace(root/'mixed','TWSE','mixed')}
    repeats = {'twse':run_trace(root/'twse-repeat'), 'tpex':run_trace(root/'tpex-repeat','TPEX')}
    equivalence = {key:{'first':semantic_view(traces[key]), 'second':semantic_view(repeats[key])} for key in repeats}
    for row in equivalence.values():
        row.update(first_semantic_sha256=digest(row['first']), second_semantic_sha256=digest(row['second']), exact_semantic_equal=row['first']==row['second'])
    errors = [e for t in [*traces.values(),*repeats.values()] for e in validate_trace(t)]
    context = publication()
    context['dimensions'] = [d['dimension_id'] for d in read(A1)['dimensions']]
    errors += context['errors'] + validate_context(context)
    if not all(x['exact_semantic_equal'] for x in equivalence.values()): errors.append({'code':'A6_DETERMINISM'})
    return {'status':'PASS' if not errors else 'HOLD', 'errors':errors, 'traces':traces, 'repeat_traces':repeats,
            'graphs':{k:graph(t) for k,t in traces.items()}, 'determinism':equivalence,
            'dimensions':dimension_coverage(), 'publication':context}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='l5-a6-acceptance-') as temp:
        evidence=build_evidence(Path(temp))
    summary={k:evidence[k] for k in ('status','errors')}
    summary.update(traces=3, dimensions=len(evidence['dimensions']), public_tools=6,
                   provider_requests=0, live_acquisition=0, production_mutations=0)
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
    return 0 if evidence['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
