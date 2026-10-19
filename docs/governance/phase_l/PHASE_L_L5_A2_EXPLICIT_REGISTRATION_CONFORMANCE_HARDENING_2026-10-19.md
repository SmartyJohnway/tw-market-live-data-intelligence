# Phase L5-A2 — Explicit Registration Conformance Hardening (2026-10-19)

Status: **TECHNICAL CONFORMANCE HARDENING COMPLETE / OWNER ACCEPTANCE PENDING**. Candidate disposition: `L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_PASS`.

Owner authority: `USER_CHAT_2026-10-19_PHASE_L_L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_AUTHORIZATION`. Exact entry main and tree: `eba001a1c1c99244e6f3f5c7333d17536f816e12` / `b2fd73c3fdc0969db1b6daa222fe5be4bfe939d0`; A1 merge `8ff92ca79af821a8641967184a26ee37db69d326` is an ancestor. A2 started from a clean worktree on `phase-l/l5-a2-explicit-registration-conformance-hardening`.

## Frozen inputs and scope

A1 technical authority remains `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_TECHNICAL_FREEZE_PASS`, Owner-accepted and merged. Its 36 dimensions, zero `DECISION_REQUIRED`, no universal `family_id` registry, complete T1–T12 matrix, `PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW`, and six-tool MCP surface remain unchanged. A1 run manifest: 32 artifacts, canonical SHA-256 `326d671e069869c3196a8dd9ba4e78525255d954f9b722bc2c3af4d91a3fbe2b`.

A2 adds one offline acceptance validator, its test-only checklist, focused synthetic mismatch tests, governance and evidence. The checklist explicitly is not a runtime registry, capability/source/dispatch authority, or plugin manifest. Current capability, route, source, schema, and callable values continue to be read from existing authorities. No runtime, public schema, Catalog, route, executor/source activation, dependency, request/result/audit semantics, or MCP behavior changes.

## 39 registration rows

A0's 39 rows are reconciled one-for-one against the frozen A1 registration authority matrix. All 30 extension-relevant rows have one and only one A2 disposition; all nine `NOT_AN_EXTENSION_POINT` rows remain negative controls. Disposition counts are recorded in `extension_relevant_coverage.json`: 11 directly validated, 10 delegated to existing deterministic gates, four structurally asserted, three semantic checks deferred to A3, and two publication checks deferred to A4. Unresolved rows: zero. New canonical authorities: zero.

The nine negative controls include identity, authorization, network policy, resources, retention, and the six-tool MCP surface. Promotion count is zero. The two historical duplication rows remain barred from current runtime authority. Their existence cannot answer current capability/source/route identity.

## Eight friction groups

All eight A0 groups retain their intentional bounded-product-contract classification and receive registration-level dispositions: schema loader (direct), lineage (direct), runtime routes (direct), typed projection (A3 semantic deferral), Audit/handoff (A3 semantic deferral), planner (direct), source seams (existing gate delegation plus explicit H/I identity checks), and test matrix (existing synchronization gate delegation). No switch or allowlist is generalized or removed.

## Conformance checks

The acceptance checker validates R1–R9 without becoming a product authority:

- R1: closed Request V3 vocabulary agrees with the canonical Catalog.
- R2: route capabilities exist; selected executor is a declared candidate; plan-only and blocked states do not select an executor.
- R3: route status, selected executor, and planner-facing disposition remain coherent; the existing Unified contract gate is retained.
- R4: selected executor route tuples have executor metadata and a callable materialized by the trusted explicit production registry builder. The known retained non-selected H1 rollback executor is taken from the existing orchestrator disposition; it is not treated as an active selected route.
- R5: typed contract/version references across loader, lineage, projection, Result, Audit and handoff resolve to the existing loader allowlist and local schemas. Transformation and semantic correctness remain A3.
- R6: named current Phase H/I source authorities are inspected; unknown source identities and selected dormant sources fail closed. The existing source registry validator remains delegated for its current scope.
- R7: portable Catalog and runtime Skill are derived views checked by existing synchronization validators.
- R8: historical duplicated inventories are explicitly rejected as current authorities.
- R9: a validator pass never activates a family or route; acceptance remains an Owner/governance boundary.

The checker uses explicit input paths and a trusted local registry builder; it does not scan arbitrary modules/directories, load entry points, invoke adapters, access providers, or write state. It emits deterministic machine-readable JSON and stable failure codes. No A1 semantics or V3 schemas are changed.

## Existing gate delegation and deferrals

`validate_source_registry`, `validate_portable_catalog_sync`, `validate_runtime_skill_guide_sync`, `validate_v1_public_contracts`, `validate_unified_market_evidence_contracts`, and `validate_phase_h_v3_contracts` all passed and are recorded against their existing obligations. A3 owns semantic projection, normalization, and lineage correctness. A4 owns publication/guide integration beyond current sync checks. L6 packaging and L7 CI/release integration remain unauthorized.

## Validation and default-ci baseline

The new validator passed, all ten focused tests passed, and every required dependency/environment/source/catalog/skill/public-contract/Phase-H validator and `compileall` passed. `git diff --check` passed before front-door update; it is rerun after the update.

`default-ci` reported 1,248 passed, 41 failed, four skipped, and five deselected. Its 41 failed test IDs match the accepted A0 entry/candidate set exactly after normalizing one historical captured string by removing the ` - AssertionError...` pytest summary suffix (the A0 evidence parser had included that suffix in one item). Candidate-only failures: zero. These failures remain failures and are not repaired or reclassified. The default-ci profile does not include this newly added focused file; its ten tests were run explicitly.

Provider requests: 0. Live market/source acquisition: 0. Production state mutations: 0. External socket attempts: `NOT_MEASURED`; no OS-wide network observation is claimed.

Disposition: `L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_PASS`. Owner acceptance is pending. L5-A3+ and L6-L7 remain unauthorized.
