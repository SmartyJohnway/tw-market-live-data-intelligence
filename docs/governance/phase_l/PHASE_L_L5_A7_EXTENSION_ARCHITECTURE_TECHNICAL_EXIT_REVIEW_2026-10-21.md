# Phase L5-A7 — Extension Architecture Technical Exit Review (2026-10-21)

**Technical disposition: `PHASE_L_L5_EXIT_REVIEW_PASS`**

**L5 status: TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED**

**Owner final closure: PENDING**

**L6-L7: NOT AUTHORIZED**

**Phase M: NOT AUTHORIZED**

Authority: `USER_CHAT_2026-10-21_PHASE_L_L5_A7_EXTENSION_ARCHITECTURE_TECHNICAL_EXIT_REVIEW_AUTHORIZATION`.

## Reviewed base and scope

The review ran on exact canonical main `d782c91f3066fc5ea77d84ed6a649a4286fad2b7`, tree `fa47f67de8ac8bc3fe574cbcd978b86a9f4c626a`, in a clean isolated worktree and branch `phase-l/l5-a7-extension-architecture-technical-exit-review`. The original checkout, its old Phase J branch, and its untracked `data/` were left untouched.

The highest architecture obligation remains frozen L0: “define the minimum evidence-family extension contract before considering any plugin framework; do not add a new family merely to prove the architecture.” This was a technical exit review only. It did not perform Owner final closure and does not authorize L6, L7, or Phase M.

A0-A6 Owner acceptances and merges were verified as ancestors of the reviewed main, including A6 PR #392 (`7748f18e33a64a912f920c6303f73da67b0ab788`) and its Owner acceptance record through PR #393 (`b7c37d2e6a78c2dce3f446bb118ff6f27f5a6059`). The A6 66-member manifest recomputes to `394ffb64d0e256b5560e1337c0147e3ffd6b7c9614f64e6b659ae2966cacdbb8`; all 66 members match the A6 candidate commit. Its integrated validator, helpers, and tests remain byte-identical to that accepted candidate. Commits after A6 changed only Owner acceptance and four current front doors.

## A0-to-A6 reconciliation

The A0 gap register has eight findings. All have final evidence and no L5 blocker remains. The machine-readable ledger also reconciles all 39 registration responsibilities, all eight bounded friction groups, and all nine negative architecture controls.

| A0 finding | Downstream closure | Final disposition |
| --- | --- | --- |
| GAP-01 family/capability/source namespace and cardinality | A1 contract; A5/A6 identity traces | Closed; namespaces remain distinct, mappings explicit, no universal runtime `family_id` registry |
| GAP-02 dispersed typed allowlists | A2 registration conformance; A3/A6 semantic traces | Closed; 30/30 extension-relevant rows accounted, no new canonical authority |
| GAP-03 Catalog publication prose | A4 publication integration and R1/R2 repairs; A6 publication join | Closed; derived views remain synchronized and non-activating |
| GAP-04 version transition authority | A1 T1-T12 / VER-01..VER-08; A6 integrity check | Closed; transition authority remains with existing owners and bytes are unchanged |
| GAP-05 replay/retention and artifact roles | A3 semantics and L2 platform authorities; A5/A6 inheritance proof | Closed; replay/refetch distinction and retention remain platform-owned |
| GAP-06 existing-family obligation proof | A5 72/72 cells; A6 75-stage / 72-edge integrated traces | Closed by two accepted existing families; no new family required |
| GAP-07 `session_status` blocked route | A4 publication contract; A6 selected-route/publication gates | Closed; Catalog support does not imply a selected executor; route remains blocked and non-executable |
| GAP-08 A0 default-ci baseline semantics | A0-R1 and repeated A5/A6/A7 exact-set comparison | Closed as acceptance semantics; 41 failures remain failing and unresolved, with no candidate-only failures |

A2 classified all 39 surfaces, directly/delegated/structurally validated or deferred semantic/publication checks, preserved nine `NOT_AN_EXTENSION_POINT` controls, and reconciled eight friction groups. A3/A4 closed the assigned deferrals; A5 and A6 exercised the resulting existing path. There are zero unresolved registration rows, zero promoted platform controls, and zero new canonical authorities.

## Frozen A1 contract completeness

Current main retains the exact frozen A1 v1 contract: 36 unique dimensions, 36/36 accounted by A6, no missing dimensions, no unexplained additions, and zero `DECISION_REQUIRED`. The classification counts are 22 REQUIRED, 2 OPTIONAL, 2 DERIVED, 4 FAMILY_SPECIFIC, and 6 PLATFORM_PROVIDED. A5 records explicit applicability for each of the 72 family/dimension cells; omission does not mean N/A.

The contract preserves replay versus refetch, family semantics subordinate to platform policy, and canonical Audit/Handoff derivation from existing lineage authorities. Authorization, retention, timeout, resource, secret, and path-containment policies stay platform-owned. A6 verifies the A1 contract and T1-T12 bytes unchanged. Deprecation remains explicit governance state, not deletion; historical identity and provenance are not rewritten.

## Authority and integrated-path review

Current Catalog support, public and typed schemas, source authority/contracts, selected Routing, planner dispositions, executor metadata and trusted callable bindings, normalization, tests, and Owner acceptance continue to have their existing distinct authorities. Portable Catalog, Quick Guide, Skill, and guides are synchronized derived views. A4 publication validation distinguishes support from executable selected routing; `session_status` remains blocked without a selected executor. No publication surface activates a route.

The A6 current-main acceptance retains one integrated existing-family path:

`Unified Request → validation → plan/preview → explicit authorization → selected route → trusted executor → source contract/transport → normalization → typed evidence → Result → Audit → citation → AI Handoff`.

A6 runs the actual six public MCP tools, retains three deterministic traces (TWSE success, TPEx success, mixed partial failure), and verifies 75 observed stages and 72 connecting edges. Current main has no runtime/product/test/schema/Catalog/route/source/executor/dependency change after the A6 candidate; later commits are Owner acceptance and front-door sync only.

The two accepted representatives, `monthly_revenue` and `material_disclosures`, are sufficient for the minimum L5 contract. A5 accounts for 72/72 family-dimension cells; A6 proves TWSE and TPEx full-success traces and a mixed `partially_failed` path. No third family or `financial_statements` is required.

## Plugin-framework decision

`PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW` remains supported. Explicit trusted registrations, the typed A1 governance contract, existing routing/executor seams, A2-A5 conformance gates, and A6 integrated acceptance cover the current architecture. This does not mean `PLUGIN_FRAMEWORK_NEVER_REQUIRED`; a separately authorized third-party extension or hot-load need would require a new architecture decision. No runtime discovery, entry-point scanning, hot loading, or plugin framework exists.

## Merged-main verification

On the exact review base, the A6 integrated acceptance test passed (35 tests). A1 contract, A2 registration, A3 semantic, A4 publication, A5 existing-family, A6 integrated, dependency, environment, `pip check`, source registry, Portable Catalog, Skill/guide, V1 exact-six, Unified contracts, Phase H V3, and compileall gates all passed. The public MCP surface remains exactly six tools.

The accepted default-ci profile reports **1,248 passed / 41 failed / 4 skipped / 5 deselected**. A7 extracted the exact 41 failed node IDs and compared them with the accepted A6 set: equality is true, candidate-only failures are 0, historical-only failures are 0, and no additional deselection was introduced. The historical failures remain failing and unresolved; no test was weakened, deleted, or reclassified.

Provider requests: 0. Live provider acquisition: 0. Production user-state mutations: 0. Unexpected external socket attempts in A6's declared parent/child instrumentation scope: 0. This is not OS-wide network observation.

The A7 diff contains only this governance record, A7 evidence, and the four authorized current front doors. No new capability/family, public schema change, route/source/executor activation, dependency change, migration, trading behavior, polling, scheduler, background acquisition, or runtime discovery is present.

## Retained non-blocking limitations

Each limitation below has a corresponding machine-readable record in `retained_nonblocking_limitations.json`.

- The 41 accepted default-ci failures remain unresolved. They do not violate L0 because the dedicated A0-A6 extension obligations pass and the set did not grow. Reconsider only when separate Phase H/I/J compatibility repair is authorized.
- Deterministic fixtures do not certify live providers. L0 requires the extension contract and does not require live acquisition to prove architecture. Reconsider under bounded, separately authorized source acceptance.
- A6 substitutes fixture bytes only at its raw transport seam in the acceptance child; it uses the real downstream planner, executor, normalization, Result/Audit, citation, and handoff path. This does not add a runtime hook or violate L0's explicit trusted seam contract. Reconsider if execution architecture changes.
- Registration knowledge remains intentionally explicit and dispersed. A2 checks conformance across 39 responsibilities, while A3-A6 verify semantic and integrated behavior. This does not create competing authority. Reconsider if coordination becomes unsafe or a second canonical claim appears.
- Third-party plugins and hot loading are unsupported now; no current L0 obligation requires them. Reconsider only after an explicit product need and architecture decision.
- Any future family still requires explicit contract conformance and Owner acceptance, as L0 requires. Review per separately authorized family proposal.
- Unified Request V3 remains closed vocabulary: semantic `capability_id` is represented by `data_needs[].type`; no alias is accepted. This preserves the existing single request authority. Reconsider only through a separately authorized public-contract/version decision.
- Publication and guides cannot activate routes; `session_status` support and blocked routing remain distinct. This preserves the explicit authorization boundary. Reconsider if a publication surface gains dispatch authority.
- Historical manifests bind original run bytes; later current files are not passed off as historical bytes. This preserves provenance. Reconsider only if an immutable artifact is proven corrupt or separately authorized reconciliation is required.

## Technical exit conclusion

All fourteen A7 exit criteria pass. A0-A6 are Owner-accepted and merged; all A0 gaps and registration responsibilities have final dispositions; unresolved L5 blockers are zero; A1 is complete at 36/36; no competing extension authority exists; representative families are sufficient; A6 integrated acceptance remains valid on current main; exact-six MCP is preserved; product/runtime authority is unchanged; historical default-ci failures have not expanded; `PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW` remains supported; and retained limitations do not violate frozen L0.

**Technical disposition: `PHASE_L_L5_EXIT_REVIEW_PASS`.** This is a technical exit only. **Owner final closure remains PENDING. L5 is not CLOSED. L6, L7, and Phase M remain NOT AUTHORIZED.** No A8 or other follow-on tranche is created or authorized.
