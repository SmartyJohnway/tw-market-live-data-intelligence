# v1.5.1 RMA-10 — Native Package / Portability

Date: 2026-11-02  
Status: **PASS / CLOSED**

## 1. Authority and scope

RMA-10 was explicitly authorized by the Owner after RMA-9 closure. The governing
contract is `POST_V1_5_V1_5_1_RMA_TEST_CONTRACT_2026-10-31.md`.

The goal was to validate the built Native distribution rather than the developer
checkout. The gate required at least two independently extracted Native bundle
locations and verification of relocation, package-integrity/tamper enforcement,
exact locked-wheel closure, Launcher, CLI, MCP, Security Master CLI and the Mode
B2 execute-once child wrapper.

This gate did not authorize product repair, commit, push, tag, release, VERSION
mutation, Stable/Tunnel repointing, Phase M, P2-P5 or RMA-11.

Candidate ZIP SHA-256:
`F4B8049B4614C0ED2C4F0799315F0810CC2AE029CEA39FE2F857A8131881D333`

Canonical package-manifest digest observed independently at both locations:
`e8b53c89306a0f8182100716d23ed62295b077d06ff1c5a90d718b2ec17f18f9`

## 2. Fresh isolated execution

Evidence root:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-10\10A-native-portability\attempt-01\`

A single fresh, network-disabled Windows Sandbox received only the candidate ZIP,
a preserved CPython 3.13.7 x64 prerequisite and the external RMA harness. The
canonical repository, Stable installation and host RMA evidence tree were not
visible inside the guest.

Explicit guest checks confirmed these host/developer paths were absent:

- `D:\Codex-Workspace\projects\tw-market-live-data-intelligence`
- `D:\Project-Library\Stable\TW-Market-1.5.0-windows-x64`
- `C:\twmarket_temp`

The same ZIP was then independently extracted into two materially different
locations, each with its own installation Home and service port:

| Case | Bundle root | Home | Port | Result |
|---|---|---|---:|---|
| A | `C:\RMA10_A\TW-Market-1.5.0-windows-x64` | `C:\RMA10_A_Home` | 18210 | PASS |
| B | `C:\Users\Public\Documents\RMA10 Relocated Bundle\TW-Market-1.5.0-windows-x64` | `C:\Users\Public\Documents\RMA10 Relocated Home` | 18211 | PASS |

## 3. Per-location portability matrix

Both locations passed the same 13 product/package checks:

1. package integrity verified before execution;
2. exact locked-wheel closure;
3. bootstrap completed from bundle-local material;
4. bootstrap dependency count matched the locked closure;
5. root `Launch-TW-Market.cmd` completed headless Setup;
6. Launcher Status returned the normal stopped projection;
7. `tw-market.cmd status --json` returned the stopped lifecycle state;
8. Security Master CLI truthfully returned `NOT_INITIALIZED`;
9. runtime marker bound itself to the actual relocated bundle root;
10. Local Service started and `/api/health` was healthy;
11. MCP startup-check returned `startup_check=ok` with adapter v2 / MCP 1.29.0;
12. the packaged Mode B2 execute-once child wrapper was present and callable;
13. normal service Stop completed.

Locked-wheel closure was exact in both locations:

```text
dependency-manifest entries   49
wheelhouse files              49
requirements lock entries     49
filenames exact               true
wheel hashes exact            true
requirements hash set exact   true
```

## 4. Tamper enforcement

Location A was then modified only inside the isolated Sandbox by appending bounded
test bytes to `README-PACKAGE.md`.

The package-integrity verifier rejected the mutation and normal CLI startup was
also blocked by package-integrity enforcement. No product source was changed.
After restoring the exact original bytes, both integrity verification and CLI
status recovered.

```text
original README-PACKAGE.md SHA-256
FDF0851D7BF327EA5D41009ACCB60DC7BC4D0D18DD5E38C8ECD0E2E72D489FB4

restored README-PACKAGE.md SHA-256
FDF0851D7BF327EA5D41009ACCB60DC7BC4D0D18DD5E38C8ECD0E2E72D489FB4
```

Tamper checks: **5 / 5 PASS**.

## 5. Harness containment observation

The guest product matrix completed `PASS` with `failed_checks=[]`. The outer
orchestrator later reported `JIT_MARKER_CLEANUP_TIMEOUT` after Sandbox count was
already zero. This did not invalidate product/package evidence.

The observation is classified under the existing harness-only `RMA-D018`
Sandbox-JIT cleanup class rather than as a new product defect.

Governed cleanup used Sandbox-JIT `-RecoverStale`, which returned
`RESTORED_BEFORE`. A subsequent read-only Status proved the Windows Sandbox VM SID
was absent from both allow and deny rights. One diagnostic orphan
`WindowsSandboxServer.exe` helper was removed by exact PID only after proving
Sandbox runtime count `0` and active JIT marker `false`.

Posthoc adjudication:
`attempt-01\RMA10_POSTHOC_JIT_ADJUDICATION.json`

Final host containment:

```text
Windows Sandbox runtime       0
WindowsSandboxServer helper   0
active Sandbox-JIT marker     false
VM SID in allow rights        false
VM SID in deny rights         false
```

## 6. Acceptance adjudication

RMA-10 satisfies the contract: the same exact Native distribution bootstrapped
and ran from two independent locations, retained identical package identity and
49-wheel dependency closure, enforced manifest integrity, and exposed all required
Launcher/CLI/MCP/Security-Master/Mode-B2 entry surfaces without any developer
checkout or Stable-installation path being available in the guest.

No RMA-10 product defect was found and no product code was changed.

RMA-10 is therefore **PASS / CLOSED**.

## 7. Next boundary

The next undecided execution boundary is:

`RMA-11 — Operator experience acceptance`

It is **NOT_STARTED** and requires a separate explicit Owner instruction. Closing
RMA-10 does not authorize RMA-11, a v1.5.1 version bump, final release-candidate
selection, commit, push, tag, publication, Phase M or P2-P5.
