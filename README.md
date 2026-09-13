# TW-Market Live Data Intelligence

[English](README.md) | [繁體中文](README.zh-TW.md)

> Local-first, governed Taiwan-market evidence for an operator and an AI
> assistant — validate first, preview bounded work, then explicitly authorize
> one execution where the capability permits it.

![Deterministic Unified Workbench overview](docs/assets/workbench-overview.png)

The repository has published release candidate
**[`1.0.0-rc.1`](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.0.0-rc.1)**.
The latest prerelease is `v1.0.0-rc.1`; the latest stable GitHub Release remains **`v0.1.0`**. Final `v1.0.0` is not released, and Phase G has not started. This is a local-first evidence workbench, not a realtime trading product.

## Why TW-Market

AI discussion needs evidence with identity, source, timestamp, caveat, and
execution provenance — not an unqualified price claim. This workbench gives a
human operator a governed local path from request validation to an AI-ready
handoff, while retaining a separate audit package.

## Quick start

```bash
git clone https://github.com/SmartyJohnway/tw-market-live-data-intelligence.git
cd tw-market-live-data-intelligence
python -m venv .venv
# Activate .venv using your shell, then:
python -m pip install -r requirements-lock.txt
python scripts/verify_environment.py
python scripts/manage_security_master.py status
```

`NOT_INITIALIZED` is the normal fresh-install state. A Security Master update
is an explicit operator action and may use official external acquisition:

```bash
python scripts/manage_security_master.py update --live
python scripts/run_unified_workbench.py
```

Open the loopback Workbench at [`/workbench/`](http://127.0.0.1:8000/workbench/).
For an MCP host, start the separate stdio launcher:

```bash
python scripts/run_unified_market_evidence_mcp.py
```

## A governed 2330 workflow

1. Create or select an installation-local Watchlist, then add `2330`.
2. Compose a Unified Market Evidence Request and validate its identity.
3. Preview the planned operation and its capability boundary.
4. Explicitly authorize and confirm one bounded execution only when the
   preview is executable.
5. Read the canonical Result and Audit Package, or export the AI-ready
   handoff for continued discussion.

## Core capabilities

- **Identity-aware requests:** Mode A validates targets against the
  installation-local Taiwan Market Identity Service.
- **Bounded execution:** Mode B previews, explicitly authorizes, and executes
  one request only when its governed capability is executable.
- **Auditable handoff:** Mode C creates a canonical Result, separate Audit
  Package, and AI-ready Markdown without dispatching another market source.
- **Persistent Watchlists are supported:** installation-local Watchlists have immutable
  revisions, optimistic concurrency, and explicit preview/commit mutation.

## Unified MCP

The MCP surface has exactly six governed tools:

`market_describe_capabilities`, `market_validate_request`,
`market_preview_request`, `market_read_result`,
`market_export_ai_handoff`, and `market_fetch_evidence`.

See the [V1 public contracts](docs/contracts/V1_PUBLIC_CONTRACTS.md) and
[current AI usage guide](docs/agent_usage_guide.md) for request, result, and
handoff semantics.

## Data and source caveats

Capability support, currentness, source provenance, and execution eligibility
are explicit product data. A supported identity does not imply an executable
source route; a preview is not an authorization; a source observation is not a
realtime guarantee. Consult the [capability matrix](docs/reference/CAPABILITY_MATRIX.md),
[source matrix](docs/reference/SOURCE_MATRIX.md), and
[governance boundaries](docs/reference/GOVERNANCE_BOUNDARIES.md) before relying
on any result.

## Safety and non-goals

There is no automatic polling, scheduler, startup market fetch, Watchlist-driven
automatic execution, trading, order routing, full-market scan, model-selected
URL/executor, or realtime guarantee. Persistent Watchlists mutate only through
explicit preview/commit. Never commit credentials, tokens, cookies, or private
market payloads.

## Documentation

- [Operator quick start](docs/operator/QUICK_START.md)
- [Local Workbench guide](docs/operator/LOCAL_WORKBENCH.md)
- [Troubleshooting](docs/operator/TROUBLESHOOTING.md)
- [Documentation index](docs/INDEX.md)
- [V1 release candidate](docs/release/V1_RELEASE_CANDIDATE.md)
- [Changelog](CHANGELOG.md)

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Report
security concerns using the grounded guidance in [SECURITY.md](SECURITY.md).

## Release status

`VERSION` records `1.0.0-rc.1`, which is published as the current prerelease.
The latest stable GitHub Release remains `v0.1.0`; final `v1.0.0` is **not
released**, and Phase G has **not started**. The RC tag is an immutable
release authority; subsequent documentation status updates do not move it.

## Project Overview

This root README is the current product entry point. Engineering history,
protocol acceptance, and prior M5/M6/M8 architecture remain available through
[Project History](docs/PROJECT_HISTORY.md), the [Engineering history / protocol
archive](docs/INDEX.md#engineering-history--protocol-archive), and
[`docs/archive/`](docs/archive/), including the
[`2026-06-30 historical README`](docs/archive/readme/README_20260630_M5LRM_ARCHITECTURE_CONVERGENCE.md).
They are retained for audit and compatibility,
not as a second current-product contract.

## License

See [LICENSE](LICENSE).
