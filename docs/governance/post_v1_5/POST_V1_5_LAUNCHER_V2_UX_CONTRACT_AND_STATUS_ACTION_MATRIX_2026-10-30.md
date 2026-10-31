# Post-v1.5 Launcher v2 — UX Contract + Status/Action Matrix

Date: 2026-10-30

Status: **OWNER_SIDE_REVIEW_ACCEPTED / IMPLEMENTATION_AUTHORIZED**

## Purpose

Launcher v2 turns the existing Windows Launcher into a product-facing daily control panel while preserving the frozen P1-A1/P1-A2 lifecycle boundaries.

The Launcher remains a thin facade. It must not create competing runtime, Security Master, MCP, PID, port, health, or installation authority.

The normal product surface has four primary dimensions:

```text
Local Runtime
Workbench
Security Master
Local MCP
```

The Launcher is host-neutral. It must not depend on OpenAI Secure MCP Tunnel, ChatGPT, Local AI Tools Supervisor, Claude, Codex, VS Code, or any other MCP host/integration.

## Authority boundaries

Canonical runtime orchestration remains:

```text
tw-market.cmd status --json
tw-market.cmd start --json
tw-market.cmd doctor --json
tw-market.cmd stop --json
```

Canonical Security Master orchestration remains:

```text
tw-market-security-master.cmd status
tw-market-security-master.cmd update --live
tw-market-security-master.cmd history
tw-market-security-master.cmd rollback <release_id>
```

Launcher v2 may call those existing surfaces but must not duplicate their underlying logic.

P1-A1 remains authoritative for package/bootstrap/installation setup. `Set Up TW-Market` remains zero-provider-network and does not install or update Security Master.

P1-A2 remains authoritative for Local Runtime lifecycle, Workbench loopback safety, explicit Start/Stop, no polling, and Local MCP readiness-only semantics.

## View model

### First-run / setup view

Shown only while package runtime or local installation is not ready.

```text
TW-Market
Package Runtime          Ready / Not set up / Needs attention
Python 3.13 x64          Ready / Required
Local Installation      Ready / Not initialized / Needs attention

[ Set Up TW-Market ]
[ Locate Python 3.13... ]   (only when needed)
```

Security Master is intentionally not installed during `Set Up TW-Market`.

After package runtime and installation become READY, the Launcher transitions to the daily view and setup engineering details no longer occupy the main surface.

### Daily view

```text
TW-Market                                      v<product version>
Taiwan Market Intelligence

Local Runtime          Workbench
Security Master        Local MCP

[ Open Workbench ]
[ Start ] [ Stop ] [ Refresh ] [ Diagnose ]

Advanced / Technical Details
```

## Primary card semantics

### Local Runtime

| Canonical launcher state | User-facing text | Severity |
|---|---|---|
| `STOPPED` | Stopped | neutral |
| `STARTING` | Starting | informational |
| `RUNNING_READY` | Running | ready |
| `RUNNING_UNHEALTHY` | Needs attention | warning |
| `PORT_CONFLICT` | Port conflict | error |
| `STALE_OWNERSHIP` | Needs attention | warning |
| `INSTALLATION_INCOMPLETE` / `STATUS_ERROR` | Needs attention | error |

### Workbench

| Evidence | User-facing text |
|---|---|
| runtime `RUNNING_READY` and validated loopback URI | Ready |
| otherwise | Unavailable |

`Open Workbench` remains explicit and uses only the validated loopback endpoint derived from canonical lifecycle state.

### Local MCP

Local MCP represents product-level MCP readiness only. It does not represent any specific host, tunnel, remote connector, or transport gateway.

| Canonical MCP status | User-facing text | Severity |
|---|---|---|
| `READY` | Ready for MCP clients | ready |
| `SERVICE_UNREACHABLE` | Runtime stopped | neutral |
| `MCP_RUNTIME_MISMATCH` | Needs attention | warning |
| missing/unknown | Unknown | neutral |

There is no `Start MCP Server` or `Stop MCP Server` control.

## Security Master lifecycle UX

Security Master is an independent explicit lifecycle on the daily view. A legal `NOT_INITIALIZED` state never blocks Local Runtime or Workbench readiness.

| Canonical status / outcome | User-facing state | Main action |
|---|---|---|
| `NOT_INITIALIZED` | Not installed | `Install` |
| `ACTIVE` | Ready | `Update` |
| live update running | Updating... | none |
| update succeeded, runtime stopped | Ready for next start | none |
| update succeeded, runtime running | Restart required | `Restart TW-Market` |
| strict X509 compatibility failure proven by current-attempt evidence | Compatibility retry available | `Retry TLS` |
| update rejected/failed with previous active release | Update failed; current release retained | `Update` / `Diagnose` |
| unavailable/corrupt/no usable status | Needs attention | `Diagnose` |

`Install` and `Update` both invoke the same governed canonical operation: `tw-market-security-master.cmd update --live`.

The wording differs because `NOT_INITIALIZED` is a first-install experience while `ACTIVE` is an update experience.

Before `Install` or `Update`, the Launcher must show an explicit confirmation that the action performs one bounded external official acquisition. No Security Master network activity occurs on Launcher open, Refresh, Start, Stop, Workbench open, or ordinary product setup.

Strict verified TLS remains the default for every Security Master live acquisition. The Launcher must never perform a silent TLS fallback. If and only if the current attempt's governed source evidence proves that every failed official source probe was blocked by `PYTHON_X509_STRICT_COMPATIBILITY`, the Launcher may expose `Retry TLS` / `Retry with Compatibility TLS`. That retry requires a second explicit user confirmation and invokes the existing canonical `--ssl-policy compatibility` path. Compatibility mode must retain certificate validation and hostname verification; `unsafe-explicit` is not a Launcher option. Non-X509 failures such as timeout, WAF/source unavailability, parser drift, schema failure, or mixed failure classes must not be relabeled as TLS compatibility failures.

The corresponding user-facing state is `Compatibility retry available` with warning severity. Declining the retry leaves Security Master unmodified and keeps the bounded retry action available for the current Launcher session. Technical Details may expose the governed reason code and diagnostic path, but the main dialog uses plain-language verified-TLS wording.

After a successful update, the Launcher must respect canonical `restart_required=true`. If Local Runtime is running, the user may explicitly restart it. If Local Runtime is stopped, the next Start is sufficient and no automatic start occurs.

`restart_required` is retained only as bounded Launcher-session state after a successful Install/Update. A newly opened Launcher must not infer whether an already-running process loaded an older Security Master release unless canonical runtime evidence explicitly proves that fact.

`Restart TW-Market` is not a new lifecycle authority or command. When explicitly selected, the Launcher performs one canonical `stop --json`, verifies the resulting stopped state, then performs one canonical `start --json` and renders the resulting state. Any failed or ambiguous step stops the sequence fail-closed.

Security Master `history` and `rollback` remain advanced maintenance operations and are not required on the main daily surface.

## Status / action matrix

### Daily runtime controls

| Launcher state | Start | Stop | Open Workbench | Refresh | Diagnose |
|---|---:|---:|---:|---:|---:|
| `STOPPED` | yes | no | no | yes | yes |
| `STARTING` | no | no | no | yes | yes |
| `RUNNING_READY` | no | yes | yes | yes | yes |
| `RUNNING_UNHEALTHY` | no | yes | no | yes | yes |
| `PORT_CONFLICT` | no | no | no | yes | yes |
| `STALE_OWNERSHIP` | confirmation-gated | no | no | yes | yes |
| `INSTALLATION_INCOMPLETE` | no | no | no | yes | limited |
| `STATUS_ERROR` | no | no | no | yes | limited |

### Security Master controls

| Security state | Install | Update | Restart TW-Market | History / Rollback |
|---|---:|---:|---:|---:|
| `NOT_INITIALIZED` | yes | no | no | advanced only |
| `ACTIVE` | no | yes | no | advanced only |
| update in progress | no | no | no | no |
| update succeeded + runtime running | no | no | yes | advanced only |
| update succeeded + runtime stopped | no | no | no | advanced only |
| strict X509 compatibility retry available | no | no (`Retry TLS` only) | no | advanced diagnostics only |
| update failed with active release retained | no | yes | no | advanced only |
| unavailable/corrupt | no | no | no | advanced diagnosis only |

Security Master mutation controls require package runtime and local installation READY. They do not require Local Runtime to be running, but mutation is offered only when runtime state is stable: `STOPPED`, `RUNNING_READY`, or `RUNNING_UNHEALTHY`. It is blocked during starting, stale-ownership, port-conflict, incomplete-installation, or unknown/error states.

## Visual hierarchy

Daily view uses four status cards in a 2x2 arrangement. Status indication is semantic and restrained:

- ready/running: positive;
- legal stopped/not-installed: neutral;
- degraded/restart-required: warning;
- unsafe/conflict/unusable: error.

`Security Master = NOT_INITIALIZED` is neutral, not an error.

`Open Workbench` is the primary daily action when Workbench is ready. Runtime controls are secondary. Package/Python/install engineering details are absent from the daily main surface after setup succeeds.

Advanced / Technical Details may expose bounded diagnostics such as product version, current runtime state, loopback endpoint, MCP transport/readiness/tool count when available, Security Master active release metadata, and raw canonical JSON. It must not expose secrets.

## Product-version presentation

The Launcher may display the packaged product version only from package/release metadata available inside the distribution. It must not infer a version from Git branch names or host integrations.

## Network boundary

The following actions remain local-only and must not cause market/provider acquisition:

```text
Launcher open
Status / Refresh
Start / Stop / Restart Local Runtime
Open Workbench
Diagnose
Set Up TW-Market
Local MCP readiness projection
```

Only an explicit Security Master `Install` or `Update` action may trigger its governed official acquisition path.

## Explicit non-dependencies

Launcher v2 must not call or require:

```text
D:\MCP-Tunnel
OpenAI Secure MCP Tunnel
Local AI Tools Supervisor
ChatGPT connector APIs
Claude/Codex/VS Code-specific integration
any host-specific MCP gateway
```

Host-specific MCP connection is deployment/integration policy outside the TW-Market product Launcher.

## Implementation scope

Authorized implementation scope is limited to:

- `packaging_native/launchers/tw-market-launcher.ps1`;
- launcher-focused tests and acceptance fixtures;
- this v2 governance record;
- minimal package metadata/read helpers only if required to render already-packaged product version.

No runtime route, executor, schema, capability catalog, MCP tool contract, Security Master acquisition logic, or provider behavior is authorized to change.

## Acceptance criteria

Implementation must demonstrate at least:

1. first-run view remains setup-only and zero-provider-network;
2. daily view hides package/Python engineering rows after setup;
3. four daily cards project Runtime, Workbench, Security Master, Local MCP truth;
4. `NOT_INITIALIZED` Security Master is legal and exposes `Install`;
5. `ACTIVE` Security Master exposes `Update`;
6. Install/Update require explicit user confirmation before `update --live`;
7. successful Security Master mutation respects `restart_required` without automatic restart;
8. Local MCP remains host-neutral readiness-only and has no daemon Start/Stop control;
9. runtime Start/Stop/Refresh/Diagnose preserve the frozen P1-A2 lifecycle semantics;
10. Workbench remains loopback-only;
11. no polling, scheduler, hidden agent, host-specific tunnel call, or automatic external acquisition is introduced;
12. strict X509 compatibility retry is evidence-gated to the current attempt, separately confirmed, verified-TLS only, and never offered for unrelated acquisition failures;
13. Windows PowerShell 5.1 parsing and launcher-focused regression tests pass.

## Review gate

This document is intended to supersede only the Launcher presentation/lifecycle composition needed for v2. It does not repeal P1-A1/P1-A2 safety boundaries.

## Owner-side review disposition

Review result: **ACCEPT**.

The contract preserves the frozen P1-A1 zero-network setup boundary, preserves P1-A2 runtime/Workbench/MCP semantics, and adds Security Master first-install/update only through the existing explicit governed CLI.

The review specifically confirms:

- no host-specific MCP integration is introduced;
- `Restart TW-Market` is only an explicit canonical Stop -> verify -> Start sequence;
- Security Master update remains explicit network-bearing work and is never triggered by setup or refresh;
- strict X509 compatibility retry is never silent, is current-attempt evidence-gated, preserves certificate/hostname verification, and requires separate user confirmation;
- `NOT_INITIALIZED` remains a legal non-blocking Security Master state;
- implementation may proceed only within the bounded Launcher/document/test scope above.

```text
LAUNCHER_V2_UX_CONTRACT = ACCEPTED
BLOCKING_FINDINGS = 0
IMPLEMENTATION = AUTHORIZED
COMMIT_PUSH = NOT_AUTHORIZED
```
