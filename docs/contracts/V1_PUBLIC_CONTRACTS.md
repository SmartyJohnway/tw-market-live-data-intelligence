# V1 public contracts

`VERSION` is the product-version authority.  The current release candidate is
`1.0.0-rc.1`.  It is intentionally distinct from the Local Service API
contract identifier, `unified_market_evidence_local_service.v1`.

## Public surfaces

The Local Service exposes governed Unified endpoints under `/api/unified`.
The current browser workbench is `/workbench/`; `/workbench/mode-a/` is a
legacy compatibility redirect, not a separate current product.

The public MCP surface has exactly six tools:

- `market_describe_capabilities`
- `market_validate_request`
- `market_preview_request`
- `market_read_result`
- `market_export_ai_handoff`
- `market_fetch_evidence`

The first five tools are read-only. `market_fetch_evidence` is the sole
execute-once action and rejects a request whose `execution_mode` is not
`execute` before authorization or source access.

## Confirmations and failures

Mode B2 requires `confirm_execution`; a network-required action also requires
`confirm_network_execution`. Persistent Watchlist mutations use a single-use
`preview_id` and `preview_hash`. These confirmations are product contracts,
not optional UI hints.

Public errors are stable reason codes. In particular, an uninitialized local
Security Master returns `SECURITY_MASTER_NOT_INITIALIZED`; no filesystem
implementation detail is part of the public contract.

## Deliberate exclusions

V1 has no scheduler, background refresh, trading or order routing,
model-selected URL, or model-selected executor. The governed request,
preview, bounded execution, Result/Audit, and AI-ready handoff path remains
the only market-evidence execution path.

The machine-readable inventory is
[`v1_public_contracts.json`](v1_public_contracts.json). It is checked by
`python scripts/validate_v1_public_contracts.py`.
