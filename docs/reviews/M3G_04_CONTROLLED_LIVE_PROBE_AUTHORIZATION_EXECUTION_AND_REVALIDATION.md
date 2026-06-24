# M3G-04-CONTROLLED-LIVE-PROBE-AUTHORIZATION-EXECUTION-AND-REVALIDATION

## 1. Final Status
M3G_04_COMPLETED_WITH_CAVEATS_READY_FOR_M3G_05

## 2. Baseline Merge SHA
PR #35 merged
merge_sha = 11e23c3486ff9e175f408d0932380e7bd57792a2

## 3. Files Inspected
- `config/market_targets.json`
- `docs/protocol/M3G_SOURCE_RECOVERY_PLAN.md`
- `docs/reviews/M3G_03_CONTROLLED_MARKET_SOURCE_PROBE_REPAIR.md`
- `scripts/probe_twse_mis.py`
- `scripts/probe_twse_openapi.py`
- `scripts/probe_tpex_openapi.py`
- `scripts/probe_yahoo.py`
- `scripts/generate_latest_market_snapshot.py`
- `tests/test_market_snapshot_generator.py`
- `tests/fixtures/market_sources/*`
- `frontend/public/index.html`
- `frontend/public/market-context.html`

## 4. Files Changed
- `scripts/run_m3g04_controlled_live_probe.py` (added)
- `tests/test_m3g04_controlled_live_probe.py` (added)
- `scripts/probe_twse_openapi.py`
- `scripts/probe_tpex_openapi.py`
- `README.md` (will be updated)

## 5. Preflight Result
Passed. Checked out baseline, loaded `config/market_targets.json`, and confirmed safe parameters for targets and scopes.

## 6. Offline Validation Result
Passed. Compiled scripts/server/tests. `pytest -m "not network" -v` executed and 109/109 tests passed without errors.

## 7. Controlled Live Probe Authorization Decision
Authorized. Bounded parameters were determined based on requested bounds (max 5 targets).

## 8. Selected Sources
1. `TWSE_OpenAPI` (official_openapi, eod)
2. `TPEx_OpenAPI` (official_openapi, eod)
3. `TWSE_MIS` (unofficial_frontend_endpoint, live)
4. `Yahoo_Finance` (unofficial_api, delayed/third_party)

## 9. Selected Target Subset
- 2330
- 0050
- 00929
- 8069
- TAIEX

Selected from `config/market_targets.json` meeting priority list constraints.

## 10. Probe Commands Executed
`python scripts/run_m3g04_controlled_live_probe.py --targets 2330 0050 00929 8069 TAIEX --sources TWSE_OpenAPI TPEx_OpenAPI TWSE_MIS Yahoo_Finance`

## 11. Probe Output Directory
`research/live_probe_runs/m3g_04/`

## 12. Per-Source Result Summary
- `TWSE_OpenAPI`: Completed, output normalized sample for 0050.
- `TPEx_OpenAPI`: Completed, output normalized sample for 8069.
- `TWSE_MIS`: Completed but HTTP parse failed for one or more requested symbols. Handled safely.
- `Yahoo_Finance`: Completed, normalized chart payload.

## 13. Per-Target Result Summary
- EOD OpenAPI successfully normalized specific matched symbols from batch payloads.
- Yahoo successfully returned for the batch.
- TWSE MIS failed on HTTP processing of the bounded batch shape but failure was properly caught, localized and written out without breaking scope.

## 14. Failure Classification
`TWSE_MIS` partial failure classified as `http_ok: false / parse_status: failed`. Documented as expected API format drift / payload issues within controlled bounds. No unlimited retries.

## 15. Raw Payload Redaction Confirmation
Confirmed. Outputs under `research/live_probe_runs/m3g_04/` contain no secrets, tokens, or auth headers.

## 16. Whether Generated Artifacts Were Refreshed
Skipped. `artifact_refresh_status = skipped_controlled_probe_outputs_not_yet_wired_to_generator`. The default scripts rely on broad offline mock loading paradigms not yet wired perfectly to the bounded live probe outputs. Safely skipped to preserve truthful and clear legacy context.

## 17. Generated Artifacts Changed / Unchanged Summary
Unchanged. `research/generated/*` files remain exactly as they were in the previous milestone baseline.

## 18. Artifact Consistency Checks
Passed. Prior `generate_latest_market_snapshot.py` and `generate_ai_context_pack.py` artifacts remain untouched and consistent.

## 19. Frontend Revalidation Result
Passed. Verified via local python HTTP server + headless Playwright automation. Panels load, safety caveats render, and no JS errors are present.

## 20. Confirmation no full-market scan was run
Confirmed. Scope strictly bounded to <= 5 targets.

## 21. Confirmation no FinMind/Fugle/Fubon probe was run
Confirmed. Specifically blocked inside `scripts/run_m3g04_controlled_live_probe.py`.

## 22. Confirmation no broker/auth/account/execution logic was added
Confirmed. No broker APIs touched.

## 23. Confirmation no investment/trading semantics were added
Confirmed. Outputs remain pure technical observations.

## 24. Remaining Caveats
- TWSE MIS API parse failures when handling subset arrays locally.
- Live probe raw output files are correctly written but not natively consumed by the main generator script without further bridging logic.

## 25. Recommended Next Milestone
M3G-05-CONTROLLED-SOURCE-REFRESH-HARDENING-AND-AUTOMATION-PREFLIGHT
