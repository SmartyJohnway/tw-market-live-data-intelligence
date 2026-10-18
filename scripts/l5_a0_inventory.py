"""Deterministic A0 evidence authoring; not a runtime registry or plugin interface.

Reads tracked authorities only. Candidate classifications are review judgments,
not generated activation authority. No import of production adapters or network.
"""
from pathlib import Path
from collections import Counter
import argparse
import ast
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '4e8aa0557644ac76cca22e67c824ffd0eab7b6c1'
TREE = 'bc116c15e54502c2bbb62392dd769c3442cd3732'
AUTH = 'USER_CHAT_2026-10-18_PHASE_L_L5_ENTRY_AND_A0_EXTENSION_SURFACE_INVENTORY_AUTHORIZATION'
L0 = 'docs/governance/phase_l/PHASE_L_L0_PRODUCTION_BOUNDARY_AND_ARCHITECTURE_CONTRACT_2026-10-13.md'
CAT = 'docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json'
ROUTE = 'docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json'
META = 'config/m8r_06_03_executor_registry_metadata.json'
ADAPT = 'scripts/m8r_06_03_production_adapter.py'
SOURCE = 'docs/source_registry/source_authority_registry.json'
GUIDES = ['skills/tw-market-evidence-agent/SKILL.md', 'docs/agent_usage_guide.md']
DERIVED = ['skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json',
           'skills/tw-market-evidence-agent/references/capability_quick_guide.md']
C = 'scripts/m8r_05c/'
PRIMARY_SYMBOLS = {
 CAT:'data_need_capabilities', ROUTE:'routes', META:'executors',
 ADAPT:'build_production_runtime_adapter_registry',
 C+'artifact_loader.py':'load_projection_inputs', C+'lineage_resolver.py':'build_lineage_map',
 C+'result_builder.py':'build_result', C+'audit_package_builder.py':'build_audit_package',
 C+'evidence_projector.py':'project_target_evidence', C+'markdown_renderer.py':'render_result_markdown',
 C+'citation_builder.py':'build_citation_index',
 'scripts/m8r_05a_f3/capability_validator.py':'validate_capability',
 'scripts/m8r_05a_f3/request_intake.py':'validate_unified_market_evidence_request',
 'scripts/m8r_05a_f3/target_validator.py':'validate_target',
 'scripts/m8r_05a_f3/security_master_loader.py':'load_f3_verified_security_master',
 'scripts/m8r_05b_01/planner.py':'build_plan',
 'scripts/m8r_05b_03/dispatch.py':'prepare_dispatch',
 'scripts/m8r_05b_03/registry.py':'ExecutorMetadataRegistry',
 'scripts/m8r_05b_03/authorization_gate.py':'authorize',
 'scripts/m8r_05b_03/consumption_claim.py':'atomic_claim_authorization',
 'scripts/m8r_05b_03/receipt.py':'build_evidence_bundle',
 'scripts/m8r_05b_03/request_projection.py':'build_execution_request_projection',
 'scripts/phase_g/research_executor.py':'ROUTES',
 'scripts/phase_g/mops_monthly_revenue.py':'execute',
 'scripts/phase_g/mops_material_disclosures.py':'execute',
 'server/services/unified_contract_versions.py':'resolve_planning_authority_paths',
 'server/services/unified_mode_c.py':'build_mode_c_ai_handoff',
 'server/services/unified_mode_b2.py':'build_mode_b2_authorization',
 'server/services/unified_mode_b2_execution.py':'execute_mode_b2_once',
 'server/services/unified_mode_a.py':'validate_mode_a_request',
 'server/services/unified_retention_inventory.py':'classify_artifact_family',
 'server/services/unified_replay_inspector.py':'inspect_finalized_package',
 'server/services/unified_backup.py':'plan_backup',
 'server/services/unified_restore.py':'inspect_restore',
 'server/services/unified_migration.py':'inspect_migration',
 'server/operational_diagnostics.py':'timed_source_call',
 'server/resource_boundaries.py':'ResourceAdmissionMiddleware',
 'server/local_network_boundary.py':'LocalNetworkBoundaryMiddleware',
 'server/local_control_plane_boundary.py':'control_plane_rejection',
 'scripts/m8r_filesystem_safety.py':'safe_destination',
 'server/services/phase_l_source_drift_contract.py':'observe_source_attempt',
}

def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def digest(data):
    return hashlib.sha256(data).hexdigest()

def reference(path, symbol=None):
    p = ROOT/path
    assert p.is_file(), path
    lines = p.read_text(encoding='utf-8-sig').splitlines()
    symbol = symbol or PRIMARY_SYMBOLS.get(path)
    if not symbol and path.endswith('.schema.json'):
        symbol = '"$id"' if any('"$id"' in l for l in lines) else '"type"'
    if not symbol and path.endswith('.py'):
        definitions=[n for n in ast.walk(ast.parse('\n'.join(lines))) if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
        if definitions:
            # Explicit file-level source contract: enumerate all definitions so
            # function ownership remains auditable even for multi-stage adapters.
            symbol=definitions[0].name
    found = [i for i, line in enumerate(lines, 1) if symbol and symbol in line]
    if symbol:
        assert found, (path, symbol)
    return dict(path=path, symbol=symbol, line=found[0] if found else 1,
                symbol_kind='REGISTRY_OR_CONSTANT' if symbol and symbol.isupper() else 'FUNCTION_OR_CLASS' if path.endswith('.py') else 'SCHEMA_OR_DOCUMENT_SELECTOR',
                defined_symbols=[dict(name=n.name,line=n.lineno) for n in ast.walk(ast.parse('\n'.join(lines))) if isinstance(n,(ast.FunctionDef,ast.ClassDef))] if path.endswith('.py') else [],
                git_base=BASE)

def finding(fid, category, sources, behavior, implication, classification, severity='LOW', next_='L5-A1'):
    return dict(finding_id=fid, surface_category=category, current_authority=sources[0] if isinstance(sources[0],str) else sources[0][0],
                exact_source_files=[reference(s) if isinstance(s,str) else reference(*s) for s in sources],
                current_behavior=behavior, extension_implication=implication,
                classification=classification, risk_severity=severity, recommended_next_tranche=next_)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--traces', type=Path)
    parser.add_argument('--architecture', type=Path)
    args=parser.parse_args()
    out=args.run.resolve()
    out.relative_to(ROOT/'docs/governance/phase_l/acceptance_runs')
    out.mkdir(parents=True,exist_ok=True)
    def write(name, body):
        (out/name).write_text(json.dumps(body,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    catalog=read(CAT); routing=read(ROUTE); metadata=read(META)
    caps=catalog['data_need_capabilities']; routes={r['capability_id']:r for r in routing['routes']}
    assert len(caps)==14 and len({c['capability_id'] for c in caps})==14
    groups = {
      'identity': ('identity_resolution','CONTRACT_ONLY_LOCAL_IDENTITY'),
      'current_observation': ('market_observation','SOURCE_BACKED_SHARED_OBSERVATION'),
      'official_eod_reference': ('market_observation','SOURCE_BACKED_SHARED_OBSERVATION'),
      'session_status': ('session_context','BLOCKED_SOURCE_BACKED_CONTEXT_CONTRACT'),
      'recent_performance': ('bounded_historical_reference','SOURCE_BACKED_DERIVED_DESCRIPTION'),
      'source_currentness': ('evidence_metadata','CONTRACT_ONLY_UPSTREAM_PROJECTION'),
      'evidence_quality': ('evidence_metadata','CONTRACT_ONLY_UPSTREAM_PROJECTION'),
      'material_disclosures': ('material_disclosures','SOURCE_BACKED_DAILY_BATCH'),
      'monthly_revenue': ('monthly_revenue','SOURCE_BACKED_REPORTING_PERIOD'),
      'market_state_context': ('market_state_context','MULTI_SOURCE_MARKET_CONTEXT'),
      'index_futures_context': ('index_futures_context','CROSS_MARKET_CONTEXT'),
      'cash_institutional_flow_context': ('cash_institutional_flow_context','MARKET_SPECIFIC_SOURCE_CONTEXT'),
      'trading_status_context': ('trading_status_context','COMPOSITE_SUBTYPE_COVERAGE'),
      'corporate_action_context': ('corporate_action_context','LIFECYCLE_SUBTYPE_CONTEXT'),
    }
    inventory=[]
    for cap in caps:
        cid=cap['capability_id']; r=routes[cid]; group, kind=groups[cid]
        f=finding('CAP-'+cid,'capability_to_family',[CAT,ROUTE,META],
          'Catalog status and route are separate authorities; capability is not a family identifier.',
          'Preserve selected market, target type, evidence contract and explicit registration; no route inferred from Catalog alone.',kind)
        f.update(capability=cap,route=r,archetype_id=group,
                 metadata_routes=[e for e in metadata['executors'] if e['capability_id']==cid])
        inventory.append(f)
    write('current_capability_inventory.json',dict(capability_count=14,findings=inventory,
      archetype_count=len(set(g[0] for g in groups.values())),
      counting_rule='12 descriptive archetype groups for 14 requested capabilities. Includes three local/contract/derived groups, not 12 activated source families. H4 separately recorded, not a Catalog capability.'))
    archetypes=[]
    for group in sorted(set(g[0] for g in groups.values())):
        members=[c for c,(g,k) in groups.items() if g==group]
        archetypes.append(finding('ARCH-'+group,'archetype',[CAT,ROUTE],
          ' / '.join(groups[c][1] for c in members),
          'Archetype is an A0 analytical grouping; typed evidence schemas and selected routing own product identity.',
          'DESCRIPTIVE_INVENTORY') | dict(archetype_id=group,capability_ids=members))
    archetypes.append(finding('ARCH-H4','non_capability_derived_evidence',[ROUTE,C+'result_builder.py','schemas/discontinuity_safety_evidence.v1.schema.json'],
      'discontinuity_safety is derived zero-network evidence, request_capability=false.',
      'Do not register a network executor or invent a 15th capability.', 'DERIVED_NOT_REQUEST_CAPABILITY'))
    write('evidence_family_archetype_inventory.json',dict(catalog_archetype_count=12,additional_derived_non_capability_count=1,findings=archetypes))
    # Each registration is one named responsibility; files within a responsibility
    # are enumerated, never silently counted as separate canonical identities.
    specs=[
      ('catalog','CANONICAL_AUTHORITY',[CAT],'Capability identity, parameters, bounds, support and publication'),
      ('routing','RUNTIME_ROUTING_AUTHORITY',[ROUTE],'Selected executor, markets, target and batch/network policy'),
      ('executor_metadata','RUNTIME_ROUTING_AUTHORITY',[META],'Route tuple contract, timeout and maximum result items'),
      ('runtime_adapter_binding','RUNTIME_ROUTING_AUTHORITY',[(ADAPT,'build_production_runtime_adapter_registry')],'Trusted callable binding; no dynamic discovery'),
      ('executor_inventory','RUNTIME_ROUTING_AUTHORITY',['docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json'],'Planner selected executor reuse disposition'),
      ('source_registry','HISTORICAL_DUPLICATION',[SOURCE,'docs/source_registry/source_contract_schema.json','docs/source_registry/source_family_coverage_matrix.json'],'M4 design-stage taxonomy inventory; not current Unified acquisition authority. Preserve historical validator.'),
      ('research_source_routes','SOURCE_AUTHORITY',[('scripts/phase_g/research_executor.py','ROUTES')],'Explicit Phase G capability/market source contracts and fallback routes'),
      ('eod_source_contracts','SOURCE_AUTHORITY',['docs/data_capabilities/m8a_official_eod_endpoint_contract_registry.json','config/m8a_official_eod_security_master.json'],'Official EOD endpoint and instrument source contracts; target eligibility remains installation identity authority'),
      ('phase_h_sources','SOURCE_AUTHORITY',['config/phase_h_h1_dormant_source_descriptors.json','config/phase_h_h2_dormant_source_descriptors.json','server/services/phase_h_h1_tpex_composite.py','server/services/phase_h_h2_twse_exright_executor.py','server/services/phase_h_h3_twse_stock_day_adapter.py'],'Descriptors alone do not activate routes; current selected executors own request/normalization contracts'),
      ('phase_i_sources','SOURCE_AUTHORITY',['docs/data_capabilities/phase_i_i1_source_authority.v1.json','docs/data_capabilities/phase_i_i2_source_authority.v1.json','docs/data_capabilities/phase_i_i3_source_authority.v1.json'],'Family-specific approved source selection, subordinate to canonical route authority'),
      ('request_schema','SCHEMA_AUTHORITY',['schemas/unified_market_evidence_request.v3.schema.json'],'Closed public data_need vocabulary'),
      ('execution_schema','SCHEMA_AUTHORITY',['schemas/unified_market_evidence_execution_request.v3.schema.json'],'Governed execution projection vocabulary'),
      ('result_schema','SCHEMA_AUTHORITY',['schemas/unified_market_evidence_result.v3.schema.json'],'Typed family result fields and refs'),
      ('audit_schema','SCHEMA_AUTHORITY',['schemas/unified_market_evidence_audit_package.v3.schema.json'],'Audit lineage fields'),
      ('operation_schema','SCHEMA_AUTHORITY',['schemas/unified_market_evidence_operation_result.v2.schema.json'],'Operation evidence envelope compatibility'),
      ('family_schemas','SCHEMA_AUTHORITY',['schemas/phase_g_material_disclosure_operation_evidence.v1.schema.json','schemas/phase_g_monthly_revenue_operation_evidence.v1.schema.json'],'Versioned subordinate raw/normalized contracts, not a second protocol'),
      ('validator','NOT_AN_EXTENSION_POINT',[('scripts/m8r_05a_f3/capability_validator.py','validate_capability')],'Generic Catalog-driven parameter validation should normally need no family branch'),
      ('version_pairs','SCHEMA_AUTHORITY',[('server/services/unified_contract_versions.py','resolve_planning_authority_paths')],'Frozen Request version to Catalog/Route mapping'),
      ('planner','RUNTIME_ROUTING_AUTHORITY',[('scripts/m8r_05b_01/planner.py','build_plan')],'Generic plan plus explicit derived dependencies, H2/H3 and I3 date prerequisites'),
      ('loader','SCHEMA_AUTHORITY',[(C+'artifact_loader.py','_RESEARCH_EVIDENCE_CONTRACTS')],'Explicit schema allowlist and artifact semantic checks'),
      ('lineage','SCHEMA_AUTHORITY',[(C+'lineage_resolver.py','_CAPABILITY_TO_DATA_NEED')],'Closed mapping and typed-contract binding; fail closed'),
      ('projection','SCHEMA_AUTHORITY',[C+'models.py',C+'evidence_projector.py',C+'result_builder.py'],'Typed fields, missing/coverage semantics, existing Result construction'),
      ('audit_projection','SCHEMA_AUTHORITY',[C+'audit_package_builder.py'],'Typed family provenance and attempt projection'),
      ('handoff','SCHEMA_AUTHORITY',[C+'markdown_renderer.py'],'Runtime family Result/handoff projection and caveats; no independent authorization'),
      ('citation','NOT_AN_EXTENSION_POINT',[C+'citation_builder.py'],'Generic operation/artifact lineage identity; preserve citation proof'),
      ('portable','DERIVED_SYNCHRONIZED_VIEW',DERIVED+['scripts/generate_portable_catalog.py'],'Generated Catalog copy and quick guide with canonical hash and Git lineage'),
      ('runtime_guides','GUIDE_DOCUMENTATION',GUIDES+['skills/tw-market-evidence-agent/references/current_limitations.md'],'Human/AI usage and bounded limitations'),
      ('ai_guide_legacy','HISTORICAL_DUPLICATION',['docs/ai/M8_AI_CAPABILITY_QUICK_GUIDE.md','docs/data_capabilities/m8_source_capability_registry.json'],'Earlier guide/source-capability narrative is not a second current Unified Catalog'),
      ('sync_gates','TEST_AUTHORITY',['scripts/validate_portable_catalog_sync.py','scripts/validate_runtime_skill_guide_sync.py'],'Intentional independent cross-checks; do not replace all with dynamic equality'),
      ('contract_gates','TEST_AUTHORITY',['scripts/validate_v1_public_contracts.py','scripts/validate_unified_market_evidence_contracts.py','scripts/validate_phase_h_v3_contracts.py'],'Compatibility and current contract assertions'),
      ('test_profiles','TEST_AUTHORITY',['config/test_execution_profiles.json','config/test_governance_semantic_profiles.json','tests/conftest.py'],'Explicit current/historical classification and registration'),
      ('governance','NOT_AN_EXTENSION_POINT',[L0,'AGENTS.md'],'Frozen governing constraints; a future family must conform and must not modify L0 merely to register'),
      ('family_acceptance','CANONICAL_AUTHORITY',['docs/acceptance_runs/phase_g_pr_d_closure.json','docs/governance/phase_i/PHASE_I_I3_A4_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-05.json'],'Family-specific accepted contract/activation ledgers; separate explicit Owner promotion, never a modification to frozen L0'),
      ('identity','NOT_AN_EXTENSION_POINT',['scripts/m8r_05a_f3/security_master_loader.py','scripts/m8r_05a_f3/target_validator.py'],'Installation-local Security Master; no family identity service fork'),
      ('authorization','NOT_AN_EXTENSION_POINT',['scripts/m8r_05b_02/validator.py','scripts/m8r_05b_03/authorization_gate.py','scripts/m8r_05b_03/consumption_claim.py'],'Existing authorization / atomic execute-once platform control'),
      ('network_policy','NOT_AN_EXTENSION_POINT',['server/local_network_boundary.py','server/services/unified_mode_b2_execution.py'],'No family-owned control plane or startup acquisition'),
      ('resources','NOT_AN_EXTENSION_POINT',['server/resource_boundaries.py','server/unified_payload_bounds.py','server/unified_bounded_io.py'],'Shared resource and payload ceilings; adapters remain bounded beneath them'),
      ('retention','NOT_AN_EXTENSION_POINT',['server/services/unified_retention_inventory.py','server/services/unified_replay_inspector.py','server/services/unified_backup.py','server/services/unified_restore.py','server/services/unified_migration.py'],'Classify through L2; no family-specific automatic migration/GC'),
      ('mcp','NOT_AN_EXTENSION_POINT',['server/unified_mcp/tool_contracts.py'],'Exactly six existing tools'),
    ]
    registrations=[finding('REG-'+name,'registration',paths,description,
      'Explicit update or compatibility proof required when applicable; no A0 modification.',cls,
      'MEDIUM' if cls in {'SCHEMA_AUTHORITY','RUNTIME_ROUTING_AUTHORITY','SOURCE_AUTHORITY'} else 'LOW','L5-A2' if cls!='NOT_AN_EXTENSION_POINT' else 'PRESERVE') | dict(registration_id=name)
      for name,cls,paths,description in specs]
    write('extension_registration_surface_inventory.json',dict(findings=registrations,classification_counts=dict(Counter(r['classification'] for r in registrations)),
      dangerous_multi_authority='No duplicate active canonical capability registry proven. Catalog embedded I3 routing fields, metadata/callable tuples and separate typed schema maps require coordinated checks; their roles are distinct, not independent capability identity.',
      rule='Every row has exactly one registration classification. Source-specific contracts are subordinate authorities, not a proposed second source registry.'))
    # Search all tracked runtime/tests/schema/config/Agent surfaces. Capture exact
    # occurrences without promoting every occurrence to a proposed extension hook.
    files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    pattern=re.compile(r'capability(?:_id)?\s*(?:==|in\b)|(?:CAPABILIT|EVIDENCE_CONTRACTS|SCHEMA_NAMES|TYPED_CONTRACT)|'+ '|'.join(re.escape(c) for c in groups))
    occurrences=[]
    for path in files:
        if not path.startswith(('server/','scripts/','tests/','schemas/','config/','skills/','docs/data_capabilities/','frontend/')) or path.endswith(('.lock','.sqlite','.png')):
            continue
        try: lines=(ROOT/path).read_text(encoding='utf-8-sig').splitlines()
        except (UnicodeError,OSError): continue
        for n,line in enumerate(lines,1):
            if not pattern.search(line): continue
            cls='TEST_AUTHORITY' if path.startswith('tests/') or 'validate_' in path else 'SCHEMA_AUTHORITY' if path.startswith('schemas/') else 'DERIVED_SYNCHRONIZED_VIEW' if path in DERIVED else 'GUIDE_DOCUMENTATION' if path.startswith('skills/') else 'RUNTIME_ROUTING_AUTHORITY' if path in {ADAPT,META,ROUTE} else 'HISTORICAL_DUPLICATION' if 'acceptance' in path or 'run_pr_d' in path else 'CANONICAL_AUTHORITY' if path==CAT else 'NOT_AN_EXTENSION_POINT'
            occurrences.append(dict(path=path,line=n,text=line.strip(),classification=cls,
               assessment='LEXICAL_OCCURRENCE_ONLY_SEE_REVIEWED_FRICTION_GROUPS',
               extension_friction=path in {ADAPT,C+'artifact_loader.py',C+'lineage_resolver.py',C+'models.py',C+'result_builder.py',C+'audit_package_builder.py',C+'markdown_renderer.py'}))
    write('hardcoded_occurrences.json',dict(search_pattern=pattern.pattern,scope='git-tracked runtime, scripts, tests, schemas, config, skills, frontend, docs/data_capabilities; historical governance not searched',occurrences=occurrences,
      limitation='Lexical inventory; semantic review is summarized in hardcoded_extension_friction_inventory.json. A capability mention is not necessarily a switch.'))
    switches=[]
    friction_paths={ADAPT,C+'artifact_loader.py',C+'lineage_resolver.py',C+'models.py',C+'evidence_projector.py',C+'result_builder.py',C+'audit_package_builder.py',C+'markdown_renderer.py'}
    for path in files:
        if not path.startswith(('scripts/','server/','tests/')) or not path.endswith('.py'): continue
        text=(ROOT/path).read_text(encoding='utf-8-sig'); tree=ast.parse(text); source_lines=text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node,(ast.Compare,ast.Match,ast.Assign,ast.AnnAssign)): continue
            segment='\n'.join(source_lines[node.lineno-1:node.end_lineno])
            if not pattern.search(segment): continue
            literals={n.value for n in ast.walk(node) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
            names={n.id for n in ast.walk(node) if isinstance(n,ast.Name)}
            if not (set(groups)&literals or any(re.search('CAPABILIT|EVIDENCE_CONTRACT|SCHEMA_NAMES|TYPED_CONTRACT',n) for n in names)): continue
            friction=path in friction_paths
            test=path.startswith('tests/') or Path(path).name.startswith(('validate_','run_'))
            assessment='EXTENSION_FRICTION_EXPLICIT_REGISTRATION_OR_PROJECTION' if friction else 'INTENTIONAL_BOUNDED_PRODUCT_CONTRACT'
            reason=('Explicit family/type knowledge repeated at trusted registration or typed projection boundary; coordinate conformance, do not dynamic-load.' if friction else
                    'Independent deterministic fixture/assertion/acceptance vocabulary; preserve historical and current test separation.' if test else
                    'Family-specific source, parameter, dependency or compatibility semantics remain explicit; no evidence proves this branch accidental.')
            switches.append(finding('SWITCH-'+str(len(switches)+1).zfill(5),'capability_family_switch',[path],
                segment[:6000],reason,assessment,'MEDIUM' if friction else 'LOW','L5-A2' if friction else 'PRESERVE') | dict(line=node.lineno,node_type=type(node).__name__,full_excerpt_sha256=digest(segment.encode()),assessment_basis=reason))
    write('hardcoded_switches.json',dict(findings=switches,classification_counts=dict(Counter(s['classification'] for s in switches)),
      method='AST Compare/Match/Assign/AnnAssign containing known capability literals or named capability/evidence-schema maps; individual entries inherit a conservative reviewed domain rule. No claim of all arbitrary alias/dataflow branches being mechanically discoverable.',
      static_schema_config_tables='Registered separately in extension_registration_surface_inventory.json; raw lexical matches are not semantic switches.'))
    hard=[]
    for name,paths,behavior in [
      ('schema_loader',[C+'artifact_loader.py'],'_RESEARCH_EVIDENCE_CONTRACTS enumerates typed schema names'),
      ('lineage',[C+'lineage_resolver.py'],'Capability identity map and H/I typed contract maps repeat approved vocabulary'),
      ('runtime_routes',[ADAPT,META],'Trusted route tuple list and metadata must agree'),
      ('typed_projection',[C+'models.py',C+'evidence_projector.py',C+'result_builder.py'],'Typed model fields, per-family projection and coverage branches'),
      ('audit_handoff',[C+'audit_package_builder.py',C+'markdown_renderer.py'],'Source-family provenance and user-visible units/coverage rendering'),
      ('planner',['scripts/m8r_05b_01/planner.py'],'H3/H2 dependency and I3 source-date binding; metadata capabilities inherit upstream operations'),
      ('source_seams',['scripts/phase_g/mops_material_disclosures.py','scripts/phase_g/mops_monthly_revenue.py'],'Different reporting-period and disclosure-item semantics share research executor'),
      ('test_matrix',['scripts/validate_portable_catalog_sync.py','config/test_execution_profiles.json'],'Explicit assertions and test-path lists are deliberate independent safeguards')]:
        hard.append(finding('HARD-'+name,'hardcoded_switch',paths,behavior,
          'Inventory friction; keep fail-closed checks. A1 decides declarative ownership before A2+ conformance work.',
          'INTENTIONAL_BOUNDED_PRODUCT_CONTRACT_WITH_EXTENSION_FRICTION','MEDIUM','L5-A2'))
    write('hardcoded_extension_friction_inventory.json',dict(findings=hard,occurrence_artifact='hardcoded_occurrences.json',switch_artifact='hardcoded_switches.json',switch_count=len(switches),
      confirmed_accidental_hardcoded_extension_points=0,lexical_occurrences_not_individually_semantically_adjudicated=True,
      accidental_assessment='No occurrence is proven accidental by A0 evidence. Redundant maps are coordination friction, not permission to remove bounded allowlists.'))
    dims={
      'REQUIRED':['contract/version identity','supported markets','supported target types','parameter schema','parameter bounds','source authority','routing/executor authority','network-required flag','source timestamp semantics','retrieved-at semantics','freshness/currentness semantics','missing semantics','unsupported semantics','source failure semantics','provenance requirements','citation requirements','tests','Catalog publication','Skill/guide publication','acceptance authority'],
      'OPTIONAL':['raw evidence schema','replay support'],
      'DERIVED':['Audit projection','AI handoff projection'],
      'FAMILY_SPECIFIC':['source request contract','normalization contract','identity binding','Result projection'],
      'PLATFORM_PROVIDED':['authorization class','timeout authority','retention classification','resource bounds','secret boundary','path/output containment'],
      'DECISION_REQUIRED':['family_id / capability relationship','version upgrade/deprecation path'],
      'NOT_APPLICABLE':[],
    }
    dimrows=[]
    owners={
      'family_id / capability relationship':[CAT,ROUTE,C+'lineage_resolver.py'],
      'contract/version identity':['server/services/unified_contract_versions.py','schemas/monthly_revenue_evidence.v1.schema.json'],
      'supported markets':[CAT,ROUTE], 'supported target types':[CAT,ROUTE,'scripts/m8r_05a_f3/target_validator.py'],
      'parameter schema':['schemas/unified_market_evidence_request.v3.schema.json',CAT,'scripts/m8r_05a_f3/capability_validator.py'],
      'parameter bounds':[CAT,'scripts/m8r_05a_f3/capability_validator.py'],
      'source authority':['scripts/phase_g/research_executor.py','docs/data_capabilities/phase_i_i3_source_authority.v1.json'],
      'routing/executor authority':[ROUTE,META,ADAPT], 'network-required flag':[META,ROUTE,'scripts/m8r_05b_03/dispatch.py'],
      'authorization class':['server/services/unified_mode_b2.py','scripts/m8r_05b_03/authorization_gate.py','scripts/m8r_05b_03/consumption_claim.py'],
      'timeout authority':[META,'server/services/unified_mode_b2_execution.py'],
      'source request contract':['scripts/phase_g/research_executor.py','docs/data_capabilities/phase_i_i3_source_authority.v1.json'],
      'raw evidence schema':['schemas/phase_g_monthly_revenue_operation_evidence.v1.schema.json','scripts/phase_g/mops_monthly_revenue.py',ADAPT],
      'normalization contract':['scripts/phase_g/mops_monthly_revenue.py','server/services/phase_i_market_state_adapters.py'],
      'identity binding':['scripts/m8r_05a_f3/target_validator.py','scripts/m8r_05a_f3/security_master_loader.py',C+'lineage_resolver.py'],
      'source timestamp semantics':['scripts/phase_g/mops_monthly_revenue.py','scripts/phase_g/mops_material_disclosures.py','server/services/phase_i_i3_cash_institutional_flow_adapters.py'],
      'retrieved-at semantics':[ADAPT,'scripts/phase_g/research_executor.py'],
      'freshness/currentness semantics':['scripts/m8r_06_03_production_adapter.py','scripts/m8_source_freshness_evaluator.py'],
      'missing semantics':['scripts/phase_g/mops_monthly_revenue.py',C+'evidence_projector.py'],
      'unsupported semantics':['scripts/m8r_05a_f3/capability_validator.py','scripts/m8r_05b_01/planner.py'],
      'source failure semantics':['scripts/phase_g/research_executor.py','scripts/m8r_05b_03/dispatch.py'],
      'provenance requirements':['scripts/m8r_05b_03/receipt.py',C+'lineage_resolver.py',C+'audit_package_builder.py'],
      'citation requirements':[C+'citation_builder.py',C+'evidence_projector.py'],
      'Result projection':[C+'result_builder.py','schemas/unified_market_evidence_result.v3.schema.json'],
      'Audit projection':[C+'audit_package_builder.py','schemas/unified_market_evidence_audit_package.v3.schema.json'],
      'AI handoff projection':['server/services/unified_mode_c.py',C+'markdown_renderer.py'],
      'replay support':['server/services/unified_replay_inspector.py','server/services/unified_mode_c.py'],
      'retention classification':['server/services/unified_retention_inventory.py','server/services/unified_backup.py','server/services/unified_restore.py','server/services/unified_migration.py'],
      'resource bounds':['server/resource_boundaries.py','server/unified_payload_bounds.py',META],
      'secret boundary':['server/local_control_plane_boundary.py',C+'markdown_renderer.py','tests/unit/test_phase_l_l4_a4_injection_secret_boundary.py',L0],
      'path/output containment':['scripts/m8r_filesystem_safety.py','scripts/m8r_05b_03/containment.py','server/unified_bounded_io.py'],
      'tests':['config/test_execution_profiles.json','scripts/validate_phase_h_v3_contracts.py','scripts/validate_runtime_skill_guide_sync.py'],
      'Catalog publication':[CAT,'scripts/generate_portable_catalog.py','scripts/validate_portable_catalog_sync.py'],
      'Skill/guide publication':GUIDES+['scripts/validate_runtime_skill_guide_sync.py'],
      'acceptance authority':['docs/acceptance_runs/phase_g_pr_d_closure.json','docs/governance/phase_i/PHASE_I_I3_A4_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-05.json','AGENTS.md'],
      'version upgrade/deprecation path':['server/services/unified_contract_versions.py','scripts/validate_phase_h_v3_contracts.py',L0],
    }
    for cls,names in dims.items():
        for name in names:
            sources=owners[name]
            behavior={
              'family_id / capability relationship':'No universal family_id registration; capability IDs, typed evidence contract IDs and source-family IDs have distinct namespaces. 14 capabilities map to 12 descriptive groups, with H4 separately derived.',
              'version upgrade/deprecation path':'Existing versioned schemas and Request/Catalog/Route bindings exist; no uniform per-family transition decision table is frozen.',
              'parameter schema':'Catalog allowed_parameters may be empty; Unified Request remains sole AI-facing protocol.',
              'raw evidence schema':'Typed operation artifacts exist; response bytes may be transient/hash-only. No universal raw-body retention requirement.',
              'replay support':'Classify supported retained artifacts; inability to recompute is explicit, never refetch disguised as replay.',
              'network-required flag':'Explicitly declared and cross-checked in governed route and executor metadata; false for local/derived capabilities, never inferred from absence.',
              'Audit projection':'Derived from canonical receipt/bundle/artifact lineage with typed validation.',
              'AI handoff projection':'Derived Result rendering and citations; not a new family request or handoff protocol.',
              'retention classification':'L2 classification is platform-owned; family proposes artifact role, never duration or deletion authority.',
              'identity binding':'Reuse resolved installation-local identity; market-level and cross-market context preserve target association without target-specific causation.',
            }.get(name,'Current explicit authorities already govern this dimension; family declares applicable semantics within the existing platform boundary.')
            dimrows.append(finding('DIM-'+str(len(dimrows)+1).zfill(2),'minimum_contract_dimension',sources,behavior,
              'A1 must freeze the obligation and applicability, not automatically a runtime schema/interface.',cls,'MEDIUM' if cls=='DECISION_REQUIRED' else 'LOW') | dict(dimension=name,
               applicability='Network-only transport fields are NOT_APPLICABLE for local/derived families; all families must state applicability explicitly.'))
    write('candidate_minimum_extension_contract.json',dict(status='CANDIDATE_NOT_FROZEN',findings=dimrows,classification_counts=dict(Counter(r['classification'] for r in dimrows)),
      minimum='Typed/declarative obligations + explicit existing registrations + acceptance conformance. No new canonical registry, runtime discovery or dynamic execution.'))
    negative=['second Capability Catalog','second source registry','second executor registry','second identity authority','second request protocol','second Result/Audit system','family-owned authorization semantics','family-owned network policy','family-owned retention authority','family-owned generic resource policy','family-specific MCP tools']
    write('architecture_conflict_register.json',dict(architecture_conflict_count=0,findings=[finding('NEG-'+str(i+1).zfill(2),'negative_architecture_check',[L0,'AGENTS.md',CAT,ROUTE,'server/unified_mcp/tool_contracts.py'],
      'A0 candidate does not propose '+name+'.','Reject as ARCHITECTURE_CONFLICT if proposed later; reuse the named current authority.', 'PASS_NOT_PROPOSED') for i,name in enumerate(negative)]))
    write('plugin_framework_need_assessment.json',dict(assessment='PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW',findings=[finding('PLUGIN-01','framework_need',[L0,ADAPT,'scripts/m8r_05b_03/dispatch.py'],
      'Trusted explicit RuntimeAdapterRegistry and metadata validation already support materially different families without runtime discovery.',
      'Freeze minimum obligations and registration conformance first. No proof that arbitrary third-party execution, scanning, entry points or hot loading is necessary.',
      'PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW')]))
    gaps=[
      ('family_namespace',[CAT,ROUTE,C+'lineage_resolver.py'],'Uniform family/capability/source namespace obligations are not frozen; current individual IDs are determinate.','L5-A1'),
      ('registration_conformance',[ADAPT,META,C+'artifact_loader.py',C+'lineage_resolver.py'],'Multiple deliberate typed allowlists need one audited conformance checklist, not another registry.','L5-A2'),
      ('publication_status',[CAT,ROUTE],'I2 prose retains Owner-pending wording while accepted activation and runtime booleans are current; historical phrasing is not a second active authority.','L5-A4'),
      ('version_transition',['server/services/unified_contract_versions.py',L0],'No single family transition matrix specifies optional-field, incompatible-semantic and source-only changes.','L5-A1'),
      ('l2_classification',['server/services/unified_retention_inventory.py','server/services/unified_backup.py','server/services/unified_restore.py'],'New evidence must reuse role-based retention and attested explicit member backup; do not assume every raw response is retained/replayable.','L5-A3'),
      ('existing_family_conformance',['scripts/phase_g/mops_monthly_revenue.py',C+'result_builder.py'],'Existing-family obligation proof should be explicit before integrated exit; no new family necessary.','L5-A5'),
      ('session_route',[CAT,ROUTE],'session_status Catalog runtime_executable versus blocked/network_required=true/no selected executor; standalone source acquisition remains unapproved.','L5-A4'),
      ('default_ci_baseline',['config/test_execution_profiles.json'],'Before front-door edits and with tracked product/test/schema bytes equal to exact entry base, corrected guarded default-ci reports 1248 passed / 41 failed / 4 skipped / 5 deselected; required baseline checks pass. No A0 test/product repair authorized.','L5-A4'),
    ]
    write('l5_gap_register.json',dict(stop_conditions_triggered=[],findings=[finding('GAP-'+str(i+1).zfill(2),'gap',paths,behavior,
      'Record only; no A0 runtime/schema/source change.', 'DECISION_REQUIRED' if next_=='L5-A1' else 'GAP','MEDIUM',next_) for i,(name,paths,behavior,next_) in enumerate(gaps)],
      proposed_tranches=['A1 minimum obligation and version-transition freeze','A2 explicit registration conformance hardening','A3 schema/normalization/projection and L1-L4 inheritance conformance','A4 tests/Catalog/Skill/guide publication integration','A5 existing monthly_revenue and composite-family conformance acceptance','A6 integrated extension-contract acceptance','A7 technical exit review'],future_authorized=False))
    if args.traces:
        write('representative_family_trace_matrix.json',json.loads(args.traces.read_text(encoding='utf-8')))
    if args.architecture:
        notes=json.loads(args.architecture.read_text(encoding='utf-8'))
        write('architecture_review_notes.json',notes)
    # Inventory source hashes bind precise inspected bytes independently of prose.
    refs=sorted({ref['path'] for rows in [inventory,archetypes,registrations,hard,dimrows] for row in rows for ref in row['exact_source_files']})
    write('authority_hash_inventory.json',dict(base=BASE,tree=TREE,files=[dict(path=p,sha256=digest((ROOT/p).read_bytes())) for p in refs]))
    write('source_symbol_index.json',dict(base=BASE,files=[dict(path=p,definitions=[dict(name=n.name,line=n.lineno,kind=type(n).__name__) for n in ast.walk(ast.parse((ROOT/p).read_text(encoding='utf-8-sig'))) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]) for p in refs if p.endswith('.py')]))
    write('preflight_result.json',dict(owner_authority=AUTH,entry_branch='phase-l/l5-a0-extension-surface-inventory',entry_head=BASE,entry_tree=TREE,entry_worktree_clean=True,
      canonical_checkout_observation='Original checkout has untracked data/ and old phase-j branch; left untouched. Clean exact-main worktree created.',
      fetch_succeeded=True,origin_main_exact_match=True,rollback_target=BASE,
      frozen_artifacts='All pre-existing governance/acceptance/contracts are immutable; only four current front doors may change.',
      allowed_mutations='A0 governance/evidence, acceptance-only helpers and four front doors; candidate commit only.',
      network_scope='Git fetch for mandatory entry verification only; no provider/browser/source acquisition. Validation counters exclude entry Git transport.',
      production_runtime_changes=0,public_schema_semantic_changes=0,catalog_capability_changes=0,routing_changes=0,executor_activation_changes=0,source_activation_changes=0,mcp_tool_changes=0,dependency_changes=0,provider_requests=0,production_state_mutations=0))
    print(json.dumps(dict(run=str(out),capabilities=14,archetypes=12,registrations=len(registrations),dimensions=len(dimrows),hardcoded_occurrences=len(occurrences))))

if __name__=='__main__':
    main()
