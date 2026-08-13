# M8R-08B Minimal Unified MCP Contract

## Status and authority

This contract defines `unified_market_evidence_mcp_adapter.v1`, a local stdio-only transport adapter over the accepted `unified_market_evidence_local_service.v1`. It introduces no market business semantics: `/api/unified/*` and the existing Phase D/M8R-07 runtime remain authoritative.

The adapter is fixed to `http://127.0.0.1:8000` by default. Process configuration may select only `http://127.0.0.1:<port>`, `http://localhost:<port>`, or `http://[::1]:<port>`. It rejects credentials, paths, query strings, fragments, non-loopback hosts, and non-HTTP schemes. It opens no listener and does not start the Workbench.

## Startup and transport

The launcher requires `mcp==1.29.0`, then makes exactly one bounded loopback compatibility check: `GET /api/unified/capabilities` must return HTTP 200 and `service_contract_version = unified_market_evidence_local_service.v1`. Failure is terminal; there is no retry, port discovery, direct-Python fallback, redirect following, proxy inheritance, or market request.

The HTTP client has finite all-phase timeouts, `trust_env=False`, no redirects, a 1 MiB POST-body limit, and an 8 MiB response limit. Stdio stdout is MCP protocol only; launcher diagnostics are stderr only.

## Exact safe tool surface

| Tool | Local Service delegation | Annotation | Effects |
| --- | --- | --- | --- |
| `market_describe_capabilities` | `GET /api/unified/capabilities` | read-only, non-destructive, idempotent, closed-world | no market network, authorization, or claim |
| `market_validate_request` | `POST /api/unified/validate-request` with `{ "request": canonical_request }` | same | no market network, authorization, execution, or claim |
| `market_preview_request` | `POST /api/unified/preview-request` with the same envelope | same | offline planning only; Preview is not Authorization |
| `market_read_result` | `POST /api/unified/result-package` with `{ "control_package_id": "umea-v1-…" }` | non-read-only, non-destructive, idempotent, closed-world | may use accepted deterministic Mode C materialization only; no market request |
| `market_export_ai_handoff` | `GET /api/unified/result-package/{id}/handoff` | non-read-only, non-destructive, idempotent, closed-world | returns existing governed handoff; no market request |

The request tools embed the committed `schemas/unified_market_evidence_request.v1.schema.json` beneath a closed `{request: …}` envelope; no hand-copied market schema exists. Result identifiers use `^umea-v1-[0-9a-f]{20}$`.

No authorization, execution, elicitation, generic HTTP proxy, source selection, executor selection, raw-artifact read, retry, or action aliases are registered. In particular, `market_authorize_request` and `market_execute_request` do not exist.

## Result and error behavior

Successes carry the Local Service JSON in MCP `structuredContent`. `market_export_ai_handoff` text is exactly the existing `ai_ready_markdown`; the adapter does not create a second renderer or duplicate a large Result into text. Failures preserve only bounded Local Service reason fields and sanitized adapter codes; they never expose exception details, paths, headers, or bodies.

The MCP adapter identity, negotiated MCP wire version, Local Service contract version, and canonical artifact schemas are independent versioned contracts.

