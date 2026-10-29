# Post-v1.5 P1-A2 — Daily Main Launcher / Runtime Control UX Contract

Date: 2026-10-29

Status: **OWNER_FROZEN**

## Purpose

P1-A2 defines the normal daily Windows Launcher UX after P1-A1 setup. It is a
thin presentation/orchestration contract over the existing lifecycle JSON
surface; it does not create a second runtime manager.

Canonical backend commands remain:

```text
tw-market.cmd status --json
tw-market.cmd start --json
tw-market.cmd doctor --json
tw-market.cmd stop --json
```

P1-A2 does not change their semantics.

## Daily launcher principles

- one status refresh when the Launcher opens;
- no timer-based background polling;
- explicit user Refresh is always available when runtime prerequisites exist;
- Start and Stop are explicit operator actions;
- each Start/Stop completion is followed by one status refresh;
- closing the Launcher does not stop TW-Market;
- starting TW-Market does not automatically open Workbench;
- no tray daemon, Windows service, scheduler, updater, or hidden background agent.

## Normalized launcher states

The Launcher projects existing lifecycle payloads into the following UI states:

| Launcher state | Canonical evidence |
|---|---|
| `SETUP_REQUIRED` | package runtime or installation not ready; route back to P1-A1 |
| `STOPPED` | `service.process=NOT_RUNNING`, `alive=false` |
| `STARTING` | `service.process=START_IN_PROGRESS` |
| `RUNNING_READY` | owned process and `service.alive=true` |
| `RUNNING_UNHEALTHY` | owned `RUNNING` process but `service.alive=false` |
| `PORT_CONFLICT` | `PORT_OCCUPIED_NOT_OWNED` |
| `STALE_OWNERSHIP` | `STALE_PROCESS_OWNERSHIP` |
| `INSTALLATION_INCOMPLETE` | installation exists but is not READY |
| `STATUS_ERROR` | bounded status command fails or yields unusable JSON |

Security Master and MCP are secondary status dimensions; they do not replace the
primary Local Runtime state.

`Security Master = NOT_INITIALIZED` does not demote `RUNNING_READY`.

## Main Launcher surface

The normal daily view presents:

```text
Local Runtime
Workbench
Security Master
Local MCP
```

Primary controls:

```text
[ Start TW-Market ]  [ Open Workbench ]
[ Refresh ]          [ Diagnose ]
[ Stop TW-Market ]
```

## Control enablement

| State | Start | Open Workbench | Refresh | Diagnose | Stop |
|---|---:|---:|---:|---:|---:|
| `SETUP_REQUIRED` | no | no | yes | limited | no |
| `STOPPED` | yes | no | yes | yes | no |
| `STARTING` | no | no | yes | yes | no |
| `RUNNING_READY` | no | yes | yes | yes | yes |
| `RUNNING_UNHEALTHY` | no | no | yes | yes | yes |
| `PORT_CONFLICT` | no | no | yes | yes | no |
| `STALE_OWNERSHIP` | confirmation-gated | no | yes | yes | no |
| `INSTALLATION_INCOMPLETE` | no | no | yes | limited | no |
| `STATUS_ERROR` | no | no | yes | limited | no |

Passive status inspection must not mutate stale ownership metadata.

For `STALE_OWNERSHIP`, Start may be offered only as an explicit operator action
with a confirmation explaining that the existing canonical start lifecycle may
remove stale **ephemeral ownership metadata** before launching. This does not
authorize deletion or repair of package runtime, Security Master, Watchlists,
governed evidence, or other business state.

## Start behavior

`Start TW-Market` invokes only the canonical `start --json` path.

Expected successful outcomes include `STARTED` and `ALREADY_RUNNING`. After the
command returns, the Launcher performs one status refresh and renders actual
state rather than assuming the service is ready.

`START_IN_PROGRESS` is informational. No hidden retry loop or automatic polling
is started; the operator may use Refresh.

## Stop behavior

`Stop TW-Market` is available only for an owned running process and invokes only
canonical `stop --json`.

A successful `STOPPED` result is followed by one status refresh. Closing the
Launcher window never implies Stop.

The Launcher must never stop a process merely because the configured port is
open. `PORT_OCCUPIED_NOT_OWNED` remains a protected foreign-process condition.

## Open Workbench

Open Workbench is enabled only when canonical status reports `service.alive=true`.
The Launcher derives the browser target only from validated canonical loopback
host/port state and appends `/workbench/`.

No arbitrary environment URL, user-supplied URL, redirect target, or non-loopback
endpoint may be launched as the Workbench target.

Opening Workbench is an explicit operator action and opens the default browser.
It performs only local loopback navigation at Launcher level; market acquisition
remains governed by later explicit Workbench actions.

## Refresh and diagnosis

Refresh performs one `status --json` call. It does not start or stop services.

Diagnose performs one `doctor --json` call and renders the canonical checks,
including PASS/WARN/FAIL, reason codes, and bounded technical details. Raw JSON
may be exposed under an optional Technical Details surface.

A stopped Local Runtime may legitimately produce doctor warnings such as local
service or MCP service unreachability. The Launcher must preserve raw warning
truth while explaining that these warnings can be expected when the runtime is
intentionally stopped.

## Security Master projection

P1-A2 is status-only for Security Master.

```text
ACTIVE          -> Ready
NOT_INITIALIZED -> Not initialized
UNAVAILABLE     -> Needs attention
```

No P1-A2 control may call `update --live`, history, rollback, activation, or
candidate qualification. Those controls belong to P3.

## Local MCP projection

P1-A2 presents readiness, not a daemon lifecycle:

```text
READY                -> Ready for MCP clients
SERVICE_UNREACHABLE  -> Local Runtime is stopped/unreachable
MCP_RUNTIME_MISMATCH -> Needs attention
```

The surface may show transport=`stdio` and tools=`6` when supported by canonical
readiness evidence. There is no Start MCP Server or Stop MCP Server button.
Host-specific ChatGPT/tunnel integration remains P4.

## Failure UX

The primary message uses stable product semantics rather than raw tracebacks.
Reason codes remain available in Technical Details.

Examples include:

- `PORT_OCCUPIED_NOT_OWNED` -> selected local port belongs to another process;
- `STALE_PROCESS_OWNERSHIP` -> stale TW-Market ownership metadata detected;
- `START_TIMEOUT` -> Local Runtime did not become healthy within the canonical bound;
- `START_FAILED` -> Local Runtime could not be started;
- `STOP_FAILED` -> owned process could not be stopped safely;
- `INSTALLATION_INCOMPLETE` -> local installation needs attention.

## Network and acquisition boundary

Launcher status, start, stop, refresh, and diagnosis are local operations. Open
Workbench is explicit local loopback browser navigation. P1-A2 itself must not
perform market/provider acquisition, external web requests, polling, or scheduled
refresh.

## Acceptance criteria for later implementation

An implementable Launcher artifact must demonstrate at least:

- stopped -> explicit Start -> healthy running state;
- running -> explicit Stop -> stopped state;
- `NOT_INITIALIZED` Security Master does not block Local Runtime readiness;
- foreign occupied port is never opened as Workbench and never stopped;
- owned process with failed health becomes `RUNNING_UNHEALTHY`;
- start-in-progress is not hidden behind retries;
- stale ownership passive inspection is read-only;
- explicit stale-ownership Start follows only canonical lifecycle behavior;
- Open Workbench uses the validated loopback endpoint only;
- closing the Launcher leaves an intentionally running service running;
- no periodic background status polling;
- MCP remains readiness-only with exactly six tools;
- no external provider acquisition is caused by Launcher lifecycle actions.

Windows Sandbox is preferred for fresh-machine launcher acceptance once the
artifact exists. This frozen design contract does not claim that implementation
acceptance has occurred.

## Owner review and freeze

Owner review on 2026-10-29 accepted this contract with no blocking findings.
Review confirmed that the normalized launcher states and reason-code handling
map to the existing lifecycle surface, that installation endpoints are bounded
to loopback hosts, and that lifecycle status/doctor paths do not perform market
provider acquisition. Sixteen reviewed lifecycle status/reason tokens were found
in the current implementation.

This freeze is design authority only. It does not constitute launcher
implementation, Windows Sandbox acceptance, release publication, or Phase M
authorization.

## Out of scope

P1-A2 does not authorize launcher implementation, Security Master lifecycle UI,
MCP host configuration, OpenAI Secure MCP Tunnel management, bundled Python,
new lifecycle APIs, runtime refactoring, release/tag mutation, P2–P5, or Phase M.

## Frozen disposition

```text
P1_A2_DAILY_MAIN_LAUNCHER_RUNTIME_CONTROL_UX = OWNER_FROZEN
OWNER_REVIEW = ACCEPT
BLOCKERS = 0
IMPLEMENTATION = NOT_STARTED
P1_A3 = NOT_AUTHORIZED
PHASE_M = NOT_AUTHORIZED
```
