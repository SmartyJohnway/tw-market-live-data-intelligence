# Phase K K0 — Lean Compatibility Charter

**Date:** 2026-10-12  
**Status:** Canonical K0 governance charter  
**Product philosophy:** `PORTABILITY_FIRST`; `CORE_INVARIANTS_MINIMAL`; `HOST_BEHAVIOR_FLEXIBLE`; `ACCEPTANCE_MACHINERY_DISPOSABLE`; `USER_EXPERIENCE_SIMPLE`; `VALIDATE_INTEROPERABILITY_NOT_BEHAVIORAL_CONFORMITY`.

> **Validate interoperability, not behavioral conformity.**
>
> 驗證不同 Agent 能否正確使用 TW-Market，而不是要求不同 Agent 表現得一模一樣。

## 1. Phase K goal and product north star

Different AI / Agent hosts should be able to use the same TW-Market canonical contract correctly without requiring host-specific forks of core evidence semantics. Phase K evaluates tool-use correctness, protocol compatibility, evidence interpretation, safety behavior, and transport/host differences. It does not compare investment-advice quality, price-prediction quality, identical reasoning paths, or identical call sequences.

Preserve the Roadmap V3.2 / Phase G–I north star: **AI can quickly obtain enough governed evidence to support the current human–AI conversation.** TW-Market remains official-source-first, target-scoped, bounded, currentness-aware, missing-aware, citation-ready, local-first, auditable, and agent-usable. It is not a broker, trading system, signal engine, prediction engine, general crawler, market-data warehouse, model-certification laboratory, or host-specific AI framework. Phase K makes the existing evidence service easier for different Agents to use; it does not add governance ceremony.

## 2. Minimal product hard invariants

The following are product invariants, distinct from host or harness implementation details:

- Canonical Unified Request / Result / Audit semantics remain authoritative.
- The public MCP surface remains exactly six tools.
- Market and security identity are handled correctly under canonical identity rules.
- Execution is explicit and bounded; governed execution is execute-once.
- Required authorization is respected.
- Missing, partial, and failure remain distinct.
- Currentness is never overstated.
- Citations, provenance, and audit lineage remain truthful.
- There is no silent source fallback or hidden background acquisition.
- Canonical evidence carries no trading recommendation, signal, or broker semantics.
- Local-first semantics are preserved.

Do not add hard invariants without a demonstrated product-contract need.

## 3. Host-flexible behavior

Unless the canonical product contract defines a real precondition, these behaviors may vary by host: whether capability discovery happens first; whether Validate precedes Preview; whether Preview is used for every read-only task; `market_read_result` versus `market_export_ai_handoff` ordering; whether Result or AI Handoff is inspected first; the number of read-only inspection calls; host confirmation UX; transport attachment mechanics; internal planning/reasoning order; exact final-answer wording; whether an adapter is required; and large-result presentation strategy.

Phase J Attempt #6 established a compatibility topic around the sequence `market_read_result -> market_export_ai_handoff`. Acceptance-harness convenience must not promote that sequence into canonical product ordering. If the product contract defines no such precondition, export-first is not a product protocol violation. These are Phase K topics; Phase J remains closed and Attempt #7 is not required.

## 4. Harness governance

> **A test harness may observe or restrict execution for test isolation, but it MUST NOT silently create a new product requirement.**

If a harness is stricter than the canonical product contract, label that restriction `HARNESS_ONLY`. `HARNESS_ONLY` failure is not a product compatibility failure. Any future compatibility validator must distinguish `PRODUCT_DEFECT`, `HOST_LIMITATION`, `ADAPTER_GAP`, `DOCUMENTATION_GAP`, `HARNESS_FAILURE`, and `TEST_INFRASTRUCTURE_FAILURE`; do not collapse them into one FAIL.

## 5. Compatibility outcome taxonomy

- `NATIVE_PASS` — interoperates without a host adapter or special documentation workaround.
- `PASS_WITH_ADAPTER` — interoperates through a documented adapter.
- `PASS_WITH_DOCUMENTATION` — interoperates after a documentation clarification.
- `PARTIAL_HOST_LIMITATION` — core interoperability works with a bounded host limitation.
- `UNSUPPORTED_HOST_CAPABILITY` — the host lacks a capability needed for that scenario; this alone is not a product failure.
- `PRODUCT_COMPATIBILITY_DEFECT` — canonical product behavior violates a supported contract.
- `TEST_INFRASTRUCTURE_FAILURE` — the evaluation infrastructure could not produce a valid result.

A compatibility matrix need not be all green. A host lacking feature X does not by itself mean TW-Market failed.

## 6. No host-specific core fork

When a host has a limitation, prefer, in order: (1) documentation, (2) packaging, (3) adapter, (4) host-specific wrapper, and only then consideration of a canonical product change. A single host must not drive changed canonical Result semantics, a competing request/result contract, a seventh MCP tool, weaker evidence safety, broken local-first semantics, or invented host-specific currentness rules.

## 7. Portability boundary

`local-first` does not mean developer-machine-specific. Product runtime, setup, and user documentation must not depend on `D:\Codex-Workspace`, `C:\Users\<developer>`, a specific Codex installation, Phase J runtime directories, pinned third-party acceptance bundles, or historical attempt folders. Historical evidence may retain original absolute paths. Acceptance infrastructure must be reproducible or disposable.

## 8. User experience boundary

Ordinary users should not need to understand `J1-21`, `Closure-R2`, `R4-R2`, `control_package_id`, `Attempt #N`, exact-head review, authorization SHA, witness proxy, or source invocation delta. The intended mental model is: install, initialize, connect an AI/Agent, and ask a Taiwan-market research question. TW-Market retrieves governed evidence when needed, tells the user its source/date/currentness, discloses missing or partial evidence, and remains bounded.

## 9. Lean future evaluation ceiling

K0 defines scope only; **no host evaluation is executed in K0**. Initial K1/K2 evaluation should target approximately 2–3 meaningfully different hosts, with an evolvable host list and no mandatory vendor. The initial common conformance suite should target approximately 5–8 scenarios, not 27 scenarios multiplied across every agent and execution layer. Select scenarios for semantic coverage, not combinatorial completeness. Suggested future categories are: (1) capability discovery / simple valid request; (2) identity correctness; (3) Preview and authorization boundary; (4) governed Result consumption; (5) stale/currentness interpretation; (6) partial/missing disclosure; (7) Result / AI Handoff interoperability; and (8) one host/transport limitation case.

The only explicit Phase J compatibility carry-forwards are (A) tool-call sequencing differences between hosts and (B) successful host-level AI Handoff consumption/export behavior. Do not reopen Phase J.

## 10. K0 boundary

K0 is governance-only. It performs no real-agent execution, provider/model inference, market/source network request, MCP runtime session, compatibility-harness build, runtime pinning, binary/vendor bundle copy, Security Master mutation, product capability change, public schema change, MCP surface change, or Phase K host evaluation. It does not start K1/K2 or broad multi-agent matrix execution.
