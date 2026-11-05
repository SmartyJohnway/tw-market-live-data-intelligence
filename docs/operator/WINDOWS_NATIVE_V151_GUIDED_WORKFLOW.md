# Windows Native v1.5.1 — Guided Operator Workflow

**This is the main user-facing improvement from v1.5.0 to v1.5.1.**
The goal is that an ordinary Windows operator can perform first-run setup,
daily operation, governed data research and AI handoff **without starting
from Python, a terminal, source code, JSON or MCP implementation details**.
The accepted evidence is the historical RMA-0 through RMA-11 real-machine /
Sandbox acceptance program, not a promise of new live E2E in this guide.

[Download Windows Native v1.5.1](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/TW-Market-1.5.1-windows-x64.zip) ·
[SHA-256 sidecar](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/TW-Market-1.5.1-windows-x64.zip.sha256) ·
[Operator Quick Start](QUICK_START.md) ·
[Published evidence and six asset checksums](../release/V1_5_1_RELEASE_PUBLICATION.md)

## First-time use — what the operator actually does

1. **Download and verify** the v1.5.1 ZIP, then extract to a writable
   local folder. Do not run an unknown or altered bundle.
2. **Double-click `Launch-TW-Market.cmd`** at the package root.
   The Launcher shows whether Python 3.13 x64, Package Runtime and
   Local Installation are ready. Python is an **external prerequisite**
   and is not installed by TW-Market. You do not need to type Python
   commands for the primary GUI installation route.
3. If prerequisites are ready, click **Set Up TW-Market**. The package
   boots from bundled offline hash-locked wheels and initializes the
   installation if appropriate. A success dialog leads to **Daily View**.
   No automatic Security Master update, provider request, Windows service
   installation, browser open or Local Runtime start happens at Setup.
4. Inspect four daily status areas: **Local Runtime, Workbench, Security
   Master, Local MCP**. Choose **Install** for an uninitialized
   Security Master only if you intend the separately confirmed official
   source acquisition. An existing Master may instead show **Update**.
5. Click **Start TW-Market** to start the Local Service, then
   **Open Workbench** once it reports Ready. Closing the Launcher window
   is **not** equivalent to Stop; Stop is a separate explicit control.

## Everyday research — guided Workbench journey

6. **Request Builder:** select an eligible target and data needs; select
   **Compose Frozen Request**. Request/selection technical JSON and
   provenance are still inspectable under expanded technical details,
   not required as the main interaction.
7. **Validate** the composed request, then **Preview**. The preview
   tells you whether the chosen capability, identity, dependencies and
   source/route are currently allowed. If blocked, follow the shown
   reason and recovery guidance; **Preview never grants execution authority**.
8. If and only if the preview is eligible, use **Authorize** to bind the
   exact plan. When data acquisition requires external network access,
   acknowledge the **separate explicit network confirmation**, then
   choose **Execute Once**. There is no hidden polling or model-chosen
   retry. The one-time authorization is consumed.
9. Use **Mode C / Result-Audit-AI Handoff** to read the canonical
   Result, supporting Audit/evidence citations and AI-ready Markdown,
   with optional JSON downloads for technical verification.
10. Use **Diagnose** and **Refresh** for truthful stopped/blocked
    status. A failed official source or validation is not reported as
    successful data. Repair a specific condition and explicitly
    re-validate/re-authorize where applicable.

## What was changed and accepted: RMA-0 through RMA-11

| Acceptance group | Verified scope / operator benefit |
|---|---|
| **RMA-0 — provenance baseline** | Distinguishes stable v1.5.0, the local patch candidate, installed Native bundle, state and rollback roots. Prevents accidental cross-version/state confusion. |
| **RMA-1 — first-run setup** | Fresh Windows Sandbox with no Python, then supplied Python 3.13 x64, GUI Setup, success dialog, Daily View, repeat Setup; clear prerequisite/setup state and no GUI/command confusion. |
| **RMA-2 — everyday Launcher** | Explicit Start/Stop, Workbench open, Refresh, Diagnose and honest service states; local port conflict/stale ownership are not silently overwritten. |
| **RMA-3 — Security Master lifecycle** | User-visible Install/Update/Restart, status budget handling for a real large Master, Doctor error truthfulness and verified-TLS compatibility retry only on grounded failures. |
| **RMA-4 — Local Service + MCP integration** | Real Local Service and six stdio MCP tools tested, including a ChatGPT-connected deployment path; host-neutral Launcher presents MCP readiness, not a fake MCP daemon. |
| **RMA-5 — identity resolution** | Code, `MARKET:CODE`, ISIN and Chinese company names resolve to the right canonical listing; unsupported/nonexistent types fail closed instead of guessing. |
| **RMA-6 — capability and execution** | Validate/Preview/Authorize/explicit network-confirmation and actual bounded execution tested; blocked capabilities/required source dates remain fail-closed; typed result coverage truthfulness fixed. |
| **RMA-7 — official source and TLS** | Real official-source usability with verified certificate/hostname handling and bounded compatibility behavior; no silent unsafe SSL fallback. |
| **RMA-8 — Result/Audit/evidence integrity** | Successful real governed executions and persisted request/plan/authorization/receipt/bundle/result/audit hash and citation chain consistency. |
| **RMA-9 — failure/recovery** | Stopped service, port conflict, stale ownership, missing runtime marker, invalid Request, tampered Control Package and source failure produce truthful bounded responses and recoverable paths. |
| **RMA-10 — portable Native package** | Validated clean/relocated package roots and HOME, including paths with spaces; offline bootstrap, Launcher, Local Service and MCP startup work with their own installation state. |
| **RMA-11 — end-user experience** | Owner-driven full Setup → Security Master → Launcher → Workbench → Build → Validate → Preview/recover → Authorize/confirm → Execute Once → Mode C E2E. Technical JSON collapsed; blocked Preview recovery, authorization-readiness, confirmation UX and AI handoff improved. |

The historical RMA-11 issue register closed D020/D021/D023/D024/D026/D027,
while **RMA-D022 and RMA-D025 remain `DEFERRED_NON_BLOCKING`**
(startup latency and a transient concurrency-limit retry).
They were not silently declared solved; normal recovery was demonstrated
for the reported concurrency episode. The entire RMA-0..11 program has
historical `PASS/CLOSED` disposition; v1.5.1's later official release
was a **separate** acceptance and publication decision.

## Security Master and TLS: no silent steps

- Setup does **not** install/update Security Master. `NOT_INITIALIZED`
  is a legitimate local initial state.
- Security Master **Install** or **Update** is an explicit operator
  request to fetch from official external sources.
- Strict verified TLS is the default. `Retry TLS` can be offered only
  when the current governed evidence supports that compatibility action;
  it requires a second confirmation and still validates the certificate
  and hostname. No silent or unsafe TLS fallback.
- If a real update requires a runtime restart, the Launcher shows a
  separate Restart action; it does not unilaterally stop the operator's
  running workload.
- Advanced History/Rollback/technical payload details remain available
  via their respective documented surfaces, not as mandatory primary UI.

## Boundaries and honest limitations

- Tier-1 platform: Windows 11 x64. CPython 3.13 x64 is required externally.
- Local stdio MCP requires a compatible client and local runtime; the
  GitHub v1.5.1 MCPB is **not** the official MCP Registry v1.5.1
  (the Registry still listed historical 1.0.0 on 2026-11-05).
- No automatic polling, scheduled provider fetch, generic full-market
  scanner, autonomous trading, broker orders or realtime guarantees.
- Watchlist v0 → v1 production migration remains
  `KNOWN_NOT_IMPLEMENTED`; signing authority remains
  `NOT_ESTABLISHED`. First-party SBOM and SHA-256 are not a
  cryptographic publisher signature.
- This guide references accepted RMA and source-equivalent release
  evidence. It does not assert a newly repeated live official-market
  E2E after GitHub publication.

## Technical background / acceptance evidence

The detailed frozen RMA records are preserved under
`docs/governance/post_v1_5`. Starting points:

- [RMA-1 first-run installation](../governance/post_v1_5/POST_V1_5_V1_5_1_RMA_1_FRESH_FIRST_RUN_INSTALLATION_2026-10-31.md)
- [RMA-2 Launcher daily operation](../governance/post_v1_5/POST_V1_5_V1_5_1_RMA_2_LAUNCHER_DAILY_OPERATION_2026-10-31.md)
- [RMA-3 Security Master lifecycle](../governance/post_v1_5/POST_V1_5_V1_5_1_RMA_3_SECURITY_MASTER_LIFECYCLE_2026-11-01.md)
- [RMA-10 portability](../governance/post_v1_5/POST_V1_5_V1_5_1_RMA_10_NATIVE_PACKAGE_PORTABILITY_2026-11-02.md)
- [RMA-11 Owner E2E](../governance/post_v1_5/POST_V1_5_V1_5_1_RMA_11_OPERATOR_EXPERIENCE_ACCEPTANCE_2026-11-03.md)
- [RMA defect register](../governance/post_v1_5/POST_V1_5_V1_5_1_RMA_DEFECT_REGISTER_2026-10-31.md)
