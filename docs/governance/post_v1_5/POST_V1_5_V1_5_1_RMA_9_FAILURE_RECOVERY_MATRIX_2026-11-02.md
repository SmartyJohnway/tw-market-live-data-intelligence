# v1.5.1 RMA-9 — Failure and Recovery Matrix

Date: 2026-11-02  
Status: **PASS / CLOSED**

## 1. Authority and scope

RMA-9 was explicitly authorized by the Owner after RMA-8 closure. The governing
contract is `POST_V1_5_V1_5_1_RMA_TEST_CONTRACT_2026-10-31.md`.

This gate deliberately exercised bounded failure conditions against the final
post-RMA diagnostic Native candidate. It did not authorize product repair,
commit, push, tag, release, version mutation, Stable/Tunnel repointing, Phase M,
or P2-P5.

Candidate SHA-256:
`F4B8049B4614C0ED2C4F0799315F0810CC2AE029CEA39FE2F857A8131881D333`

Preserved ACTIVE Security Master fixture SHA-256:
`0ABD67479E6D323032AA9BAC1862D59CEFD4F7036BF32FE7737E203A753FDDE4`

Both execution gates used fresh, isolated, network-disabled Windows Sandboxes.
## 2. Gate 9A — Native / lifecycle failure and recovery

Evidence:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-9\9A-native-failure-recovery\attempt-01\`

Guest result: **19 / 19 checks PASS**.

Verified behavior:

- stopped service was reported truthfully as lifecycle `NOT_RUNNING` and Launcher `STOPPED`;
- MCP startup against the stopped Local Service failed closed with
  `local_service_unavailable`, then recovered after a normal Start;
- an unrelated listener produced `PORT_CONFLICT`, then normal service health
  recovered after that exact fixture process was stopped;
- stale ownership produced `STALE_OWNERSHIP`; Start without confirmation returned
  `CONFIRMATION_REQUIRED / STALE_PROCESS_OWNERSHIP`, while explicit stale-owner
  confirmation enabled bounded recovery;
- a missing runtime marker produced `SETUP_REQUIRED / PACKAGE_RUNTIME_NEEDS_ATTENTION`
  and exact marker restoration returned the Launcher to its normal stopped state;
- uninitialized Security Master state reported `NOT_INITIALIZED`, and the preserved
  qualified fixture restored `ACTIVE` state;
- a deliberately corrupted isolated active pointer failed closed; restoring its
  exact original bytes restored `ACTIVE` state;
- final Local Service health and MCP startup-check both returned healthy/ready.
## 3. Gate 9B — governed failure and recovery

Evidence:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-9\9B-governed-failure-recovery\attempt-01\`

Posthoc-adjudicated result: **23 / 23 checks PASS**.

Verified behavior:

- invalid Request V3 returned deterministic `validation_status=invalid` with
  `REQUEST_SCHEMA_INVALID` and created no authority package;
- required `session_status` preview was truthfully `unsupported_capability` and
  could not be authorized; no authority package was created;
- a byte-tampered Control Package was rejected with HTTP 409 before claim,
  receipt, bundle, or evidence creation;
- the candidate's fixed child contract intentionally projects internal execution
  orchestration failures as public `mode_b2_execution_unavailable`; the original
  harness incorrectly required the internal artifact-hash reason to cross that boundary;
- restoring the exact Control Package request bytes restored manifest integrity;
- with networking disabled, the restored approved monthly-revenue execution was
  consumed truthfully as `consumed_failed / failed` rather than false success;
- the failed execution still produced verified Receipt, Bundle, Result V3, Audit
  Package and Handoff with integrity flags true and `result_status=failed`;
- the Local Service remained healthy after the external source failure;
- a fresh Preview/Authorization could be issued afterward, proving a bounded
  retry path without replaying the consumed failed ticket.
## 4. Harness-only defect dispositions

`RMA-D018` — **CLOSED_PASS**. The 9A outer orchestrator sampled the JIT marker
immediately before final cleanup completed. Guest evidence was already PASS; final
JIT evidence independently records `PASS_RESTORED`, no policy drift and complete
cleanup. Final host containment showed zero Sandbox runtime and no active marker.

`RMA-D019` — **CLOSED_PASS**. The 9B harness incorrectly expected internal
`control_package_artifact_hash_mismatch` to be exposed by the public execution API.
Direct inspection of the exact candidate ZIP proved both the internal artifact-hash
guard and the fixed child projection of `OrchestrationError` to public
`mode_b2_execution_unavailable`. The tamper was still rejected before consumption.

No RMA-9 product defect was found and no product code was changed.

## 5. Acceptance adjudication

RMA-9 satisfies the contract acceptance criteria:

- failures were represented truthfully;
- all tested unsafe/invalid paths failed closed;
- governed public reason codes were preserved at their defined boundaries;
- durable state was either unchanged or finalized into a truthful failed execution;
- each recoverable condition had a bounded recovery path;
- governance rejection was not misclassified as product corruption.
## 6. Final containment and next boundary

Final host containment after both Sandbox gates:

- Windows Sandbox runtime count: `0`;
- Windows Sandbox Server helper count: `0`;
- active Sandbox-JIT marker: `false`;
- both JIT runs: `PASS_RESTORED`;
- Stable installation and Secure MCP Tunnel were not repointed or modified;
- no evidence was deleted;
- no commit, push, tag, release, or VERSION change was performed.

RMA-9 is therefore **PASS / CLOSED**.

The next undecided execution boundary is `RMA-10`. It is **NOT_STARTED** and
requires a separate explicit Owner instruction. Closing RMA-9 does not authorize
RMA-10, RMA-11, a v1.5.1 version bump, release publication, Phase M, or P2-P5.
