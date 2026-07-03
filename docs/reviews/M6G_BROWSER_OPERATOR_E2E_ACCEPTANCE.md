# M6G Browser/Operator E2E Acceptance

## Purpose

M6G adds a browser/operator acceptance layer for the local FastAPI plus readonly frontend workflow. It is not feature development, source expansion, trading functionality, polling, scheduling, or a canonical package mutation.

M6G exists because script/static acceptance cannot prove that a real operator can open the frontend, operate the DOM, generate the actual watchlist payload, and reach the same local API path used for validation, planning, and explicit bounded observation.

## Relationship to M6E and M6F

- M6E is script/operator check-only acceptance. It aggregates local validators and API/MCP/frontend contract checks without executing browser automation.
- M6F fixed operator-blocking defects found by actual clone-and-run use: frontend row payload generation had to include item `id`, and FastAPI execution had to honor `TW_MARKET_SSL_POLICY` when no query parameter is provided.
- M6G prevents similar regressions by adding an optional Playwright browser path plus non-browser regression tests for report schema, skip behavior, final status logic, check-only no-execution behavior, artifact path bounds, and SSL policy propagation.

## Command

```bash
python scripts/run_m6g_browser_operator_e2e.py --check-only
```

Check-only may start local FastAPI and browser automation, but it must not execute live observation, poll, schedule, mutate M5F, write `frontend/public`, or write `research/generated`.

## Installing browser tooling

Browser automation is optional for default CI. To run the full browser path:

```bash
python -m pip install playwright
python -m playwright install chromium
python scripts/run_m6g_browser_operator_e2e.py --check-only
```

If Playwright or Chromium is unavailable, the script writes an M6G report with `final_status=skipped_with_caveats` and actionable install/run instructions.

## Explicit bounded live operator check

Live mode is manual and explicit:

```bash
python scripts/run_m6g_browser_operator_e2e.py --execute-bounded-live-check --ssl-policy compatibility
```

or:

```bash
python scripts/run_m6g_browser_operator_e2e.py --execute-bounded-live-check --ssl-policy strict
```

Live mode may execute one bounded observation through the frontend path. If browser live button automation is unavailable after browser payload validation, the script may fall back to the same local FastAPI endpoint used by the frontend and records that caveat. Live output is observation evidence only, not canonical context, not realtime-guaranteed, and not trading output.

## Scenario A: non-network browser check-only

The check-only scenario starts local FastAPI, opens `frontend/readonly-preview/M5KLocalAIWorkbench.html`, loads the default watchlist, edits an actual DOM row, clicks Plan, captures validate/plan request payloads, and verifies every generated item includes `id`, `symbol`, `category`, `adapter`, `preferred_sources`, and `enabled`. The `id` format must be `category:symbol`. The script also verifies that `/api/m5k/live-observation/execute` is not called in check-only mode and no repeated execution/polling occurs.

## Scenario B: SSL policy propagation

M6G includes an API-level assertion adjacent to the browser flow:

- no query `ssl_policy` plus `TW_MARKET_SSL_POLICY=compatibility` resolves to `compatibility`,
- explicit query `ssl_policy=strict` overrides the environment,
- invalid environment/query policy fails closed before execution.

This preserves strict TLS as default, explicit compatibility opt-in, explicit unsafe-only behavior, and no silent fallback.

## Scenario C: optional explicit live check

If an operator runs live mode, the report records the exact mode, timestamp, requested SSL policy, effective temporary server environment SSL policy, browser execute SSL policy source (`env` or `default`), targets, whether network calls may have occurred, output artifacts, and caveats. The frontend execute button does not currently append an `ssl_policy` query parameter, so non-strict browser live policy is applied explicitly through the temporary FastAPI process environment; strict uses the server default with no compatibility override. It does not assert exact price, market direction, recommendation, ranking, target price, or buy/sell/hold.

## Report artifacts

M6G writes only:

- `research/live_observation_runs/m6g_browser_operator_e2e/latest_browser_operator_e2e_report.json`
- `research/live_observation_runs/m6g_browser_operator_e2e/latest_browser_operator_e2e_report.md`

## Forbidden behavior boundaries

M6G must not mutate M5F, change M5F schema, change observation/source-health/conversation semantics, create parallel contracts, write `frontend/public`, write `research/generated`, write production/prod paths, add broker/auth/orders, add polling/scheduler/startup network calls, perform full-market scans, expose raw endpoint payloads in product/AI surfaces, silently disable TLS verification, or produce trading outputs.
