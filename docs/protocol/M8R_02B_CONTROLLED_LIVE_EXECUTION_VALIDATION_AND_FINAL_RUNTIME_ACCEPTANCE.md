# M8R-02B Controlled Live Execution Validation and Final Runtime Acceptance

Status: `m8r_02b_controlled_live_execution_validation_no_go`

Decision: `NO_GO`

Validation run ID: `m8r02b-20260715T020000Z`

Verified starting HEAD: `751ad3a1102cb6fd432410717355c35bea08365c`.

Validation date/timezone: `2026-07-15`, UTC execution timestamps.

## Runtime environment

- Repository path: `/workspace/tw-market-live-data-intelligence`
- Branch: `work`
- Python: recorded in `research/m8r/live_validation/m8r02b-20260715T020000Z/validation_manifest.json`
- Network gate: explicit `--operator-confirmed --allow-network` for each live case
- Artifact root: `research/m8r/live_validation/m8r02b-20260715T020000Z`

## Scope and boundary

M8R-02B added a manually invoked validation harness only. It did not add API, MCP, frontend, scheduler, polling, alerts, automatic refresh, or background execution.

The harness compiles bounded M8R requests, builds approvals, uses `FilesystemApprovalConsumptionStore`, executes through the production executor registry and one-shot orchestrator, builds M8 context core, builds `ai_market_context.v1` when possible, writes receipt-scoped artifacts, and audits retained artifacts for raw/full-market keys.

## Exact cases attempted

| Case | Target | Source family | Result | Network requests | Identity/currentness |
|---|---|---:|---:|---:|---|
| `TWSE_MIS_LISTED_2330` | TWSE equity `2330`, route `tse_2330.tw` | `TWSE_MIS` | `passed_with_caveats` | 1 | returned `2330`; live-ish currentness unresolved |
| `TWSE_MIS_OTC_6488` | TPEx equity `6488`, route `otc_6488.tw` | `TWSE_MIS` | `passed_with_caveats` | 1 | returned `6488`; live-ish currentness unresolved |
| `TWSE_MIS_TAIEX` | TWSE index `TAIEX`, route `tse_t00.tw` | `TWSE_MIS` | `passed_with_caveats` | 1 | exact index route; live-ish currentness unresolved |
| `TWSE_OPENAPI_EOD_2330` | TWSE equity `2330` EOD | `TWSE_OPENAPI` | `passed_with_caveats` | 1 | official EOD/reference |
| `TPEX_OPENAPI_EOD_6488` | TPEx equity `6488` EOD | `TPEX_OPENAPI` | `failed_runtime_contract` | 1 | source returned no retained matching bounded row (`target_not_present_in_source_result`) |
| `TAIFEX_MIS_FUTURE_EXACT` | TAIFEX monthly regular `TX 202607` | `TAIFEX_MIS` | `passed_with_caveats` | 2 | returned product `TX`, expiry `202607`, session `regular` |
| `TAIFEX_MIS_OPTION_EXACT` | TAIFEX monthly regular `TXO 202607 20000 C` | `TAIFEX_MIS` | `failed_runtime_contract` | 2 | no successful bounded option observation; exact option identity not proven |
| `TAIFEX_OPENAPI_FUTURE_EXACT` | TAIFEX monthly regular `TX 202607` | `TAIFEX_OPENAPI` | `passed_with_caveats` | 1 | returned contract-level `TX 202607` |
| `TAIFEX_OPENAPI_OPTION_EXACT` | TAIFEX monthly regular `TXO 202607 20000 C` | `TAIFEX_OPENAPI` | `failed_runtime_contract` | 1 | no retained matching option row; exact option identity not proven |

## Source-family decision table

| Source family | Target | Live execution | Identity | Timing/currentness | Retention | AI package | Result |
| ------------- | ------ | -------------: | -------: | -----------------: | --------: | ---------: | ------ |
| `TWSE_MIS` | 2330, 6488, TAIEX | yes | pass | live-ish, unresolved/currentness caveat | pass | valid | `passed_with_caveats` |
| `TWSE_OPENAPI` | 2330 | yes | pass | official EOD/reference | pass | valid | `passed_with_caveats` |
| `TPEX_OPENAPI` | 6488 | yes | no retained target row | official EOD/reference unavailable for target | pass | blocked/partial | `failed_runtime_contract` |
| `TAIFEX_MIS` | TX 202607 future; TXO 202607 20000 C option | yes | future pass; option not proven | live-ish snapshot/caveats | pass | future valid; option blocked | `mixed_failed_runtime_contract` |
| `TAIFEX_OPENAPI` | TX 202607 future; TXO 202607 20000 C option | yes | future pass; option not proven | official derivatives EOD/statistical | pass | future valid; option blocked | `mixed_failed_runtime_contract` |

## Negative controls

- Dry-run all-required manifest built plans and approvals, then preflighted with `allow_network=false`; adapters were not invoked and `network_operations_attempted=0`.
- Missing consumption store is covered by the runner/unit preflight and blocks single-use approval before network execution.
- Approval replay is protected by `FilesystemApprovalConsumptionStore`; replay checks report `network_operations_attempted=0`.
- Modified-plan approval mismatch is covered by existing M8R plan/approval hash tests.
- Unsupported TAIFEX identities remain blocked before network by M8R request normalization for weekly/after-hours/missing exact identity.

## Retention and raw-data audit

All retained artifacts under the accepted validation roots were audited for forbidden keys including `raw_payload`, `response_body`, `html`, `cookies`, `authorization`, `headers`, `api_key`, `access_token`, `refresh_token`, `sockjs_frames`, `full_option_chain`, `raw_rest_records`, `rest_rows`, and `whole_market_rows`. The audit result was `passed` with no forbidden-key hits. Whole-market OpenAPI execution retained only bounded observations or explicit missing-context records for the approved target.

## M8 core and AI package result

Successful TWSE MIS, TWSE OpenAPI, TAIFEX MIS future, and TAIFEX OpenAPI future cases built M8 context core and `ai_market_context.v1` with caveats. Failed TPEx/TAIFEX option cases produced explicit missing-context records and did not upgrade production readiness.

## Runtime-critical acceptance

Runtime-critical safety properties passed: network is disabled by default, operator/network gates are explicit, single-use approvals require an authoritative store, artifacts are bounded to relative approved roots, receipt fields report one-shot/no polling/no scheduler/no background/no retry semantics, and raw/full-market retention audit passed.

## Final answers

- Are the production adapters implemented? **Yes**, with accepted M8R-02A adapters.
- Are individual live sources operational? **Partially**. TWSE MIS, TWSE OpenAPI, TAIFEX MIS future, and TAIFEX OpenAPI future returned bounded evidence; TPEx OpenAPI for 6488 and exact TXO option cases did not pass.
- Is the one-shot runtime safe and traceable? **Yes for the validated harness controls**.
- Can the full runtime produce `ai_market_context.v1` from real results? **Yes for successful/partial real cases, but not all required cases**.
- Is production live execution ready for controlled consumer integration? **No**.

## Readiness flags

```json
{
  "package_schema_ready": true,
  "offline_packaging_ready": true,
  "production_orchestrator_contract_ready": true,
  "production_executor_adapters_ready": true,
  "production_live_execution_ready": false,
  "m8r_02a_required": false,
  "m8r_02b_required": true,
  "live_validation_completed": false
}
```

## Decision and successor

`NO_GO`: exact TAIFEX option identity was not proven, TPEx OpenAPI target `6488` did not return a retained bounded EOD row, and therefore the required full source-family / exact-future / exact-option acceptance criteria were not met.

Recommended successor: `M8R-02B-DEFECT-CORRECTION-AND-EXACT-OPTION-TPEX-REVALIDATION`, scoped to (1) verify TPEx OpenAPI target selection or source availability for `6488`, (2) provide separately evidenced exact TXO monthly option identity that both TAIFEX MIS and TAIFEX OpenAPI can return, and (3) rerun M8R-02B without weakening exact-identity requirements.

## Coverage limitation

The successful cases prove only the bounded MVP paths explicitly executed here. They do not prove all TWSE securities, all TPEx securities, all TAIFEX products, weekly options, after-hours derivatives, all market phases, or endpoint schemas forever.
