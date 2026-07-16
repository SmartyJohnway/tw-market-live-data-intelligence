# M8R-02B-F2 Conversational Derivatives Intent Resolution and Current Contract Execution

Status: `m8r_02b_f2_no_go_pending_true_taifex_mis_conversational_current_execution`

Decision: `NO_GO`

Starting baseline: `8e5e39c75f5e6d22b2573ada5d3c6348a11bc91b`.

## Scope

F2 adds a bounded conversational derivatives resolution layer for Taiwan TAIFEX futures/options prompts. It does not add frontend, chat UI, API/MCP service, scheduler, polling, alerts, portfolio logic, trading recommendations, broker integration, or automatic order creation. M8R-04 remains blocked pending a separate AI conversation input/output design review.

## New contracts

- Intent schema: `m8r_derivatives_conversational_intent.v1`.
- Exact intent schema: `m8r_derivatives_exact_intent.v1`.
- Resolution artifact: `m8r_derivatives_resolution_record.v1`.
- AI-safe projection: `m8r_ai_conversation_resolution.v1`.

## Exact versus conversational mode

Exact mode is selected only when the user supplies a complete bounded contract identity such as `TXO 202607 40000 C monthly`. Exact mode uses exact match only and fails closed as `exact_contract_unavailable` when the requested identity is not present. It does not automatically replace expiry, strike, call/put, monthly/weekly type, or session.

Conversational `resolve_current` mode is selected for incomplete natural-language market intent such as `現在台指期怎麼樣？` or `現在台指選擇權怎麼樣？`. It discovers the current bounded contract universe at execution time, applies documented policy, generates exact request targets, records assumptions, and discloses the resolved identities to the AI package.

## Supported reviewed phrase set

Product aliases include `台指期`, `台指期貨`, `大台`, `TX`, `TAIEX futures`, `台指選`, `台指選擇權`, `台指週選`, `TXO`, and `TAIEX options`.

Time and expiry aliases include `現在`, `目前`, `當下`, `最新`, `current`, `now`, `latest`, `近月`, `最近月`, `最近到期`, `front month`, `nearest expiry`, and `next expiry`.

Monthly/weekly preferences are explicit only for `月選`/`monthly` and `週選`/`weekly`. Near/current without monthly/weekly means nearest active expiry, not automatically monthly.

Strike phrases include `附近`, `價平`, `ATM`, `平值`, `around market`, `near reference`, bounded numeric anchors such as `45000附近`, and bounded reviewed Chinese-number anchors such as `四萬五附近`.

Call/put phrases include `call`, `買權`, `C`, `put`, `賣權`, `P`, `call 跟 put`, `買賣權`, `both`, and `兩邊`. Unspecified option call/put defaults to both.

## Current contract resolution policy

Execution sequence:

1. Parse deterministic intent.
2. Discover current TAIFEX contract universe in the same one-shot context.
3. Resolve exact identities.
4. Run same-execution freshness guard.
5. Perform at most one conversational re-resolution if a current/near inferred identity becomes stale.
6. Fetch bounded exact targets.
7. Build AI package with conversation resolution provenance.

Futures resolve `TX` to nearest active regular-session monthly future.

Options resolve `TXO` to nearest active TAIFEX MIS executable expiry by default, both call and put, and nearest actually listed strike to the reference basis. `nearest_active` is not rewritten to monthly; explicit monthly and weekly preferences filter only when the user says monthly or weekly. The selected set is capped at six exact option contracts and does not retain the full option chain.

## Monthly, weekly, strike, and call/put policies

- Explicit monthly → nearest active monthly contract.
- Explicit weekly → nearest active weekly contract.
- Current/near only → nearest active TAIFEX MIS executable expiry regardless of weekly/monthly; the resolver records the selected contract type and does not describe a monthly contract as weekly or vice versa.
- Strike uses nearest actually listed strike to the current/reference basis or explicit anchor.
- Ties select both equidistant strikes deterministically.
- Option call/put omitted → both.

## Freshness guard

The guard verifies the resolved expiry, strike, call/put, session, and exact runtime identity still exist before execution. Conversational mode may re-resolve once using the original user intent and records `reresolution_count`. Exact mode does not re-resolve and returns `exact_contract_unavailable` when the explicit identity is unavailable.

## Lower-level TAIFEX MIS reason preservation

TAIFEX MIS adapter failures preserve bounded lower-level reasons:

- `requested_month_not_available` → `source_identity_scope_unavailable`
- `requested_strike_not_available` → `source_identity_scope_unavailable`
- `option_exact_identity_not_unique` → `source_identity_not_unique`
- `runtime_symbol_mismatch` → `source_identity_mismatch`
- unknown malformed payloads → `source_payload_invalid`

Issue objects may include `detail_reason` but do not retain raw selector payloads.

## Controlled live validation matrix

Implemented CLI: `scripts/run_m8r_conversational_derivatives_context.py`.

Required gate flags: `--text`, `--operator-confirmed`, `--allow-network`, and `--artifact-root`.

Live prompts for a new run ID:

- `CONVERSATIONAL_TAIFEX_FUTURE_CURRENT`: `現在台指期怎麼樣？`
- `CONVERSATIONAL_TAIFEX_OPTION_CURRENT_BOTH`: `現在台指選擇權怎麼樣？`
- `CONVERSATIONAL_TAIFEX_OPTION_MONTHLY_BOTH`: `現在台指選擇權近月月選 call 跟 put 怎麼樣？`
- `CONVERSATIONAL_TAIFEX_OPTION_EXPLICIT_STRIKE_AREA`: `看一下台指選擇權四萬五附近的 call 跟 put`
- `EXACT_TAIFEX_OPTION_UNAVAILABLE_NEGATIVE_CONTROL`: `TXO 202607 40000 C monthly`
- Optional: `CONVERSATIONAL_TAIFEX_OPTION_WEEKLY_BOTH`: `現在最近到期的台指週選怎麼樣？`

The prior OpenAPI-only run is superseded. F2 remains `NO_GO` until a new controlled run proves TAIFEX MIS current futures/options execution for all required conversational cases. Each future operator run must store `derivatives_intent.json`, `derivatives_resolution_record.json`, MIS operation results, optional OpenAPI enrichment, and AI package artifacts under the supplied run root.

## Readiness flags

```json
{
  "m8r_02b_historical_status": "NO_GO",
  "m8r_02b_f1_status": "NO_GO",
  "m8r_02b_f2_status": "NO_GO",
  "m8r_02b_final_disposition": "NO_GO_PENDING_TRUE_TAIFEX_MIS_CONVERSATIONAL_CURRENT_EXECUTION",
  "conversational_derivatives_resolution_ready": true,
  "conversational_derivatives_eod_resolution_ready": true,
  "conversational_derivatives_live_execution_ready": false,
  "exact_derivatives_execution_ready": true,
  "production_live_execution_ready": false,
  "live_validation_completed": false,
  "m8r_02b_required": true,
  "m8r04_completed": false
}
```

## Successor gate

Recommended successor: `M8R-03B-AI-CONVERSATION-INPUT-OUTPUT-DESIGN-REVIEW`.

Do not set the immediate successor to M8R-04 until operators and reviewers separately accept the conversation model, disclosure style, follow-up handling, uncertainty language, and trading-language boundaries.
