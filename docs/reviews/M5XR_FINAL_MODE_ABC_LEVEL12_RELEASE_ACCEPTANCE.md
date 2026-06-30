# M5XR Final Mode ABC Level 1/2 Release Acceptance

## 1. Executive Summary

Task ID: `M5XR-FINAL-MODE-ABC-LEVEL12-RELEASE-ACCEPTANCE`.

This clean-room acceptance used repository artifacts and existing runners only. The repository currently produces a valid Level 1 M5F Canonical Package, a bounded Level 2 live observation, and a conversation package suitable for AI discussion with explicit no-trading-signal caveats. Release recommendation: **Local Release Candidate**, not Production Ready, because live observation depends on browser endpoint candidates and explicitly lacks a realtime SLA.

Operator Ready: **Yes**, for local governed operation.

## 2. Repository State

Inspected artifacts: `README.md`, `docs/`, architecture docs, operator guides, release docs, `config/m5k_default_watchlist.json`, `config/m5l_live_source_adapter_matrix.json`, M5F package artifacts under `research/staging/m5f/m5f_canonical_market_context_01/`, FastAPI server, MCP server, frontend readonly preview, and scripts.

Generated/updated acceptance evidence:

- `research/live_observation_runs/m5k/latest_observation.json`
- `research/live_observation_runs/current_conversation_context/conversation_context.json`
- `research/live_observation_runs/current_conversation_context/conversation_context.md`
- this report

No M5F artifact, contract schema, source-health semantics, observation semantics, `frontend/public`, or `research/generated` product artifact is intentionally modified by this acceptance PR.

## 3. Mode A Level 1 — Current M5F Canonical Product

### Inspected canonical artifacts

- Canonical JSON: `research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json`
- AI Context Pack: `research/staging/m5f/m5f_canonical_market_context_01/ai_context_pack.json`
- AI Context Markdown: `research/staging/m5f/m5f_canonical_market_context_01/ai_context_pack.md`
- ChatGPT Briefing: `research/staging/m5f/m5f_canonical_market_context_01/chatgpt_briefing.md`
- Capability Summary: `research/staging/m5f/m5f_canonical_market_context_01/capability_summary.json`
- Canonical Source Health: `research/staging/m5f/m5f_canonical_market_context_01/source_health.json`
- Manifest: `research/staging/m5f/m5f_canonical_market_context_01/sha256_manifest.json`
- Validation Report: `research/staging/m5f/m5f_canonical_market_context_01/validation_report.json`

### What Canonical actually contains

- Package ID: `m5f_canonical_market_context_01`
- Schema: `m5f_canonical_market_context.v1`
- Source: `TWSE_OpenAPI`
- Source date: `2026-06-26`
- Symbols: `0050, 00929, 2330`
- Failed targets: `[]`
- Global caveats: `not_realtime_guaranteed, not_trading_signal, not_production_current_state, source_risk_present, freshness_must_be_displayed`
- Capability summary: readonly `True`, realtime supported `False`, production ready `False`
- Validation status: `passed`; checks: `exact_file_set, manifest_hashes, symbols_source_date_values, lineage_hashes, required_caveats, required_false_flags, no_trading_recommendation_fields, no_endpoint_payload_leakage`
- Manifest type: SHA-256 manifest present and validated by M5F validator.

### What Canonical intentionally does NOT contain

Canonical intentionally does not contain current realtime quotes, raw endpoint payload leakage, trading recommendations, buy/sell/hold fields, target prices, or production-current-state claims. It is a reviewed, historical/stale, readonly Level 1 context.

### Why Canonical is Level 1

Canonical is Level 1 because it is a stable, validated, readonly historical evidence snapshot that can be consumed by FastAPI, MCP, frontend preview, and AI context tooling without network calls or live refresh side effects.

### Canonical vs Live Observation

Canonical is curated Level 1 context from `TWSE_OpenAPI` on `2026-06-26`. Live Observation is Level 2 bounded execution from the watchlist and may contact source endpoints at operator request time. Live Observation is not promoted into Canonical and must display freshness, delay, source risk, and caveats.

FastAPI readonly endpoints were covered by M5IJ acceptance checks: `/api/health`, `/api/governance`, `/api/context/canonical`, `/api/context/snapshot`, `/api/context/source-health`, `/api/context/capability-summary`, and `/api/context/briefing`.

## 4. Mode A Level 2

Mode A Level 2 is intentionally empty by design. Mode A represents Canonical Package acceptance only. Level 2 live observation belongs to Mode B/C and must not be fabricated or merged back into M5F Canonical.

## 5. Mode B Level 1 — Watchlist, Adapter Matrix, Capability Matrix, Route Planning, Source Health Plan

Configured watchlist: `config/m5k_default_watchlist.json`.
Adapter matrix: `config/m5l_live_source_adapter_matrix.json`.
Capability matrix: `docs/capability_matrix.md`.
Source health plan/check-only command: `python scripts/run_m5q_source_health_probe.py --check-only`.

| Symbol | Market | Instrument Type | Selected Adapter | Source Family | Source Type | Supported Status | Expected Observation Route |
|---|---|---|---|---|---|---|---|
| 0050 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_0050.tw |
| 00878 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_00878.tw |
| 00919 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_00919.tw |
| 00929 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_00929.tw |
| 00934 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_00934.tw |
| 00939 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_00939.tw |
| 00940 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_00940.tw |
| 00981A | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_00981A.tw |
| 1569 | tpex | listed_or_otc_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | otc_1569.tw |
| 2317 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_2317.tw |
| 2324 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_2324.tw |
| 2330 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_2330.tw |
| 2603 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_2603.tw |
| 2609 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_2609.tw |
| 3293 | tpex | listed_or_otc_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | otc_3293.tw |
| 3483 | tpex | listed_or_otc_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | otc_3483.tw |
| 3543 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_3543.tw |
| TAIEX | twse | index | twse_mis_taiex_index_quote | TWSE_MIS | official_browser_json_endpoint_candidate | planned | tse_t00.tw |
| TX | taifex | futures | taifex_mis_tx_futures_quote | TAIFEX | official_browser_json_endpoint | planned | taifex_mis_getQuoteList |

Operator interpretation: if the operator observes a configured symbol, the route table above shows the adapter and source selected by the existing route planner.

## 6. Mode B Level 2 — Bounded Observation

Command executed at retrieval time: `python scripts/run_m5k_live_observation.py --watchlist config/m5k_default_watchlist.json --execute-live-observation`.
Timestamp: `2026-06-30T08:24:34Z`.
Targets: `0050, 00878, 00919, 00929, 00934, 00939, 00940, 00981A, 1569, 2317, 2324, 2330, 2603, 2609, 3293, 3483, 3543, TAIEX, TX`.
network_calls_may_have_occurred: `true`.

| symbol | market | instrument_type | adapter | source | status | observation_status | reference_only | price_like_value | price_semantics | source_timestamp | retrieved_at | freshness | delay | failure_reason | recommended_next_step | display_caveats |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TX | taifex | futures | taifex_mis_tx_futures_quote | TAIFEX | ok | value_available | False | 46730.0 | last_trade_price_or_settlement_fallback_as_reported_by_taifex_mis | 2026-06-30T13:44:59+08:00 | 2026-06-30T08:24:34Z | stale_or_closed_session | delay_seconds_measured_from_source_timestamp_not_exchange_realtime_sla |  | Review freshness/caveats; rerun bounded observation manually if needed. | freshness_must_be_displayed; live_observation_not_canonical; no_realtime_sla_verified; no_trading_signal |
| 0050 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 107.8 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 00878 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 33.5 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 00919 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 29.5 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 00929 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 30.78 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 00934 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 28.21 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 00939 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 21.46 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 00940 | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 12.65 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 00981A | twse | listed_etf | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 31.28 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 1569 | tpex | listed_or_otc_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 45.9 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 2317 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 251.0 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 2324 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 35.3 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 2330 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 2410.0 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 2603 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 184.5 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 2609 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 52.0 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 3293 | tpex | listed_or_otc_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 789.0 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 3483 | tpex | listed_or_otc_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 90.2 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| 3543 | twse | listed_equity | twse_mis_equity_etf_quote | TWSE_MIS | ok | value_available | False | 29.05 | last_or_current_quote_as_reported_by_source | 2026-06-30T06:30:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |
| TAIEX | twse | index | twse_mis_taiex_index_quote | TWSE_MIS | ok | value_available | False | 46125.91 | last_or_current_quote_as_reported_by_source | 2026-06-30T05:33:00Z | 2026-06-30T08:24:34Z | current observation candidate; realtime status not guaranteed by M5K | not_realtime_guaranteed |  | Review freshness/caveats; rerun bounded observation manually if needed. | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal |

### Observation Summary

- healthy: `18`
- degraded: `1`
- failed: `0`
- unsupported: `0`
- reference_only: `0`

Degraded observations are degraded when freshness is stale/closed-session or source caveats prevent realtime interpretation. In this run, `TX` is degraded because `freshness_assessment=stale_or_closed_session` and delay is measured from source timestamp, not an exchange realtime SLA. Reference-only exists for observations that are useful as descriptive context but must not be treated as a current price. This run has no reference-only observation in `latest_observation.json`, while the conversation package can preserve reference-only state from its source-health overlay. No price-like value in this report should be interpreted as a trading recommendation or guaranteed current market price.

## 7. Mode C Level 1 — Conversation Package

Generated final Conversation Package:

- `research/live_observation_runs/current_conversation_context/conversation_context.json`
- `research/live_observation_runs/current_conversation_context/conversation_context.md`

Conversation package sections verified:

- Watchlist Summary: present.
- Observation Summary: healthy/degraded/failed/unavailable context is present under `observation_summary` and `ai_guidance_summary`.
- Per Symbol Observation: present in `per_symbol_observations`.
- Canonical Summary: package `m5f_canonical_market_context_01`, symbols `0050, 00929, 2330`.
- Source Health Summary: present under `source_health_summary`.
- AI Guidance Summary: descriptive only `True`, trading recommendation `False`.
- Current Caveats: `live_observation_not_canonical, not_realtime_guaranteed, freshness_must_be_displayed, source_may_be_delayed_or_unavailable, no_trading_signal`

Acceptance result: Conversation Context alone is sufficient for AI discussion of current observation state because it embeds watchlist, canonical summary, latest observation state, source health summary, caveats, and AI guidance. No additional repository artifact is required for the AI handoff discussion, although operators can inspect source artifacts for audit depth.

## 8. Mode C Level 2 — Simulated ChatGPT Reasoning From Conversation Package Only

以下回答只使用 `conversation_context.json` / `conversation_context.md` 所表達的狀態，不使用外部 AI 或額外市場資料。

- 哪些資料目前可信？可信的是「描述性與治理狀態」：watchlist 範圍、Canonical 是 historical/stale Level 1、Latest Observation 是 bounded Level 2、以及每筆 observation 的 source/freshness/delay/caveat。價格欄位只能作為 source-reported observation，不可當作保證即時價格。
- 哪些 observation 是 reference-only？Conversation Package 的 guidance 標示 reference-only observations: `0050, 2330, 3483`。
- 哪些 observation 不可視為 current price？所有標的都不可被視為保證 current price；reference-only、unavailable、stale_or_closed_session、以及帶有 `not_realtime_guaranteed` 的 observation 尤其不可當作 current price。
- 哪些來源 degraded？Conversation guidance 標示 degraded observations: `0050, 2330, 3483, TX`；來源限制主要來自 TWSE_MIS browser endpoint candidate、TAIFEX browser JSON endpoint、source risk、staleness、與無 realtime SLA。
- 哪些標的是 unavailable？`none`。
- Canonical Package 提供什麼？提供 `0050, 00929, 2330` 的 validated Level 1 historical context、source date、governance caveats、readonly AI context and briefing。
- Latest Observation 提供什麼？提供 bounded watchlist 的 per-symbol source-reported observation, source timestamp, retrieval timestamp, freshness, delay, source/adapter, and caveats。
- 目前最大的資料限制？沒有 verified realtime SLA；browser endpoint candidates may be fragile/delayed/unavailable；Canonical is not production current state；no polling/scheduler/full-market scan；raw endpoint payload excluded。
- 下一步建議人工如何處理？人工應檢查 freshness/delay/caveats；若需要更新，僅手動執行 bounded observation runner；必要時比對官方/商業來源；不要把任何輸出轉成買賣建議、排序或目標價。

## 9. Previous Findings Verification

No prior `M5X` manual-acceptance findings file was present in repository artifacts during this clean-room review. Therefore, no finding is hidden; the table records the verifiable status from available artifacts.

| Previous Finding | Current Status | Evidence |
|---|---|---|
| M5F must remain historical/stale and not realtime. | Resolved | M5F validation report passes and governance flags `current_realtime=false`, `production_current_state=false`, `stale_status=stale`. |
| FastAPI readonly product endpoints must remain available and live probe disabled. | Resolved | M5IJ check-only reports all readonly endpoints passed and disabled legacy live probe paths. |
| MCP must expose readonly canonical behavior and not legacy live tool. | Resolved | M5IJ check-only reports `legacy_mcp_live_tool_not_listed`, `legacy_mcp_live_tool_disabled_direct_call`, and `mcp_readonly_canonical` passed. |
| Frontend public artifacts must not be written by acceptance. | Resolved | `git diff --name-only` contains no `frontend/public/` path after cleanup. |
| `research/generated` must not be written by acceptance. | Resolved | Accidental local regeneration was reverted before final validation/commit; final changed paths exclude `research/generated/`. |
| Raw endpoint payload must not be exposed in product surfaces. | Resolved | M5F validation and M5IJ checks include no endpoint payload leakage/raw-or-trading-field checks. |
| Unlisted M5X-specific manual findings. | Not Applicable | No `M5X` finding artifact was found under `docs/reviews` or release docs. |

## 10. Operator Acceptance

Operator path:

Clone → Install → Validate → Run → Observe → Read → Discuss with AI

Result: **Operator Ready**.

Reason: README/runbooks document local-first operation; validation scripts exist; FastAPI and MCP readonly surfaces exist; bounded observation runner exists; frontend readonly preview exists; conversation package builder exists. Operator readiness is local and governed, not production market-data service readiness.

## 11. Architecture Acceptance

Current data flow:

```text
M5F Canonical (TWSE_OpenAPI historical/stale)
      │
      ├── AI Context Pack / Markdown / Briefing
      ├── Capability Summary
      ├── Source Health
      ├── FastAPI readonly endpoints
      ├── MCP readonly tools
      └── Frontend readonly preview

Watchlist + Adapter Matrix + Capability Matrix
      │
      ▼
Explicit bounded observation runner
      │
      ├── TWSE_MIS browser endpoint candidate
      ├── TAIFEX browser JSON endpoint
      └── Source Health check-only / probe plan
      │
      ▼
Latest Observation
      │
      ▼
Conversation Package
      │
      ├── FastAPI/MCP/frontend-readable context
      └── AI Discussion handoff
```

Canonical participates as Level 1 historical context. Source Health participates as caveat and source-family status context. Adapter Matrix maps symbols/instrument classes to sources. Capability Matrix records current product capability and limitations. No broken product workflow link was found in validation; M5IJ acceptance passed.

## 12. Release Recommendation

Chosen status: **Local Release Candidate**.

Justification: the local product validates, exposes readonly FastAPI/MCP/frontend surfaces, can run bounded observation, and can generate an AI conversation package. It is not Production Ready because realtime is not guaranteed, source adapters include fragile browser endpoints, and operation remains explicit/manual and local-first.

## 13. Remaining Caveats

- No realtime SLA is verified.
- TWSE_MIS/TAIFEX browser endpoints may change or become unavailable.
- Canonical remains historical/stale and must not be treated as latest market data.
- Live observation is bounded and explicit only; no scheduler/polling/full-market scan.
- Raw endpoint payloads are excluded from product outputs.
- No trading recommendation, ranking, buy/sell/hold, or target-price use is allowed.

## 14. Recommended Next Milestone

Proceed to a governed release-candidate hardening milestone: stabilize operator docs, add reproducible acceptance transcripts, expand source-health evidence without increasing probing frequency, and evaluate official or commercial data-source contracts for stronger realtime/delay semantics.

## Validation Results

- PASS: `python -m compileall .`
- PASS: `pytest -m 'not network'` (662 passed, 1 warning).
- PASS: `python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01`
- PASS: `python scripts/run_m5ij_end_to_end_acceptance.py --check-only`
- PASS: `python scripts/run_m5q_source_health_probe.py --check-only`
- PASS: `python scripts/build_m5n_conversation_context.py --watchlist config/m5k_default_watchlist.json --out-dir /workspace/tw-market-live-data-intelligence/research/live_observation_runs/current_conversation_context`
- PASS: `python scripts/validate_governance_policy_manifest.py --json`

## Forbidden Behavior Confirmation

This acceptance did not modify M5F, observation semantics, source-health semantics, or contracts; did not introduce schemas; did not write `frontend/public` in final patch; did not perform full-market scan, polling, or scheduler execution; did not expose raw endpoint payload; and does not provide buy/sell/hold, target prices, security ranking, or trading recommendations.
