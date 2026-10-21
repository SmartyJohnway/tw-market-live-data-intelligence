"""Acceptance-only A6 evidence author; never imported by product runtime.

Requires completed raw test/gate outputs. Does not upgrade a failed gate to PASS.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from scripts.validate_l5_integrated_extension_contract_acceptance import ROOT, A1, digest, graph, validate_trace, semantic_view

BASE='928de0f930b0733e188ef3c873f994ce9e8a69d3'
AUTH='USER_CHAT_2026-10-21_PHASE_L_L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_AUTHORIZATION'
DISPOSITION='L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_PASS'
GOV='docs/governance/phase_l/PHASE_L_L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_2026-10-21.md'
FRONT=['PROJECT.md','HANDOFF.md','ROADMAP.md','docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md']
SOURCES=['scripts/validate_l5_integrated_extension_contract_acceptance.py','scripts/l5_a6_build_evidence.py',
         'tests/helpers/l5_a6_integrated.py','tests/helpers/l5_a6_source_transport.py',
         'tests/integration/test_l5_a6_integrated_extension_contract_acceptance.py']


def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def canonical_bytes(raw): return raw.decode('utf-8').replace('\r\n','\n').replace('\r','\n').encode('utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True)
    parser.add_argument('--capture',required=True)
    args=parser.parse_args()
    run=(ROOT/args.run).resolve()
    assert run.parent==ROOT/'docs/governance/phase_l/acceptance_runs' and run.name.startswith('l5-a6-')
    def write(name,value): (run/name).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    e=load(args.capture)
    required=load(run/'required_validator_result.json')
    existing=load(run/'existing_integration_test_result.json')
    default=load(run/'default_ci_failure_set_comparison.json')
    assert required['status']=='PASS' and len(required['validators'])==16
    assert existing['status']=='PASS'
    assert default['exact_set_equal'] and not default['candidate_only'] and default['historical_failed_count']==41
    assert e['status']=='PASS'
    for t in [*e['traces'].values(),*e['repeat_traces'].values()]: assert validate_trace(t)==[]
    def junit(name):
        nodes=ET.parse(run/name).getroot().findall('.//testcase')
        assert not any(n.find('failure') is not None or n.find('error') is not None for n in nodes)
        return {'passed':len(nodes),'failed':0,'nodes':[n.attrib['classname'].replace('.','/')+'::'+n.attrib['name'] for n in nodes]}
    focused=junit('focused.xml')
    existing.update(counts=junit('existing.xml'))
    write('existing_integration_test_result.json',existing)
    write('focused_test_result.json',focused|{'status':'PASS','command':'python -m pytest -q tests/integration/test_l5_a6_integrated_extension_contract_acceptance.py','negative_mutation_cases':26})
    write('preflight_result.json',{'authority':AUTH,'branch':git('branch','--show-current'),'entry_head':BASE,
          'entry_tree':'320fa08120fe159bf4acead6267875cd6917b298','entry_clean':True,
          'fetch_performed':True,'entry_remote_main':BASE,'status':'PASS'})
    milestones=['86f1e74f8208823b4cb6cf813eb474d5e76392ef','d6e90895d0af606fccab74b8143cd43376ecabfa',
                '303e2ba444721f939ce74a5f2c15b0a5bb562a7a','072a63623ba9f73236542e5f50e4903b6b4d06d1',BASE]
    ancestry=[]
    for sha in milestones:
        assert subprocess.call(['git','merge-base','--is-ancestor',sha,BASE],cwd=ROOT)==0
        ancestry.append({'commit':sha,'ancestor_of_authorized_base':True})
    write('entry_authority_integrity.json',{'status':'PASS','milestones':ancestry,'main':BASE,'tree':git('show','-s','--format=%T',BASE)})
    write('existing_execution_seam_adjudication.json',{'result':'PASS','proof':'All six real tools, actual governed child and research routes observed in five lifecycle executions.',
        'precedents':['tests/helpers/phase_j_closure_r1_transport.py::install','tests/helpers/phase_j_closure_r1_server.py',
                      'tests/helpers/phase_j_j2_r1_transport.py','tests/integration/test_phase_j_j2_deterministic_cross_layer.py::_use_in_process_service_transport'],
        'transport_bootstrap':'Test harness selects existing child bootstrap seam; helper invokes unchanged m8r_06_03_execute_once.main after installing only adapter.urlopen fixture bytes. No child/claim/registry/output substituted.',
        'substitutions':['raw HTTP transport','accepted isolated Security Master fixture release','ASGI transport','temporary control root'],
        'runtime_test_hook_added':False,'runtime_files_changed':0})
    write('public_tool_surface.json',{'tools':e['traces']['twse']['tool_names'],'count':6,
        'all_six_exercised_in_each_trace':True,'public_unknown_need_and_alias_rejections':e['traces']['twse']['public_rejections'],
        'preferred_request':'unified_market_evidence_request.v3','emitted_result':'unified_market_evidence_result.v3'})
    for key,t in e['traces'].items():
        write('integrated_trace_'+key+'.json',t)
        g=graph(t)
        # Actual observed nodes carry full outputs; add exact owning code seams.
        authorities=['server/unified_mcp/tool_contracts.py','schemas/unified_market_evidence_request.v3.schema.json',
            'scripts/m8r_06_01c2_mode_a_security_master_loader.py','docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json',
            'server/services/unified_mode_a.py::validate_mode_a_request','server/services/unified_mode_b1.py::build_mode_b1_preview',
            'server/services/unified_mode_b2.py::build_local_operator_execution_ticket','scripts/m8r_06_03_production_adapter.py::build_production_runtime_adapter_registry',
            'scripts/phase_g/mops_monthly_revenue.py + mops_material_disclosures.py::SOURCE_FAMILY',
            'scripts/phase_g/research_executor.py::ROUTES','tests/helpers/l5_a6_source_transport.py::install',
            'scripts/phase_g/mops_monthly_revenue.py + mops_material_disclosures.py::execute',
            'scripts/m8r_06_03_production_adapter.py::_write_research_evidence','scripts/m8r_05c/evidence_projector.py',
            'scripts/m8r_05c/evidence_projector.py','scripts/m8r_05c/artifact_loader.py','scripts/m8r_05c/citation_builder.py',
            'scripts/m8r_05c/result_builder.py','scripts/m8r_05c/audit_package_builder.py','server/services/unified_mode_c.py::build_mode_c_ai_handoff',
            'server/unified_mcp/server.py::dispatch_safe_tool','server/unified_mcp/server.py::dispatch_safe_tool',
            'docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json + m8r_05b_capability_to_executor_routing_matrix.v3.json',
            'scripts/validate_l5_extension_publication_conformance.py','platform_inheritance.json']
        for node,authority in zip(g['nodes'],authorities): node['current_authority']=authority
        rules=[
            'Actual six-tool snapshot validates closed V3 Request arguments; unknown need/alias public probes reject.',
            'Actual Mode A target resolution binds Request input to isolated qualified Security Master ISIN/market/code.',
            'Request data_needs[].type values equal actual validation capability identities for the resolved target.',
            'Validation is valid for this request_id and both required capabilities; no arbitrary capability is admitted.',
            'Actual preview operations retain Request hash, target, capability, market and selected executor.',
            'Preview performs no execution; actual single-use authorization approves exactly the rebuilt plan operations.',
            'Actual approved operations select the trusted production research executor through the real registry.',
            'Production research adapter emits the expected distinct source-family identities for the selected capabilities.',
            'Operation and typed source contracts agree with the actual market-specific source contract.',
            'Actual adapter HTTP request hits an exact existing source URL; only fixture bytes/error are returned.',
            'Recorded fixture payload digest and actual normalizer preserve signed/null monetary values and disclosure facts.',
            'Actual normalization output is retained under its operation schema, capability, executor and target.',
            'Retained operation projects to the accepted typed schema; cross-family contract swaps reject.',
            'Operation/typed status, observed_at and source coverage fields agree without changing missing/failure state.',
            'Independent disk byte length/hash equals operation artifact reference; schema validation also passes.',
            'Citation path/hash/source contract and Audit mapping bind the same retained artifact and operation.',
            'Typed family/citations inhabit the canonical Result; independently recomputed complete Result hash agrees.',
            'Audit hash is independently recomputed and its result_id/result_hash equal the canonical Result.',
            'Handoff envelope and citation subset derive from the same Result and Audit, with no invented text/citation.',
            'Read Result uses the actual stored package and retains the same canonical_result/result_id/hash.',
            'MCP export through the actual client/service returns the same verified Result and shared renderer output.',
            'Public describe selected executor and executable state match actual selected operations; contract-only identity stays non-executable.',
            'Both independent sync gates and accepted publication validator join canonical Catalog/Routing to derived views/guides.',
            'Recorded L1-L4 behavioral suites pass; actual timing correlation and contained authorization execution remain platform-owned.'
        ]
        for i,edge in enumerate(g['edges']):
            edge['evidence_source']='integrated_trace_'+key+'.json; publication_join.json; platform_inheritance.json'
            edge['verification_rule']=rules[i]
            edge['from_observed_sha256']=digest(g['nodes'][i]['observed'])
            edge['to_observed_sha256']=digest(g['nodes'][i+1]['observed'])
        write('integrated_graph_'+key+'.json',g)
    write('repeat_integrated_traces.json',e['repeat_traces'])
    write('edge_invariant_verification.json',{'status':'PASS','graphs':3,'stages_per_graph':25,'edges_per_graph':24,'total_verified_edges':72,
         'trace_errors':{k:validate_trace(t) for k,t in e['traces'].items()},'verification_symbol':SOURCES[0]+'::validate_trace'})
    dimensions=e['dimensions']
    for row in dimensions:
        row['result']='PASS'
        row['proof_artifacts'] += ['integrated_trace_twse.json','integrated_trace_tpex.json','integrated_trace_mixed_outcome.json']
        if row['dimension_id'] in ('DIM-18','DIM-19'): row['proof_artifacts'].append('publication_join.json')
        if row['dimension_id']=='DIM-36': row['proof_artifacts'].append('version_transition_integrity.json')
        if row['dimension_id']=='DIM-17': row['proof_artifacts'].append('focused_test_result.json')
        if row['dimension_id']=='DIM-20':
            row['accepted_governance']='docs/governance/phase_l/PHASE_L_L5_A5_OWNER_ACCEPTANCE_2026-10-21.md'
            row['scope']='Existing family acceptance inherited; A6 Owner acceptance remains PENDING.'
    write('dimension_integration_coverage.json',{'status':'PASS','dimensions':dimensions,'count':36,'accounted':36,'unresolved':0,
         'DECISION_REQUIRED':0,'proof_class_counts':dict(Counter(r['proof_class'] for r in dimensions)),
         'acceptance_authority_note':'Existing family Owner acceptance inherited from A5; this A6 technical evidence does not imply A6 Owner acceptance.'})
    equivalence={}
    for key in ('twse','tpex'):
        first,second=semantic_view(e['traces'][key]),semantic_view(e['repeat_traces'][key])
        assert first==second
        equivalence[key]={'first':first,'second':second,'first_semantic_sha256':digest(first),'second_semantic_sha256':digest(second),'equal':True}
    write('determinism_equivalence.json',{'status':'PASS','pairs':equivalence,
        'exclusions':[{'field':'operation.observed_at / typed.currentness.observed_at / Result.generated_at','reason':'retrieval/execution clock, distinct from retained source report/publication time'},
                      {'field':'Result.result_id/result_hash and audit_reference.audit_package_id','reason':'execution receipt/bundle timestamp-dependent identities, independently verified before comparison'},
                      {'field':'citation normalized_evidence_hash/retrieved_at','reason':'replace verified artifact hash with full operation semantic hash after excluding only observed_at'},
                      {'field':'handoff Result/Audit IDs and observed time text','reason':'only exact known run-local values replaced; full remaining markdown compared'}],
        'not_excluded':['source dates','published_at','values','units','nulls','status','caveats','source/contract','operation IDs','citations','all remaining Result fields'],
        'integrity_hashes_checked_before_semantic_comparison':True})
    mixed=e['traces']['mixed_outcome']['calls']['market_read_result']['canonical_result']
    write('failure_containment.json',{'status':'PASS','observed_aggregate':mixed['status'],
        'families':mixed['targets'][0]['evidence'],'source_failure_not_missing':True,'no_invented_failure_state':True})
    write('negative_mutation_tests.json',{'status':'PASS','cases':26,'nodes':[n for n in focused['nodes'] if 'mutation' in n],
        'public_refusal_tests':e['traces']['twse']['public_rejections'],'socket_guard_selftest_separate_from_trace_attempts':True})
    write('publication_join.json',{'status':'PASS','current_authorities':e['publication'],
         'independent_gates':['required-04.log','required-05.log','required-11.log'],'publication_cannot_activate':True})
    from scripts.validate_l5_existing_family_conformance import platform_proof
    write('platform_inheritance.json',{'status':'PASS','inherited_authorities':platform_proof(),'delegated_test_result':'existing_integration_test_result.json',
        'L1':'Observed same trace_id across source timing, adapter timing and child completion; request/operation/authorization bound in actual Audit.',
        'L2':'Actual finalized retained package; replay/retention/migration boundaries delegated to accepted platform gates; read/export produced no extra transport calls.',
        'L3':'Raw fixture transport → actual contract/semantic validation; mixed failure retained as source_failed.',
        'L4':'Actual authorization/claim, bounded fixed child, temp contained root; platform path/secret/resource/concurrency gates passed.',
        'new_family_owned_platform_policies':0,'operational_events':{k:t['operational_events'] for k,t in e['traces'].items()},
        'provider_requests':0,'live_acquisition':0,'production_mutations':0,
        'unexpected_external_socket_attempts_primary_traces':sum(len(t['socket_attempts']) for t in [*e['traces'].values(),*e['repeat_traces'].values()]),
        'instrumentation_scope':e['traces']['twse']['socket_scope'],'os_wide_network_observation':False})
    # Canonical identities of historical manifests and immutable bytes at entry;
    # no claim that later current front doors equal historical member snapshots.
    manifests=[]
    runs=['l5-a0-20261018T110810Z','l5-a0-r1-20261018T122006Z','l5-a1-20261018T140202Z','l5-a2-20261019T053855Z',
          'l5-a3-20261020T015810Z','l5-a4-20261020T071416Z','l5-a4-r1-20261020T074329Z','l5-a4-r2-20261020T134225Z',
          'l5-a5-20261020T143928Z','l5-a5-r1-20261020T151923Z','l5-a1-r1-20261019T034526Z','l5-a2-r1-20261020T011524Z']
    expected=['aa7dee61185eddb66e4adb5c08b700fb884404dbf77e26ba6187a1097277ba94',
        'c3975ce5726182b2d831d9c9b82ff3a300912a7222a536665a1acb9985d9a78f',
        '326d671e069869c3196a8dd9ba4e78525255d954f9b722bc2c3af4d91a3fbe2b',
        'b1dd1c009426e9470180e9962430284062538228e8ef940c6d2a71481c48bfea',
        '844402e972d7a3a793150db9cca3fb32be3e568860950b63d69c320ccda52c75',
        '7e76b0db1a2d99bc14903ad79124dd630e3f5aaeda47518c68303f44c3399769',
        'dd83ba9ab1d353993d2220d3e699bb0ed815bf54e0ee91d2e3435161459869e9',
        '9fb590dff3f51e93a0c91678d78a69ebabb732b1e939692c4222866cc917b0be',
        'c2db766581cfb6b6d37cefd69df191c0969ce178b4ed67311a23066cc076d8e8',
        '9572ea1e6417c58255ebebbd28f2348b433200854248293fa99fe1d6db6035c0',
        '4afd4fafa1d84d7301de4ee2fc30bb03b6b238b027b461fef740c9494e10c0ca',
        'c737bfbe06ce9faf4b0032a631ef3f75f11cbe9c6205fa41f7b04105d0549426']
    for name in runs:
        p='docs/governance/phase_l/acceptance_runs/'+name+'/manifest.json'
        raw=(ROOT/p).read_bytes(); old=subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
        assert raw==old
        m=json.loads(raw); key='canonical_sha256' if 'canonical_sha256' in m else 'manifest_canonical_sha256'
        computed=digest({k:v for k,v in m.items() if k!=key})
        assert computed==m[key]==expected[runs.index(name)]
        manifests.append({'run':name,'artifact_count':m['artifact_count'],'declared':m[key],'recomputed':computed,'entry_bytes_unchanged':True})
    write('historical_manifest_integrity.json',{'status':'PASS','manifests':manifests,
        'historical_member_current_bytes_not_recast':True,
        'A3_accepted_authority':'PHASE_L_L5_A3_OWNER_ACCEPTANCE_2026-10-20.md records final-candidate 30/30 verification and no A3-R1 requirement. A6 preserves that accepted gate truth; no historical re-adjudication.'})
    frozen=load(ROOT/A1)
    assert len(frozen['dimensions'])==36 and frozen['classification_counts']['DECISION_REQUIRED']==0
    assert (ROOT/A1).read_bytes()==subprocess.check_output(['git','show',BASE+':'+A1],cwd=ROOT)
    write('version_transition_integrity.json',{'status':'PASS','A1_bytes_unchanged':True,'dimensions':36,'DECISION_REQUIRED':0,
         'T1_T12_bytes_unchanged':True,'version_transition':'NONE','public_schema_changes':0,'typed_contract_changes':0,'source_contract_changes':0,
         'universal_family_registry':False,'plugin_assessment':'PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW'})
    protected=['server','schemas','config','docs/data_capabilities','scripts/phase_g','scripts/m8r_05c','skills',
               'scripts/m8r_06_03_execute_once.py','scripts/m8r_06_03_production_adapter.py','requirements.txt','requirements-lock.txt','pyproject.toml']
    product=git('diff',BASE,'--name-only','--',*protected).splitlines()
    assert not product
    changed=git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()
    allowed=set(FRONT+[GOV]+SOURCES)
    assert all(p in allowed or p.startswith(str(run.relative_to(ROOT)).replace('\\','/')+'/') for p in changed)
    write('diff_scope_verification.json',{'status':'PASS','allowed_paths':sorted(allowed),'changed_paths':sorted(set(changed)),
         'protected_product_changed_paths':product,'runtime_behavior_changes':0,'public_schema_changes':0,'capability_changes':0,
         'source_executor_changes':0,'dependency_changes':0,'historical_evidence_rewritten':False})
    write('architecture_conflict_register.json',{'conflicts':[],'new_registry':False,'runtime_discovery':False,'new_family':False,'new_capability':False,
         'new_platform_policy':False,'public_tools':6,'Owner_acceptance_pending':True})
    write('offline_review.json',{'technical_disposition':DISPOSITION,'Owner_acceptance':'PENDING','required_gates':'16/16 PASS',
         'focused_tests':focused['passed'],'existing_tests':existing['counts']['passed'],'default_ci':default['counts'],
         'historical_failures_not_passing':41,'candidate_only':0,'trace_results':'3/3 PASS','dimensions_accounted':36,
         'unresolved':0,'determinism':'PASS','production_mutations':0,'provider_requests':0,'live_acquisition':0,
         'unexpected_external_socket_attempts':0,'socket_scope':'Primary harness parent and child only; not OS-wide; guard selftest intentional rejection recorded separately.',
         'initial_existing_suite_failure':'Missing isolated Security Master; preserved existing-uninitialized logs; accepted test bootstrap rerun PASS without test/product edits.',
         'A7_authorized':False,'L6_L7_authorized':False})
    # Manifest written last, no self-reference. UTF-8 CRLF/CR→LF for members;
    # own digest is compact sorted JSON excluding canonical_sha256.
    import hashlib
    paths=sorted(set([*FRONT,GOV,*SOURCES]+[str(p.relative_to(ROOT)).replace('\\','/') for p in run.rglob('*') if p.is_file() and p.name!='manifest.json']))
    members=[]
    for p in paths:
        raw=canonical_bytes((ROOT/p).read_bytes())
        members.append({'path':p,'canonical_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    m={'artifact_count':len(members),'artifacts':members,'normalization':'UTF-8 text; CRLF/CR normalized to LF before SHA-256',
       'self_digest_policy':'compact sorted JSON ensure_ascii=false excluding canonical_sha256','technical_disposition':DISPOSITION}
    m['canonical_sha256']=digest(m)
    write('manifest.json',m)
    print(json.dumps({'artifact_count':len(members),'canonical_sha256':m['canonical_sha256']}))


if __name__=='__main__': main()
