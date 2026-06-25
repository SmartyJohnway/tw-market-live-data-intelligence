# M3G Controlled Source Refresh Bridge Design

## Purpose
This document outlines the **design** for a future automated bridge that will safely promote controlled live probe evidence into production-ready generated artifacts (`research/generated/*` and `frontend/public/*`).

*Note: This is a design-only document. The bridge itself must not be implemented or activated until a future milestone explicitly authorizes it.*

## Source of Truth Hierarchy

When attempting to refresh generated artifacts, the system must respect the following source of truth hierarchy, prioritizing safety and predefined constraints over newly discovered data:

1. **Protocol Docs and Caveat Register**: Absolute constraints (e.g., prohibited sources, required caveats, boundaries).
2. **Controlled Live Probe Outputs**: Recent, validated evidence artifacts stored in `research/controlled_live_probe_outputs/`.
3. **Reviewed Generated Artifacts**: The previous stable state in `research/generated/`.
4. **Frontend Readonly Artifacts**: Display-layer artifacts in `frontend/public/`.

## Preconditions for Artifact Refresh
Before the bridge can execute a refresh of production artifacts, all of the following preconditions must be met:
- The refresh is explicitly authorized under an active, controlled milestone.
- Valid, non-stale evidence artifacts exist in the controlled output directory.
- The `contract_status` for the source to be promoted must be `normalized_pass` (or explicitly authorized for promotion despite warnings).
- Target symbols must strictly fall within the bounded watchlist in `config/market_targets.json`.

## Fail-Closed Behavior
If any validation step fails during the bridge execution (e.g., missing evidence, identity mismatch, source not authorized):
- The bridge must **fail closed**.
- It must **not** overwrite existing artifacts with empty or degraded data unless explicitly instructed to do so to reflect an outage.
- It must log the failure and exit.

## Allowed vs. Prohibited Sources

### Allowed Sources for Refresh Promotion
- `TWSE_OpenAPI` (EOD only)
- `TPEx_OpenAPI` (EOD only)
- `TWSE_MIS` (Live candidate, with caveats)
- `Yahoo_Finance` (Bounded low-frequency candidate, identity-validated)

### Prohibited / Deferred Sources
The following sources are strictly prohibited from being promoted to generated artifacts in the current phase:
- `FinMind`
- `Fugle`
- `Fubon`
- Any broker, authentication, or account execution endpoints.
- Any full-market scans (only bounded watchlist targets are allowed).

## Caveat Preservation Rule
The bridge must preserve all caveats defined in the caveat register (`M3G_CURRENT_CAVEATS_REGISTER.md`) and the original evidence envelopes when writing to downstream artifacts. It must not silently drop safety warnings or limitations (e.g., `offline_mode`, `identity_mismatch`, bounded scope).

## Non-Mutation Rule
The bridge **must not write** to `research/generated/*` or `frontend/public/*` unless a future milestone explicitly authorizes its implementation and execution. Currently, it exists solely as a conceptual design to inform that future milestone.
