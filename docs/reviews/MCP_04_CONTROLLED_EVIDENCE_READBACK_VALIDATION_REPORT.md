# MCP-04 Controlled Evidence Readback Validation Report

## Final status

MCP-04 validation status: **passed with one minimal schema hardening change**.

The MCP-03 governed evidence readback surface remains bounded to readonly local evidence summaries under `research/live_probe_runs/m3g_04/`. MCP-04 did not execute a live probe, did not call the controlled live-probe tool, did not perform network calls as part of validation, and did not refresh production, generated, or frontend artifacts.

## Scope

MCP-04 reviewed the MCP server implementation and unit-test coverage for the governed evidence readback tool:

- MCP-01 readonly local context tools.
- MCP-02 explicit controlled live-probe evidence tool: `run_m3g04_controlled_live_probe_evidence`.
- MCP-03 readonly evidence readback tool: `read_m3g04_latest_controlled_probe_evidence`.
- Legacy direct source-specific MCP probe tools remaining unavailable.
- Readback governance metadata, argument validation, evidence directory boundaries, evidence shape validation, filter semantics, and fail-closed behavior.

## Non-goals

MCP-04 explicitly did **not** authorize or perform:

- live probe execution;
- network calls from the MCP-04 validation work;
- production refresh;
- generated artifact writes;
- frontend artifact writes;
- full-market scan;
- staging writes;
- durable evidence promotion;
- trading signals, buy/sell/hold output, or realtime claims;
- FinMind, Fugle, Fubon, broker, auth, cookies, tokens, or credential enablement;
- direct restoration of legacy source-specific MCP probe tools.

## Reviewed MCP surfaces

### MCP-01 readonly local context tools

The MCP server continues to expose the readonly local context tools for existing local artifacts. Their shared governance metadata states readonly local artifact access with `network_calls=false`, `production_refresh=false`, `frontend_refresh=false`, and `live_probe_execution=false`.

### MCP-02 controlled live-probe evidence tool

The only live-probe MCP surface remains `run_m3g04_controlled_live_probe_evidence`. MCP-04 did not call it. Unit tests continue to verify validation failures do not invoke `run_controlled_probe_runner`, while valid controlled execution is isolated to the explicit controlled runner path.

### MCP-03 readonly evidence readback tool

The only governed evidence readback MCP surface remains `read_m3g04_latest_controlled_probe_evidence`. The implementation reads local `run_summary_*.json` files under `research/live_probe_runs/m3g_04/` and returns structured governance, scope, selected run paths, scanned run paths, and freshness caveats.

### Legacy probe tools

The legacy direct source-specific MCP probe names remain unavailable and are not listed as callable tools:

- `probe_twse_openapi`
- `probe_tpex_openapi`
- `probe_yahoo_finance`
- `probe_twse_mis`
- `probe_finmind`

## Validation method

MCP-04 used static review plus non-network unit tests. The review checked:

1. MCP tool registration and call dispatch.
2. Readback governance metadata.
3. Readback argument allowlist and validation.
4. Evidence directory pinning to `research/live_probe_runs/m3g_04/`.
5. Absence of arbitrary filesystem path parameters.
6. Absence of readback calls into `run_controlled_probe_runner`.
7. JSON parse failures and shape failures returning fail-closed structured responses.
8. Explicit source and target filter semantics.
9. `max_runs` selection semantics.
10. No realtime, production-current, or trading-signal claims in readback responses.

## Governance findings

The evidence readback governance payload includes the required MCP-03 controls:

- `network_calls=false`
- `live_probe_execution=false`
- `production_refresh=false`
- `frontend_refresh=false`
- `generated_artifact_writes=false`
- `evidence_readback_only=true`
- `full_market_scan=false`
- `trading_signal=false`

The readback statement also says no network calls were made, no live probe was executed, generated and frontend artifacts were not updated, production snapshots were not updated, and the response is not a realtime guarantee, not production current market state, and not a trading signal.

## Readback boundary findings

Readback is fixed to `research/live_probe_runs/m3g_04/` through the MCP server constant and resolved path check. The readback argument validator accepts only:

- `requested_sources`
- `requested_targets`
- `max_runs`

Unsupported arguments, including path-like inputs, fail closed with `unsupported_argument`. This prevents arbitrary filesystem read through the MCP-03 surface.

The readback implementation does not call `run_controlled_probe_runner`; MCP-04 retained and strengthened tests around readonly behavior without invoking live probes.

## Fail-closed behavior findings

MCP-03 fail-closed behavior is reasonable and now has coverage for these cases:

- unsupported arguments fail closed;
- invalid `max_runs` fails closed;
- invalid source filters fail closed;
- invalid target filters fail closed;
- duplicate requested source filters fail closed;
- duplicate requested target filters fail closed;
- missing evidence directory returns `no_evidence_available`;
- empty evidence directory returns `no_evidence_available`;
- invalid JSON returns `invalid_evidence_json` and does not silently skip to older evidence;
- invalid evidence shape returns `invalid_evidence_shape`;
- duplicate sources or targets inside evidence content now fail closed as invalid evidence shape;
- valid evidence that does not match explicit filters returns `no_matching_evidence_available`.

## Evidence shape and filter semantics findings

The canonical readback shape validator requires:

- root JSON object;
- `targets` as a string list;
- `sources_requested` as a string list;
- `results` as an object or array.

MCP-04 added minimal hardening so duplicate `targets` or duplicate `sources_requested` values inside evidence content are treated as invalid evidence shape. This avoids ambiguous evidence summaries when applying subset filter semantics.

Filter semantics remain explicit:

- when no source filter is supplied, `source_filters_applied` is `[]`;
- when no target filter is supplied, `target_filters_applied` is `[]`;
- requested sources must be a subset of `sources_requested` in the evidence summary;
- requested targets must be a subset of `targets` in the evidence summary;
- `max_runs` applies after matching, so nonmatching newer summaries can be scanned without consuming the selected-run budget.

## Tests run

MCP-04 validation ran the requested non-network checks:

```bash
python -m compileall server tests
pytest -m "not network" tests/unit/test_mcp_server.py
pytest -m "not network"
```

All completed successfully in this environment.

## Limitations

- MCP-04 did not execute live probes, so it did not validate any external source freshness, availability, latency, or market-data semantics.
- MCP-04 did not inspect credentials, cookies, tokens, `.env`, broker integrations, or authenticated APIs.
- MCP-04 did not refresh generated artifacts, frontend artifacts, staging artifacts, or production snapshots.
- MCP-04 did not promote local evidence into durable production state.
- MCP-04 did not claim the readback evidence is realtime or current market state.

## Next recommended step

Proceed with a small MCP-05 documentation and operator-readiness review that keeps the same governance boundary: no live probe by default, no production refresh, no generated/frontend artifact writes, and no durable evidence promotion unless a future milestone explicitly authorizes those actions.
