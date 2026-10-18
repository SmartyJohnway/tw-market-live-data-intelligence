# Phase L5-A0 — Evidence-Family Extension Surface Inventory & Minimum Contract Preflight

Date: 2026-10-18 (Asia/Taipei). Status: OWNER-ACCEPTED AND MERGED (PR #380; merge commit `241a5249987c008a28d959677704eee483a1c216`).

Disposition: `L5_A0_EVIDENCE_FAMILY_EXTENSION_SURFACE_INVENTORY_COMPLETE`.

## Authority and exact entry

Owner authority: `USER_CHAT_2026-10-18_PHASE_L_L5_ENTRY_AND_A0_EXTENSION_SURFACE_INVENTORY_AUTHORIZATION`.
Canonical repository: `D:\Codex-Workspace\projects\tw-market-live-data-intelligence`.
After successful `git fetch origin`, origin/main matched exactly:

- HEAD: `4e8aa0557644ac76cca22e67c824ffd0eab7b6c1`.
- Tree: `bc116c15e54502c2bbb62392dd769c3442cd3732`.
- Branch: `phase-l/l5-a0-extension-surface-inventory`.
- Clean entry worktree: `D:\Codex-Workspace\projects\tw-market-live-data-intelligence-phase-l5-a0`.
- Rollback target: the exact entry commit; no persistent product state is changed.

The original checkout's old branch and untracked `data/` were left untouched.
The initial unquoted PowerShell tree expression failed; the quoted revision expression returned the exact required tree. No alternate base was substituted.

Highest L5 architecture authority is the frozen
`PHASE_L_L0_PRODUCTION_BOUNDARY_AND_ARCHITECTURE_CONTRACT_2026-10-13.md`:
define the minimum evidence-family extension contract before considering a plugin framework;
do not add a family merely to prove architecture. L1–L4 accepted closure and current runtime
authorities constrain this inventory. Historical documents remain historical.

Evidence run: [l5-a0-20261018T110810Z](acceptance_runs/l5-a0-20261018T110810Z/).
The timestamp identifies package assembly, not a claimed live acquisition time.

## Current capability and family archetypes

The Catalog contains 14 unique capability IDs. This inventory groups them into **12 descriptive
archetypes**, including three local/metadata/blocked-context groups. These are analytical groupings,
not a new family registry or 12 activated source families. H4 is one additional derived,
non-request-capability contract and is excluded from the 12.

| Capability | Archetype and actual boundary |
|---|---|
| identity | Contract-supported local Identity Service/F3 resolution; no standalone executor |
| current_observation, official_eod_reference | Shared source-backed observation infrastructure, different current/EOD projections |
| session_status | Source-backed context contract: Catalog says runtime_executable, but current route is blocked, network_required=true, with no selected executor |
| recent_performance | Bounded source-backed historical derivation; selected TWSE H3 only, 1..20 sessions |
| source_currentness, evidence_quality | Contract-supported upstream metadata projections, zero source invocation |
| material_disclosures | Official daily disclosure batch; typed items and bounded fallback |
| monthly_revenue | Latest available reporting period; distinct from publication/retrieval dates |
| market_state_context | Three official source contracts compose market context; units/dates remain source-native |
| index_futures_context | TAIFEX TX context associated with TWSE cash targets; source market differs from target market |
| cash_institutional_flow_context | Two market-specific source contracts, one logical family/route, normalized evidence V2 |
| trading_status_context | Selected TPEx attention/disposition/native-cmode composite; incomplete subtype coverage |
| corporate_action_context | Selected TWSE pre-announcement lifecycle context; H3 dependency and derived H4 safety |

`discontinuity_safety` is not a fifteenth requested capability. Catalog support, schema support,
registered callable, and selected route are separate facts. Catalog-wide market support does
not imply every market route executes. The session-status Catalog/blocked-route mismatch is recorded as a publication/
route interpretation gap, not a newly activated route.

There are nine source-backed archetype traces covering ten capability IDs and four local/
contract/context traces covering the remaining IDs. Each source-backed trace records 24 stages,
including source contracts, validation, authorization, evidence, normalization, timing, status,
Result/Audit/citation/handoff, retention and acceptance. See `representative_family_trace_matrix.json`.
`source_symbol_index.json` gives exact Python definitions/lines; `authority_hash_inventory.json`
binds the inspected source bytes. Specific shared seams include `validate_capability`, `build_plan`,
`build_production_runtime_adapter_registry`, `prepare_dispatch`, `dispatch_prepared`,
`load_projection_inputs`, `build_lineage_map`, `build_result`, `build_audit_package`,
`build_citation_index`, and `build_mode_c_ai_handoff`.

## Actual extension pipeline and registration authority

The durable flow still applies:

source inventory → source contract → capability → schema → adapter → normalization →
timing/currentness → Result projection → tests → Skill/guide → acceptance.

Production adds explicit route/executor registration, authorization/execute-once binding,
artifact hashes/lineage, and cross-phase conformance to that flow. Some families share an executor;
some compose several sources; some capabilities have no source execution at all.

The 39 registration-responsibility rows have exactly one classification each:

| Classification | Rows |
|---|---:|
| CANONICAL_AUTHORITY | 2 |
| RUNTIME_ROUTING_AUTHORITY | 5 |
| SCHEMA_AUTHORITY | 12 |
| SOURCE_AUTHORITY | 4 |
| DERIVED_SYNCHRONIZED_VIEW | 1 |
| TEST_AUTHORITY | 3 |
| GUIDE_DOCUMENTATION | 1 |
| HISTORICAL_DUPLICATION | 2 |
| NOT_AN_EXTENSION_POINT | 9 |
| ACCIDENTAL_HARDCODING | 0 confirmed |

Rows represent responsibilities and may enumerate multiple files. They are not interchangeable
independent activation authorities. The current Catalog owns capability support; routing V3 owns
selected routes; executor metadata owns tuple contracts/bounds; the closed callable registry binds
trusted adapters. The planner reuse-disposition inventory is another explicit runtime planning input.
Public/family schemas own shapes; source-specific routes/contracts own acquisition semantics;
Owner acceptance owns promotion. Portable JSON and generated quick guide are synchronized views.

The M4 `docs/source_registry/source_authority_registry.json` and older M8 aggregate registry do
not independently activate current Unified acquisition. Phase G `research_executor.ROUTES`,
official EOD endpoint contracts, Phase H selected executors/descriptors, and Phase I source
authorities must be interpreted with current routing. A0 does not replace these with a second registry.

## Hard-coded switches and extension cost

The lexical scan records 6,541 capability/schema/map mentions across tracked runtime, tests,
schemas, config, skills, frontend and capability documents. This count is not a count of defects. An additional AST inventory records 1,243 switch/map sites: 110 reviewed-domain extension-friction entries and 1,133 conservative bounded-contract entries; arbitrary alias/dataflow discovery is not claimed.
Eight reviewed friction groups cover loader schema maps, lineage maps, runtime route tuples,
typed projections, Audit/handoff, planner dependencies, source seams and test matrices.

Lexical occurrences are not individually semantically adjudicated; the eight reviewed groups
provide the bounded semantic assessment. No switch was proven accidental. Closed allowlists, historical compatibility maps and independent
test assertions can be intentional safeguards. Generic parameter validation, authorization,
identity, citation identity, containment, resource policy and retention policy should remain platform
seams. Disclosure items versus monthly reporting-period semantics, market compositions, source
date alignment and H2/H3/H4 safety are necessarily family-specific.

Cost is a conservative audited path inventory, not LOC, historical patch count, or a guarantee that
every listed file must change for every extension:

| Existing archetype | Catalog/public/family schema paths | Runtime routing inputs | Derived files | Runtime code paths | Named family test files | Guide surfaces | Acceptance surfaces | Coordinated review path lower bound |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| material_disclosures | 7 | 4 | 2 | 10 | 2 | 3 | 1 | 14 |
| monthly_revenue | 7 | 4 | 2 | 10 | 2 | 3 | 1 | 14 |
| observation/EOD | 6 | 4 | 2 | 11 | 2 | 3 | 1 | 15 |
| recent_performance | 6 | 4 | 2 | 12 | 1 | 3 | 1 | 15 |
| market_state_context | 6 | 4 | 2 | 10 | 2 | 3 | 1 | 15 |
| index_futures_context | 6 | 4 | 2 | 11 | 2 | 3 | 1 | 15 |
| institutional flow | 6 | 4 | 2 | 10 | 2 | 3 | 1 | 14 |
| trading status composite | 8 | 4 | 2 | 10 | 2 | 3 | 1 | 16 |
| corporate actions | 7 | 4 | 2 | 10 | 2 | 3 | 2 | 16 |

Exact enumerated paths and counting definitions are in `extension_cost_matrix.json`.
Nine independent registration responsibilities must be reconciled: Catalog support, public schemas,
family contract, selected route, planner disposition, executor metadata, callable binding, source
contract/normalization, and Owner acceptance. The final path-count column includes implementation
files and must not be interpreted as a count of independent canonical authorities. Frozen L0 is
a governing constraint, not a per-family registration file to edit.
The dangerous maintenance risk is disagreement between dispersed typed-contract maps, or between
Catalog embedded I3 routing metadata and selected routing/metadata/callables. No two active
registrations independently claiming the same canonical identity were proven. Preserve existing
fail-closed cross-checks; A2 may propose conformance hardening only after A1 authority decisions.

## Candidate minimum contract — not frozen

All 36 requested dimensions are classified: REQUIRED 20; OPTIONAL 2; DERIVED 2;
FAMILY_SPECIFIC 4; PLATFORM_PROVIDED 6; DECISION_REQUIRED 2; NOT_APPLICABLE 0 as primary classes.
Applicability is explicit per family; transport/rate-limit/removal requirements are not applicable
to purely local/derived evidence. An empty parameter map is a required explicit declaration.

Required obligations cover identity/version, market/target/parameter bounds, source/routing authority,
explicit network declaration, source/retrieval/currentness/missing/unsupported/failure semantics,
provenance/citation, tests, publication and acceptance. Raw response schema/persistence and replay
support are optional capabilities whose absence must be explicit. Normalization, source requests,
identity association and Result content remain family-specific. Audit and handoff derive existing
canonical lineage. Authorization, timeout authority, retention classification, generic resources,
secret policy and output containment remain platform-owned. Families can declare stricter bounded
requirements but cannot invent authorization or generic policy.

Two decisions belong to A1: stable family↔capability relationship/cardinality without a second Catalog,
and version upgrade/deprecation transitions. A0 introduces no family_id schema or runtime interface.

## Cross-phase compatibility and versioning

- L1: reuse trace/request/execution identities, bounded operational events, monotonic adapter/source
  timing, governed failure codes and network-attempt accounting. Audit remains evidence truth.
- L2: classify existing retained evidence for READ_EXISTING/replay separately from refetch; retain
  version/hash/projector dependencies. Backup/restore uses explicit attested members. Unknown
  compatibility remains fail-closed; no automatic migration, retention duration or deletion policy.
- L3: network sources require transport → contract → semantic validation, including encoding,
  empty response, publication delay, rate limit, removal and target/universe checks. The observation
  helper is not a universal production semantic validator or retry policy. Local derivations still
  require semantics/provenance even when transport dimensions do not apply.
- L4: inherit loopback/control-plane boundaries, request/output caps, finite timeouts, contained
  atomic artifacts, disk admission and fail-fast per-process concurrency. Source content remains
  data; secret/dependency/hostile-content review cannot be bypassed by a family adapter.

L1/L2/L3/L4 result: `COMPATIBLE_WITH_REQUIRED_CONFORMANCE`. This is architecture compatibility,
not acceptance of future implementations. Every candidate dimension links to these obligations.

Eight version boundaries are inventoried: family schema, Catalog, route, Unified Request, Result,
Audit, handoff and source contract. Existing V3 Request/Result/Audit exact-hash protection and closed
vocabularies prohibit assuming a same-version optional-field change is harmless. New family/public
fields or incompatible semantics require an explicit version/compatibility decision by existing
schema/contract authorities. Source-only changes can leave normalized family/Result contracts
stable when equivalence is proven; source contract and acceptance still move as needed.
Handoff has no independent per-family version. No new versioning system is introduced.

## Framework assessment, conflicts and gaps

Assessment: `PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW`. Existing explicit trusted registrations and typed
seams cover the observed archetypes. Runtime discovery, entry-point scanning, hot loading and
third-party execution have no demonstrated need and would add L4/L6 obligations prematurely.

All eleven negative architecture checks pass; confirmed architecture conflicts: 0.
No second Catalog/source/executor/identity authority, request protocol, Result/Audit system,
family-owned authorization/network/retention/resource policy or family-specific MCP tool is proposed.

Next-tranche gaps: family namespace/cardinality; immutable-schema version transitions; dispersed
registration/projection knowledge; minimum source-contract fields; explicit L2/L3/L4 conformance;
existing-family acceptance checklist; and stale I2 Owner-pending Catalog prose. The session-status
Catalog-versus-blocked route distinction also needs publication reconciliation. None authorizes
A0 repairs. Historical acceptance tests surfaced by broad regression are recorded separately.

Proposed sequence, **not authorized**:

1. A1 — freeze minimum obligations, applicability, namespace/cardinality and version transitions.
2. A2 — harden explicit registration conformance without discovery or a second authority.
3. A3 — schema, normalization, projection and inherited L1–L4 conformance.
4. A4 — test/Catalog/Skill/guide publication integration.
5. A5 — acceptance using existing monthly_revenue plus a representative composite family.
6. A6 — integrated deterministic extension-contract acceptance.
7. A7 — technical exit review.

## Offline review and acceptance limits

The required supply-chain/environment/pip/source/Catalog/guide/V1/Unified/V3/compile/diff checks
passed. The additional unmodified-main `default-ci` baseline did **not** pass:
1,248 passed, 41 failed, four skipped, five deselected. It ran before front-door edits while all
tracked product/test/schema/config bytes were still the exact entry base. The failures remain
visible; A0 does not claim a green full regression or repair current/historical test governance.

The first acceptance-only audit hook used the getaddrinfo port argument as a host, falsely
recording `11224`; its raw failed run is preserved. The corrected hook rerun recorded zero external
attempts, with the localhost test passing and the other 41 failures remaining. The old raw
`external_socket_attempts=1` is an invalid instrumentation result, not actual provider traffic.
Counters cover guarded Python validation and inherited Python subprocesses, not unrelated OS traffic.
Required entry Git fetch is control-plane repository transport and excluded from market/provider
counters. Provider requests: 0; validation external socket attempts: 0; production state mutations: 0.

`offline_review.json` records the evidence and limitations. The A0 COMPLETE disposition means
the existing path is mapped sufficiently to define A1. It does not freeze the contract, accept
a future family, certify all current regression tests, or constitute Owner acceptance.

## Stop boundary

L4 remains CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`.
L5 is STARTED; L5-A0 is OWNER-ACCEPTED AND MERGED via PR #380 at `241a5249987c008a28d959677704eee483a1c216`.
L5-A1+, L6/L7, Phase M, live acquisition, activation, product/schema/dependency changes and new
evidence families remain unauthorized. No financial_statements, plugin framework or seventh MCP
tool is introduced. L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`. L5-A1+ remains NOT AUTHORIZED.
