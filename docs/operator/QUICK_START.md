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

<a id="source-first-run"></a>
## Path C — Source checkout (developer / contributor path)

This is the primary source-onboarding authority. The verified S2 environment is
**Windows 11 / CPython 3.13 / current repository source**, with an existing
installed dependency environment passing `verify_environment.py` and completely
isolated fresh application state. Linux, macOS,
container startup, fresh network clone, dependency download and full locked-graph
reinstallation were not verified by that smoke. The frozen `v1.5.0` distribution is a separate source/artifact
identity; stay on `main` for current development.

### 1. Acquire source and dependencies

From PowerShell, with CPython 3.13 available:

```powershell
git clone https://github.com/SmartyJohnway/tw-market-live-data-intelligence.git
cd tw-market-live-data-intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -B scripts/verify_environment.py
python -B scripts/validate_phase_h_v3_contracts.py
```

Clone and pip installation may require external network. With an existing checkout
and a previously prepared compatible wheelhouse, dependency installation may use
`python -m pip install --no-index --find-links <wheelhouse> -r requirements-lock.txt`.
S2 does not download dependencies or market data. `verify_environment.py` checks
imports, supported Python and the exact `mcp==1.29.0` pin; it does not initialize
application state. CPython 3.13 is canonical; 3.11 remains noncanonical source
compatibility, and 3.12 is unsupported for the v1.5.0 release contract.

### 2. Initialize the application installation (offline)

Choose writable roots **outside the checkout**. These example environment settings
select the normal Windows installation; use different empty disposable roots for
tests. Preserve the same settings in every service/MCP terminal.

```powershell
$env:TW_MARKET_HOME = Join-Path $env:LOCALAPPDATA 'TW-Market'
$env:TW_MARKET_STATE_ROOT = Join-Path $env:TW_MARKET_HOME 'state'
python -B scripts/tw_market_lifecycle.py status --json
python -B scripts/tw_market_lifecycle.py init --home "$env:TW_MARKET_HOME" --state-root "$env:TW_MARKET_STATE_ROOT" --json
python -B scripts/manage_security_master.py status
python -B scripts/run_unified_workbench.py --startup-check
```

Before init, a fresh installation reports `INSTALLATION_NOT_INITIALIZED`; service
startup is blocked. Init returns `INSTALLATION_READY` with
`installation.installation_status = READY` and `network_on_init = false`.
It creates `meta/installation.json`, `config/settings.json`, HOME cache/log
directories and STATE_ROOT `security-master`, `watchlists`, `governed` directories.
It does not activate Security Master, create Watchlists, acquire data or start a
service. Init is idempotent: it preserves installation ID and existing metadata /
settings. It refuses to silently adopt pre-existing business state
(`EXISTING_STATE_REQUIRES_EXPLICIT_TRANSFER`).

`--home` / `--state-root` override their environment counterparts. Without a HOME
override, HOME is `%LOCALAPPDATA%\TW-Market`; state defaults to HOME\state.
Once initialized, metadata binds the state root; a conflicting requested root is
`STATE_ROOT_CONFLICT`, not a migration command. Runtime/temp paths are separately
keyed by installation ID under the system temp directory. Do not reuse another
installation's Security Master / Watchlist / governed-root override variables.

### 3. Start Local Service, then use Workbench

The Workbench launcher starts the loopback Local Service and serves its UI:

```powershell
python -B scripts/run_unified_workbench.py --host 127.0.0.1 --port 8000
```

Keep this foreground process running. Open
[Workbench](http://127.0.0.1:8000/workbench/); `GET /api/health` and
`GET /api/unified/capabilities` are no-acquisition checks. Stop this foreground
service with **Ctrl+C in its terminal**. Do not launch a second service on the same
port. A different unused port can be selected explicitly.

A fresh initialized installation still has Security Master `NOT_INITIALIZED`.
Workbench preload reports `status = not_initialized`, `security_master_loaded =
false`, with schema/catalog loaded, and exits 0. Health, UI and capability
inspection remain available. This is useful startup readiness, not identity or
market-evidence readiness. An identity-dependent validation request fails closed
with HTTP 503 / `SECURITY_MASTER_NOT_INITIALIZED`; no fixture identity is substituted.

### 4. MCP uses the running Local Service

In a second terminal, activate the same environment and select the same HOME /
STATE_ROOT as above. Keep Local Service running; MCP does not start it for you.
For the default service address:

```powershell
python -B scripts/run_unified_market_evidence_mcp.py --service-url http://127.0.0.1:8000 --startup-check
python -B scripts/run_unified_market_evidence_mcp.py --service-url http://127.0.0.1:8000
```

Use the second command as the MCP host's stdio process; stdout is protocol-only.
Startup-check verifies the pinned SDK, tool contract and Local Service capability
contract, then exits (`startup_check=ok` is on stderr). It succeeds without ACTIVE
Security Master. With installation initialized but service absent, it exits 3
(`local_service_unavailable`). Without installation initialization it exits 2.
For another service port, use the matching loopback `--service-url` (or
`UNIFIED_MARKET_EVIDENCE_SERVICE_URL`). Plain stdio serving waits for its first
input frame before checking the service; an empty-stdin exit is not a readiness
proof. Use `--startup-check` for verification without an MCP client.

### 5. Identity availability and explicit network actions

Security Master ACTIVE gates identity-dependent resolution/validation and flows
that require that identity; it does **not** gate all application startup.
When the operator explicitly intends official identity acquisition, the separate
network action is `python scripts/manage_security_master.py update --live`.
This is not a prerequisite for the offline startup checks above and is never run
by the S2 smoke. Other unavailable/corrupt identity states may fail closed;
`NOT_INITIALIZED` does not imply every identity error is benign.

Initialization, status, preload, Local Service health/UI/capabilities and MCP
startup-check require no external acquisition. Service/MCP checks use loopback.
Market evidence acquisition remains separately explicit, bounded and auditable.
For the isolated regression, run
`python -B -m pytest -p no:cacheprovider tests/integration/test_source_onboarding_first_run.py -q`.
It uses fresh roots and a child-process audit guard, never the user's real
installation; it does not install dependencies, use a browser, activate identity,
or prove live-provider availability.

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
