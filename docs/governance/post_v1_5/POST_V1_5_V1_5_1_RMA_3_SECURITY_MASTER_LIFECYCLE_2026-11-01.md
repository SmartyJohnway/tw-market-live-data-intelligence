# Post-v1.5 — v1.5.1 RMA-3 Security Master Lifecycle

Date: 2026-11-01 (Asia/Taipei)
Status: **PASS / CLOSED**

## 1. Purpose and authority

RMA-3 validates the built Native product's Security Master lifecycle: first install,
verified-TLS update/retry, qualification/activation, restart semantics, stopped-runtime
recovery, failed-update retention, history, and bounded rollback.

Repository checkpoint throughout closure remained:

```text
branch        main
HEAD          b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
origin/main   3f2e5b3a3588d3778d5a4b380c9d8e0a2f41ca05
VERSION       1.5.0
```

No commit, push, tag, release, VERSION mutation, Phase M start, P2-P5 start, or
evidence deletion is authorized by this closure.
## 2. Real install / TLS / activation evidence

Primary live-network lifecycle evidence is retained under:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\attempt-02\`

That attempt proved the supported first-install path from `NOT_INITIALIZED`. Strict
verified TLS first produced the allowlisted `PYTHON_X509_STRICT_COMPATIBILITY`
condition. The Launcher exposed an explicit compatibility retry only after evidence
was present; compatibility mode retained certificate validation and hostname
verification. The retry completed official-source materialization, qualification,
and activation of release `security-master-20261101T033334Z` with:

```text
Security Master      ACTIVE
record_count         54842
execution_eligible   2204
restart_required     true
```

No silent TLS fallback, `unsafe-explicit` Launcher route, certificate-verification
disable, or hostname-verification disable was accepted.
## 3. D006 / D007 bounded repair closure

D006 root cause was proven as the too-small Security Master status subprocess budget
inside `scripts/tw_market_lifecycle.py::_sm_status()`. A 30-second candidate remained
insufficient in fresh Sandbox; the final bounded candidate is 60 seconds and still
fails closed as `CHECK_TIMEOUT` on `subprocess.TimeoutExpired`.

Before formal retest, targeted regression was 2/2 PASS and the two directly affected
unit-test files were 56/56 PASS. Formal fresh-Sandbox closure evidence is retained at:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\attempt-06-fix-retest-60s\`

It proved post-ACTIVE Status/Doctor stability, `RESTART_COMPLETE`, return to
`RUNNING_READY`, and managed-service PID replacement `4680 -> 7124`.

D007 was simultaneously closed: a controlled lifecycle Doctor failure
`FAIL / INVALID_PORT` is now projected by Launcher as `DOCTOR_FAILED / INVALID_PORT`
while retaining the underlying payload/reason.

`RMA-D006` and `RMA-D007` are therefore **CLOSED_PASS** for the validated candidate.
## 4. Remaining lifecycle / recovery closure

Final isolated lifecycle evidence is retained under:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\attempt-08-remaining-lifecycle\`

Using a preserved official-acquisition-derived two-release fixture, the fresh
network-disabled Sandbox proved:

```text
history A=QUALIFIED / B=ACTIVE                  PASS
failed update retains active pointer B          PASS
failed update leaves history stable             PASS
stopped-runtime next Start -> RUNNING_READY B    PASS
bounded rollback B -> A                         PASS
history A=ACTIVE / B=QUALIFIED                  PASS
next Start after rollback -> RUNNING_READY A     PASS
bounded rollback A -> B                         PASS
invalid rollback -> REJECTED / release_missing  PASS
invalid rollback retains active pointer          PASS
final B ACTIVE / A QUALIFIED history             PASS
```

Attempt-08 completed with `failed_checks=[]`, guest `PASS`, orchestrator `PASS`, and
Sandbox-JIT `PASS_RESTORED` with zero residual Sandbox runtime processes and no
active JIT marker.
## 5. Defect and cross-group disposition

`RMA-D005` is **CLOSED_PASS** as a harness-only defect: the presence-safe evidence
handling and rejection matching were corrected in later preserved attempts, and the
RMA-3 lifecycle subsequently completed without that summarization failure.

`RMA-D006` and `RMA-D007` are **CLOSED_PASS** as described above.

`RMA-D001 — Production Evidence TLS Policy Integration` remains **OPEN** for the
broader RMA-6/RMA-7 source-by-source matrix. That does not keep RMA-3 open: RMA-3
proved the Security Master lifecycle's governed strict-TLS / evidence-gated retry
behavior. RMA-D001 asks whether every advertised executable production capability
has a governed usable official-source route under the supported runtime.

RMA-3 also closes RMA-2's cross-group requirement for an explicit Restart after a
successful Security Master update: the validated candidate reached ACTIVE with
`restart_required=true`; the final D006 retest then proved explicit Restart,
managed-service PID replacement, and return to `RUNNING_READY`.

## 6. Final RMA-3 disposition

All required RMA-3 scenarios in the RMA Test Contract have accepted evidence.
RMA-3 disposition is therefore **PASS / CLOSED**.

The next RMA group is `RMA-4 — Local Service + MCP real integration`, but this
closure record does not itself authorize starting RMA-4 or publishing a release.
## 7. Evidence/artifact identity

```text
RMA-0 baseline Native ZIP
58FF0FCE0D258E1C43C3531DE90CE640641986F35DDCA58D8C1DBABCBFA00D4F

D006/D007 60-second diagnostic candidate ZIP
905FEF6EA830F318A6CC786416B4E68F9E1F2676949B5208F955C13A2C77A374

Two-release remaining-lifecycle fixture ZIP
0ABD67479E6D323032AA9BAC1862D59CEFD4F7036BF32FE7737E203A753FDDE4
```

The diagnostic candidate and lifecycle fixture are **NONCANONICAL TEST ARTIFACTS**
and **NOT RELEASE-ELIGIBLE**. They exist to prove the bounded repair and lifecycle
semantics. A later release decision must build and recertify a canonical artifact
under its own release authority; this RMA-3 closure does not promote either ZIP.
