# Post-v1.5 — v1.5.1 RMA-1 Fresh First-Run Installation

Date: 2026-10-31 (Asia/Taipei)
Status: **PASS / ACCEPTANCE COMPLETE**

## 1. Purpose

RMA-1 validates a normal first-run path from the real built Native distribution,
using isolated Windows Sandbox state rather than the developer source tree.

Final acceptance evidence root:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-1\attempt-16\`

Candidate identity remained unchanged:

```text
HEAD          b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
VERSION       1.5.0
Native ZIP    58FF0FCE0D258E1C43C3531DE90CE640641986F35DDCA58D8C1DBABCBFA00D4F
wheel count   49
```

No provider-network acquisition, product-code mutation, commit, push, tag,
release, version change, or evidence deletion was performed by RMA-1.
## 2. Final acceptance sequence

Attempt-16 replayed the exact two-stage first-run sequence:

1. fresh Sandbox with networking disabled and no `python.exe` / `py.exe`;
2. built Native bundle extracted under Unicode + space path;
3. first GUI showed `First-time setup`, Python `Required`, runtime `Not set up`,
   and Setup disabled;
4. first GUI and its launcher process tree exited cleanly;
5. offline CPython 3.13.7 x64 seed was supplied through the supported PATH route;
6. second GUI showed Python `Ready` and enabled `Set Up TW-Market`;
7. Setup completed and displayed the explicit success dialog;
8. the success dialog was dismissed and the GUI transitioned to Daily View;
9. headless Status / SecurityStatus and repeat Setup were verified afterward.

Primary UI evidence:

- `output\ui-setup-result-dialog-via-main.json`
- `output\03b-setup-result-dialog-via-main.png`
- `output\ui-daily-view.json`
- `output\04-daily-view.png`
- `host-gui-observation\observer.jsonl` and captured Sandbox screenshots.
## 3. Acceptance result

Attempt-16 `output\result.json` records `status=PASS` and an empty
`failed_checks` array. All required RMA-1 checks are true, including:

```text
network disabled                 PASS
RMA-0 ZIP identity               PASS
Unicode + space path             PASS
fresh no-Python state            PASS
source-template fail-fast        PASS
first GUI prerequisite state     PASS
first GUI process-tree teardown  PASS
CPython 3.13.7 x64 seed          PASS
second GUI Ready / Setup enabled PASS
Setup success dialog             PASS
runtime marker / venv            PASS
installation metadata / READY    PASS
Daily View System Status         PASS
Daily View Local Runtime Stopped PASS
Security Master Not installed    PASS
SecurityStatus NOT_INITIALIZED   PASS
repeat Setup / idempotence       PASS
49-wheel exact closure           PASS
installation ID stability       PASS
```
## 4. Harness and cleanup closure

The final orchestrator records:

```text
guest readiness handshake       PASS on attempt 1
guest exit                       0
Host WinCLI observer             PASS
Sandbox-JIT                      PASS_RESTORED
post sandbox count               0
post Sandbox host-process count  0
post active JIT marker           false
```

During harness diagnosis it was proven that `wsb list --raw` itself can launch a
short-lived `WindowsSandboxServer.exe`. The final orchestrator therefore avoids
calling `wsb list` after the final orphan cleanup and records the killed
Sandbox-Server PID as evidence. This is RMA infrastructure behavior, not a
TW-Market product dependency.

Attempts 01–15 remain preserved. They document harness evolution, the attempt-07
runtime-verification symptom, later successful isolated replays, and the final
Daily View observation race. No historical evidence is rewritten or deleted.

## 5. Defect disposition and next group

`RMA-D002` is closed by attempt-16 because the corrected external harness reaches
all intended RMA-1 product gates.

`RMA-D003` is no longer a release blocker: the exact two-stage first-run sequence
passes without any product-code change, after multiple successful diagnostic
replays. The attempt-07 failure remains preserved as historical evidence; its
specific transient trigger was not proven.

RMA-1 disposition: **PASS**.

The next authorized group is `RMA-2 — Launcher daily operation`.
RMA-1 PASS does not authorize `VERSION=1.5.1`, commit, push, tag, release,
Phase M, or P2–P5.
