# Phase J Closure-R2-R1 semantic-alignment correction

Disposition: `PHASE_J_FINAL_CLOSURE_R2_R1_SEMANTIC_ALIGNMENT_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW`.

The blocked predecessor is `62dd88cef8da9c13ffcbd3dec57232e6bfd6678f`. Its governance evidence remains unchanged. The adapter formerly discarded retrieval timing when exchange timing was absent. The correction retains the accepted M8 retrieval-age assessment only under the frozen source policy. TWSE_MIS still allows retrieved-only freshness, does not require an exchange timestamp, and has the unchanged 900-second policy window. No classifier, threshold, schema, route, capability, renderer or MCP change was added.

Validated implementation: `f299eef4b76ce113313ea9c6add8da660cd23ea8`, tree `ce660cbe63deab1d9bfbbae826a488a37825fd96`, directly descending from the blocked predecessor. Only production adapter integration changed; remaining changes are acceptance infrastructure/tests. This evidence directly follows the frozen implementation.

| Case | Source time | Retrieval/evaluation | Typed result |
| --- | --- | --- | --- |
| J1-21 | 2026-09-01T05:30:00Z | 2026-10-08T06:00:00Z | available/full_success; stale_intraday_snapshot; 3198600 seconds; family_specific; safe_for_ai_context=false |
| Retrieved-only production path | absent | 2026-10-08T06:00:00Z | fresh_intraday_snapshot; all three retrieved-only/non-realtime flags true |
| Retrieved-only helper replay | absent | retrieval 06:00:00Z; evaluation 06:15:01Z | stale_intraday_snapshot; 901 seconds under frozen policy |
| Missing/invalid timing or policy | absent/invalid | missing/invalid | unresolved/unknown |

The recent and J1-21 witnesses traverse actual Local Service validation, preview, authorization, execute-once, genuine adapter normalization, Result V3, Audit V3, and stored handoff. Independent server receipts and canonical hashes bind the same packages. Each performs one fixture-backed source invocation and zero additional execution. The old retrieval witness is explicitly a private production-helper replay, not a full service-layer coverage claim. No new cells are promoted.

New correction tests: 34 passed (including 12 receipt mutations and 8 policy-gate cases). Existing Closure-R2: 55 passed. M8 freshness: 14 passed. Expanded focused suite: 462 passed, 2 pre-existing Mode C legacy-filename failures, 1 skipped. Both failures reproduce at the exact base. All current and applicable historical authority validators pass their governed checks; historical hard blocks are preserved.

Clean-archive default-CI on both base and implementation: 1288 collected, 1283 selected, 1233 passed, 46 failed, 4 skipped, 5 deselected. Exact failure sets are equal; candidate-only failures = 0. The profile remains non-green. Full failure node lists and environment/network-guard bindings are in the JSON.

Strict duplicate-key JSON scan, compileall, diff check and immutable-authority checks pass. Market GET/HEAD/POST, Browser Use, Firecrawl, real-agent/provider execution and host Security Master acquisition/mutation are all zero. Host selector hash is unchanged. MCP remains six tools. External ephemeral acceptance roots were removed after capture.

The only derived remaining closure obligation is `real_agent_layer`. Phase J remains STARTED, Roadmap unchecked, Phase K NOT_STARTED, real-agent authorization NOT_GRANTED, and PR #326 OPEN/DRAFT/UNMERGED. No Phase-J completion or independent acceptance is claimed.
