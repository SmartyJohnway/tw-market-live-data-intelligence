# M3G-07 Current Caveats Register and Controlled Refresh Governance Repair

## Final Status
Completed. Governance documentation and caveat registries have been successfully updated to accurately reflect the post-M3G-06 state. No live probes were run, and no generated or frontend artifacts were modified.

## Files Changed
- `README.md`: Downgraded `run_all_probes.py` to a legacy/manual section, added explicit M3G project boundaries/status, updated the recommended milestone to M3G-08, and linked new protocol docs.
- `docs/protocol/M3G_CONTROLLED_LIVE_PROBE_OUTPUT_CONTRACT.md`: Created to strictly define the schema, allowed statuses, and non-propagation rules for live probe evidence.
- `docs/protocol/M3G_CONTROLLED_SOURCE_REFRESH_BRIDGE_DESIGN.md`: Created as a design-only document outlining the hierarchy of truth, preconditions, fail-closed behaviors, and allowed/prohibited sources for a future artifact refresh bridge.
- `docs/protocol/M3G_CURRENT_CAVEATS_REGISTER.md`: Created to catalog all M3G boundaries, limits, and deferred items in a clear, actionable table format.
- `docs/protocol/M3G_SOURCE_RECOVERY_PLAN.md`: Updated to bring the status post-M3G-06, recording completed items and defining M3G-07/M3G-08 as the next governance and preflight steps.
- `docs/recommended_architecture.md`: Reworded claims about Yahoo Finance to emphasize it as an unofficial, bounded, low-frequency candidate requiring identity validation, and explicitly labeled TWSE MIS as a fragile live candidate.

## What Was Intentionally Not Changed
- No live network probe scripts (`scripts/run_all_probes.py`, `scripts/run_m3g04_controlled_live_probe.py`) or probe implementations were modified.
- No files in `research/generated/*` or `frontend/public/*` were touched.
- No modifications were made to `config/market_targets.json`.
- No updates to broker/auth configurations or FinMind/Fubon/Fugle implementations were made.

## Confirmation: No Live Probes Were Run
I confirm that no live probes against Yahoo Finance, TWSE MIS, or any OpenAPI/Broker endpoints were executed during this task.

## Confirmation: No Artifacts Were Refreshed
I confirm that no generated AI context packs, matrix artifacts, or frontend display files were refreshed or updated.

## Remaining Caveats and Recommended Next Milestone
- The automated refresh bridge (`M3G_CONTROLLED_SOURCE_REFRESH_BRIDGE_DESIGN.md`) remains purely conceptual and un-implemented.
- Stale generated artifacts remain in the repository as readonly historical context.
- **Recommended Next Milestone**: `M3G-08-CONTROLLED-SOURCE-REFRESH-BRIDGE-PREFLIGHT` (Strictly Preflight/Design Validation, not production activation).
