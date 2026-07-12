# M8 through M8B consolidated final acceptance

Final status: `m8_through_m8b_consolidated_acceptance_pass_with_caveats`

## 1. Purpose
Consolidate runtime behavior, registries, inventories, tests, README/operator instructions, and acceptance documents for M8-00 through M8B.

## 2. Baseline and reviewed merge history
Baseline contains PR #129 at `5353c9817f94e23b078dc107eda147b27c41022d` in the local repository snapshot. Accepted work covers PR #120 through PR #129.

## 3. Accepted M8-00 scope
Source timing/authority governance, capability registry, freshness evaluator, multi-source context builder, controlled conversation context, and M8-00 acceptance are accepted.

## 4. Accepted M8A scope
TWSE/TPEx official latest EOD adapters, currentness resolver, closure evidence support, context integration, and conversation projection are accepted with security-master caveats.

## 5. Accepted M8B scope
TAIFEX OpenAPI official derivatives EOD/statistical/reference contexts are accepted for futures, options, final settlement, large-trader OI, Put/Call Ratio, and BlockTrade.

## 6. Active source families
TWSE_MIS, TWSE_OPENAPI, TPEX_OPENAPI, TAIFEX_OPENAPI, and NCDR_DGPA_CLOSURE_CAP are active as governed sources/evidence.

## 7. Declared but non-executable source families
TAIFEX_MIS and MOPS remain declared but not runtime executable.

## 8. Source authority model
Official documented OpenAPI sources remain distinct from live-ish hidden/browser sources and supporting closure evidence.

## 9. Timing and freshness model
Runtime observations carry source-specific timing and currentness metadata; no source is upgraded to realtime SLA.

## 10. Currentness model
TAIFEX derivatives statuses are derivatives-specific: `current_official_derivatives_eod`, `stale_official_derivatives_eod`, `delayed_one_trading_day`, `matches_expected_latest_trade_date_after_emergency_closure`, `unresolved_date_mismatch`, and `session_semantics_unresolved`.

## 11. Emergency closure evidence model
TAIFEX closure confirmation requires target-date-specific official TAIFEX evidence; NCDR/DGPA evidence is supporting only.

## 12. Cash-market official EOD capability
TWSE_OPENAPI and TPEX_OPENAPI provide latest-EOD official cash-market context, not historical backfill.

## 13. Derivatives official EOD/statistical capability
TAIFEX_OPENAPI provides official derivatives EOD/statistical/reference context with bounded retained scope.

## 14. Live-ish cash-market capability
TWSE_MIS remains a live-ish cash-market snapshot source and is not realtime guaranteed.

## 15. Multi-source context builder
The M8 builder combines source observations with provenance and timing without hidden fetches or model calls.

## 16. Controlled conversation projection
Conversation context is compact, source-attributed, caveated, and excludes raw payload retention.

## 17. Operator confirmation model
Controlled refreshes require explicit operator confirmation.

## 18. Whole-market fetch versus bounded retention
Some official endpoints are whole-endpoint fetches, but retained observations are bounded by selectors and limits.

## 19. Bounded aggregate retention
Put/Call Ratio defaults to latest 1 retained row with hard max 60. Final settlement defaults to latest 1 row per product with hard max 100. Truncation is visible.

## 20. Raw-payload policy
Raw payloads are not retained or exposed.

## 21. Runtime failure/status contracts
Accepted statuses include successful, empty, unavailable, source error, schema drift, parse failure, invalid fields, date mismatch, partial success, zero-trade, unresolved session, no-match, invalid scope, and operator confirmation required.

## 22. Observation completion rules
Adapter completion timestamps and durations are finalized after processing for success, no-match, schema-drift, and error paths.

## 23. Product/session/quotation-unit caveats
TAIFEX quotation units, settlement currencies, and multipliers remain product-specific and incomplete; unknown sessions remain caveated.

## 24. Security-master caveat
No complete canonical production security master is introduced; unknown/unclassified instruments fail closed.

## 25. Registry/inventory reconciliation
`m8_source_capability_registry.json` now records one canonical active M8-through-M8B state and keeps historical state separate.

## 26. README/operator documentation reconciliation
README now documents the M8 architecture and bounded validation commands.

## 27. CI and validation evidence
Release validation is recorded in the PR/final report and in `docs/reviews/M8_THROUGH_M8B_FULL_NON_NETWORK_BASE_HEAD_VALIDATION.md`; full non-network was run on base and head with identical pre-existing M5D failures and passing M8-family tests.

## 28. Boundary preservation
No scheduler, polling, startup fetch, DB persistence, persistent cache, model call, recommendation, trading signal, Yahoo, FinMind, MOPS adapter, or TAIFEX_MIS implementation is added.

## 29. Known caveats
TWSE_MIS is live-ish only; TWSE/TPEx are latest EOD only; TAIFEX calendar evidence remains provisional; Large-trader OI is concentration data; Options Close is not Last.

## 30. Deferred capabilities
TAIFEX_MIS live-ish derivatives context is deferred to M8C-00.

## 31. Accepted capabilities matrix
| Capability | Source | Implemented | Runtime executable | Official/live-ish | Bounded retained scope | Direct AI context / compact currentness provenance | Currentness evaluated | Primary caveat |
|---|---|---:|---:|---|---:|---:|---:|---|
| TWSE MIS live-ish | TWSE_MIS | yes | yes | live-ish | yes | yes | yes | not realtime guaranteed |
| TWSE official EOD | TWSE_OPENAPI | yes | yes | official | yes | yes | yes | latest EOD only |
| TPEx official EOD | TPEX_OPENAPI | yes | yes | official | yes | yes | yes | latest EOD only |
| TAIFEX futures EOD | TAIFEX_OPENAPI | yes | yes | official | yes | yes | yes | product metadata incomplete |
| TAIFEX options EOD | TAIFEX_OPENAPI | yes | yes | official | yes | yes | yes | strict bounded option scope |
| TAIFEX final settlement | TAIFEX_OPENAPI | yes | yes | official reference | yes | yes | product-specific | historical reference possible |
| TAIFEX large-trader OI | TAIFEX_OPENAPI | yes | yes | official statistics | yes | yes | yes | concentration, not investor positioning |
| TAIFEX Put/Call Ratio | TAIFEX_OPENAPI | yes | yes | official statistics | yes | yes | yes | no sentiment classification |
| TAIFEX BlockTrade | TAIFEX_OPENAPI | yes | yes | official statistics | yes | yes | yes | no directional inference |
| NCDR/DGPA closure evidence | NCDR_DGPA_CLOSURE_CAP | yes | yes | supporting evidence | yes | direct: no; provenance: yes | n/a | not TAIFEX-specific confirmation |
| TAIFEX MIS | TAIFEX_MIS | no | no | live-ish candidate | n/a | no | no | deferred to M8C |

## 32. Final result and next task
Final result: `m8_through_m8b_consolidated_acceptance_pass_with_caveats`.

Next task: `M8C-00-TAIFEX-MIS-LIVEISH-DERIVATIVES-CONTEXT-PREFLIGHT`.

Boundary machine-check tokens: scheduler added = false; polling added = false; startup fetch added = false; DB persistence added = false; model call added = false; trading recommendation added = false.
