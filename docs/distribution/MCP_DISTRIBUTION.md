# Unified MCP distribution

TW-Market provides a local, stdio-based Unified MCP server. It does not provide
a hosted market-data service.

## Current GitHub distribution

The current GitHub stable MCPB is published with governance-frozen release
[`v1.5.0`](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0).
GitHub Immutable Releases enforcement is not enabled for this release.

- [MCPB bundle](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.0/tw-market-unified-mcp-v1.5.0-win-x64.mcpb)
- [SHA-256 sidecar](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.0/tw-market-unified-mcp-v1.5.0-win-x64.mcpb.sha256)

Frozen MCPB SHA-256:

```text
8c7a02eb93a6224ca61f3c6c46014972c1045b8d19c358e1fbe6636e3d4bad5a
```

Release source identity:

```text
commit acaf726a5b59baee4c5a30521ea5a5d5ec0cec76
tree   d44f66dc154c21326ac8b105d2f15fd793f6071b
```

## Runtime compatibility

The v1.5.0 MCPB manifest declares:

- platform: Windows (`win32`)
- Python runtime: `>=3.13,<3.14`
- transport: local stdio
- product version: `1.5.0`

## Install into an MCP client

1. Download the `.mcpb` and SHA-256 sidecar from the v1.5.0 GitHub Release.
2. Verify the local file hash before importing it.
3. Import/install the `.mcpb` using your MCP client's local package workflow.
4. Confirm the server starts locally over stdio and exposes exactly six tools.

PowerShell hash check:

```powershell
(Get-FileHash .\tw-market-unified-mcp-v1.5.0-win-x64.mcpb -Algorithm SHA256).Hash.ToLower()
```

The package contains the TW-Market application projection plus the accepted
Windows Python dependency payload required by the MCP server. It does not add a
seventh tool, hosted proxy, scheduler, or background market fetch.

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

The official MCP Registry identity remains:

[`io.github.SmartyJohnway/tw-market-live-data-intelligence`](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.SmartyJohnway/tw-market-live-data-intelligence)

GitHub Release publication and MCP Registry publication are independent. The
v1.5.0 A7 GitHub release did **not** update Registry metadata; the currently
published Registry package metadata therefore remains on the historical
`v1.0.0` package until a separately authorized Registry publication occurs.

Do not treat Registry metadata as proof that GitHub v1.5.0 was unpublished, and
do not treat GitHub v1.5.0 as proof that Registry metadata was updated.

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

The source launcher is a development path; it is not the frozen v1.5.0 MCPB
artifact. Use the GitHub release asset when you need the published distribution.

## Publication provenance

The v1.5.0 MCPB was frozen and published as part of the same release artifact
set as the Windows Native ZIP, checksums, first-party SBOM, and typed
publication manifest. Its server-side and downloaded-byte SHA-256 were verified
against the frozen release identity after publication.

The MCPB does not redefine the release source commit/tree. GitHub-generated
source archives are platform-generated from the tag; Docker is a validation /
provenance surface only and no v1.5.0 container-registry publication is claimed.

## Safety boundary

This distribution preserves the governed local-first contract: explicit
validation, preview, and one bounded execution only after explicit
authorization. It does not provide trading, order routing, a scheduler,
background polling, automatic Watchlist execution, a full-market scan, or a
realtime guarantee.

For the broader operator paths, see
[Operator Quick Start](../operator/QUICK_START.md) and the
[AI / Agent usage guide](../agent_usage_guide.md).
