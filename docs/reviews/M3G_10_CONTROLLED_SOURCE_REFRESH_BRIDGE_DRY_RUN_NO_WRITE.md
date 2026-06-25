# M3G-10 Completion Report: Controlled Source Refresh Bridge Dry-Run No-Write

## 1. Final Status

**Status:** COMPLETE (Dry-Run / No-Write Phase)

M3G-10 verifies that the post-M3G-09 controlled live probe evidence adapter can feed the downstream artifact pipeline entirely in memory:

```text
controlled live probe evidence fixture
→ M3G-09 adapter
→ latest market snapshot
→ watchlist observations
→ AI context pack
→ ChatGPT briefing
```

This milestone does **not** authorize production artifact refresh. It does not execute live network probes, does not write `research/generated/*`, and does not write `frontend/public/*`.

## 2. Files Changed

* `docs/protocol/M3G_CONTROLLED_LIVE_PROBE_OUTPUT_CONTRACT.md` — aligned canonical run summary `results` shape with the implemented dict-by-source runner output.
* `docs/protocol/M3G_LIVE_PROBE_TO_SNAPSHOT_MAPPING_CONTRACT.md` — added compatibility note for legacy array-shaped run summaries.
* `scripts/m3g_live_probe_to_snapshot_adapter.py` — switched fallback mapping to explicit `None` checks so valid falsy evidence values such as `0.0` and `0` seconds survive mapping.
* `scripts/generate_latest_market_snapshot.py` — preserves adapter-provided `delayed_quote`, `stale_quote`, and explicit delay/freshness semantics instead of blindly converting Yahoo/TWSE MIS candidates to `live_candidate`.
* `scripts/generate_watchlist_observations.py` — emits a dedicated delayed quote observation so delayed data is not collapsed into live candidate language.
* `scripts/generate_ai_context_pack.py` — adds delayed quote counting to freshness/delay summaries.
* `scripts/run_m3g10_bridge_dry_run.py` — adds a no-write, in-memory bridge verification utility.
* `tests/unit/test_m3g10_bridge_dry_run.py` — validates valid, blocked identity mismatch, and official EOD bridge scenarios.
* Existing tests were extended for adapter zero-value preservation, delayed quote snapshot semantics, and delayed quote observations.

## 3. Dry-Run Boundary

M3G-10 only calls pure in-memory build/render functions. It intentionally avoids CLI entrypoints that write production files:

* Uses `build_adapter_report(...)` instead of executing live probes.
* Uses `build_snapshot(..., mock_inputs=...)` instead of `generate_snapshot()`.
* Uses `build_watchlist_observations(snapshot)` instead of `generate_observations()`.
* Uses `build_ai_context_pack(snapshot, observations)` instead of `generate_ai_context_pack.py` `main()`.
* Uses `render_chatgpt_briefing(pack)` instead of `generate_chatgpt_briefing.py` `main()`.

## 4. Semantic Preservation Checks

The dry-run report records whether these source governance semantics survive the pipeline:

* `identity_mismatch` blocks source propagation.
* `failed_targets` and `unsupported_targets` remain visible in the adapter report.
* `delayed_quote`, `stale_quote`, and `eod_reference` are not collapsed into generic live language.
* Official OpenAPI sources remain `eod_reference` only.
* TWSE MIS remains `unofficial_frontend` with `unofficial_source_risk` caveats.
* Yahoo Finance remains `third_party` with `third_party_coverage_caveats`.

## 5. Validation Commands

```bash
python -m compileall scripts tests
pytest -m "not network" tests/unit/test_m3g_live_probe_to_snapshot_adapter.py tests/unit/test_m3g10_bridge_dry_run.py tests/test_generate_latest_market_snapshot.py tests/test_generate_watchlist_observations.py tests/test_generate_ai_context_pack.py tests/test_generate_chatgpt_briefing.py
python scripts/run_m3g10_bridge_dry_run.py tests/fixtures/m3g_live_probe_evidence/run_summary_valid.json --targets-config config/market_targets.json
```

## 6. Remaining Boundaries

* Production generated artifact writes remain unauthorized.
* Frontend refresh remains unauthorized.
* Live network probe execution remains outside this dry-run milestone.
* Staging writes should be handled by a future M3G-11 milestone only after this no-write bridge remains green.

## 7. Recommended Next Milestone

`LEGACY-01-RUN-ALL-PROBES-HARD-GATE` or `M3G-11-CONTROLLED-REFRESH-STAGING-WRITE`.

The safer ordering is to hard-gate legacy probe execution before enabling any staging write path.
