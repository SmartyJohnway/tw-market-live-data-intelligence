# M5Q Source Health Operator Guide

## When to run source health

Run M5Q when the operator needs bounded evidence for the question: “Are the live observation sources usable right now?” It is a manual regression probe for representative routes only, not a scanner and not a trading workflow.

## How to run check-only

```bash
python scripts/run_m5q_source_health_probe.py --check-only
```

Check-only performs no network calls and no writes. It validates the default watchlist, the M5L source adapter matrix, the selected targets (`2330`, `0050`, `3483`, `TAIEX`, `TX`), the route plan, and the governance boundaries: bounded targets, no full-market scan, no polling, no scheduler, no M5F mutation, no `frontend/public` write, and no `research/generated` write.

## How to run explicit health probe

```bash
python scripts/run_m5q_source_health_probe.py --execute-health-probe
```

Execution may perform bounded network calls for only the selected health targets. It writes normalized reports under `research/live_observation_runs/source_health/`:

- `source_health_report.json`
- `source_health_report.md`
- `latest_source_health_report.json`
- `latest_source_health_report.md`

## How to interpret healthy / degraded / failed / unsupported

- `healthy`: the route is supported, observation status is `ok`, a value is present, the value is not reference-only, and no fatal freshness/source failure is detected.
- `degraded`: the route responds with reference-only data, unavailable value, partial data, stale/closed-session freshness, or caveats that prevent current-like interpretation.
- `failed`: the route is expected to be supported but the request, parsing, target lookup, or normalization fails.
- `unsupported`: the route is intentionally out of scope or not implemented by the current adapter matrix.

## How source health differs from live observation

M5K live observation collects bounded Level 2 observations for operator discussion. M5Q source health reduces representative M5K/M5L routes into a regression report focused on source usability. M5Q does not add sources, does not scan the market, does not schedule polling, does not mutate M5F, and does not publish frontend artifacts.

## How to use source health in ChatGPT conversation context

After running an explicit health probe, open the frontend operator workbench or call `GET /api/conversation/context`. If `latest_source_health_report.json` exists, the conversation context includes `source_health_status = "available"`, summary counts, per-source-family status, degraded/failed targets, and caveats. If no report exists, it includes `source_health_status = "not_available"`. Raw endpoint payload is excluded.

## Troubleshooting

- If check-only fails, inspect watchlist validation and `config/m5l_live_source_adapter_matrix.json` validation errors.
- If a target is `failed`, inspect the failure reason and retry manually later; do not infer a current value from yesterday’s close or reference-only data.
- If a target is `degraded`, display the caveats and freshness fields before discussing reliability with AI.
- If `/api/source-health/latest` returns `not_available`, run the explicit probe or confirm the report exists under `research/live_observation_runs/source_health/`.

## Safety boundaries

M5Q must not mutate M5F, write `frontend/public`, write `research/generated`, add broker/auth flows, place orders, poll, schedule, run at startup, emit buy/sell/hold, emit rankings, emit target prices, include raw endpoint payload in product reports or conversation context, or perform full-market scans.
