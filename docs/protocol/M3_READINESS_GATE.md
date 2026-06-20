# M3 Readiness Gate

This document serves as the formal readiness gate evaluation following the completion of the M2 milestone series. It assesses whether the repository is adequately prepared to begin **M3-01-AI-MARKET-CONTEXT-PACK-DESIGN**.

## Readiness Decision Table

| Criteria | Status | Notes |
| :--- | :--- | :--- |
| **1. Source contracts exist** | Pass | Consolidated in `M2_SOURCE_CONTRACT_BASELINE.md`. |
| **2. Official vs unofficial semantics are clear** | Pass | Clear distinctions made between TWSE/TPEx OpenAPI, MIS, and third parties. |
| **3. EOD vs delayed/live semantics are clear** | Pass | Baseline reports accurately capture limitations of each freshness class. |
| **4. Target taxonomy exists** | Pass | Available in `docs/protocol/TARGET_TAXONOMY.md`. |
| **5. Symbol format registry exists** | Pass | Available in `docs/protocol/SYMBOL_FORMAT_REGISTRY.md`. |
| **6. Source-target support matrix exists** | Pass | Defined in `docs/protocol/SOURCE_TARGET_SUPPORT_MATRIX.md`. |
| **7. Support status semantics exist** | Pass | Explicit states defined in `docs/protocol/SUPPORT_STATUS_SEMANTICS.md`. |
| **8. Normalized schema inventory exists** | Pass | Captured in `docs/protocol/M2_NORMALIZED_SCHEMA_INVENTORY.md`. |
| **9. Generated reports are compatible** | Pass | Validated offline. Report format supports current schemas. |
| **10. AI unsafe uses explicitly prohibited** | Pass | Documented prohibitions against trading signals and high-frequency polling. |
| **11. Runtime config schema migration not required for M3 design** | Pass | M3-01 is design-only and relies on existing generated outputs, negating immediate need for `market_targets.json` migration. |
| **12. Production ingestion not required for M3 design** | Pass | M3-01 uses static context generation without continuous loops. |

## M3 Readiness Decision

**Decision:** `READY_FOR_M3_DESIGN_WITH_CAVEATS`

The repository successfully established a stable source-contract baseline and taxonomy during M2. Because M3-01 focuses purely on the *design* of the AI-readable context pack utilizing the current reports, the existing `config/market_targets.json` does not pose a blocker.

### Recommended Next Milestone
The recommended next milestone is:
`M3-01-AI-MARKET-CONTEXT-PACK-DESIGN`

*Note: M2E-02 (Target Config Schema and Validation) is deferred until runtime migration is explicitly required.*

---

## Safe M3 Starting Scope

### Allowed for M3-01:
1. Design AI-readable context pack structure.
2. Define source attribution blocks.
3. Define freshness / staleness / delay metadata section.
4. Define target-class support warnings.
5. Define source caveat blocks.
6. Define normalized sample summaries.
7. Define explicit "not investment advice / no trading signal" guardrails.
8. Design only; no runtime generator unless separately authorized.

### Not Allowed for M3-01:
1. Do not generate live market briefing yet.
2. Do not create scheduled or automatic market updates.
3. Do not add buy/sell/hold semantics.
4. Do not add trading signal labels.
5. Do not rank securities as investment recommendations.
6. Do not perform full-market scanning.
7. Do not call broker APIs.
8. Do not write production DB tables.
9. Do not infer real-time status from EOD sources.
10. Do not hide source caveats from the AI context.