# Post-v1.5 — v1.5.1 RMA-11 Operator Experience Acceptance

Date: 2026-11-03 (Asia/Taipei)
Status: **PASS / CLOSED**

## 1. Acceptance scope

RMA-11 validates TW-Market from a non-developer daily-user perspective. The normal entry is the built bundle-root `Launch-TW-Market.cmd`; the operator must be able to complete setup, manage Security Master, start/stop runtime, use Workbench, recover from governed blocking states, authorize explicit execution, execute once, and understand Result/Audit/AI handoff without needing Python, venv, PowerShell implementation paths, MCP internals, or source-tree commands.

Acceptance contract: the primary experience is understandable, truthful and recoverable; technical detail remains available without becoming the primary workflow.

## 2. Owner-driven E2E disposition

Owner-driven Windows Sandbox acceptance completed the real operator path:

`First-time Setup -> Security Master -> Start -> Workbench -> Request Builder -> Compose -> Validate -> Preview -> recover blocked needs -> Authorize -> explicit network confirmation -> Execute Once -> Mode C Result/Audit/AI Handoff`.

The final successful execution consumed a single-use authorization and reported `EXECUTION ATTEMPTED — succeeded; authorization consumed = YES.` Result/Audit export produced AI-ready Markdown, Canonical Result JSON and Audit JSON from a six-operation execution receipt with 6 succeeded / 0 failed. Audit artifact, bundle, receipt and result integrity verification flags were all true.

## 3. RMA-11 defect disposition

RMA-11 discovered and resolved the following operator-path defects:

- `RMA-D020` — primary-path technical payload exposure: **CLOSED_PASS**.
- `RMA-D021` — Workbench selection-schema drift: **CLOSED_PASS**.
- `RMA-D023` — blocked-preview recovery UX: **CLOSED_PASS**.
- `RMA-D024` — authorization-readiness / governed I3 date-authority recovery: **CLOSED_PASS**.
- `RMA-D026` — network-confirmation / audit-reference execution UX: **CLOSED_PASS**.
- `RMA-D027` — Mode C recent-performance / AI-handoff semantic inconsistency: **CLOSED_PASS**.

`RMA-D022` remains `DEFERRED_NON_BLOCKING` as isolated D021 offline-retest lifecycle/startup latency evidence. `RMA-D025` is also `DEFERRED_NON_BLOCKING`: one Validate attempt hit the intentional process-local `resource_concurrency_limit`; the same running Sandbox subsequently returned HTTP 200 on direct validation probe and the Owner immediately retried the normal flow successfully. No persistent gate leak or release-blocking failure was reproduced. The operator-message/retry UX debt is preserved rather than erased.

D027 closure used the same already-executed governed predecessor package and a new noncanonical diagnostic projector candidate. It re-materialized Mode C locally with `external_market_network_executed=false`; recent return became `-4.375% / available / 5td`, Recent Performance rendered exactly once, request/result/audit identities remained consistent, the receipt remained 6/6 succeeded, and all audit-integrity flags remained true.

## 4. Validation and candidate status

The final D027 diagnostic Native ZIP SHA-256 is `5b115a255844f816dbe4239177778c70c21ce980596e99bddc30508618de4bfa`. Package integrity passed. D027 targeted regression passed; affected non-historical regression passed 127/127 with 6 historical cases deselected; `git diff --check` passed.

All RMA-11 diagnostic candidates remain **noncanonical** and `release_eligible=false`. RMA-11 closure does not select `VERSION=1.5.1`, does not make the current dirty working tree a release candidate, and does not authorize commit, push, tag, publish, Registry publication, Phase M or P2–P5.

## 5. Final RMA-11 acceptance

RMA-11 is **PASS / CLOSED**. The normal built-Native operator path is accepted as understandable, truthful and recoverable for the tested v1.5.1 patch candidate content, with advanced technical detail available but no longer required as the primary workflow.

With this closure, `RMA-0` through `RMA-11` all have recorded **PASS/CLOSED** dispositions and there are no open RMA release blockers. The RMA program is therefore complete.

The next boundary is a **separate v1.5.1 release-gate / final-candidate decision** under the Test Contract. Before a release candidate can be proposed, the accumulated uncommitted RMA repairs must be assembled into exact final bytes and the required current test/release governance gates must pass with no unreviewed unrelated mutation. Only a later explicit Owner authorization may select `VERSION=1.5.1`, commit/push release changes, build a final release candidate, tag or publish.

No RMA evidence, historical gate record, frozen v1.5.0 tag or published asset is modified by this closure.

## 6. Final frontdoor reconciliation verification

Current-authority reconciliation completed across `PROJECT.md`, `HANDOFF.md`, `docs/governance/INDEX.md`, the RMA Release Preflight/Continuity record, the Defect Register, and the latest `docs/PROJECT_HISTORY.md` summary. A contradiction scan found no current-frontdoor residue claiming `RMA-11 NOT_STARTED`, `NEXT_UNDECIDED`, or another remaining RMA execution group.

The active Defect Register table was machine-counted as 27 sequential entries (`RMA-D001` through `RMA-D027`): 25 `CLOSED_PASS`, 2 `DEFERRED_NON_BLOCKING` (`RMA-D022`, `RMA-D025`), and zero release blockers. `git diff --check` passed after reconciliation.

Final host isolation state has zero running Windows Sandbox environments and no active Sandbox-JIT marker. A system-managed idle `WindowsSandboxServer.exe` helper may respawn even with zero Sandbox environments; it is not treated as an active guest or RMA evidence dependency.
