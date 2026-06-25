# M3G-09 Completion Report: Controlled Live Probe to Snapshot Mapping Contract and Adapter Preflight

## 1. Final Status
**Status:** COMPLETE (Preflight Phase)

The mapping contract has been defined, and a strict, offline, read-only adapter has been implemented and tested. No production artifacts were refreshed, and no real live probes were executed.

## 2. Files Changed
* `docs/protocol/M3G_CONTROLLED_SOURCE_REFRESH_BRIDGE_DESIGN.md` (Updated canonical path)
* `docs/protocol/M3G_CONTROLLED_SOURCE_REFRESH_BRIDGE_PREFLIGHT.md` (Added M3G-09 status)
* `docs/protocol/M3G_CURRENT_CAVEATS_REGISTER.md` (Added caveats CAV-M3G-015 to 017)
* `docs/protocol/M3G_LIVE_PROBE_TO_SNAPSHOT_MAPPING_CONTRACT.md` (New contract document)
* `scripts/m3g_live_probe_to_snapshot_adapter.py` (New offline adapter module)
* `tests/unit/test_m3g_live_probe_to_snapshot_adapter.py` (New adapter unit tests)
* `tests/fixtures/m3g_live_probe_evidence/*` (New synthetic JSON evidence fixtures)
* `docs/reviews/M3G_09_CONTROLLED_LIVE_PROBE_TO_SNAPSHOT_MAPPING_CONTRACT_AND_ADAPTER_PREFLIGHT.md` (This document)

## 3. Adapter Behavior Summary
The new adapter (`scripts/m3g_live_probe_to_snapshot_adapter.py`) successfully bridges the gap between controlled live probe evidence and the downstream `build_snapshot` generator in an entirely offline and read-only manner.
*   **Symbol Standardization:** It localizes a minimal canonical mapping for current probe sources (stripping `.TW`, `.TWO`, and prefix mappings for `TWSE_MIS`).
*   **Partial Fail-Closed:** If an individual source's referenced `output_file` is missing, the adapter correctly flags that specific source as blocked but continues to map valid sources (returning `adapter_status = partial_mapping`).
*   **Total Fail-Closed:** If the top-level run summary is malformed, or if all sources are blocked due to identity mismatches, the adapter halts and returns appropriate error statuses (e.g., `malformed_input` or `identity_mismatch_blocked`).
*   **Memory-Only Output:** It returns an in-memory dictionary structured exactly as the legacy `mock_inputs` parameter expected by `generate_latest_market_snapshot.py`, preserving `failed_targets` and generating a detailed execution report.

## 4. Tests Added
Comprehensive unit tests were added in `tests/unit/test_m3g_live_probe_to_snapshot_adapter.py`:
*   `test_standardize_symbol`: Verifies localized symbol stripping logic.
*   `test_valid_run_summary_mapping`: Validates standard mapping for TWSE_MIS and Yahoo_Finance.
*   `test_yahoo_identity_mismatch_blocks_mapping`: Confirms identity mismatches cleanly block artifact propagation.
*   `test_official_openapi_mapping`: Confirms official sources strictly map as EOD references.
*   `test_missing_output_file_fails_closed`: Verifies partial failure propagation when an evidence file is missing.
*   `test_malformed_run_summary_fails_closed`: Verifies total failure propagation for unreadable summaries.
*   `test_failed_targets_preserved`: Checks that target-level failures survive the mapping intact.
*   `test_snapshot_generator_integration_in_memory`: Confirms the generated in-memory `mock_inputs` object successfully passes through `build_snapshot` using a strict mock target config without crashing.

## 5. Validation Commands and Results
Ran the following validation commands to ensure purely offline success:

```bash
PYTHONPATH="${PYTHONPATH}:/app/scripts:/app/server" python -m compileall scripts server tests
PYTHONPATH="${PYTHONPATH}:/app/scripts:/app/server" pytest -m "not network" -v tests/unit/test_m3g_live_probe_to_snapshot_adapter.py
```
**Results:** All files compiled successfully. All 9 offline tests passed in ~0.18s. No network requests or file writes occurred during execution.

## 6. Explicit Confirmations
As strictly required by the boundaries of this preflight:
*   [x] **No live probes run:** Network execution remained completely blocked.
*   [x] **No generated artifacts refreshed:** The adapter is 100% read-only and `research/generated/*` was untouched.
*   [x] **No frontend artifacts changed:** `frontend/public/*` remains unaffected.
*   [x] **No broker/auth touched:** No authentication endpoints were activated or configured.
*   [x] **No full-market scan:** Symbol handling remained strictly bounded by mock fixtures.
*   [x] **No `run_all_probes.py` executed:** Avoided legacy runner entirely.

## 7. Remaining Blockers
*   **Write Authorization:** The bridge is functionally ready in memory, but production execution (writing the outputs to `research/generated/`) remains unauthorized and requires an explicit dry-run milestone.

## 8. Recommended Next Milestone
The recommended next milestone is:
`M3G-10-CONTROLLED-SOURCE-REFRESH-BRIDGE-DRY-RUN-NO-WRITE`
(To exercise the bridge logic end-to-end dynamically while keeping the final save/write function disabled.)
