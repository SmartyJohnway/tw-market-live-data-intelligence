# TW-Market Live Data Intelligence

[English](README.md) | [繁體中文](README.zh-TW.md)

[![Stable v1.5.1](https://img.shields.io/badge/stable-v1.5.1-2ea44f)](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0)
![Windows 11 x64](https://img.shields.io/badge/Windows-11%20x64-0078d4)
![Python 3.13](https://img.shields.io/badge/Python-3.13-3776ab)
[![MCP six tools](https://img.shields.io/badge/MCP-exactly%206%20tools-5c4ee5)](docs/reference/MCP_REFERENCE.md)
[![License MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

> Local-first, governed Taiwan-market evidence infrastructure for human operators
> and AI agents — validate first, preview bounded work, then explicitly authorize
> one execution only when the current capability and route permit it.

## Architecture at a glance

```mermaid
flowchart LR
    H[Human / Operator] --> W[Unified Workbench]
    A[AI Agent] --> M[Six-tool MCP]
    W --> R[Unified Runtime]
    M --> R
    R --> V[Validate + Identity]
    V --> P[Preview + Route Bounds]
    P --> X[Explicit Authorization]
    X --> E[Execute Once]
    E --> S[Governed Official / Approved Sources]
    S --> O[Result + Audit + AI Handoff]
    L[Persistent Watchlists] --> W
```

## Current stable release

**TW-Market `v1.5.1` is the latest stable GitHub Release**, published on
2026-11-04 (23:57 Asia/Taipei). ProductVersion: `1.5.1`.

- Frozen source commit: `1f3666eefdca7e2e9a1c88099f802696bf7970d6`
- Frozen source tree: `d67e9bc1db34ff268b5b8d0f2a301d1a211df3b6`
- [GitHub v1.5.1 Release](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.1)
- [Windows Native ZIP](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/TW-Market-1.5.1-windows-x64.zip)
- [Native SHA-256 sidecar](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/TW-Market-1.5.1-windows-x64.zip.sha256)
- [Windows MCPB](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/tw-market-unified-mcp-v1.5.1-win-x64.mcpb)
- [MCPB SHA-256 sidecar](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/tw-market-unified-mcp-v1.5.1-win-x64.mcpb.sha256)
- [First-party dependency SBOM](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/TW-Market-1.5.1-first-party-sbom.json)
- [Publication manifest](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/TW-Market-1.5.1-publication-manifest.json)
- [Verified publication record](docs/release/V1_5_1_RELEASE_PUBLICATION.md)

The `v1.5.1` tag/source and six published assets remain immutable under release
governance. Later documentation-only commits on `main` are **not** new `v1.5.1`
release bytes. GitHub Immutable Releases platform enforcement is not asserted.
Previous `v1.5.0` remains a valid frozen historical release.

## Choose your path

| Path | Best for | Start here |
|---|---|---|
| **Windows Native ZIP** | Normal local operator / Workbench use | [Download v1.5.1 Native ZIP](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/TW-Market-1.5.1-windows-x64.zip) |
| **Windows MCPB** | AI / MCP client | [Download v1.5.1 MCPB](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/tw-market-unified-mcp-v1.5.1-win-x64.mcpb) |
| **Source checkout** | Developer / contributor | [Source/developer path](docs/operator/QUICK_START.md#path-c--source-checkout-developer--contributor-path) |

For a **60-second orientation and first-run sequence**, use the
[Operator Quick Start](docs/operator/QUICK_START.md). The Native ZIP is the
recommended operator path; source checkout is not the default installation path
for every user.

For developer-only source checkout, `python scripts/run_unified_workbench.py`
and `python scripts/run_unified_market_evidence_mcp.py` remain explicit advanced
entry points; neither replaces the built Native bundle-root Launcher.

## What TW-Market is

TW-Market is a governed evidence and research workbench for Taiwan-market data.
It gives a human operator or AI agent a deterministic path from target identity
and capability validation to bounded source acquisition, canonical Result/Audit
materialization, citations, and an AI-ready handoff.

It is intentionally **not** a broker, autonomous trader, portfolio system,
general-purpose crawler, or realtime-price guarantee.

Core product characteristics:

- **Local-first:** installation state, Security Master, Watchlists, evidence, and
  audit artifacts remain under explicit local control.
- **Identity-aware:** Taiwan cash instruments use ISIN as durable identity and
  `MARKET:CODE` as listing/routing identity.
- **Preview before execute:** validation and preview do not authorize network
  acquisition; execution is explicit, bounded, and auditable.
- **Persistent Watchlists are supported:** installation-local Watchlists use immutable
  revisions, optimistic concurrency, and explicit preview/commit mutation.
- **Evidence, not conclusions:** source authority, timing/currentness, missingness,
  caveats, and citations remain visible to downstream humans and AI.

## Governed workflow

A typical `2330` flow is:

1. Create or select an installation-local Watchlist and add `2330`.
2. Compose a Unified Market Evidence Request and validate identity/capability.
3. Preview the exact planned operation and its route boundary.
4. Explicitly authorize one bounded execution only if the preview is executable.
5. Read the canonical Result and Audit Package, or export the AI-ready handoff.

Unified Request v3 is preferred. Request v1/v2 remain supported compatibility
contracts; historical supported Result/Audit packages remain readable without
rewriting their canonical bytes or provenance.

The Unified MCP surface remains exactly six governed tools:

`market_describe_capabilities`, `market_validate_request`,
`market_preview_request`, `market_read_result`,
`market_export_ai_handoff`, and `market_fetch_evidence`.

See the [AI usage guide](docs/agent_usage_guide.md) and
[V1 historical public contracts](docs/contracts/V1_PUBLIC_CONTRACTS.md) for the
current request/result/handoff semantics and compatibility boundary.

<details>
<summary>View the full Unified Workbench screenshot</summary>

![Deterministic Unified Workbench overview](docs/assets/workbench-overview.png)

</details>

## Current evidence capabilities

Current governed product scope includes:

- installation-local Taiwan Market Identity Service and persistent Watchlists;
- official material-disclosure and monthly-revenue evidence for eligible
  TWSE/TPEx company common shares;
- selected bounded market-state, index-futures, institutional-flow,
  corporate-action, and recent-performance context where current Catalog and
  Routing authority make the requested market/target executable;
- canonical Result/Audit lineage, citations, timing/currentness semantics, and
  AI-ready Markdown handoff.

Capability support is not the same as route executability. A known instrument,
schema, or capability does not by itself authorize source acquisition. Always
validate and preview against the current Catalog and selected Routing.

Research evidence is intentionally bounded. It does not imply arbitrary history,
realtime disclosures, a full-market scanner, `financial_summary`, investment
advice, or trading signals.

## Safety boundary

There is **no automatic polling, scheduler, startup market fetch, Watchlist-driven
automatic execution, trading, or order routing**. There is also no silent source
fallback or model-selected executor/URL. Missing evidence is not converted to
zero, and execution success is not presented as a realtime guarantee.

## Source/developer quick start

Use the [primary source first-run sequence](docs/operator/QUICK_START.md#source-first-run)
for dependencies, offline lifecycle initialization, Local Service, Workbench and
MCP preflight. Initialization and Security Master activation are separate:
identity-dependent operations fail closed while identity is unavailable, but
health/UI/capability inspection can start after installation initialization.
The source MCP stdio adapter requires the running loopback Local Service.

The release ZIP/MCPB installation paths are documented separately; keep those
operator instructions distinct from this source/developer path.

## MCP distribution and registry boundary

The published GitHub `v1.5.1` Release includes the Windows MCPB and its
SHA-256 sidecar. This local stdio package exposes exactly six governed tools.

The separate official MCP Registry identity,
`io.github.SmartyJohnway/tw-market-live-data-intelligence`, was checked through
the official live Registry API on 2026-11-05: its **Latest active version is
`1.0.0`**. GitHub `v1.5.1` publication does **not** imply Registry
`v1.5.1` publication; updating `server.json` requires separate authorization.

See [MCP distribution](docs/distribution/MCP_DISTRIBUTION.md) for installation
and [Unified MCP Reference](docs/reference/MCP_REFERENCE.md) for the six tools.

Docker is a validated local `linux/amd64` build/acceptance and provenance
surface only. **No Docker registry image is published** for `v1.5.1`.

## Documentation

Operator and product docs:

- [Operator quick start](docs/operator/QUICK_START.md)
- [Local Workbench guide](docs/operator/LOCAL_WORKBENCH.md)
- [Troubleshooting](docs/operator/TROUBLESHOOTING.md)
- [AI / agent usage guide](docs/agent_usage_guide.md)
- [AI discovery entry (`llms.txt`)](llms.txt)
- [Capability matrix](docs/reference/CAPABILITY_MATRIX.md)
- [Source matrix](docs/reference/SOURCE_MATRIX.md)
- [Documentation index](docs/INDEX.md)

Engineering/governance front doors:

- [PROJECT.md](PROJECT.md) — current project/product authority
- [ROADMAP.md](ROADMAP.md) — canonical Roadmap V3.2
- [HANDOFF.md](HANDOFF.md) — current operational handoff
- [AGENTS.md](AGENTS.md) — repository and AI collaboration rules

Historical engineering and acceptance records remain available for audit and
compatibility, but they are not a second current-product contract. Start with
[Project History](docs/PROJECT_HISTORY.md) or the
[Engineering history / protocol archive](docs/INDEX.md#engineering-history--protocol-archive).

## Release history and provenance

- **`v1.5.1`** — current stable GitHub Release (2026-11-04), six verified assets.
- **`v1.5.0`** — prior frozen stable GitHub Release (2026-10-28).
- **`v1.0.0`** — historical GitHub stable release, and current MCP Registry
  package version (verified in the official Registry on 2026-11-05).
- **`v1.0.0-rc.1`** — historical prerelease.
- **`v0.1.0`** — earlier GitHub stable release.

The published `v1.5.1` assets include Native ZIP/checksum, MCPB/checksum,
first-party SBOM and typed publication manifest. SHA-256, provenance and SBOM
prove integrity/traceability, **not cryptographic publisher signatures**;
signing authority remains `NOT_ESTABLISHED`.
See the [post-publication record](docs/release/V1_5_1_RELEASE_PUBLICATION.md)
for exact SHA-256 values and preserved non-blocking diagnostic results.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Report
security concerns using [SECURITY.md](SECURITY.md). Never commit credentials,
tokens, cookies, or private market payloads.

## License

See [LICENSE](LICENSE).
