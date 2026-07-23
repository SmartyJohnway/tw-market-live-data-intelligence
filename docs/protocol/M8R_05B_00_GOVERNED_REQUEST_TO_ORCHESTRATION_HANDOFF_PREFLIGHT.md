# M8R-05B-00 governed request-to-orchestration handoff preflight — inventory findings

## Purpose and boundary

This static, non-network preflight inventories the boundary after F3. F3 produces only `unified_market_evidence_request_validation.v1`; its schema fixes `operation_count_computed=false`, `operation_count=0`, and `orchestrator_projection_required=true`. A `validation_status=valid` result is a planning candidate, **not** runtime-ready or execution-authorized. F3 uses a deep copy for `normalized_request`, emits stable sorted candidates/issues, resolves canonical targets, and distinguishes `contract_supported`, `runtime_executable`, and `provisional` capability results.

## Inventory method

The inventory used static inspection of the F3 implementation/schema/tests, the unified capability catalog, bounded request/planner surfaces, controlled executors, and their unit tests. No runner, approval artifact, token, or market endpoint was invoked. Evidence pointers are recorded in the two machine-readable inventories.

## Initial disposition

No existing surface is a direct consumer of the F3 validation schema. The M8R-03D controlled watchlist executor is the only adapter-required candidate selected for currently runtime-executable TWSE/TPEX observation and official-EOD routes: it has explicit preflight/execute separation, bounded writes, approval checks, and single-use consumption. Its request/preview approval contract differs from the required 05B immutable plan binding, so it is not direct reuse. The M8R-02 one-shot orchestrator and M8R-03D planner are reference-only because both use different plan vocabularies. M7G is blocked pending a governed immutable approval contract.

## Initial routing conclusion

The authoritative catalog is `docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json` and contains seven F3-accepted IDs. Two TWSE/TPEX runtime-executable capability families have an adapter-required selected executor; the remaining capability families are deliberately plan-only or blocked until 05B defines an operation/evidence contract. TAIFEX provisional capability results remain plan-only and can never imply execution.

## Commit-1 decision

The routing is sufficiently deterministic to define the 05B-01 offline planner, **with caveats**: the planner must emit no executable authorization and must represent unavailable executor routes explicitly. Commit 2 will define immutable input binding, logical-operation/batch-group semantics, partial-plan policy, owner-approval separation, and the M8R-05B-01/02/03 implementation split. This document is incomplete by design until that contract work is committed.

## Commit-1 correction: approval and session-status reconciliation

`capability_requires_execution_approval` mirrors the authoritative capability catalog. It is deliberately different from final orchestration-package owner approval: derived, non-executing `identity`, `source_currentness`, and `evidence_quality` require no execution approval and use `inherits_from_upstream` package policy. A package containing an approved network operation may still require owner approval under the strictest-operation package policy.

The session-status inventory now distinguishes local deterministic classifiers (`m7e_market_clock_session_state`, `m8a_market_day_currentness_resolver`, and `m8r_eod_expected_trade_date_resolver`) from the NCDR/DGPA closure-feed adapter. Local builders use explicitly supplied calendar/closure evidence only. The closure adapter can retrieve current external evidence but lacks a 05B immutable plan/authorization binding. Consequently `session_status` remains **blocked**, and its whole-capability route is network-required whenever current authoritative closure evidence is requested; local-only state does not satisfy that evidence need unless prior evidence is explicitly bound.

## Revised Commit-1 decision: GO_TO_COMMIT_2_WITH_CAVEATS

Approval semantics now match the catalog, every selected executor is adapter-required and reusable, and every unresolved route is explicit. The offline 05B-01 planner may proceed only as a design/planning projection: it must preserve blocked session-status and plan-only/provisional outcomes, create no approval or authorization, and never claim runtime-ready or execution-authorized status. Commit 2 remains the handoff-contract work described above.
