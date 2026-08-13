# M8R-08B Minimal Unified MCP Implementation Review

## Scope

M8R-08B implements the accepted M8R-08A safe-tool adapter only. The implementation is a new stdio sidecar that delegates through bounded fixed loopback HTTP to the existing `/api/unified/*` Local Service. It has no Mode A/B/C imports, legacy `server/mcp_server.py` import, market source access, listener, action tool, or second semantic stack.

Baseline: `5826c3697ac1fd06eb17fa83058b0d61a4d79b37`.

Branch: `codex/m8r-08b-minimal-unified-mcp`.

Implementation code head: `54896691628e7bed5d5eaeb2e37893b512030e20`.

Final head: this documentation closure commit (reported exactly in PR closure metadata after its final-head test run).

## Implementation evidence

- Dependency manifest and actual repository runtime: `mcp==1.29.0`.
- Adapter identity: `unified_market_evidence_mcp_adapter.v1`.
- Bound service identity: `unified_market_evidence_local_service.v1`.
- Tool count and names: exactly five: describe capabilities, validate, preview, Result read, and AI handoff export.
- Canonical Request authority is loaded from committed schema bytes; the registered nested input schema is concrete rather than `{}`.
- The subprocess integration test uses real MCP stdio and a real TCP `127.0.0.1` Local Service test server, proving tool discovery, annotations, startup compatibility check, exact routes/envelopes, structured content, and stderr-only startup logging.
- HTTP controls: loopback-only URL validation, no proxy environment, no redirects or retries, finite timeout, 1 MiB request bound, and 8 MiB response bound.

Changed implementation surfaces are `requirements.txt`, `server/unified_mcp/`, `scripts/run_unified_market_evidence_mcp.py`, and the four focused test modules. Documentation adds the protocol, this review, local operator guide, and index links.

The annotation matrix is exact: describe/validate/preview are read-only; Result read and handoff export are not read-only because accepted deterministic Mode C materialization may write local governed artifacts. All five are non-destructive, idempotent, and closed-world.

## Governance findings

`market_authorize_request` and `market_execute_request` are absent. The adapter cannot construct authorization or execution input, select sources or executors, or read raw evidence artifacts. `market_read_result` and `market_export_ai_handoff` preserve existing Mode C behavior and cause no additional external market request.

## Test closure

- Focused M8R-08B plus historical MCP regression: `56 passed`, `0 failed`, `0 warnings`.
- M8R-07 / Mode C / operator routing selection: `84 passed`, `0 failed`, `1 warning` (existing Starlette HTTPX deprecation warning).
- Default CI: `913 passed`, `0 failed`, `0 skipped`, `1 warning`, `252.18s`, return code `0`.
- Actual closure runtime SDK: `importlib.metadata.version("mcp") == "1.29.0"`.
- Dedicated adapter startup and remaining static checks are run against this documentation final head.

Automated test execution is offline/loopback only; automatic external market-network calls are zero. MCP Inspector was not run: `npx --no-install @modelcontextprotocol/inspector` found no installed Inspector and refused package installation, which this closure does not mutate the environment to perform. A real host smoke is `NOT_RUN_REQUIRES_OPERATOR_RESTART`: restart/reconfigure a supported MCP host with the operator command in the local client guide, confirm stdio discovery and the five tools, and verify authorization/execution remain absent.

## Closure recommendation

Pending the recorded final-head static/startup checks, the deterministic adapter closure is suitable for `PASS_WITH_CAVEATS` solely because Inspector and a dynamically attached real-host session were not available. Neither caveat changes the automated real stdio-to-loopback acceptance evidence.
