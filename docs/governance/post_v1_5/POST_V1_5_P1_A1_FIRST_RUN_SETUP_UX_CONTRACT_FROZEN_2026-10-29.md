# Post-v1.5 P1-A1 — First-run / Setup UX Contract

Date: 2026-10-29

Status: **OWNER_FROZEN**

## Purpose

P1-A1 freezes the first-run / setup UX boundary for the Windows Native operator
path before launcher implementation. It does not itself constitute implementation
or Windows Sandbox acceptance evidence.

The accepted setup model is **P1-Minimal**:

- external CPython 3.13 x64 remains a prerequisite;
- the operator is not required to type Python or PowerShell commands;
- a distinct Windows Launcher orchestrates existing canonical bootstrap and
  installation lifecycle commands;
- setup performs no automatic external network activity;
- setup does not acquire market data or initialize/update Security Master;
- setup does not start Local Runtime, open Workbench, or start MCP;
- setup never auto-deletes, auto-repairs, overwrites, or adopts existing state.

## Launcher architecture boundary

Candidate human entry:

```text
Launch-TW-Market.cmd
        -> launcher/tw-market-launcher.ps1
        -> Windows PowerShell 5.1 + WinForms
```

The Launcher is a thin operator facade only. Existing lifecycle authority remains
canonical. It must not implement competing PID, port, health, installation,
Security Master, or MCP lifecycle authority.

Canonical orchestration remains:

```text
pre-bootstrap: validate prerequisite -> bootstrap.ps1
post-bootstrap: tw-market.cmd status --json
conditional:    tw-market.cmd init --json
```

`tw-market.cmd` remains the canonical lifecycle CLI and is not repurposed as the
human GUI entry.

## First-run authority

`Set Up TW-Market` authorizes only:

1. creation/verification of the package-derived local runtime; and
2. explicit local installation initialization through the existing lifecycle.

It does **not** authorize:

- Security Master `update --live`;
- TWSE / TPEx / TAIFEX acquisition;
- evidence execution;
- Local Service start;
- Workbench automatic open;
- MCP process start;
- background work, scheduler or polling;
- PATH/Registry mutation, Windows service installation, scheduled tasks or UAC.

## Python prerequisite contract

The current Native contract remains external **CPython 3.13 x64**.
The user is not required to type Python commands.

Discovery is bounded to validated local candidates. A candidate is accepted only
if a probe proves CPython 3.13, 64-bit, Windows AMD64/x86_64. Wrong versions,
32-bit builds, PyPy, and Windows Store aliases/stubs are rejected.

Automatic Python installation or download is outside P1-A1. The Launcher must not
invoke `winget`, Microsoft Store, Chocolatey, Scoop, pip networking, or arbitrary
package/download commands.

## Existing runtime and state

A valid existing package runtime is reused. A valid existing installation is
reused. Setup is idempotent.

Unsafe, stale, relocated, incomplete, or unverifiable derived runtime state must
fail closed. P1-A1 does not authorize automatic deletion or repair.

If fresh installation initialization encounters existing non-empty canonical
business state, the existing lifecycle must return the explicit-transfer boundary.
The Launcher must not adopt, move, rename, delete, overwrite, or merge that state.

A fresh Security Master `NOT_INITIALIZED` result is a legal setup completion
state, not product corruption.

## Setup completion boundary

P1-A1 ends when:

```text
Package Runtime    READY
Installation       READY
```

It does not require Security Master activation and does not start the Local
Runtime. Daily runtime control is delegated to P1-A2.

## Acceptance evidence boundary

This frozen contract records design authority only. It does not claim that the
Launcher has been implemented or accepted on a fresh machine.

After an implementable artifact exists, Windows Sandbox acceptance is required.
The preferred harness is the existing Sandbox-JIT orchestrator. The source bundle
is mounted/read as input, copied to a guest-local writable location before
bootstrap, and acceptance evidence is returned through the designated writable
output directory.

Acceptance must distinguish specification/probe statements from observed artifact
results. At minimum it must cover missing/wrong/valid Python, repeated setup,
valid existing installation reuse, `NOT_INITIALIZED`, tampered package, stale
runtime, existing business state, zero automatic market/provider acquisition, and
clean Sandbox/JIT teardown.

## Owner freeze

Owner authorization on 2026-10-29 freezes this P1-A1 contract as the boundary for
P1 launcher design and implementation. Any change that weakens the zero-network,
no-auto-repair, no-auto-Security-Master, or thin-facade boundaries requires a new
explicit governance decision.

P1-A2 — Daily Main Launcher / Runtime Control UX Contract is the next active
bounded tranche. P1 implementation remains **NOT_STARTED** until the launcher UX
contracts are complete and separately authorized.
