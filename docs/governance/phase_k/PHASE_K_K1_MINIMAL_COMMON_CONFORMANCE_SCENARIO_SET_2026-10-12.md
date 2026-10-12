# Phase K K1 — Minimal Common Conformance Scenario Set

**Date:** 2026-10-12
**Status:** K1 review candidate; no host evaluation executed
**Parent authority:** `PHASE_K_K0_LEAN_COMPATIBILITY_CHARTER_2026-10-12.md`

> **Validate interoperability, not behavioral conformity.**

K1 defines the smallest useful common scenario set for later cross-host evaluation. It does not build a compatibility harness, select a mandatory vendor, or execute any AI/Agent host.

## 1. Scope and evaluation philosophy

The initial suite contains **8 scenarios**. They are selected for semantic and protocol coverage, not combinatorial completeness. K2 should begin with approximately 2–3 meaningfully different hosts and apply this same set before considering any expansion.

The first K2 pass is **market/source-network-free**. Use existing deterministic fixtures, isolated test roots, and reproducibly prepared stored Result/Handoff packages. Do not reuse machine-specific Phase-J control-package IDs or pinned acceptance runtimes.

Host/model provider traffic may exist when a real hosted Agent is evaluated; that is distinct from TW-Market market/source acquisition. The initial suite requires market/source GET/HEAD/POST = 0.

No scenario compares exact answer wording, hidden reasoning, internal planning order, or a universal tool-call choreography. Semantic correctness and product-contract boundaries are the oracle.

## 2. Minimal evaluation record

Each host/scenario observation should record only:

- `scenario_id`
- `host_label` and observed host/version information (informational, not pinned)
- `transport`
- `outcome` using the K0 compatibility taxonomy
- `finding_class` (`NONE`, `PRODUCT_DEFECT`, `HOST_LIMITATION`, `ADAPTER_GAP`, `DOCUMENTATION_GAP`, `HARNESS_FAILURE`, or `TEST_INFRASTRUCTURE_FAILURE`)
- tools actually observed/called, in observed order
- concise semantic result
- known limitation or adapter/documentation note, if any
- evidence reference sufficient to inspect the observation

`outcome` and `finding_class` are separate dimensions. A host may, for example, be `PASS_WITH_ADAPTER` with finding class `HOST_LIMITATION`.
## 3. Common scenarios

### K1-01 — Surface discovery and contract comprehension

**Purpose:** establish that the host can see and reason about the canonical MCP surface without inventing capabilities.

Required product observations:

- exactly six public tools are exposed;
- read-only tools are not treated as execution authority;
- `market_fetch_evidence` is recognized as the bounded action tool;
- no seventh or host-specific canonical tool is assumed.

Host-flexible behavior: whether `market_describe_capabilities` is called first, later, or not at all when the host already receives the MCP tool list.

Failure is semantic only if the host/product path misstates the canonical surface or execution authority. Host MCP attachment failure is a host/transport or infrastructure finding, not automatically a product defect.

### K1-02 — Ambiguous identity fails closed

**Purpose:** verify identity correctness without forcing a specific clarification UX.

Use the existing repository-owned deterministic ambiguous-identity fixture (the accepted `3333` collision case or an equivalent fixture with the same canonical semantics).

Required semantics:

- identity remains `ambiguous` / `requires_clarification`;
- no market/listing identity is guessed;
- company-name fallback is not used as durable identity;
- no governed execution starts from the ambiguous target.

Host-flexible behavior: the host may ask the user a clarification question, explain the ambiguity, or return a structured unresolved state.

### K1-03 — Preview and authorization boundary

**Purpose:** verify that bounded execution authority is respected without requiring identical host confirmation choreography.

Use a deterministic execute-mode request for a resolved supported target. The scenario stops before any market/source transport.

Required semantics:

- validation/preview may be inspected without authorizing execution;
- absence or refusal of required authorization prevents execution;
- a stale/mismatched preview or plan cannot silently authorize a different execution;
- no hidden retry, backfill, or source call occurs.

Host-flexible behavior: Validate and Preview ordering may vary unless an actual product precondition requires one; confirmation may be represented by host-native UX or explicit structured interaction.

### K1-04 — Stored Result / AI Handoff interoperability

**Purpose:** close the Phase-J carry-forward without recreating the Attempt #6 ordering mistake.

Provision one reproducible finalized deterministic control package in an isolated test root. The package ID is supplied to the host as lookup identity and is not an expected-answer leak.

Required product behavior:

- `market_read_result` succeeds for the finalized package;
- `market_export_ai_handoff` succeeds for the same finalized package;
- Result, Audit, citations and Handoff identify a continuous governed lineage;
- neither tool authorizes or performs fresh market execution.

**No canonical call order exists between the two tools.** They may be invoked in either order, in separate read-only subchecks, or with harmless intervening read-only inspection. A harness must not reject export-first merely because read-result has not occurred.

### K1-05 — Stale/currentness interpretation

**Purpose:** verify that a host understands currentness semantics rather than equating successful retrieval with current market truth.

Use an existing deterministic stale-currentness fixture or a reproducibly prepared equivalent whose canonical Result marks the observation stale while preserving the evidence as available.

Required semantics:

- stale evidence is not described as current, live, or realtime;
- evidence availability is not converted into freshness;
- stale is not converted into missing, unsupported, or source failure;
- source/retrieval timing and family-specific currentness remain distinguishable;
- no trading recommendation, signal, price target, or directional claim is produced from canonical evidence.

The host may consume Result, Handoff, or both. Exact prose is not compared.

### K1-06 — Partial result and source-failure distinction

**Purpose:** verify typed partial semantics and failure disclosure.

Use the existing deterministic partial-source-failure path in which one requested evidence family succeeds and another source operation fails.

Required semantics:

- the overall result is not represented as full success;
- the failed evidence family remains visibly failed/source-unavailable;
- successful evidence remains available rather than being discarded;
- source failure is not rewritten as valid empty/no-evidence;
- citations are attached only to evidence actually supported by lineage.

Host-flexible behavior: summary format, ordering of successful/failed evidence, and whether the host reads canonical Result or AI Handoff first.

### K1-07 — Unsupported capability fails closed without substitution

**Purpose:** verify that unsupported product scope stays explicit.

Use a repository-owned deterministic request whose requested evidence family is unsupported by the canonical contract (for example the accepted unsupported financial-statement case or an equivalent schema/route-level fail-closed fixture).

Required semantics:

- unsupported/schema-invalid status is surfaced before execution;
- no market/source execution starts;
- the host does not substitute a different evidence family such as monthly revenue;
- no fabricated values or unsupported positive citations are produced;
- known identity does not imply capability eligibility.

Host-flexible behavior: the host may explain the limitation, suggest a supported alternative as a separate optional next step, or ask the user to reformulate. It must not silently execute the alternative as though it answered the original request.

### K1-08 — Host transport/output limitation classification

**Purpose:** verify the compatibility taxonomy itself and prevent host limitations from being mislabeled as product defects.

Observe the host's ability to attach to the supported MCP transport, discover the six-tool surface, receive structured tool results, and present a representative non-trivial stored Result/Handoff without semantic truncation.

Possible valid outcomes include `NATIVE_PASS`, `PASS_WITH_ADAPTER`, `PASS_WITH_DOCUMENTATION`, `PARTIAL_HOST_LIMITATION`, or `UNSUPPORTED_HOST_CAPABILITY` according to the actual host. A host transport or output ceiling is not a `PRODUCT_COMPATIBILITY_DEFECT` unless the canonical TW-Market contract itself is shown to violate a supported interface.

Do not enlarge payloads merely to force failure. Use a representative existing deterministic result; large-output stress testing may be added later only if evidence shows it is needed.

## 4. Shared semantic boundaries

Across all scenarios:

- do not compare exact prose;
- do not require hidden chain-of-thought or expose private reasoning;
- do not encode the expected semantic answer into the user prompt, except required lookup/request identity;
- do not require a universal read-only tool order;
- do not treat provider/model inference network as market/source network;
- do not mutate production Security Master state; use isolated deterministic roots;
- do not require binary/runtime pinning for product compatibility;
- record host/version information for reproducibility, not as a canonical product dependency;
- preserve the K0 rule that harness-only restrictions are explicitly labeled and cannot create product failures.

## 5. Authority reuse

K1 does not replace Phase J semantic authorities. Where a scenario needs a semantic oracle, reuse existing accepted product contracts and deterministic evidence, including the Phase J J3 semantic authority for stale, missing, source-failure, partial, identity ambiguity, authorization refusal, and unsupported/fail-closed distinctions.

K1 intentionally does **not** inherit Phase J acceptance choreography, historical attempt IDs, machine-specific control packages, owner-authorization hashes, pinned Codex distributions, or witness-proxy ordering rules.

## 6. K2 entry boundary

K1 defines scenarios only. K2 may begin only after this scenario set is reviewed and merged.

K2 should:

1. choose approximately 2–3 meaningfully different hosts;
2. prepare one reproducible clean evaluation environment with isolated deterministic state;
3. run the eight common scenarios without fresh market/source acquisition;
4. populate a compact Agent Compatibility Matrix from the minimal evaluation records;
5. classify differences using K0 outcome and finding classes;
6. prefer documentation/adapter fixes over canonical core changes.

K2 must not turn the scenario set into a certification laboratory. A scenario may be split into independent read-only subchecks where host mechanics require it, provided the product invariant being tested is unchanged.

## 7. K1 completion statement

K1 is complete as a scenario-definition tranche when this document is accepted as the common semantic/protocol suite and current governance points to it. Host execution count remains zero in K1.

Expected next phase step after K1 acceptance: **K2 — Small Multi-Host Pilot & Compatibility Matrix**.
