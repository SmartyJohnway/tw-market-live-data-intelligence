# Operator Quick Start

TW-Market `v1.5.0` is the current stable GitHub release. Choose the path that
matches how you want to use the product; source checkout is no longer the
default path for every user.

| Path | Best for | Primary requirement |
|---|---|---|
| **Windows Native ZIP** | Local operator / Workbench | Windows 11 x64 + CPython 3.13 x64 |
| **Windows MCPB** | AI / MCP client | Windows + Python `>=3.13,<3.14` + MCPB-capable client |
| **Source checkout** | Developer / contributor | Canonical development runtime: CPython 3.13 |

The stable release is:

- [GitHub Release v1.5.0](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0)
- frozen source commit `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`
- frozen source tree `d44f66dc154c21326ac8b105d2f15fd793f6071b`

## Path A — Windows Native ZIP (recommended operator path)

Download:

- [TW-Market-1.5.0-windows-x64.zip](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.0/TW-Market-1.5.0-windows-x64.zip)
- [SHA-256 sidecar](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.0/TW-Market-1.5.0-windows-x64.zip.sha256)

Verify the archive before extraction:

```powershell
(Get-FileHash .\TW-Market-1.5.0-windows-x64.zip -Algorithm SHA256).Hash.ToLower()
```

Expected SHA-256:

```text
dd2098d094e1ea2373d68f535694cdaefd7483ea82896783444f9ae74bf2ea67
```

Extract the ZIP to a writable application directory and enter the extracted
`TW-Market-1.5.0-windows-x64` directory. Then run:

```powershell
& .\bootstrap\bootstrap.ps1
.\tw-market.cmd status --json
.\tw-market.cmd init --json
```

Bootstrap verifies the payload and creates the package-local runtime from the
included exact hashed wheels with pip networking disabled. Bootstrap does **not**
initialize business state or acquire market data. `init` establishes the local
installation; the Taiwan Market Identity Service can still correctly report
`NOT_INITIALIZED` until you explicitly update the Security Master.

Initialize or refresh the Security Master only when you intend to perform that
official external acquisition:

```powershell
.\tw-market-security-master.cmd status
.\tw-market-security-master.cmd update --live
```

Start the local service and inspect health:

```powershell
.\tw-market.cmd start --json
.\tw-market.cmd status --json
.\tw-market.cmd doctor --json
```

Open the Workbench at:

```text
http://127.0.0.1:8000/workbench/
```

Stop the local service with:

```powershell
.\tw-market.cmd stop --json
```

The Native distribution does not require administrator privileges, registry or
PATH changes, a Windows service, a scheduled task, an updater, or Docker.

## Path B — Windows MCPB (AI / MCP client path)

Download the current GitHub MCPB directly from `v1.5.0`:

- [tw-market-unified-mcp-v1.5.0-win-x64.mcpb](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.0/tw-market-unified-mcp-v1.5.0-win-x64.mcpb)
- [SHA-256 sidecar](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.0/tw-market-unified-mcp-v1.5.0-win-x64.mcpb.sha256)

Expected MCPB SHA-256:

```text
8c7a02eb93a6224ca61f3c6c46014972c1045b8d19c358e1fbe6636e3d4bad5a
```

Import/install the local `.mcpb` through your MCP client's package workflow.
The package runs a local Python stdio server and exposes exactly six governed
tools; it is not a hosted market-data endpoint.

The MCPB is **not** the operator administration surface for creating or updating
the installation-local Security Master. If the MCP server reports
`NOT_INITIALIZED`, initialize the same local installation through the Native or
source operator path first. The platform-default HOME is
`%LOCALAPPDATA%\TW-Market` unless explicitly overridden.

See [MCP distribution](../distribution/MCP_DISTRIBUTION.md) for the exact tool
surface, Registry boundary, runtime requirement, and provenance.

## Path C — Source checkout (developer / contributor path)

Use source checkout when you are developing, testing, or contributing rather
than installing the frozen release bundle:

```bash
git clone https://github.com/SmartyJohnway/tw-market-live-data-intelligence.git
cd tw-market-live-data-intelligence
# For the exact published v1.5.0 source, use: git checkout v1.5.0
python -m venv .venv
# Activate .venv using your shell
python -m pip install -r requirements-lock.txt
python scripts/verify_environment.py
python scripts/manage_security_master.py status
```

Stay on `main` for current development. Checkout `v1.5.0` when you need the
exact frozen release source rather than later post-release documentation or
development commits.

CPython 3.13 is the canonical release/build/CI runtime. Python 3.11 remains
noncanonical source/developer compatibility; Python 3.12 is unsupported for the
v1.5.0 release contract.

A fresh source installation can correctly report `NOT_INITIALIZED`. Initialize
or refresh the Security Master only through the explicit operator action:

```bash
python scripts/manage_security_master.py update --live
```

Then start either the Workbench or the source MCP launcher:

```bash
python scripts/run_unified_workbench.py
# or, for an MCP host:
python scripts/run_unified_market_evidence_mcp.py
```

## Governed product flow

All three entry paths converge on the same product semantics:

```text
Request
-> Validate / Identity
-> Preview
-> explicit authorization
-> execute once
-> Result
-> Audit
-> AI Handoff
```

The MCP surface remains exactly six tools. Request V3 is preferred; Request
V1/V2 remain compatibility contracts. Capability support alone does not imply
an executable route: the current Catalog, selected Routing, and preview result
remain authoritative.

## Safety boundary

Starting TW-Market does not authorize polling, a scheduler, startup market
acquisition, Watchlist-driven automatic execution, trading, order routing,
full-market scans, or realtime guarantees. Market acquisition remains explicit.

For detailed operation, see [Local Workbench](LOCAL_WORKBENCH.md),
[Troubleshooting](TROUBLESHOOTING.md), and the
[AI / Agent usage guide](../agent_usage_guide.md).
