# Unified MCP distribution

TW-Market provides a local, stdio-based Unified MCP server. It does not provide
a hosted market-data service.

## Current GitHub distribution

The latest GitHub Stable MCPB is part of frozen
[`v1.5.1`](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.1),
published 2026-11-04. Immutable Tags/assets are release-governance policy;
GitHub Immutable Releases platform enforcement is not asserted.

- [MCPB bundle](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/tw-market-unified-mcp-v1.5.1-win-x64.mcpb)
- [MCPB SHA-256 sidecar](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/tw-market-unified-mcp-v1.5.1-win-x64.mcpb.sha256)
- [Release provenance / all six hashes](../release/V1_5_1_RELEASE_PUBLICATION.md)

Frozen MCPB SHA-256:

```text
3bc7b12184076e241e61abf4c4525c846de12bce5aa2340c52ead497be2f9a39
```

Frozen v1.5.1 source identity:

```text
commit 1f3666eefdca7e2e9a1c88099f802696bf7970d6
tree   d67e9bc1db34ff268b5b8d0f2a301d1a211df3b6
```

The packaged MCPB manifest declares Windows (`win32`), CPython
`>=3.13,<3.14`, local stdio, ProductVersion `1.5.1` and exactly six tools.

## Install into an MCP client

1. Download `v1.5.1` .mcpb and SHA-256 sidecar from GitHub.
2. Verify exact local SHA-256 before importing the package.
3. Import/install via an MCPB-capable client's local package workflow.
4. Verify local stdio startup and the **six named tools below**; client
   installation must not be mistaken for Security Master activation.

```powershell
(Get-FileHash .\tw-market-unified-mcp-v1.5.1-win-x64.mcpb -Algorithm SHA256).Hash.ToLower()
```

The package contains the first-party application projection and
exact accepted offline Python dependency payload. It does not introduce
another executor, network proxy, scheduler or background acquisition.

## Exact six-tool surface

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

Validation and preview never authorize execution. `market_fetch_evidence` is the
bounded execution surface and still requires the governed request/authorization
semantics of the product.

## Installation state and Security Master

Identity-dependent operations can legitimately fail closed as `NOT_INITIALIZED`
until an operator activates the installation-local Taiwan Market Identity Service.
Application installation initialization is separate from Security Master activation;
see the [source first-run sequence](../operator/QUICK_START.md#source-first-run)
for the offline source path.

The MCPB is an AI/MCP distribution, not the operator administration surface for
Security Master creation or refresh. Use the Windows Native or source operator
path to initialize the same installation first. Unless explicitly overridden,
the platform-default TW-Market HOME is:

```text
%LOCALAPPDATA%\TW-Market
```

Security Master acquisition remains explicit. Starting an MCP server does not
initialize identity data and does not perform a market fetch.

## MCP Registry boundary

The official MCP Registry identity is:
[`io.github.SmartyJohnway/tw-market-live-data-intelligence`](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.SmartyJohnway%2Ftw-market-live-data-intelligence/versions/latest).

A fresh official Registry GET on **2026-11-05** returned
`server.version=1.0.0` and `status=active` / `isLatest=true`;
its MCPB URL still points to the historical `v1.0.0` GitHub asset.
The repository `server.json` matches that historical Registry declaration.

**GitHub `v1.5.1` publication is not MCP Registry `v1.5.1`
publication.** Updating Registry metadata requires separately authorized
publication; do not bump `server.json` to match GitHub as a doc fix.

## Source launcher alternative

Developers can run the same exact-six MCP contract from a source checkout after
following the [source first-run sequence](../operator/QUICK_START.md#source-first-run).
Offline lifecycle initialization and a running loopback Local Service are required.
The source MCP adapter does not start Local Service; keep both processes on the
same HOME / STATE_ROOT and run `--startup-check` before normal stdio serving.
Security Master ACTIVE separately gates identity-dependent operations.

With those prerequisites satisfied:

```bash
python scripts/run_unified_market_evidence_mcp.py
```

The source launcher is a development path, not the frozen `v1.5.1`
MCPB asset. Use the published binary when a frozen release identity is needed.

## Publication provenance

The `v1.5.1` MCPB was published alongside Native ZIP, checksum sidecars,
first-party SBOM and typed Publication Manifest. All six assets were
independently downloaded and SHA-256 revalidated **after publication**.
The exact Release/source identity remains the annotated `v1.5.1` Tag,
not later `main` documentation commits.

Docker is local build/validation/provenance only; no `v1.5.1` Docker
registry publication is claimed. Signing authority remains
`NOT_ESTABLISHED`: SHA-256 and SBOM do not constitute publisher signatures.

## Safety boundary

This distribution preserves the governed local-first contract: explicit
validation, preview, and one bounded execution only after explicit
authorization. It does not provide trading, order routing, a scheduler,
background polling, automatic Watchlist execution, a full-market scan, or a
realtime guarantee.

For the broader operator paths, see
[Operator Quick Start](../operator/QUICK_START.md) and the
[AI / Agent usage guide](../agent_usage_guide.md).
