# Phase L5-A1 — Minimum Evidence-Family Extension Contract (2026-10-18)

Status: **TECHNICAL CONTRACT FREEZE COMPLETE / OWNER ACCEPTANCE PENDING**. Disposition: `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_TECHNICAL_FREEZE_PASS`. This document and its companion JSON are governance/architecture authorities only, not runtime registry, public schema, plugin manifest, or activation.

Owner authority: `USER_CHAT_2026-10-18_PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_FREEZE_AUTHORIZATION`. Entry main/tree: `0a1b3bf3b18b009cc8f54c6207a468612d337f9f` / `efacdd6ac413bce4f2238be61344171f7639780e`; branch `phase-l/l5-a1-minimum-extension-contract-freeze` began clean. L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`.

Highest authority is frozen L0, `PHASE_L_L0_PRODUCTION_BOUNDARY_AND_ARCHITECTURE_CONTRACT_2026-10-13.md`: define the minimum family extension contract before considering a plugin framework; do not add a family merely to prove architecture. The accepted flow remains source inventory → source contract → capability → schema → adapter → normalization → timing/currentness → Result projection → tests → Skill/guide → acceptance.

## Identity and cardinality

No universal runtime `family_id` or extension registry is required. “Evidence family” is a conformance concept. Capability/data_need, typed evidence contract, source contract/source authority, executor identity, and routing identity remain separate namespaces with existing owners. Explicit mappings may be N:M: one typed contract may serve multiple capabilities; a capability may compose multiple typed contracts; multiple source contracts may normalize to one stable contract. Each resolved routing context selects exactly one trusted executor; blocked/contract-only contexts may select none. Names never establish mappings. Monthly revenue and material disclosures share the trusted research executor while retaining distinct typed evidence and market source contracts; `market_state_context` composes three source contracts. H4 remains derived, not a request capability. Full identifiers are in the A1 identity evidence.

## Minimum contract

All 36 A0 dimensions are resolved one-for-one: **22 REQUIRED, 2 OPTIONAL, 2 DERIVED, 4 FAMILY_SPECIFIC, 6 PLATFORM_PROVIDED, 0 DECISION_REQUIRED**. Each dimension records applicability, declarer, canonical owner, registration surfaces, version owner, acceptance proof, and a NOT_APPLICABLE rule in [the frozen candidate JSON](PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT.v1.json). No dimensions were dropped or added. Every family declares APPLICABLE or NOT_APPLICABLE with rationale and evidence; omission never implies no network, retention, replay, timeout, authorization, or identity binding. Optional raw evidence and replay must be declared; replay is distinct from refetch. Audit and handoff derive from canonical authorities. Family-specific semantics cannot override platform policy.

The 39 A0 registration responsibilities remain in their existing Catalog, schema, source, routing, executor, planner, callable, test, guide, synchronized-view, and Owner-acceptance surfaces. Intentional cross-checks remain. No new registry or dynamic discovery is introduced.

## Versioning, deprecation, and L1-L4

T1-T12 resolve the eight existing version boundaries. `MUST_MOVE`, `MAY_MOVE`, and `MUST_NOT_MOVE` apply to the named transition only; companion changes invoke their own row. Source-only movement preserves normalized semantics only with proof. Additive optional normalized fields use a new evidence-contract version. Frozen Request V3 remains closed; a new public capability requires explicit Catalog and Request version decisions. Result, Audit, and handoff move only when their public shape or compatibility requires it. No per-family handoff version is added.

Deprecation is explicit governance state, not deletion. Old identity stays bound to old semantics; historic bytes remain readable under declared versions or fail closed. Source deprecation never rewrites provenance. Removal or migration requires separate Owner authorization.

L1 reuses correlation, diagnostics, failure codes, timing and network-attempt accounting. L2 requires artifact roles, READ_EXISTING/replay/refetch distinction, retention classification, backup/restore and migration compatibility; policy stays platform-owned. L3 source-drift obligations apply to network-backed sources; local/derived families explicitly mark transport-only items N/A. L4 security/resource controls remain mandatory, including control-plane boundary, containment, bounded inputs/outputs, hostile-source handling, secrets/dependencies, timeout, concurrency, disk and memory policy. The evidence matrix defines proof; it does not accept future implementations.

## Framework and scope

`PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW`: a typed governance contract, existing explicit registrations, trusted adapter binding, and conformance acceptance cover current evidence. A1 changes governance/evidence only. Runtime, MCP, Catalog capabilities, routing/activations, schemas, Request/Result/Audit semantics, dependencies, and production state do not change. Provider requests: 0; live acquisition: 0; production state mutations: 0. No OS-wide network observation is claimed. Front doors record A0 merged, A1 technical freeze complete / Owner acceptance pending, A2+ and L6-L7 not authorized. A1 PASS does not authorize A2.
