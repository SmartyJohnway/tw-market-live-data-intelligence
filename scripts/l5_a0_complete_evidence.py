"""A0-only deterministic trace/cross-phase/cost evidence authoring."""
from pathlib import Path
import ast
import hashlib
import json
import re
import sys
from l5_a0_inventory import ROOT, CAT, ROUTE, META, ADAPT, L0, C, GUIDES, DERIVED, finding, reference

out=(ROOT/sys.argv[1]).resolve()
out.relative_to(ROOT/'docs/governance/phase_l/acceptance_runs')
def write(name,data):
    (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
notes=json.loads((out/'architecture_review_notes.json').read_text(encoding='utf-8'))
cross=[]
for phase,row in notes['cross_phase_invariants'].items():
    paths=list(dict.fromkeys(re.search(r'(?:server|scripts|docs)/[^ :]+',s).group(0).split('::')[0] for s in row['platform_seams']))
    cross.append(finding('CROSS-'+phase,'cross_phase',paths,
        ' '.join(row['obligations']),
        'Future existing-family conformance must prove inheritance; no second operational, retention, drift or security authority.',
        row['result'],'MEDIUM','L5-A3') | dict(phase=phase,platform_seams=row['platform_seams'],obligations=row['obligations']))
write('cross_phase_invariant_matrix.json',dict(result='COMPATIBLE_WITH_REQUIRED_CONFORMANCE',findings=cross,
    caveat='A0 proves architecture compatibility from current authorities; no future family implementation has been accepted. L3 helper is not a universal production semantic validator.'))
versions=[]
for i,row in enumerate(notes['version_authority_matrix']):
    boundary=row['boundary']
    paths=[L0,'server/services/unified_contract_versions.py','scripts/validate_phase_h_v3_contracts.py']
    if boundary=='Evidence-family schema': paths+=['schemas/monthly_revenue_evidence.v1.schema.json',C+'artifact_loader.py']
    elif boundary=='Capability Catalog': paths+=[CAT]
    elif boundary=='Routing matrix': paths+=[ROUTE]
    elif boundary=='Unified Request': paths+=['schemas/unified_market_evidence_request.v3.schema.json']
    elif boundary=='Unified Result': paths+=['schemas/unified_market_evidence_result.v3.schema.json',C+'result_builder.py']
    elif boundary=='Audit': paths+=['schemas/unified_market_evidence_audit_package.v3.schema.json',C+'audit_package_builder.py']
    elif boundary=='AI handoff': paths+=['server/services/unified_mode_c.py']
    else: paths+=['scripts/phase_g/research_executor.py','docs/data_capabilities/phase_i_i3_source_authority.v1.json']
    versions.append(finding('VER-'+str(i+1).zfill(2),'version_boundary',paths,
        row['current_owner'],row['incompatible_semantics'],'DECISION_REQUIRED' if boundary not in {'AI handoff','Source contract'} else 'EXISTING_AUTHORITY','HIGH','L5-A1') | row)
write('versioning_authority_matrix.json',dict(result='CURRENT_OWNERS_IDENTIFIED_TRANSITION_DECISIONS_REQUIRED',findings=versions,
    rule='No automatic version bump rule or new version system is frozen. Existing immutable hashes/read compatibility constrain any A1 proposal.'))

common={
 'capability_catalog':([CAT],'Catalog owns capability IDs, parameter rules, support/limitations; not activation alone.'),
 'unified_request_validation':(['server/services/unified_mode_a.py','scripts/m8r_05a_f3/request_intake.py','scripts/m8r_05a_f3/capability_validator.py','schemas/unified_market_evidence_request.v3.schema.json'],'Declared Request version and Catalog parameter/market/target validation; Phase G intake has scope checks.'),
 'parameter_validation_bounds':(['scripts/m8r_05a_f3/capability_validator.py',CAT],'Explicit allowed_parameters; unknown keys/type/bounds fail closed. H3 lookback 1..20; remaining current families use empty parameter map.'),
 'target_market_compatibility':(['scripts/m8r_05a_f3/target_validator.py','scripts/m8r_05b_01/planner.py',ROUTE],'Resolve via installation Security Master; route supported markets/type/scope constrain executable universe.'),
 'routing_authority':([ROUTE,'scripts/m8r_05b_01/planner.py'],'Selected route only; optional omissions, required blocks and derived dependencies explicit.'),
 'executor_registry':([META,ADAPT,'scripts/m8r_05b_03/registry.py','scripts/m8r_05b_03/dispatch.py'],'Executor/capability/market tuple binds trusted callable, contract, finite timeout and resource bounds.'),
 'network_authorization':(['server/services/unified_mode_b2.py','server/services/unified_mode_b2_execution.py','scripts/m8r_05b_02/validator.py','scripts/m8r_05b_03/authorization_gate.py','scripts/m8r_05b_03/consumption_claim.py'],'Validation / preview / server-owned explicit authorization / atomic claim / execute once; no startup acquisition.'),
 'identity_binding':(['scripts/m8r_05a_f3/security_master_loader.py','scripts/m8r_05a_f3/target_validator.py','scripts/m8r_05c/lineage_resolver.py'],'ISIN durable cash identity and MARKET:CODE routing; exact source code binding; context association never causation.'),
 'operation_evidence':(['schemas/unified_market_evidence_operation_result.v2.schema.json','scripts/m8r_05b_03/receipt.py','scripts/m8r_05b_03/evidence_aggregation.py'],'Typed evidence artifacts inventoried by receipt/bundle path, size/hash and operation binding.'),
 'result_projection':([C+'artifact_loader.py',C+'lineage_resolver.py',C+'evidence_projector.py',C+'models.py',C+'result_builder.py','schemas/unified_market_evidence_result.v3.schema.json'],'Validate typed artifacts then project existing Result; no independent family Result protocol.'),
 'audit_provenance':([C+'audit_package_builder.py','schemas/unified_market_evidence_audit_package.v3.schema.json'],'Governed lineage is Audit truth; operational diagnostics remain subordinate.'),
 'ai_handoff_citation':([C+'citation_builder.py',C+'markdown_renderer.py','server/services/unified_mode_c.py'],'Verified Result/Audit derives handoff; citation IDs bind operation/artifact; units, coverage and caveats preserved.'),
 'replay_retention':(['server/services/unified_replay_inspector.py','server/services/unified_retention_inventory.py','server/services/unified_backup.py','server/services/unified_restore.py','server/services/unified_migration.py'],'READ_EXISTING != REPLAY != REFETCH; retained normalized artifacts are governed evidence, raw response persistence is source-specific. No migration/GC policy invented.'),
 'test_registration':(['config/test_execution_profiles.json','config/test_governance_semantic_profiles.json'],'Register applicable current deterministic tests and retain historical acceptance separation.'),
 'skill_guide':(GUIDES+DERIVED+['scripts/validate_runtime_skill_guide_sync.py','scripts/validate_portable_catalog_sync.py'],'Publish current capabilities/limits through synchronized existing Skill and guides; portable copy derives Catalog.'),
}
families={
 'material_disclosures':dict(source=['scripts/phase_g/research_executor.py','scripts/phase_g/mops_material_disclosures.py'],schemas=['schemas/phase_g_material_disclosure_operation_evidence.v1.schema.json','schemas/material_disclosure_evidence.v1.schema.json'],normal='Latest completed official daily CSV with governed official JSON fallback; exact company-code rows; timestamp required; item cap/truncation explicit.',time='published_at per item; source_report_date and coverage_through distinct from observed_at. Daily batch is not realtime.',status='available / partial / no_evidence_in_covered_scope / source_failed / binding_failed; parse/encoding/empty errors are failures, not no disclosure.',tests=['tests/unit/test_phase_g_material_disclosures.py','tests/unit/test_phase_g_result_v2_projection.py'],accept=['docs/acceptance_runs/phase_g_pr_d_closure.json']),
 'monthly_revenue':dict(source=['scripts/phase_g/research_executor.py','scripts/phase_g/mops_monthly_revenue.py'],schemas=['schemas/phase_g_monthly_revenue_operation_evidence.v1.schema.json','schemas/monthly_revenue_evidence.v1.schema.json'],normal='Latest available official monthly reporting period; strict CSV structure then governed official JSON fallback; exact company-code binding.',time='reporting_period and source_report_date are separate from observed_at; do not infer publication freshness from retrieval.',status='available / not_yet_available / source_failed / binding_failed; absent revenue is not zero.',tests=['tests/unit/test_phase_g_monthly_revenue.py','tests/unit/test_phase_g_mode_c_v2.py'],accept=['docs/acceptance_runs/phase_g_pr_d_closure.json']),
 'market_observation':dict(source=['scripts/m8r_06_03_production_adapter.py','scripts/m8a_twse_official_eod_adapter.py','scripts/m8a_tpex_official_eod_adapter.py','docs/data_capabilities/m8a_official_eod_endpoint_contract_registry.json','scripts/m5k_common.py'],schemas=['schemas/unified_market_evidence_operation_result.v2.schema.json','scripts/m8r_06_03_production_adapter.py'],normal='current_observation and official_eod_reference share controlled normalized observation/EOD infrastructure, with different projections and currentness rules. m8r_06_03_operation_evidence.v1 is an adapter envelope constant, not a standalone schema file.',time='Exchange/source observation, retrieved_at and official effective trade date are distinct; no unsupported realtime guarantee; calendar closure/freshness inputs governed.',status='Missing reference, source failure, unknown currentness and stale observation remain distinct; official EOD diagnostics preserved.',tests=['tests/unit/test_m8r_06_03_production_adapter.py','tests/unit/test_l3_a2_eod_diagnostic_propagation.py'],accept=['docs/governance/phase_l/PHASE_L_L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_2026-10-15.md']),
 'bounded_historical_reference':dict(source=['server/services/phase_h_h3_twse_stock_day_adapter.py','server/services/phase_h_h3_twse_stock_day_walker.py','server/services/phase_h_h3_twse_governed_end.py','server/services/phase_h_recent_performance.py',ADAPT],schemas=['schemas/recent_performance_evidence.v1.schema.json'],normal='Selected TWSE H3 route only; bounded completed-session lookback 1..20 plus governed end; maximum three unique monthly source requests.',time='Per-row trade_date/retrieved_at; source continuity and governed end binding, not unbounded accumulated history.',status='source_failed / binding_failed / no_evidence_in_covered_scope and insufficient completed observations explicit; H4 prevents ordinary-return interpretation across discontinuity.',tests=['tests/unit/test_phase_h_imp_6_v3_projection_handoff.py'],accept=['docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.json']),
 'market_state_context':dict(source=['docs/data_capabilities/phase_i_i1_source_authority.v1.json','config/phase_i_i1_dormant_source_descriptors.json','server/services/phase_i_i1_production_candidate.py','server/services/phase_i_market_state_adapters.py'],schemas=['schemas/market_state_context_evidence.v1.schema.json'],normal='TWSE FMTQIK plus exact 股票 breadth TWTAZU; TPEx MAINBOARD. Three source contracts compose market context; source units stay native.',time='Independent official dates and retrieved_at; mismatched components yield partial; currentness unknown without separately governed session/calendar input.',status='partial, unavailable, source_failed and binding_failed preserve component provenance; no whole-market breadth fallback or target causation.',tests=['tests/unit/test_phase_i_i1_market_state.py','tests/unit/test_phase_i_i1_production_activation.py'],accept=['docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json']),
 'index_futures_context':dict(source=['docs/data_capabilities/phase_i_i2_source_authority.v1.json','server/services/phase_i_i2_production_transport.py','server/services/phase_i_i2_production_candidate.py','server/services/phase_i_i2_index_futures_adapters.py'],schemas=['schemas/index_futures_context_evidence.v1.schema.json'],normal='TAIFEX TX regular-session standard monthly outright context attached to eligible TWSE cash common shares; excludes weekly/spread/night products.',time='TAIFEX official trade date, retrieval and cash alignment are separate; currentness unknown; no synthetic continuous series.',status='complete / partial / unavailable / source_failed / binding_failed remain explicit; unsupported TPEx target fails closed.',tests=['tests/unit/test_phase_i_i2_a4_activation.py','tests/unit/test_phase_i_i2_production_transport.py'],accept=['docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json']),
 'cash_institutional_flow_context':dict(source=['docs/data_capabilities/phase_i_i3_source_authority.v1.json','server/services/phase_i_i3_cash_institutional_flow_adapters.py','server/services/phase_i_i3_cash_institutional_flow_production_candidate.py'],schemas=['schemas/cash_institutional_flow_context_evidence.v2.schema.json'],normal='TWSE T86 and TPEx 3insti sources; same logical family and normalized V2; batch same-market, at most two mixed-market dispatches; zero retry/raw persistence.',time='TWSE source date bound by governed calendar/currentness before authorization; TPEx source-native observation date remains independent. Retrieval does not prove finality.',status='Source absence, binding failure and failed transport never become zero flow; source-native currentness/finality uncertainty preserved.',tests=['tests/unit/test_phase_i_i3_execution_date.py','tests/unit/test_phase_i_i3_a4_activation.py'],accept=['docs/governance/phase_i/PHASE_I_I3_A4_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-05.json']),
 'trading_status_context':dict(source=['config/phase_h_h1_dormant_source_descriptors.json','server/services/phase_h_h1_tpex_composite.py','server/services/phase_h_trading_status_adapters.py'],schemas=['schemas/trading_status_context_evidence.v1.schema.json','schemas/trading_status_context_evidence.v2.schema.json','schemas/trading_status_context_composite.v1.schema.json'],normal='Selected TPEx composite attention/disposition plus native cmode; cmode unresolved semantics cannot supply canonical changed-method coverage. Legacy attention registry remains distinct from selected composite.',time='Snapshot/source effective dates explicit; partial subtype coverage never implies complete market status.',status='Per-source failures and binding failures; uncovered suspension/resumption/changed-method remain coverage gaps, not negative evidence.',tests=['tests/unit/test_l3_a4_h1_composite_negative_fixture_matrix.py','tests/unit/test_phase_j_b03_a2_6_stage_b_activation.py'],accept=['docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json']),
 'corporate_action_context':dict(source=['config/phase_h_h2_dormant_source_descriptors.json','server/services/phase_h_h2_twse_exright_executor.py','server/services/phase_h_corporate_action_adapters.py'],schemas=['schemas/corporate_action_context_evidence.v1.schema.json','schemas/discontinuity_safety_evidence.v1.schema.json'],normal='Only TWSE TWT48U_ALL pre-announcement selected; explicit same-target H3 dependency and derived H4 discontinuity safety; final TWT49U remains inactive.',time='Lifecycle pre-announcement, event/effective window and retrieval distinct; cannot treat pre-announcement as final entitlement.',status='coverage_incomplete blocks ordinary-return interpretation; capital reduction manual verification and split/consolidation/par changes remain source gaps.',tests=['tests/unit/test_phase_j_b04_a3_h2_executor.py','tests/unit/test_phase_j_b04_a3_end_to_end_projection.py'],accept=['docs/governance/phase_j/PHASE_J_J_B04_A3_NETWORK_FREE_IMPLEMENTATION_ACCEPTANCE_2026-10-08.json','docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.json']),
}
traces=[];cost=[]
for name, row in families.items():
    capability_ids=['current_observation','official_eod_reference'] if name=='market_observation' else ['recent_performance'] if name=='bounded_historical_reference' else [name]
    cells=[]
    for stage,(paths,behavior) in common.items():
        cells.append(finding('TRACE-'+name+'-'+stage,stage,paths,behavior,'Existing shared seam; future conformance must preserve it.','PLATFORM_PROVIDED','LOW','L5-A3'))
    for stage,paths,behavior in [
      ('source_inventory_and_contract',row['source'],'Current selected source authority / constants. Source URLs are observations, not permission to acquire.'),
      ('adapter_source_seam',row['source'],row['normal']),
      ('raw_and_normalized_evidence_contract',row['schemas']+row['source'],'Typed operation/normalized schema; raw HTTP response storage is source-specific, not assumed.'),
      ('normalization',row['source'],row['normal']),
      ('timestamp_semantics',row['source']+row['schemas'],row['time']),
      ('currentness_freshness',row['source']+row['schemas'],row['time']),
      ('missing_unsupported_failure',row['source']+row['schemas'],row['status']),
      ('family_tests',row['tests'],'Existing deterministic family and projection tests; historical acceptance remains separate.'),
      ('acceptance_governance',row['accept'],'Accepted historical stage / current closure; consumed live authority is not rearmed.')]:
        cells.append(finding('TRACE-'+name+'-'+stage,stage,paths,behavior,'Family-specific semantic proof belongs inside the existing Unified pipeline.','FAMILY_SPECIFIC','MEDIUM','L5-A3'))
    traces.append(dict(archetype_id=name,capability_ids=capability_ids,findings=cells))
    # Cost = explicit audited paths/roles, not LOC and not inferred historical patch count.
    canonical=[CAT,'schemas/unified_market_evidence_request.v3.schema.json',
        'schemas/unified_market_evidence_execution_request.v3.schema.json',
        'schemas/unified_market_evidence_result.v3.schema.json',
        'schemas/unified_market_evidence_audit_package.v3.schema.json']+[p for p in row['schemas'] if p.endswith('.schema.json')]
    routing=[ROUTE,META,ADAPT,'docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json']
    runtime=list(dict.fromkeys([p for p in row['source'] if p.endswith('.py')]+[ADAPT,C+'artifact_loader.py',C+'lineage_resolver.py',C+'models.py',C+'evidence_projector.py',C+'result_builder.py',C+'audit_package_builder.py',C+'markdown_renderer.py']))
    docs=GUIDES+['skills/tw-market-evidence-agent/references/current_limitations.md']
    cost.append(finding('COST-'+name,'extension_ergonomics',[CAT,ROUTE,META]+row['source'],
      'Current explicit maintenance surface measured by deduplicated paths and named authority roles.',
      'Counts are a conservative audited minimum, not a promise all files must change or a historical implementation diff.',
      'AUDITED_MINIMUM_TOUCHPOINTS','MEDIUM','L5-A2') | dict(archetype_id=name,
        canonical_registration_points=dict(count=len(set(canonical)),unit='distinct canonical Catalog/public-or-family schema paths',files=sorted(set(canonical))),
        canonical_files=sorted(set(canonical)),runtime_routing_authorities=dict(count=4,files=routing),
        derived_synchronized_files=dict(count=len(DERIVED),files=DERIVED),
        runtime_code_touchpoints=dict(count=len(runtime),files=runtime),
        family_specific_test_files=dict(count=len(row['tests']),files=row['tests']),
        documentation_skill_surfaces=dict(count=len(docs),files=docs),
        governance_acceptance_surfaces=dict(count=len(row['accept']),files=row['accept']),
        source_contract_and_implementation_seams=dict(count=len(row['source']),files=row['source']),
        coordinated_review_path_lower_bound=len(set(canonical+routing+row['source']+row['accept'])),
        independent_registration_responsibilities=dict(count=9,roles=['Catalog capability support','public Request/Result/Audit schemas','subordinate family contract','selected route','planner executor disposition','executor tuple metadata','trusted callable binding','source request/normalization authority','Owner acceptance']),
        role_count_note='Nine independently checked registration responsibilities, not nine independent activation systems. Distinct path count includes implementation and is only coordinated review cost; not all paths must change. Derived/docs/tests are conformance checks, not independent activators.'))
for name in ['identity','source_currentness','evidence_quality','session_status']:
    cells=[]
    summary=('F3 installation-local Security Master identity resolution; contract_supported, no standalone source executor.' if name=='identity' else
      'Upstream metadata projection; contract_supported, deterministic dependency IDs, zero source invocation.' if name!='session_status' else
      'Catalog runtime_executable, actual route BLOCKED, network_required=true, no selected executor; complete authoritative closure evidence not bound by approved executor.')
    for stage,(paths,behavior) in common.items():
        if stage in {'network_authorization','executor_registry','routing_authority'}:
            behavior=summary+' Existing control-plane cannot execute an unselected/blocked route; no new acquisition is implied.'
        elif stage=='result_projection':
            behavior=summary+' Existing envelope projector handles explicit absent/plan-only/failed binding; identity also appears in canonical_identity from F3, not a fabricated successful source operation.'
        elif stage=='parameter_validation_bounds':
            behavior='Catalog declares empty parameters; generic validator rejects unknown keys. No family-owned parameter language.'
        elif stage=='operation_evidence':
            behavior=summary+' No family source artifact is created by A0. Any upstream operation inventory remains bound to its original receipt/bundle.'
        elif stage=='identity_binding':
            behavior='Identity uses verified installation-local F3 authority; metadata and session context cannot create or replace durable identity.'
        elif stage=='target_market_compatibility':
            behavior='identity requires resolved target; metadata/session target_required=false. Catalog/route market declarations and unresolved TAIFEX caveats remain explicit.'
        cells.append(finding('TRACE-'+name+'-'+stage,stage,paths,behavior,'Preserve non-executing/blocked state and canonical shared projection lineage.','PLATFORM_PROVIDED','LOW','L5-A1'))
    special=[
      ('source_inventory_and_contract',[ROUTE,'scripts/m8r_05a_f3/security_master_loader.py'] if name=='identity' else [ROUTE,'scripts/m8r_05b_01/planner.py'] if name!='session_status' else [ROUTE,'scripts/market_clock_session_state.py'],summary),
      ('adapter_source_seam',[ROUTE,META,ADAPT],summary+' No approved standalone adapter to invoke.'),
      ('raw_and_normalized_evidence_contract',['schemas/unified_market_evidence_result.v3.schema.json',C+'evidence_projector.py'],'Existing Result envelope/canonical identity; separate provider-body schema NOT_APPLICABLE to identity/metadata. Session raw artifact NOT_APPLICABLE until governed route exists.'),
      ('normalization',['scripts/m8r_05a_f3/target_validator.py',C+'evidence_projector.py'],'Preserve F3 canonical identity and upstream metadata; no provider normalization introduced. Session computation from supplied evidence is not authoritative closure acquisition.'),
      ('timestamp_semantics',[ROUTE,C+'evidence_projector.py'],'Upstream source/observed/currentness metadata retain original meaning; identity authority release is not a new market observation; session local clock cannot prove official closure.'),
      ('currentness_freshness',[ROUTE,C+'evidence_projector.py'],'No fabricated freshness guarantee. Missing upstream evidence or blocked source status remains explicit.'),
      ('missing_unsupported_failure',['scripts/m8r_05b_01/planner.py',C+'evidence_projector.py'],'Unresolved identity fails closed. Metadata requires upstream operation IDs; blocked session required need blocks plan, optional need may be omitted; never converts source failure to no-evidence.'),
      ('family_tests',['tests/unit/test_m8r_06_02_mode_b1_preview.py','tests/unit/test_m8r_05c_lineage.py'],'Existing planning/lineage deterministic coverage; no standalone network family acceptance claimed.'),
      ('acceptance_governance',[L0,'AGENTS.md',ROUTE],'Current frozen platform constraints and explicit unselected/contract route truth; no independent live acceptance or activation authority exists for these standalone routes.'),
    ]
    for stage,paths,behavior in special:
        cells.append(finding('TRACE-'+name+'-'+stage,stage,paths,behavior,'Explicit NOT_APPLICABLE applies to provider execution where no selected executor exists; preserve the stated current block.','BLOCKED_SOURCE_CONTRACT' if name=='session_status' else 'LOCAL_OR_UPSTREAM_PROJECTION','MEDIUM','L5-A1'))
    traces.append(dict(archetype_id=name,capability_ids=[name],findings=cells))
write('representative_family_trace_matrix.json',dict(source_backed_trace_count=len(families),contract_context_trace_count=4,covered_catalog_capability_count=14,
    stage_count_per_source_backed_trace=len(traces[0]['findings']),findings=traces,
    rule='9 selected source-backed archetype traces (10 capability IDs including current/EOD pair); 4 local/contract/blocked-context traces, all 24 stages. Descriptive grouping is not a new product family registry.'))
write('extension_cost_matrix.json',dict(method='Explicit named authority-role and deduplicated file counts from current conformance traces; conservative lower bound, not LOC or speculative patch count.',findings=cost,
    dangerous_multi_authority='Typed contract maps repeat across loader/lineage/projector/Audit/Markdown and Catalog contains I3 route metadata. Existing distinct role checks prevent independent activation; A2 should prove agreement without deleting independent tests.'))
dims=json.loads((out/'candidate_minimum_extension_contract.json').read_text(encoding='utf-8'))
for dim in dims['findings']:
    dim['cross_phase_obligations']={p:'cross_phase_invariant_matrix.json#CROSS-'+p for p in ('L1','L2','L3','L4')}
write('candidate_minimum_extension_contract.json',dims)
paths=set()
def collect(value):
    if isinstance(value,dict):
        for ref in value.get('exact_source_files',[]): paths.add(ref['path'])
        for v in value.values(): collect(v)
    elif isinstance(value,list):
        for v in value: collect(v)
for file in out.glob('*.json'):
    collect(json.loads(file.read_text(encoding='utf-8')))
write('source_symbol_index.json',dict(base=notes['entry']['head'],files=[dict(path=p,definitions=[dict(name=n.name,line=n.lineno,kind=type(n).__name__) for n in ast.walk(ast.parse((ROOT/p).read_text(encoding='utf-8-sig'))) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]) for p in sorted(paths) if p.endswith('.py')]))
write('authority_hash_inventory.json',dict(base=notes['entry']['head'],tree=notes['entry']['tree'],files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in sorted(paths)]))
print(json.dumps(dict(traces=len(traces),cost_rows=len(cost),versions=len(versions),cross_phases=len(cross))))
