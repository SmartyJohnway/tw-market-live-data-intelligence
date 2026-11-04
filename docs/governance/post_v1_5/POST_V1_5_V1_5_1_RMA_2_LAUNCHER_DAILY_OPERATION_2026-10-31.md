# Post-v1.5 — v1.5.1 RMA-2 Launcher Daily Operation

Date: 2026-10-31 (Asia/Taipei)
Closure reconciled: 2026-11-01 (Asia/Taipei)
Status: **PASS / CLOSED — CROSS-RMA3 RESTART EVIDENCE SATISFIED**

## 1. Purpose

RMA-2 validates truthful daily control behavior from the real built Native
launcher, including normal lifecycle operation and adverse-state projection.

Candidate identity remained unchanged:

```text
HEAD          b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
origin/main   3f2e5b3a3588d3778d5a4b380c9d8e0a2f41ca05
VERSION       1.5.0
Native ZIP    58FF0FCE0D258E1C43C3531DE90CE640641986F35DDCA58D8C1DBABCBFA00D4F
```

No product-code mutation, version change, commit, push, tag, release, or evidence
deletion was performed by RMA-2.

## 2. Normal daily-operation acceptance

Primary happy-path evidence:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-2\attempt-04\`
Attempt-04 records `status=PASS` with `failed_checks=[]`. It proved:

```text
STOPPED projection / daily buttons        PASS
Start -> RUNNING_READY                    PASS
Workbench Ready / Local MCP Ready         PASS
loopback Workbench URI + HTTP 200          PASS
Open Workbench real browser window         PASS
Refresh preserves service PID/ownership    PASS
no periodic launcher polling               PASS
Diagnose modal + Doctor                    PASS
GUI Stop -> canonical STOPPED              PASS
second Start                               PASS
close Launcher keeps service running       PASS
reopen Launcher projects RUNNING_READY     PASS
explicit Restart                           PASS
Restart replaces managed service PID       PASS
final Stop / final STOPPED                 PASS
installation ID stability                  PASS
```

All daily controls were invoked by exact child HWND + Win32 `BM_CLICK`, with
control name, HWND, WinForms class and enabled state retained in `result.json`.
Host WinCLI screenshots independently show the Launcher and local Workbench.

## 3. Adverse-state projection acceptance

Final state-projection evidence:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-2\attempt-14\`
Attempt-14 proved the canonical projection matrix from isolated real lifecycle
conditions without importing product modules into the package under test:

```text
lifecycle NOT_RUNNING                  -> Launcher STOPPED
START_IN_PROGRESS                      -> STARTING
owned process + health false           -> RUNNING_UNHEALTHY
foreign loopback listener              -> PORT_CONFLICT
stale ownership metadata               -> STALE_OWNERSHIP
incomplete installation                -> INSTALLATION_INCOMPLETE
invalid configured port                -> STATUS_ERROR / INVALID_PORT
```

The stale-ownership Start path returned `CONFIRMATION_REQUIRED` and preserved the
ownership-file hash. Package-integrity guards before and after the fixture matrix
both passed with zero `app/**/__pycache__` directories. Final Base projection
returned `STOPPED`.

Attempt-14 original `result.json` is retained unchanged and contains one false
aggregate check: `status_error_actions`. The underlying UI evidence shows two
same-name `Diagnose` WinForms controls; the harness selected the first disabled
control even though the Daily View `Diagnose` control was enabled. `Start`,
`Stop`, and `Open Workbench` were disabled and `Refresh` was enabled as required.

The independent evidence adjudication is retained at:

`attempt-14\review\status-error-actions-adjudication.json`

It hashes the original result and UI snapshot and records
`state_projection_disposition=PASS_WITH_EVIDENCE_ADJUDICATION`. No original
evidence file was rewritten.
## 4. Harness defect disposition

Attempts 01–03 documented bounded GUI automation defects. Attempt-04 replaced
coordinate-based clicks with exact child-HWND invocation and passed the complete
normal daily-operation path.

Attempts 05–13 are retained as state-projection harness evolution. They exposed
only external-test defects: Python seed nesting, PowerShell automatic-variable
collisions, Sandbox-ID timing, fixture interleaving, stderr capture behavior,
and an attempted helper import that created `app/scripts/__pycache__` and was
correctly rejected by package integrity. No product fix was selected from those
runs.

Attempt-14 uses a standalone non-product-import fixture with Win32 process
identity and bounded loopback listeners. It closes the intended state-projection
coverage. `RMA-D004` is therefore **CLOSED_PASS** and is not a release blocker.

## 5. Cross-RMA3 Security Master update + Restart closure

The RMA Test Contract also requires an **explicit Restart after Security Master
update**. The original RMA-2 attempt-15 is retained as historical evidence of a
fail-closed live acquisition that did not reach `restart_required`.

RMA-3 subsequently supplied the missing successful-update state. Attempt-02
proved real official-source acquisition, evidence-gated verified-TLS compatibility
retry, `QUALIFIED -> ACTIVE`, and `restart_required=true`. The initial Restart
then exposed RMA-D006, which was localized to the undersized Security Master
status timeout rather than to Restart semantics themselves.

The bounded D006 repair was formally retested under:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\attempt-06-fix-retest-60s\`

The fresh isolated candidate returned `RESTART_COMPLETE`, replaced the managed
service PID `4680 -> 7124`, and the first post-Restart Launcher Status returned
`RUNNING_READY`. This directly satisfies RMA-2's cross-group requirement.

Overall RMA-2 disposition is therefore **PASS / CLOSED** for the validated
candidate. The detailed RMA-3 authority is
`POST_V1_5_V1_5_1_RMA_3_SECURITY_MASTER_LIFECYCLE_2026-11-01.md`.

## 6. Containment and next boundary

RMA-2 evidence is retained. No historical attempt is deleted or rewritten.
Sandbox-JIT cleanup for the final runs returned to a clean Host state with no
active JIT marker and no residual Sandbox host processes.

Current release semantics remain unchanged:

```text
VERSION          1.5.0
v1.5.1           candidate outcome only
commit/push/tag  NOT AUTHORIZED
release          NOT AUTHORIZED
Phase M          NOT AUTHORIZED
P2-P5            NOT AUTHORIZED
DELETE           NOT AUTHORIZED
```

RMA-2 has no remaining execution dependency. RMA-3 is now PASS/CLOSED and the
next undecided RMA boundary is `RMA-4 — Local Service + MCP real integration`.
This record does not itself authorize RMA-4, release publication, or version mutation.
