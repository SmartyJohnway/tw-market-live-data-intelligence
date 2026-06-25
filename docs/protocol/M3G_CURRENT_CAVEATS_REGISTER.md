# M3G Current Caveats Register

## Purpose
This document centralizes the current project constraints, boundaries, and known limitations (caveats) for the M3G phase. It acts as a primary source of truth to ensure no future automation or agent accidentally violates these boundaries.

## Caveats Register

| caveat_id | category | applies_to | meaning | required_handling | blocks_next_step? | repair_or_deferral |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CAV-M3G-001` | Scope Boundary | All Probes / Artifacts | The project strictly evaluates a small subset of predefined symbols. Full market coverage is prohibited. | Must adhere exclusively to `config/market_targets.json`. Full market sweeps must be blocked. | No | Defer to future phases. |
| `CAV-M3G-002` | Output Boundary | AI Context / Briefings | This project is an operational workbench. Generated outputs provide evidence, not trading signals. | All artifacts must explicitly state they are not investment advice. | No | Permanent boundary. |
| `CAV-M3G-003` | Realtime Guarantee | Source Definitions | There is no official real-time guarantee. All sources must define `freshness_status` and `delay_status`. | Ensure explicit labeling of delay semantics. Do not infer "live" status without explicit proof. | No | Permanent boundary. |
| `CAV-M3G-004` | Source Authority | `TWSE_OpenAPI`, `TPEx_OpenAPI` | Official OpenAPI sources provide only End-Of-Day (EOD) data, not intraday live data. | Must be explicitly labeled as `eod`. Must never be presented as realtime. | No | Permanent boundary. |
| `CAV-M3G-005` | Source Reliability | `TWSE_MIS` | The endpoint is unofficial, fragile, rate-limited, and prone to breaking without notice. | Requires strict timeouts, low retry counts, and explicit failure/delay caveats. | No | Defer to ongoing maintenance. |
| `CAV-M3G-006` | Source Authority | `Yahoo_Finance` | It is an unofficial, third-party endpoint requiring explicit structured identity validation. | Do not treat as "highly reliable." Must enforce identity matching and fail closed if a mismatch occurs. | No | Defer to ongoing maintenance. |
| `CAV-M3G-007` | Artifact State | Generated Artifacts | Stale generated artifacts provide historical context but do not represent current live market state. | Treat `research/generated/*` as readonly and historical unless explicitly updated via the controlled refresh bridge. | No | Permanent boundary. |
| `CAV-M3G-008` | Legacy Operations | `run_all_probes.py` | This script is a legacy manual path. It is not the current controlled refresh automation path. | Do not run this script automatically. Only run when explicitly authorized by a future milestone. | No | Permanent boundary. |
| `CAV-M3G-009` | Source Eligibility | `FinMind`, `Fugle`, `Fubon` | Third-party aggregation and broker-authenticated execution endpoints are currently prohibited/deferred. | Do not enable these sources in automated probes. | No | Defer to future phases. |
| `CAV-M3G-010` | Artifact Refresh | Refresh Automation | Production artifacts are currently explicitly readonly. There is no active automated refresh bridge. | The refresh bridge remains a design-only concept. Do not modify generated artifacts. | Yes (for automation) | Address in M3G-08 or later. |
