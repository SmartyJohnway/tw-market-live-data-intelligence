# MCP-02 — Explicit Controlled Live Probe Tools

## Final status

Completed. The MCP server now keeps the MCP-01 readonly context tools as the default local context surface and adds exactly one explicit governed controlled live-probe evidence tool: `run_m3g04_controlled_live_probe_evidence`.

## Scope

Changed files:

- `server/mcp_server.py`
- `tests/unit/test_mcp_server.py`
- `docs/reviews/MCP_02_EXPLICIT_CONTROLLED_LIVE_PROBE_TOOLS.md`
- `docs/protocol/M3G_CURRENT_CAVEATS_REGISTER.md`

## Behavior

`list_tools()` now exposes:

- the six MCP-01 readonly local context tools;
- one MCP-02 explicit controlled probe tool, `run_m3g04_controlled_live_probe_evidence`.

The MCP server still does not expose these legacy probe tool names:

- `probe_twse_openapi`
- `probe_tpex_openapi`
- `probe_yahoo_finance`
- `probe_twse_mis`
- `probe_finmind`

Those legacy names remain unavailable and do not execute live probe logic.

## Governance controls

The controlled MCP tool requires all of the following before execution:

- `confirm_controlled_live_probe: true`
- `requested_sources` within the governed controlled source allowlist:
  - `TWSE_OpenAPI`
  - `TPEx_OpenAPI`
  - `TWSE_MIS`
  - `Yahoo_Finance`
- `requested_targets` within `config/market_targets.json` standard-symbol allowlist;
- duplicate sources or targets are rejected before execution;
- `max_targets` between 1 and 5, with requested target count at or below the bound;
- `no_artifact_writes: true`
- `no_frontend_writes: true`
- `no_production_refresh: true`

The MCP tool response includes governance metadata with:

- `surface: MCP explicit controlled live probe tool`
- `execution_mode: explicit_confirmed_controlled_probe`
- `production_refresh: false`
- `frontend_refresh: false`
- `artifact_writes: false`
- `full_market_scan: false`
- `trading_signal: false`
- caveats for controlled evidence collection only, no production refresh, no frontend refresh, no live-market guarantee, and no trading signal.

## Execution boundary

Confirmed execution is routed only through the bounded controlled runner wrapper for `scripts/run_m3g04_controlled_live_probe.py`. The MCP module does not import the legacy individual probe modules and does not directly expose broad legacy probe functions.

The wrapper executes the runner with the repository on `PYTHONPATH` but with an isolated temporary working directory. This preserves runner compatibility while preventing repository `research/generated/*`, `frontend/public/*`, or production artifact writes from the MCP surface. If the runner produces a temporary `run_summary_*.json`, the MCP response includes that summary before the temporary directory is removed. MCP-02 does not persist controlled evidence into the repository; durable evidence readback or persistence is deferred to MCP-03 or another explicit milestone.

The wrapper is injectable so unit tests can monkeypatch it. The unit tests do not perform live network calls.

## Fail-closed cases

The controlled tool fails closed without executing the runner when:

- explicit confirmation is missing or false;
- requested source scope is empty, malformed, duplicated, or outside the allowlist;
- requested target scope is empty, malformed, duplicated, outside `config/market_targets.json`, or above bounds;
- write/refresh prohibitions are not explicitly set to true;
- the controlled runner path is missing before subprocess launch;
- the controlled runner times out after subprocess launch;
- the controlled runner raises an error after subprocess launch.

Validation and missing-runner failures preserve `network_calls: false`, `live_probe_execution: false`, and `runner_started: false`. Post-launch timeout or runner-error responses do not claim no network/live execution; they include `runner_started: true` and `network_calls_may_have_occurred: true` while still stating that generated artifacts, frontend artifacts, and production snapshots were not updated.

## Non-goals

MCP-02 did not authorize or implement:

- full-market scans;
- `scripts/run_all_probes.py` execution;
- direct legacy live probe MCP tools;
- FinMind, Fugle, Fubon, broker, auth, or credentialed automation;
- production refresh;
- staging writes;
- `research/generated/*` writes;
- `frontend/public/*` writes;
- frontend refresh;
- trading signals, buy/sell/hold outputs, or realtime guarantees.

## Validation commands

- `python -m compileall server tests`
- `pytest -m "not network" tests/unit/test_mcp_server.py`
- `pytest -m "not network"`

## Next recommended step

MCP-03 should evaluate whether controlled MCP probe evidence should remain runner-output-only or gain a separate, explicitly governed local evidence-readback tool for `research/live_probe_runs/m3g_04/`, without promoting evidence into production snapshots or frontend artifacts.
