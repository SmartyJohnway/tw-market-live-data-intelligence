# MCP-03 Governed Controlled Evidence Readback

## Final status

MCP-03 adds one explicit governed readonly MCP tool for controlled evidence readback:

- `read_m3g04_latest_controlled_probe_evidence`

The tool reads existing local controlled probe summary evidence only. It does not execute live probes, refresh production snapshots, refresh frontend artifacts, write generated artifacts, or promote evidence into production state.

## Scope

MCP-03 is limited to readonly filesystem readback of durable controlled evidence summaries already present in the repository under:

- `research/live_probe_runs/m3g_04/`

The tool is intended for research evidence inspection and governance review. It is not a production market-data access surface.

## Behavior

The tool accepts optional bounded filters:

- `requested_sources`: optional source allowlist filter restricted to the MCP-02 controlled source set:
  - `TWSE_OpenAPI`
  - `TPEx_OpenAPI`
  - `TWSE_MIS`
  - `Yahoo_Finance`
- `requested_targets`: optional target allowlist filter restricted to standard symbols in `config/market_targets.json`.
- `max_runs`: optional bounded integer from 1 to 5, defaulting to 1.

When valid evidence exists, the latest `run_summary_*.json` files are selected by filename in descending order up to `max_runs`, parsed as JSON, and returned with governance metadata, requested scope, resolved scope, selected run paths, filter metadata, and freshness/delay caveats.

## Governance controls

Every response states that MCP-03 is a readonly evidence readback surface and includes governance metadata:

- `surface`: `MCP controlled evidence readonly readback tool`
- `execution_mode`: `readonly_local_controlled_evidence_read`
- `network_calls`: `false`
- `live_probe_execution`: `false`
- `production_refresh`: `false`
- `frontend_refresh`: `false`
- `generated_artifact_writes`: `false`
- `evidence_readback_only`: `true`
- `full_market_scan`: `false`
- `trading_signal`: `false`

The response caveats explicitly include:

- `controlled_evidence_readback_only`
- `not_live_probe_execution`
- `not_production_refresh`
- `not_frontend_refresh`
- `not_generated_artifact_refresh`
- `not_live_market_guarantee`
- `no_trading_signal`

## Readback directory and path restrictions

MCP-03 does not accept arbitrary file paths. The implementation uses the fixed evidence directory:

- `research/live_probe_runs/m3g_04/`

The tool rejects unsupported arguments such as `path`, absolute paths, or traversal-like arbitrary path requests because they are not part of the schema or implementation. It only discovers files matching `run_summary_*.json` directly from the allowed evidence directory.

## Fail-closed cases

The tool fails closed for:

- missing evidence directory: `status: no_evidence_available`
- empty evidence directory: `status: no_evidence_available`
- invalid `max_runs`: `status: failed_closed`, `failure_reason: invalid_max_runs`
- unsupported arguments: `status: failed_closed`, `failure_reason: unsupported_argument`
- invalid source list shape: `status: failed_closed`, `failure_reason: invalid_source_scope`
- source outside allowlist: `status: failed_closed`, `failure_reason: source_outside_allowlist`
- duplicate sources: `status: failed_closed`, `failure_reason: duplicate_source_scope`
- invalid target list shape: `status: failed_closed`, `failure_reason: invalid_target_scope`
- target outside `config/market_targets.json`: `status: failed_closed`, `failure_reason: target_outside_allowlist`
- duplicate targets: `status: failed_closed`, `failure_reason: duplicate_target_scope`
- invalid evidence JSON: `status: invalid_evidence_json` with the evidence file path relative to the repo and parse error

In all fail-closed cases, the tool does not invoke the controlled probe runner and does not attempt to repair or infer evidence.

## Non-goals

MCP-03 does not authorize or perform:

- live probe execution
- network calls
- full-market scans
- `scripts/run_all_probes.py`
- direct legacy live probe MCP tools
- FinMind, Fugle, Fubon, broker, or authentication enablement
- production refresh
- staging writes
- `research/generated/*` writes
- `frontend/public/*` writes
- frontend refresh
- trading signals
- buy/sell/hold recommendations
- realtime claims
- durable evidence promotion into production snapshots or frontend artifacts

## Validation commands

The MCP-03 implementation was validated with:

```bash
python -m compileall server tests
pytest -m "not network" tests/unit/test_mcp_server.py
pytest -m "not network"
```

## Next recommended step

Review MCP-03 evidence readback responses from existing `research/live_probe_runs/m3g_04/run_summary_*.json` files and decide whether MCP-04 should add a governed comparison/reporting layer. Any future production refresh, generated artifact refresh, frontend refresh, or durable evidence promotion should remain separately authorized and explicitly scoped.
