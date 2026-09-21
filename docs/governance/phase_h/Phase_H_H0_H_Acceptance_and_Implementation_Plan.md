# Phase H H0-H Acceptance and Implementation Plan

Status: `OWNER_ACCEPTED / FROZEN`

Owner acceptance date: `2026-09-21`
Accepted amendments: `A1, A2`
Planning blockers: `0`

Baseline: `dcafdfd756c6c32f138690d33900c59b0786ff7e`

This document plans later work. It does not authorize production implementation, source activation, bounded live network use, licensed-provider integration, preferred-version promotion, or release.

## 1. Authority and product boundary

The immutable authority is the complete H0-A through H0-G set under `docs/governance/phase_h/`, the exact V3 schemas, Catalog V3, and Routing Matrix V3. Where older roadmap language differs, frozen authority wins.

Phase H supplies interpretation-safety evidence. Every later execution remains explicit, target-scoped, data-need-scoped, time-bounded, authorized, execute-once, and auditable. It does not create a historical database, corporate-action warehouse, adjusted-price engine, technical-analysis engine, scheduler, polling loop, background refresh, automatic backfill, recommendation engine, or seventh MCP tool.

Four states remain independent:

1. contract support;
2. source authority;
3. runtime implementation;
4. runtime activation.

At this planning baseline, V3 contracts exist, V2 is preferred, V3 runtime is inactive, Phase H active source count is zero, and the MCP surface contains exactly six tools.

## 2. Existing architecture to reuse

Later implementation should extend the existing Phase G path rather than create a parallel runtime:

`Mode A intake and explicit schema dispatch → F3 identity resolution → 05B-01 planner → 05B-02 authorization and consumption binding → 05B-03 route-aware registry and execute-once dispatch → 05C Result/Audit/Markdown projection → Local Service → existing six MCP tools`.

The Orchestration Plan, Authorization, Consumption Binding, Execution Request, Operation Result, Receipt, and Bundle stay at their truthful versions unless a separately reviewed incompatibility proves a version change is necessary. Phase H uses the existing installation-local Taiwan Market Identity Service and exact market plus security-code binding. It does not introduce fuzzy company-name binding or another security master.

## 3. Dependency DAG

```text
H0-G frozen authority
        +--> H-IMP-0 passive V3 compatibility
                    +--> H-IMP-1 H4 fixture-only component
                    +--> H-IMP-2 H1 dormant executor --+
                    +--> H-IMP-3 H2 dormant executor --+--> with H-IMP-6 --> H-ACT-H1/H2
                    +--> H-IMP-6 V3 projection/handoff -+

H0-G frozen authority --> H3-R --> H3-I --+
H-IMP-0 -----------------------> H-IMP-6 --+--> H-ACT-H3

H-IMP-1 + H-IMP-6 + one dormant implemented slice
        --> H-IMP-7D deterministic selected-slice E2E (zero network)
        --> H-ACT-H1/H2/H3 route-level bounded-live, rollback and activation
        --> H-ACC-7L selected-product live E2E (active routes only)
        --> H-ACT-V3
```

`H-IMP-1`, fixture construction, and V3 projection scaffolding may proceed in parallel after H-IMP-0 design interfaces are fixed. `H3-I` cannot begin before H3-R produces an Owner-accepted source-authority decision. Source activation and V3 preferred promotion are separate gates.

## 4. Tranches and recommended order

### H-IMP-0 — Passive V3 compatibility

Add explicit V3 schema dispatch, validation, preview representation, and test-only Result/Audit plumbing while keeping V2 preferred. A V3 request whose Phase H route is inactive must fail closed or preview as blocked/plan-only. No source, executor, Local Service current authority, or MCP behavior is activated.

Exit requires V1/V2 regression, valid/invalid V3 request tests, truthful inactive preview, six-tool snapshot, no startup network, and byte-preserved historical V1/V2 artifacts.

### H-IMP-1 — H4 deterministic component

Implement `discontinuity_safety_evidence.v1` as a pure zero-network function against frozen fixtures. This can precede source activation because component readiness differs from production interpretability readiness. Missing, failed, ambiguous, unsupported, or misaligned upstream evidence must yield `coverage_incomplete`.

`no_material_discontinuity_detected` is legal only when the complete relevant declared H2 scope for the exact H3 comparison window was successfully retrieved, source-contract validated, exactly bound, has no failed or uncovered relevant source family/subtype, revision state is sufficiently resolved, and no effective relevant event exists in the window. All other cases block ordinary interpretation.

### H-IMP-2 — H1 dormant executor and adapters

Implement source-specific normalization, exact binding, lifecycle representation, coverage accounting, source drift failure, normalized evidence, fixtures, and dormant registry descriptors. Do not recompute exchange surveillance decisions.

The first activation candidate is `H1-TPEX-ATTENTION-OPENAPI`: official structured JSON, verified ODGL authority, daily current snapshot, and exact `SecuritiesCompanyCode` binding. It may activate only as an explicitly partial H1 route. With only this route active, the full five-type declared H1 scope is not complete, so target absence cannot become `no_evidence_in_covered_scope` for the whole H1 capability.

Next eligible routes are TPEx disposition, TPEx changed-trading, TWSE changed-trading, and the governed TPEx suspension history fallback. TWSE attention/disposition/suspension and TPEx current suspension remain blocked from activation until their exact license mappings close. H1 lifecycle completeness issue `H0-SRC-02` continues to constrain completeness claims.

### H-ACT-H1 — H1 route-by-route activation

Each route independently passes source authority, transport, license, exact binding, normalization, source-drift, no-row, currentness, fixture, Owner-authorized bounded-live probe, rollback rehearsal, and Owner activation approval. The bounded-live probe occurs while the route remains inactive or eligible; it is source-activation evidence, not product E2E. There is no bulk “activate H1” action. Catalog and Route state must expose the exact active subset.

### H-IMP-3 — H2 dormant executor and adapters

Implement separate preannouncement and official-final lanes, source-specific normalization, exact binding, blank/zero/not-announced distinction, revision uncertainty, coverage accounting, and dormant descriptors.

The safest first activation candidate is the paired TPEx structured routes:

- `H2-TPEX-EXRIGHT-PRE-OPENAPI` (`tpex_exright_prepost`);
- `H2-TPEX-EXRIGHT-FINAL-OPENAPI` (`tpex_exright_daily`).

Both are official, structured, free ODGL sources and preserve the distinction between preannouncement and final official reference. The pairing does not authorize inferred correction or supersession links. `H0-SRC-03` keeps revision/cancellation completeness constrained.

TWSE `TWT48U_ALL` is a later eligible preannouncement route. TWSE `TWT49U` remains optional and inactive until provider contract, licensing, credentials/configuration, portable absence behavior, and bounded-live evidence are separately approved. Capital-reduction browser exports remain manual verification. Par-value/split/reverse-split/share-consolidation source gaps remain blocked and visible.

### H-ACT-H2 — H2 route-by-route activation

Apply the same per-route gates as H1. Unsupported relevant subtypes remain in `uncovered_event_subtypes`; source absence never narrows applicability. Incomplete coverage forces H4 `coverage_incomplete`.

### H3-R — Bounded-history source resolution

Research `H0-SRC-09` through `H0-SRC-12` in a separately authorized, bounded research tranche. For TWSE and TPEx determine official machine-readable availability, one-shot bounded retrieval, fresh-install behavior, license/authentication, date depth, exact target binding, completed-session semantics, full-session volume semantics, rate/size limits, and portability. Local accumulation is not a fallback.

The research output is an Owner-reviewed source-authority decision. Until then, `recent_performance` remains contract-supported, runtime-inactive, and blocked.

### H3-I — H3 dormant implementation

Only after H3-R approval, implement bounded request-time acquisition for 1–20 sessions. Preserve governed end observation, exact N-th prior completed-session endpoint, N+1 distinct closes, baseline-specific proof, completed-session range and volume, temporal alignment, raw unadjusted return, and partial/insufficient/unavailable distinctions. Durable OHLCV accumulation is forbidden.

### H-ACT-H3 — H3 source/capability activation

H3 activation is distinct from V3 preferred-version promotion. Each approved TWSE or TPEx default/optional-provider route independently passes its source, transport, license, binding, session, volume, portability, fixture, bounded-live, and Owner gates. An activated H3 route may serve explicit V3 requests while V2 remains preferred. If no route passes, H3 remains blocked without preventing truthful H1/H2 incremental activation.

### H-IMP-6 — Result V3, Audit V3, and AI handoff

Extend existing 05C version-aware projection. Result V3 deterministically embeds H1/H2/H3/H4 typed evidence without fabricating success for unexecuted routes. Audit V3 records attempts, source role, activation state, provider/license state, target binding, requested window, coverage, failures, canonical relative artifact references, H4 inputs, rule version, derived state, and interpretation guard. Existing V1/V2 read/verify paths remain byte-preserving.

H5 is a deterministic composition/projection layer over current quote, H1, H2, H3, H4, and caveats. It is not a request data need, source, executor, opinion engine, or new MCP tool. It may expose facts and guards; it may not emit buy/sell/hold, sentiment, target price, signal, or causal claims.

### H-IMP-7D — Deterministic selected-slice E2E

Run network-free fixture E2E for one dormant implemented H1, H2, or H3 slice. It proves multi-target mixed success, inactive/partial routes, Result/Audit/AI handoff, rollback-model simulation, V2 unaffected behavior, authorization lineage, execute-once control, and zero startup execution. It neither activates a route nor uses external network.

### H-ACC-7L — Selected-product bounded-live E2E

After at least one route has independently completed its H-ACT-Hx route-level live and rollback proof and is Owner-approved active, run one separately Owner-authorized selected-product-slice live E2E. It uses only already approved active routes and records exact request, result, audit, handoff, transport, call bound, network declaration, and rollback evidence. No broad crawling, retry storm, full-market scan, or persistence is permitted.

### H-ACT-V3 — Controlled preferred-version promotion

This is independent of code completion and capability activation. Entry requires `H-IMP-7D` and `H-ACC-7L`, V1/V2 backward compatibility, V3 validation/preview/authorization, Result/Audit/AI handoff validation, clean citation/lineage, fail-closed error and partial/no-evidence semantics, source-role/activation-state integrity, six-tool and V2 regressions, fresh-install behavior, and verified rollback. Owner approval is mandatory.

## 5. Incremental activation rule

Incremental activation is allowed. A truthful state such as “H1 executable subset; H2 partial; H3 unavailable; H4 coverage incomplete” is valid. It is allowed only when Catalog, Routing, preview, Result, Audit, and handoff expose the same exact route/capability state; unsupported subtypes remain visible; and H4 cannot emit the no-discontinuity state without complete relevant coverage.

Capability and route state transitions remain explicit:

`CONTRACT_FROZEN → SOURCE_AUTHORITY_READY → EXECUTOR_IMPLEMENTED → UNIT_ACCEPTANCE_PASS → INTEGRATION_ACCEPTANCE_PASS → BOUNDED_LIVE_ACCEPTANCE_PASS (when applicable) → OWNER_ACTIVATION_APPROVED → RUNTIME_ACTIVE`.

No transition implies another.

## 6. Source-gate inventory

| Route set | Current class | Blocking/open gates | Planned disposition |
|---|---|---|---|
| TPEx H1 attention/disposition/changed trading | `READY_FOR_ADAPTER_IMPLEMENTATION` | lifecycle completeness `H0-SRC-02` limits full-scope claims | implement dormant; activate individually after bounded-live and Owner approval |
| TWSE H1 changed trading | `READY_FOR_ADAPTER_IMPLEMENTATION` | `H0-SRC-02` limits completeness | implement dormant; route-specific activation |
| TPEx H1 suspension history fallback | `READY_FOR_ADAPTER_IMPLEMENTATION` as governed fallback | `H0-SRC-02`; not arbitrary bounded history | preserve fallback role; do not promote to universal history |
| TWSE attention/disposition/suspension | `REQUIRES_SOURCE_CONTRACT_PREFLIGHT` | `H0-SRC-01A/B/C` | close exact license mapping before activation |
| TPEx current suspension | `REQUIRES_SOURCE_CONTRACT_PREFLIGHT` | `H0-SRC-01E` | close exact license mapping before activation |
| TPEx H2 pre/final and TWSE pre | `READY_FOR_ADAPTER_IMPLEMENTATION` | `H0-SRC-03` limits revision completeness | implement separately by lifecycle stage |
| TWSE TWT49U final | `REQUIRES_AUTOMATION_RESEARCH` / optional licensed | `H0-SRC-04` | separate provider/Owner gate; portable installation works without it |
| TWSE/TPEx capital reduction browser CSV | `MANUAL_ONLY` | `H0-SRC-05/06` | no scraper task; manual evidence only |
| TWSE/TPEx par/split/consolidation | `BLOCKED` | `H0-SRC-07/08` | retain uncovered/source-gap state |
| TWSE/TPEx bounded recent history | `BLOCKED` pending research | `H0-SRC-09/10/11/12` | H3-R before H3-I |

Every row above expands to individual route activation records in `PHASE_H_H0_H_IMPLEMENTATION_GATE_MATRIX.json`; an open issue for one route does not block an unrelated eligible route. Aggregate `capability_open_issue_ids` are informational only. The selected route's `route_activation_blocker_issue_ids`, its common prerequisites, and the global H-ACT acceptance rules are the activation authority. `H0-SRC-02` and `H0-SRC-03` constrain complete coverage claims but do not, by themselves, block eligible route activation.

## 7. Promotion ladder

| Stage | Meaning | Required proof | Runtime effect |
|---|---|---|---|
| P0 | frozen contracts only | H0-G integrity | none |
| P1 | passive V3 validation | H-IMP-0 acceptance | V2 still preferred; no Phase H execution |
| P2 | dormant components | unit/component fixtures for H1/H2/H3/H4/projection | all Phase H routes inactive |
| P3 | selected routes eligible | per-route authority and implementation gates | eligible, not active |
| P4 | selected routes active for explicit V3 requests | per-route bounded live + rollback + Owner activation | exact subset active; V2 preferred |
| P5 | deterministic then bounded-live selected-slice V3 E2E | H-IMP-7D then H-ACC-7L, Result/Audit/handoff, failure, rollback and compatibility evidence | promotion candidate |
| P6 | V3 preferred promotion | independent Owner H-ACT-V3 approval | V3 preferred; V2 rollback retained |

Each stage is reversible. Eligibility, activation, E2E completion, preferred-version promotion, and release remain separate decisions.

## 8. Critical path and parallel work

The critical path for a minimally useful product slice is H-IMP-0 → H-IMP-6 and one approved H1 or H2 dormant adapter in parallel → H-IMP-7D → its route-level H-ACT-Hx bounded-live, rollback, and Owner activation → H-ACC-7L → H-ACT-V3. H3 has its own longer path, H3-R → H3-I → H-IMP-7D → H-ACT-H3 → H-ACC-7L, because no default bounded machine source is proven. Full H2 interpretation coverage additionally remains constrained by `H0-SRC-05` through `08`, and optional TWSE final reference by `H0-SRC-04`.

After H-IMP-0 fixes passive V3 interfaces, non-critical work that may proceed in parallel without activation includes H4 fixture-only logic, V3 projector/Audit scaffolding, dormant H1/H2 adapters, official-shaped fixtures, and AI handoff design. H3-R may also proceed under its separate Owner research authorization. Parallel work must share frozen schema interfaces and may not perform live network calls unless H3-R has explicit bounded-probe approval.

## 9. Portability dependency record

| Dependency | Fresh install | Optional | Licensed / credentialed | Manual | Portable default |
|---|---|---|---|---|---|
| V3 schemas/catalog/routing | required | no | no | no | bundled, inactive |
| eligible TWSE/TPEx official OpenAPI routes | network needed only on explicit execution | route may be inactive | free ODGL where verified; no credentials | no | installation remains valid offline; execution fails closed |
| unresolved-license H1 routes | no | yes | license mapping unresolved | no | inactive |
| TWT49U | no | yes | licensed and credential/config dependent | no | provider_unavailable; installation valid |
| capital-reduction browser exports | no | yes | official human surface | yes | no automated route |
| par/split/consolidation source gaps | no | yes | unresolved | no | blocked/uncovered |
| H3 free bounded route | no until H3-R proves it | yes | unresolved | browser history is manual only | H3 blocked |
| H3 optional provider | no | yes | licensed/credentialed | no | provider_unavailable; no local accumulation |
| H4 component | required when projected | no | no | no | zero-network derived evidence |
| V1/V2 historical readers | required | no | no | no | retained unchanged |

## 10. Test and fixture architecture

- Unit contract tests: exact schema branches, arithmetic, coverage sets, lifecycle, path grammar, and derived-state truth tables.
- Component tests: official-source-shaped fixtures per route, exact binding, normalization, no-row, malformed source, source drift, and attempt provenance.
- Zero-network integration: intake through Result/Audit/Markdown using injected fixtures and isolated artifact roots.
- V3 deterministic E2E: multi-target mixed success, inactive routes, partial support, citation graph, canonical paths, and historical V1/V2 immutability.
- Bounded live acceptance: separate non-default profile; explicit Owner approval and call cap.
- Regression: V1/V2, six MCP tools, authorization/consumption, execute-once, containment, no startup network, and no persistence creep.

Default CI stays network-free. Fixtures are test snapshots, never runtime authority.

## 11. Evidence and acceptance rules

No prose-only PASS is valid for promotion. Each PASS record must include requirement/test ID, fixture or live target, request/result/audit hashes, source contract, code commit, schema hashes, timestamp, and network declaration. Live evidence additionally records authorization, transport, attempts/fallback, call count, and target-bounded artifacts.

No-row may become no-evidence only after the complete declared governed scope was retrieved, source-contract validated, and searched by exact target identity. Partial coverage, unsupported subtype, source failure, and binding failure remain distinct.

## 12. Rollback model

- Source route rollback: `active → inactive`; planner/preview reports the route unavailable or plan-only. Preserve governed artifacts.
- Capability rollback: `runtime_executable → contract_supported/plan_only`; other active capabilities remain unaffected.
- Preferred-version rollback: V3 preferred returns to V2 preferred while V1/V2/V3 historical packages remain readable and immutable. New V3 execution fails closed or is disabled; stored V3 evidence is never rewritten to V2.

Rollback triggers include source-schema drift, binding ambiguity, changed no-row semantics, missing license/config, schema-validation failure, Audit lineage failure, inconsistent H4 state, unsafe path, unexpected network behavior, V2 regression, or MCP regression. No rollback silently substitutes an unofficial source.

## 13. Owner stop gates

An implementing agent must stop for explicit Owner approval before:

1. conducting H3 external source research;
2. activating any source route;
3. executing any bounded-live network test;
4. integrating or configuring a licensed provider;
5. promoting V3 to preferred request/result authority;
6. publishing a production release.

H3-R research also requires its own authorization because it investigates external sources. Passing fixture tests does not authorize any of these gates.

## 14. Completion and release boundary

Phase H may be marked complete when an Owner-approved governed V3 product slice runs end-to-end with truthful partial/source-gap reporting, H4 fail-closed interpretation safety, Result/Audit/AI handoff evidence, V1/V2 compatibility, six MCP tools, fresh-install portability, bounded live proof for every active route, and verified rollback. Optional licensed or unresolved subtypes need not all be solved if they remain explicitly unsupported and cannot enable false-complete interpretation.

Implementation completion does not itself authorize a public release. Release readiness separately requires documentation truthfulness, portable installation, security and MCP regression, release manifest/evidence, and Owner release approval. No version number is selected here.

## 15. Current non-mutation declaration

- preferred request authority: V2;
- V3 runtime: inactive;
- Phase H active sources: 0;
- MCP tools: 6;
- production/runtime/source activation changes in H0-H: none.
