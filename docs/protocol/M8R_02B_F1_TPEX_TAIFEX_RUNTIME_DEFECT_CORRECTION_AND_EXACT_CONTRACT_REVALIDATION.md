# M8R-02B-F1 TPEx/TAIFEX Runtime Defect Correction and Exact Contract Revalidation

Status: `m8r_02b_f1_go`

Decision: `GO`

Revalidation run ID: `m8r02b-f1-20260715T170000Z`.

Historical validation run ID: `m8r02b-20260715T020000Z` remains `NO_GO`; its artifacts were not rewritten.

## Corrected defects

- TPEx `6488` is now covered by a bounded validation seed entry in the official EOD security-master seed. The seed remains incomplete and fail-closed for unknown symbols.
- TAIFEX MIS production execution now separates the source-native context type from the orchestration-requested context type. The source-native context type is preserved in `provenance.source_native_context_type` while the source context binds to the requested context type for AI package construction.
- TAIFEX MIS option runtime-symbol corroboration no longer requires literal `YYYYMM` inside the runtime symbol. The fail-closed corroboration checks non-empty accepted option grammar, product prefix, and normalized strike, while exact expiry/call-put/session remain validated from resolver identity.

## Bounded option discovery

Discovery artifact: `research/m8r/live_validation/m8r02b-f1-20260715T170000Z/taifex_option_contract_discovery.json`. Discovery run `m8r02b-f1-discovery-20260715T150001Z` found the selected `TXO/TX 202607 40000 C` identity in both `TAIFEX_MIS` and `TAIFEX_OPENAPI` bounded identity evidence before operator selection.

Selected operator identity for revalidation:

```json
{
  "product": "TXO",
  "underlying": "TX",
  "expiry": "202607",
  "strike": "40000",
  "call_put": "C",
  "contract_type": "monthly",
  "session": "regular"
}
```

The discovery artifact retained only bounded identity metadata, per-source counts, and status/reason codes; it did not retain raw option-chain rows, SockJS frames, cookies, headers, tokens, prices, volume, open interest, bid/ask ladders, or full-chain payloads. Operator selection is recorded separately in `operator_selected_option_contract.json` with authorization reference `user_prompt_PR141_NEXT_COMMIT_explicit_selection_TXO_TX_202607_40000_C_monthly_regular`.

## Revalidated cases

The F1 evidence set preserves the two previously corrected non-option cases by explicit prior F1 receipt reference and contains a new option live execution subrun sequenced after corrected cross-source discovery and authorized operator selection:

| Case | Result | Notes |
|---|---|---|
| `TPEX_OPENAPI_EOD_6488` | `passed_with_caveats` | TPEx official EOD row retained as `equity`; AI package valid. |
| `TAIFEX_MIS_FUTURE_EXACT` | `passed_with_caveats` | Exact `TX 202607` monthly regular identity retained; native context type preserved; requested context type bound to `liveish_observation`; AI package valid. |
| `TAIFEX_MIS_OPTION_EXACT` | `passed_with_caveats` | Selected `TXO/TX 202607 40000 C` monthly regular identity retained; runtime symbol grammar/product/strike corroboration passed without literal `YYYYMM`; AI package valid. |
| `TAIFEX_OPENAPI_OPTION_EXACT` | `passed_with_caveats` | Same selected option identity retained at contract level; AI package valid. |

Historical accepted cases inherited by reference from immutable M8R-02B evidence:

- `TWSE_MIS_LISTED_2330`
- `TWSE_MIS_OTC_6488`
- `TWSE_MIS_TAIEX`
- `TWSE_OPENAPI_EOD_2330`
- `TAIFEX_OPENAPI_FUTURE_EXACT`

## Final disposition

```json
{
  "m8r_02b_historical_status": "NO_GO",
  "m8r_02b_f1_status": "GO",
  "f1_network_execution_performed": true,
  "historical_source_execution_artifacts_unchanged": true,
  "f1_execution_artifacts_new": true,
  "live_execution_code_base_commit_sha": "08d18d9c6c3cfe0f5307c7dfd19afb8ad0d7af49",
  "live_execution_worktree_dirty": true,
  "live_execution_patch_commit_sha": "fd41cdc0adc272a63e99e09c7d34978461e33fe9",
  "m8r_02b_final_disposition": "GO_AFTER_CORRECTIVE_REVALIDATION",
  "production_executor_adapters_ready": true,
  "production_live_execution_ready": true,
  "live_validation_completed": true,
  "m8r_02b_required": false
}
```

Recommended successor: `M8R-04-CONTROLLED-AI-CONVERSATION-HANDOFF`.
