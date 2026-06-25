# M3G Controlled Source Refresh Bridge Preflight

## 1. Purpose and Scope
This document provides a preflight readiness assessment for implementing a future "Controlled Source Refresh Bridge." The bridge's purpose is to safely promote evidence from controlled live probes (`research/live_probe_runs/*`) into production-ready generated artifacts (`research/generated/*`) while strictly enforcing all M3G caveat, boundary, and fail-closed policies.

This preflight:
- Maps the available live probe outputs to the expected artifact contracts.
- Documents the input assumptions of the current artifact generators.
- Identifies gaps, mapping requirements, and blockers.

## 2. Explicit Non-Goals
- This is **not** an implementation document.
- It does **not** implement bridge code.
- It does **not** authorize modifying generated artifacts, running live probes, or automatically promoting artifacts to the frontend.
- It does **not** expand the probe scope beyond the configured watchlist.

## 3. Current Source-of-Truth Hierarchy
When promoting data, the bridge must respect this hierarchy:
1. **Protocol Docs and Caveat Register**: Absolute constraints (prohibited sources, required caveats).
2. **Controlled Live Probe Outputs**: Recent, validated evidence in `research/live_probe_runs/`.
3. **Reviewed Generated Artifacts**: Previous stable state in `research/generated/`.
4. **Frontend Readonly Artifacts**: Display-layer artifacts.

## 4. Existing Controlled Live Probe Output Shape
Live probes produce a `run_summary_<timestamp>.json` and per-source files containing:
- Run-level fields: `timestamp`, `targets`, `sources_requested`, `results`.
- Source-level fields: `source_id`, `status`, `contract_status`, `http_ok`, `parse_status`, `normalization_status`, `failed_targets`, `errors`, `output_file`.
(Defined in `docs/protocol/M3G_CONTROLLED_LIVE_PROBE_OUTPUT_CONTRACT.md`)

## 5. Existing Generated Artifact Consumers & Current Assumptions

Current artifact generators rely on offline mock inputs or already generated upstream JSONs. None of them currently consume the controlled live probe output schema.

| Generator | Current Input Assumption |
| :--- | :--- |
| `generate_latest_market_snapshot.py` | Reads `config/market_targets.json` and takes `mock_inputs` dictionary directly from test fixtures or CLI mapping. Defaults to offline mode if `mock_inputs` is not provided. It **does not** read `run_summary.json` or live probe evidence files. |
| `generate_watchlist_observations.py` | Reads the existing `research/generated/latest_market_snapshot.json`. |
| `generate_ai_context_pack.py` | Reads the existing `research/generated/latest_market_snapshot.json` and `research/generated/watchlist_observations.json`. |
| `generate_chatgpt_briefing.py` | Reads the existing `research/generated/ai_context_pack.json`. |
| `M3E Frontend Viewer` | Fetches `research/generated/ai_context_pack.json` via native fetch(). |

## 6. Bridge Readiness Matrix (Gap Analysis)

This matrix maps fields from the controlled live probe output to the requirements of the generators (the entry point for all downstream artifacts).

| downstream artifact | current generator | current input assumptions | controlled live probe fields available | missing fields / transformations | caveats required | can bridge safely now? | required before implementation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `latest_market_snapshot` | `generate_latest_market_snapshot.py` | Target config + direct mock symbol dicts | `run_summary` timestamp, per-source `output_file` paths | Must parse `output_file` to extract normalized symbol data, map timestamp to `generated_at_utc`. | Maintain `offline_mode` if no input | `No (Blocked)` | `needs_mapping`: Bridge must unwrap `output_file` payloads into snapshot mock_inputs. |
| `latest_market_snapshot` | `generate_latest_market_snapshot.py` | Infers offline failures | `contract_status`, `http_ok`, `status`, `errors` | Map `contract_status` to `source_health` block. | `identity_mismatch`, `eod_reference_only` | `No (Blocked)` | `needs_mapping`: Bridge must translate probe errors to snapshot `failed_sources`. |
| `latest_market_snapshot` | `generate_latest_market_snapshot.py` | `target_class_mapping_unknown` | `failed_targets` array | Map probe `failed_targets` into snapshot `failed_symbols`. | `offline_mode_no_local_input` | `No (Blocked)` | `needs_mapping`: Bridge must populate `failed_symbols` from summary array. |
| `latest_market_snapshot` | `generate_latest_market_snapshot.py` | Mock assumptions | Freshness/delay/staleness inside `output_file` JSONs | Must correctly extract staleness metrics. | `stale`, `delayed` | `No (Blocked)` | `needs_mapping`: Ensure delay semantics are extracted from evidence. |
| `ai_context_pack` | `generate_ai_context_pack.py` | `latest_market_snapshot.json` | None directly (relies on snapshot) | Bridge only touches snapshot; pack generator just reads it. | `unofficial_source_risk` | `No` (waits for snapshot) | Snapshot bridging must be fixed first. |
| `chatgpt_briefing` | `generate_chatgpt_briefing.py` | `ai_context_pack.json` | None directly | N/A | Preserved from pack | `No` (waits for pack) | Snapshot bridging must be fixed first. |
| `watchlist_observations` | `generate_watchlist_observations.py` | `latest_market_snapshot.json` | None directly | N/A | Preserved from snapshot | `No` (waits for snapshot) | Snapshot bridging must be fixed first. |
| `frontend UI` | `M3E Frontend Viewer` | `ai_context_pack.json` | None directly | N/A | Rendered from JSON | `No` | Snapshot bridging must be fixed first. |

## 7. Required Bridge Input and Output Contract
- **Input Contract:** `research/live_probe_runs/<run_id>/run_summary_<timestamp>.json` and referenced `output_file` JSONs.
- **Output Contract:** Execution of `generate_latest_market_snapshot.py` using a structured injection of the parsed evidence, resulting in an updated `research/generated/latest_market_snapshot.json` and subsequent downstream artifacts.

## 8. Required Fail-Closed Rules
Future implementation must:
- Refuse to write generated artifacts if input summary is missing or malformed.
- Refuse if source `contract_status` is failed or `identity_mismatch`, unless the artifact strictly supports failed source display.
- Preserve failed_targets, unsupported_targets, warnings, errors.
- Preserve source freshness/staleness/delay caveats explicitly.
- Never turn unofficial live candidates into official realtime claims.
- Never produce buy/sell/hold/ranking/target-price language.
- Never expand beyond the bounded watchlist.

## 9. Required Caveat Propagation Rules
- Maintain global boundary caveats (e.g. `offline_mode` or `unofficial_source_risk`).
- Ensure all caveats from `contract_status` (like `identity_mismatch`) flow through to the snapshot `caveats` array.

## 10. M3G-09 Status (Adapter Preflight)
During the M3G-09 milestone:
* A strict mapping contract was created (`M3G_LIVE_PROBE_TO_SNAPSHOT_MAPPING_CONTRACT.md`).
* An offline, read-only adapter module was implemented (`scripts/m3g_live_probe_to_snapshot_adapter.py`) with deterministic synthetic fixtures.
* The bridge implementation remains blocked until explicit future authorization allows generated artifact writes. No production refresh is active.

## 11. Recommended Next Steps
The next milestone (`M3G-10-CONTROLLED-SOURCE-REFRESH-BRIDGE-DRY-RUN-NO-WRITE`) should focus on performing an end-to-end dry run of the bridge logic using the new adapter, ensuring all fail-closed and fail-open states behave correctly without writing any production artifacts.
