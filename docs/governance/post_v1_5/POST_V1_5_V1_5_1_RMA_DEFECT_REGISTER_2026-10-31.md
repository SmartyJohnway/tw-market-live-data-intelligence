# Post-v1.5 — v1.5.1 RMA Defect Register

Date: 2026-10-31 (Asia/Taipei)
Last reconciled: 2026-11-03 (Asia/Taipei)
Status: **RMA CLOSED / PRE-RELEASE DEFECT AUTHORITY**

This register is the single working defect ledger for the v1.5.1 RMA tranche.
It does not replace historical governance records and does not authorize fixes,
commits, pushes, version bumps, tags or releases.

## 1. Classification model

Severity:

- `BLOCKER` — prevents a safe/credible v1.5.1 release.
- `MAJOR` — substantial product defect; release disposition required.
- `MINOR` — bounded usability/diagnostic defect with no contract break.
- `NOTE` — observation, debt or improvement; not a defect by itself.

Status:

- `OPEN`
- `REPRODUCED`
- `FIX_AUTHORIZED`
- `FIXED_PENDING_RETEST`
- `CLOSED_PASS`
- `NOT_A_BUG_GOVERNED_REJECTION`
- `EXTERNAL_CONDITION`
- `DEFERRED_NON_BLOCKING`

## 2. Required defect fields

Every unexpected RMA result must record:

| Field | Required content |
|---|---|
| ID | Stable `RMA-D###` identifier |
| RMA group | RMA-0 through RMA-11 |
| Area | Launcher / Runtime / Security Master / MCP / Source / TLS / Evidence / Package / UX |
| Symptom | Exact observed behavior |
| Reproducible | Yes / No / Intermittent / Not yet retested |
| Severity | BLOCKER / MAJOR / MINOR / NOTE |
| Status | One governed status above |
| Public capability affected | Exact capability or `none` |
| Contract expectation | What current authority requires |
| Evidence | Log/artifact/screenshot/result references |
| Root cause | Proven / probable / unknown |
| Release blocker | Yes / No / Pending adjudication |
| Fix scope | Exact files/authority allowed to change |
| Fix commit | SHA when one exists |
| Retest | RMA case + PASS/FAIL |
| Owner disposition | authorization / defer / reject / close |

## 3. Active register

| ID | RMA | Area | Symptom | Severity | Status | Release blocker |
|---|---|---|---|---|---|---|
| RMA-D001 | RMA-7 | Production source / TLS trust integration | Cold Native Python/OpenSSL trust depended on lazy Windows root-store population; bounded repair moved verified production TLS to the governed bundled certifi trust set and fresh cold Native retest qualified all 23 production source cases with verified TLS and product parser/schema PASS | BLOCKER | CLOSED_PASS | No |
| RMA-D002 | RMA-1 | Test harness | Sandbox harness defects across early attempts prevented trustworthy observation of the full first-run path | NOTE | CLOSED_PASS | No |
| RMA-D003 | RMA-1 | Launcher / Runtime / UX | Attempt-07 reported `RUNTIME_VERIFICATION_FAILED` after bootstrap, but exact two-stage replays later passed without product-code change | BLOCKER (historical) | CLOSED_PASS | No |
| RMA-D004 | RMA-2 | Test harness / GUI automation | Attempt-01 coordinate-based GUI automation mis-clicked Security Master `Install` while intending daily-operation controls, making the final `Stop` observation invalid | NOTE | CLOSED_PASS | No |
| RMA-D005 | RMA-3 | Test harness / evidence summarization | Attempt-01 preserved valid Security Master source evidence but the external harness threw under StrictMode when optional probe fields were absent; later preserved RMA-3 attempts corrected the presence-safe handling/rejection matching and completed the lifecycle without recurrence | NOTE | CLOSED_PASS | No |
| RMA-D006 | RMA-3 / RMA-2 cross-gate | Lifecycle / Launcher / Security Master restart integration | ACTIVE 54,842-record Security Master state exceeded the original 10-second and first 30-second status budgets; a bounded 60-second budget passed fresh ACTIVE/Restart retest without weakening fail-closed behavior | BLOCKER | CLOSED_PASS | No |
| RMA-D007 | RMA-3 | Launcher Doctor projection | Lifecycle Doctor failure was incorrectly wrapped as `DOCTOR_COMPLETE`; Launcher now returns `DOCTOR_FAILED` while preserving the underlying failure payload/reason | MAJOR | CLOSED_PASS | No |
| RMA-D008 | RMA-4 | Test harness / Local Service contract negotiation | Attempt-01 HTTP capability probe omitted `X-TW-Market-Service-Contract`, so the service correctly negotiated legacy v1 while the harness incorrectly required v2 | NOTE | CLOSED_PASS | No |
| RMA-D009 | RMA-5 | Test harness / PowerShell environment setup | Preflight used `$home`, which collides case-insensitively with PowerShell's read-only `$HOME`; candidate status therefore targeted the user home instead of the intended isolated RMA Home before any RMA-5 product probe ran | NOTE | CLOSED_PASS | No |
| RMA-D010 | RMA-5 | Test harness / identity acceptance predicate | Attempt-02 incorrectly required `resolution_status=resolved` for an existing warrant whose Security Master identity is known but execution eligibility is blocked; product correctly returned `unsupported_security_type`, canonical identity, `unsupported_instrument_type`, and a non-plannable preview | NOTE | CLOSED_PASS | No |
| RMA-D011 | RMA-6 | Test harness / planner status vocabulary | RMA-6 6B attempt-01 expected orchestration `plan_status=ready`, while the current planner contract correctly emits `plan_ready`; affected executable cases were otherwise valid, ready-for-confirmation, authorization-eligible, and zero-network | NOTE | CLOSED_PASS | No |
| RMA-D012 | RMA-6 | Test harness / H2 dependency construction | RMA-6 6B attempt-01 requested `corporate_action_context` alone; the current planner correctly requires same-target H3 recent-performance evidence and returned `required_h3_dependency_missing / plan_only_not_executable`; corrected attempt-02 supplied the governed H3 dependency and passed | NOTE | CLOSED_PASS | No |
| RMA-D013 | RMA-6 / RMA-8 cross-gate | Result V3 coverage / typed evidence truthfulness | Live `trading_status_context` had all three TPEx source components `source_failed` with zero covered status types, yet canonical Result/Handoff reported `full_success` because V3 typed coverage treated any non-null evidence object as provided | BLOCKER | CLOSED_PASS | No |
| RMA-D014 | RMA-7 | Test harness / source qualification projection | 7D attempt-03 produced five false negatives because the generic probe imposed a 4 MiB read ceiling on TPEx EOD and projected H1/H2 response metadata with keys that did not match the product decoder contract; corrected clean retest qualified all five | NOTE | CLOSED_PASS | No |
| RMA-D015 | RMA-7 | Test harness / JSON serialization | 7D attempt-04 wrote the five-case inventory with a UTF-8 BOM, causing the probe to fail before source acquisition; attempt-05 used UTF-8 without BOM and completed 5/5 qualification | NOTE | CLOSED_PASS | No |
| RMA-D016 | RMA-8 | Test harness / Windows Sandbox ID resolution | 8B attempt-01 started a single fresh Sandbox but performed a one-shot `wsb list --raw` lookup before the environment was reliably enumerable; the harness raised `SANDBOX_ID_RESOLUTION_FAILED` before any guest/product probe executed. Clean attempt-02 used bounded unique-ID resolution, crossed this gate, ran the guest, and restored Sandbox/JIT cleanly. | NOTE | CLOSED_PASS | No |
| RMA-D017 | RMA-8 | Test harness / lineage reviewer acceptance predicate | 8B attempt-02 reviewer read response-only `control_package_manifest_hash` from persisted `authorization.json`, creating a false manifest-binding failure, and unconditionally required every probe to be a successful execution even though RMA-8 acceptance applies to successful executions. Preserved guest file-manifest evidence and posthoc adjudication proved both actual successful cases bind the exact control manifest hash and pass every remaining lineage check. | NOTE | CLOSED_PASS | No |
| RMA-D018 | RMA-9 / RMA-10 cross-gate | Test harness / Sandbox-JIT cleanup sampling | RMA-9 9A first exposed cleanup-state sampling around Sandbox-JIT restoration. RMA-10 attempt-01 reproduced the same harness/containment class after the product guest had already passed: the outer orchestrator timed out waiting for the active marker after Sandbox count reached zero. Governed `-RecoverStale` returned `RESTORED_BEFORE`; read-only Status proved the VM Sandbox SID absent from allow/deny rights, and one diagnostic orphan `WindowsSandboxServer.exe` helper was removed by exact PID only after runtime=0 and marker=false. Final host containment is zero Sandbox runtime/server and no active marker. | NOTE | CLOSED_PASS | No |
| RMA-D019 | RMA-9 | Test harness / tamper reason-code acceptance predicate | 9B attempt-01 correctly rejected a tampered Control Package with HTTP 409 and zero claim/receipt/bundle/evidence creation, but the harness incorrectly required the internal `control_package_artifact_hash_mismatch` code to cross the fixed child boundary. Exact candidate-ZIP bytes prove the child intentionally projects `OrchestrationError` as public `mode_b2_execution_unavailable`; posthoc adjudication accepted the governed public code together with exact byte restoration and the no-consumption invariant. | NOTE | CLOSED_PASS | No |
| RMA-D020 | RMA-11 | Workbench / UX | Primary operator path exposed implementation-heavy request/provenance payloads. Bounded frontend repair moved both Unified Request JSON and selection provenance behind default-collapsed Advanced disclosures while preserving Generated Request + Validate as the normal path. Owner E2E accepted the repaired hierarchy. | MAJOR | CLOSED_PASS | No |
| RMA-D021 | RMA-11 | Workbench / Request Builder | `Compose Frozen Request` failed because selection v3 lagged the active 14-capability authority. Bounded schema repair aligned selection v3 to 14 capabilities; Owner E2E generated valid Unified Request v3 without schema-invalid failure. | BLOCKER | CLOSED_PASS | No |
| RMA-D022 | RMA-11 / D021 retest | Test environment / lifecycle startup | Fresh offline D021 retests hit lifecycle `SERVICE_START_TIMEOUT` / Security Master `CHECK_TIMEOUT` before Builder/API probe; direct packaged Composer validation and later owner flows passed. Preserved as non-blocking latency/startup evidence. | NOTE | DEFERRED_NON_BLOCKING | No |
| RMA-D023 | RMA-11 | Workbench / blocked-preview recovery UX | Blocked Preview exposed internal reason codes without recovery guidance. Bounded repair translated blockers, identified affected capabilities and added `Review Evidence Needs`; Owner E2E recovered to `ready_for_confirmation` without external procedural instruction. | BLOCKER | CLOSED_PASS | No |
| RMA-D024 | RMA-11 | Workbench / authorization readiness | TWSE institutional-flow request could preview as confirmable but then fail authorization on missing governed source-date authority. Repair projects authorization readiness before authorization, refuses to guess dates, and gives a recoverable Evidence Needs path; Owner E2E recovered to full-possible ready-for-confirmation. | BLOCKER | CLOSED_PASS | No |
| RMA-D025 | RMA-11 | Workbench / resource concurrency UX | One normal Validate attempt surfaced `resource_concurrency_limit`; same running Sandbox then returned HTTP 200 on direct validation probe and immediate normal retry succeeded. No persistent gate leak reproduced; operator busy/retry messaging debt is preserved. | NOTE | DEFERRED_NON_BLOCKING | No |
| RMA-D026 | RMA-11 | Workbench / Execute Once confirmation UX | Network-required authorization exposed a disabled confirmation control and unexplained operator-reference prompt. Repair added explicit network-confirmation gating plus inline editable `Audit reference (not a password)`; Owner E2E completed one-shot execution and single-use authorization consumption. | BLOCKER | CLOSED_PASS | No |
| RMA-D027 | RMA-11 | Mode C / Result-AI handoff | Canonical Result carried complete 5-day recent-performance evidence while derived metric said unavailable and Markdown rendered Recent Performance twice. Projector repair consumes governed `baselines[].recent_return_pct` and renders V3 Recent Performance once; same 6/6 execution predecessor reprojected locally with no new market network and consistent Result/Audit/Handoff. | BLOCKER | CLOSED_PASS | No |

### RMA-D001 — Production Evidence TLS Policy Integration

Current state: **CLOSED_PASS**. Release blocker: **No**.

Prior owner-side real-machine observation indicated:

- `recent_performance` succeeded on its tested official route;
- `current_observation`, `monthly_revenue`, and `material_disclosures` encountered
  strict X509 compatibility failure on the tested Windows / CPython 3.13 path.

At initial registration this record deliberately did not declare a specific
library, endpoint, certificate-chain, or runtime-integration root cause. RMA-7A
through RMA-7D subsequently supplied the required source-by-source and trust-store
evidence; the current root-cause and repair qualification is recorded below.

Release rule: if a currently advertised executable capability is reproducibly
unusable on the supported runtime because its production source path lacks a
governed verified-TLS compatibility route, the defect is a `v1.5.1` blocker.

Security rule: acceptable repair must retain certificate validation and hostname
verification. Silent fallback and verification disable are forbidden.

RMA-2 cross-gate attempt-15 added real Native evidence under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-2\attempt-15\`. In a fresh
network-enabled Sandbox, real Security Master strict acquisition returned
`SECURITY_MASTER_UPDATE_FAILED / official_acquisition_or_qualification_failed`
and left Security Master `NOT_INITIALIZED`. The failure did **not** expose the
specific X509 evidence required for the Launcher compatibility-retry offer, so
no retry was performed and the product remained fail-closed. This is relevant
reproduction evidence for the broader production-source/TLS investigation, but
it does not yet prove that RMA-D001's exact source-by-source X509 mechanism is
the cause. RMA-3/RMA-7 must preserve and inspect the lower-level acquisition
probe evidence before root-cause or fix authorization.

RMA-3 attempt-01 then preserved that lower-level evidence under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\attempt-01\output\security-evidence-install-strict\`.
Both fresh TWSE ISIN identity probes (`strMode=2` and `strMode=4`) failed before
HTTP with `URLError -> SSLCertVerificationError`,
`transport_error_class=tls_certificate_verification`, and
`transport_reason_code=TLS_CERTIFICATE_VERIFICATION_FAILED`; transport success
was 0/2 and the principal decision was
`BLOCKED_BY_OFFICIAL_SOURCE_PROBE_FAILURE`. This is materially different from
the allowlisted `PYTHON_X509_STRICT_COMPATIBILITY` condition, so the Launcher was
correct not to offer a compatibility retry. The evidence strengthens the TLS /
trust investigation but still does not establish whether the cause is Sandbox /
CPython trust-store behavior, the official certificate chain, or product runtime
integration. No repair is authorized from this observation alone.

RMA-6D attempt-01 added a fresh network-enabled Sandbox capability matrix under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-6\6D-live-execution\attempt-01\`.
Several production routes raised only generic `URLError` at the preserved operational-event layer, while other routes returned without usable evidence. No `X509` signature is present in the preserved RMA-6D output, so that attempt alone did not prove the narrow TLS/X509 mechanism.

RMA-7 7B attempt-01 now provides direct source-by-source reproduction evidence under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-7\7B-tls-source-probe\attempt-01\`.
A fresh Native Setup using CPython 3.13.7 / OpenSSL 3.0.16 tested 23 inventoried
production source cases. Every source was attempted once under `strict` and once
under the governed verified `compatibility` context, with zero retries and no
certificate or hostname verification disable. All 23 strict attempts failed before
HTTP with `URLError -> SSLCertVerificationError`; 14 reported verify code 19
(`self-signed certificate in certificate chain`) and 9 reported verify code 20
(`unable to get local issuer certificate`). The compatibility attempts reproduced
the same 14/9 distribution, so clearing `VERIFY_X509_STRICT` did not establish a
usable route in this fresh environment. Product parser/schema logic was therefore
not reached in any of the 46 transport attempts, and no raw source payload was
persisted. At that checkpoint RMA-D001 was
`OPEN / REPRODUCED / ROOT_CAUSE_LOCALIZATION_REQUIRED`. This evidence still did
not by itself distinguish product/runtime trust-store
integration from Windows/Sandbox trust state or provider-chain behavior.

RMA-7 7C attempt-01 then localized the trust differential under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-7\7C-trust-localization\attempt-01\`.
Across six representative official hosts, Windows PowerShell / Schannel returned
HTTP 200 for 6/6 and the certifi bundle already installed in the Native runtime
(version 2026.7.22, 121 CA certificates) also returned HTTP 200 for 6/6 while
retaining `CERT_REQUIRED` and hostname verification. Python default strict failed
6/6. The existing compatibility policy recovered 4/6 but still failed
`mis.twse.com.tw` and `openapi.taifex.com.tw`; this confirms that clearing
`VERIFY_X509_STRICT` alone is not a complete trust solution. The fresh runtime had
no `SSL_CERT_FILE`, `SSL_CERT_DIR`, Requests/cURL CA override, or HTTP(S) proxy
environment configured. `ssl.get_default_verify_paths()` exposed no active cafile
or capath, while the default Python context held only about 11-12 CA certificates.
These observations localized RMA-D001 to Python/OpenSSL trust-material selection /
integration on the supported Native runtime rather than a general outage of the
official providers. RMA-7D subsequently completed the required determinism and
full certifi source/parser qualification.

RMA-7D evidence is retained under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-7\7D-trust-determinism\`.
Two independent fresh Sandboxes reproduced the same cold-to-primed trust mutation:
Windows `ROOT` certificates changed from 16 to 18 and Python default-context CA
certificates changed from 11 to 13 immediately after the first successful
Windows-native HTTPS request; the before/after trust-set hashes were identical
across both attempts. This closes the 7B/7C discrepancy as a deterministic lazy
Windows automatic-root/intermediate retrieval timing effect.

Before any Windows-native priming, the already governed bundled
`certifi==2026.7.22` CA set then qualified the complete 23-source inventory with
certificate verification enabled, hostname verification enabled, HTTP 2xx, and
product parser/schema PASS for every case. Machine adjudication records
`inventory_count=23`, `certifi_qualified_count=23`, `qualified_exact=true`, and
`all_verified=true`. `certifi` is already locked in `requirements-lock.txt`,
the Native wheelhouse lock and the dependency SBOM, so no new dependency is
required.

Root cause is therefore proven: the pre-repair strict and compatibility construction
in `scripts/ssl_policy.py` depended on non-deterministically populated
platform/default Python trust material; compatibility only cleared
`VERIFY_X509_STRICT` and did not make the trust anchor set deterministic.

The Owner explicitly authorized bounded repair in
`USER_CHAT_2026-11-01_BOUNDED_REPAIR_RMA_D001`. The repair uses the already bundled
governed certifi CA set for verified production TLS contexts, retains certificate
and hostname verification, preserves strict-vs-compatibility flag semantics, and
adds no silent fallback. Fresh packaged cold-Sandbox retest under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-7\7E-d001-bounded-repair\attempt-01-cold-production-matrix\`
qualified all 23 declared production source cases: 23/23 production usable,
23/23 product parser/schema PASS, verified TLS retained, zero retry, explicit SSL
context for every route, and policy semantics PASS. Diagnostic candidate SHA-256:
`F4B8049B4614C0ED2C4F0799315F0810CC2AE029CEA39FE2F857A8131881D333`.

The historical Phase-I I1 activation remains preserved; the exact authorized
post-repair I1 file delta is governed by
`POST_V1_5_V1_5_1_RMA_D001_I1_LIVE_TESTED_SUPERSESSION_2026-11-01.json`.
RMA-D001 is therefore `CLOSED_PASS` and no longer a release blocker.

### RMA-D002 — RMA-1 Sandbox Harness Invocation / ZIP Root

Attempt-01 evidence is retained under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-1\attempt-01\`. The Sandbox itself
started and JIT cleanup completed `PASS_RESTORED`, but TW-Market was not validly
launched. Proven harness causes: the guest `Run-Capture` helper used the reserved
PowerShell automatic variable name `$Args`, so child arguments were lost; and the
harness assumed ZIP contents were extracted directly into the destination while
the package contains top-level directory `TW-Market-1.5.0-windows-x64`.

Classification: test-harness issue only; product bytes were not implicated and no
release blocker is created. Fix scope is restricted to the external RMA harness.
Attempt-01 must remain preserved. Attempt-02 reached the real first-run GUI and
proved network-disabled ZIP/hash/path/fresh-prerequisite/source-template gates,
but exposed two additional harness assumptions: WinForms controls were surfaced
as `ControlType.Pane` rather than `ControlType.Button`, and the harness did not
wait for the first GUI window to fully disappear before reopening it after Python
provisioning. Attempt-03 removed those assumptions and proved the same gates, but
then exposed a third harness-contract mistake: it expected environment variable
`TW_MARKET_BOOTSTRAP_PYTHON` to drive Launcher discovery. The actual product
contract accepts `-PythonPath`, `py.exe -3.13`, PATH `python.exe`, or the user-facing
`Locate Python 3.13...` action; the environment variable is not a Launcher
selection authority. Attempt-04 then tried to automate that standard Windows file
picker, but the dialog was not exposed through the assumed top-level process-title
mechanism; the attempt stopped before Setup and JIT again restored host policy.
Attempts 01–04 are preserved. RMA-1 will use the equally supported PATH discovery
route after explicitly proving the fresh no-Python state; the full Locate-Python
operator interaction is deferred to RMA-11. Attempt-11 added explicit first-GUI
process-tree teardown proof and showed the parent `cmd.exe` did exit, with no
remaining bundle launcher process reported after close, but the harness treated
the empty/null process-list serialization as a non-zero count and stopped before
the second GUI. This is another bounded D002 harness defect, not product evidence;
its null-safe count is corrected in attempt-12. Attempt-12 then completed Setup,
created a READY installation, returned `STOPPED`, preserved Security Master as
`NOT_INITIALIZED`, passed repeat Setup/idempotence, exact 49-wheel closure and
installation-ID stability. Its only three failed checks were GUI Daily View text
checks because the harness broke from its Setup wait as soon as installation
metadata appeared, a few moments before the success modal was rendered; Host
WinCLI captured that success modal while the guest immediately sampled the still-
blocked underlying First-time setup form. Attempt-13 corrects this observation
race by explicitly waiting for and dismissing the success modal (or observing the
post-modal System Status render) before sampling Daily View. Attempt-16 finally
closed the observation gap by reading the success modal through the main-window
Automation tree, dismissing `確定`, and then proving Daily View `System Status`,
Local Runtime `Stopped`, and Security Master `Not installed`. Its guest result is
`PASS` with `failed_checks=[]`; the orchestrator also passed with JIT
`PASS_RESTORED` and zero residual Sandbox host processes. `RMA-D002` is therefore
**CLOSED_PASS**.

### RMA-D003 — Native First-Run Setup Runtime Verification Failure

RMA-1 attempt-07 reproduced a real user-facing first-run failure in a fresh,
network-disabled Windows Sandbox using the exact RMA-0 Native ZIP. Python 3.13.7
x64 was supplied through the supported PATH discovery route. The GUI reached
`Python 3.13 x64 = Ready`, enabled `Set Up TW-Market`, created both
`runtime/runtime-marker.json` and `runtime/venv`, then displayed:
`Setup did not complete: RUNTIME_VERIFICATION_FAILED` before Local Installation
metadata was created.

Minimum evidence is retained under
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-1\attempt-07\`, including
`host-gui-observation\manual-setup-plus8s.jpg`,
`host-gui-observation\manual-advanced-technical-details.jpg`, and
`output\manual-runtime-probe.json`. The post-failure manual probe is read-only and
shows that the built runtime subsequently returns valid JSON from both
`tw-market.cmd status --json` and Launcher `Status -Headless`, with installation
state correctly reported as `INSTALLATION_NOT_INITIALIZED`. Therefore the current
failure is bounded to the Setup transition immediately after bootstrap rather than
a permanently unusable runtime.

Reproducible: **Yes**. Severity: **BLOCKER**. Status: **REPRODUCED**. Public
capability affected: Native first-run setup / normal-user onboarding. Contract
expectation: a fresh supported user must be able to complete local runtime and
installation setup without manual Python or lifecycle commands. Release blocker:
**Yes** until RMA-1 retest passes.

Root cause is not yet proven. A same-Sandbox isolated-bundle probe then replayed
`bootstrap -> tw-market.cmd status --json` without using the failed GUI instance.
The first status at effectively 0 ms after bootstrap, plus 100 ms, 500 ms and
2000 ms repeats, all returned exit code 0 and a single parseable JSON payload with
`INSTALLATION_NOT_INITIALIZED`. Evidence is retained as
`output\first-post-bootstrap-probe.json`. This weakens and does not support a
generic post-bootstrap timing/noisy-status explanation as the sole root cause.
The failure is now narrowed toward the exact Launcher Setup process / GUI event
context or another state specific to that invocation.

Attempts 08–10 then isolated the main path/context variables without changing
product bytes. Attempt-08 used separate ASCII+space bundles: original Headless
Setup returned `SETUP_COMPLETE`, and original GUI Setup created a READY
installation. Attempt-09 used true Unicode `測試` (`U+6E2C U+8A66`) bundle paths;
both Headless and GUI setup succeeded, and Host WinCLI captured the explicit
successful `TW-Market Setup` completion dialog while the GUI used default
`%LOCALAPPDATA%\TW-Market`. Attempt-10 replayed the exact three code points seen
in the failed attempt-07 runtime path (`U+769C U+7948 U+5CAB`, rendered
`皜祈岫`); Headless and GUI setup again succeeded and both reached READY
installation state. All three diagnostic Sandboxes were network-disabled, used
the exact RMA-0 ZIP, and ended with JIT `PASS_RESTORED`, zero Sandbox instances,
and no active JIT marker.

These results rule out ASCII-vs-Unicode path, spaces, default HOME, Headless-vs-
GUI Setup in isolation, and the attempt-07 unusual path code points as sufficient
causes. The remaining material sequence difference is the RMA-1 acceptance flow
used by attempts 06/07: open a fresh no-Python GUI, verify Setup is disabled,
close that GUI, seed Python, then launch a second GUI and perform Setup. The next
reproduction therefore targets that exact two-stage first-run sequence and will
prove complete process-tree teardown between the two GUI launches.

Launcher `Invoke-Lifecycle` currently requires its entire merged stdout/stderr
payload to parse as JSON, while the later Security Master path already uses a
last-JSON payload parser. That remains a robustness investigation lead, but the
successful isolated replays mean it is **not proven causal**. The GUI Technical
Details view also replaces the lower-level raw status with the higher-level
`SETUP_BLOCKED / RUNTIME_VERIFICATION_FAILED` result, reducing first-failure
observability.

No product-code fix was applied. Attempts 12, 13 and 15 repeatedly reached READY
installation state in the exact two-stage first-run sequence, and attempt-16 then
passed the complete RMA-1 contract including the success modal and Daily View.
The final replay used the same candidate bytes and exact RMA-0 ZIP; only the
external acceptance harness changed. The attempt-07 symptom therefore remains
preserved as a real historical observation, but it is not reproducible as a
current release-blocking product failure under the corrected exact-sequence
acceptance.

Fix scope: **none selected**. Fix commit: none. Root cause: **unproven transient
trigger / acceptance-environment interaction**. Retest: **RMA-1 attempt-16 PASS**.
Status: **CLOSED_PASS**. Release blocker: **No**. This closure does not erase or
reinterpret attempt-07 evidence and does not authorize a product-code repair.

## 4. Candidate fixes already present before RMA

These are not open defects. They are baseline changes that require RMA regression:

| Commit | Candidate change | Required RMA coverage |
|---|---|---|
| `b38fde12` | Launcher v2 UX + native entry guard | RMA-1, RMA-2, RMA-11 |
| `8b482be4` | explicit verified TLS compatibility retry for Security Master | RMA-3, RMA-7 |
| `b84f9fc8` | package Mode B2 execute-once wrapper | RMA-4, RMA-6, RMA-8, RMA-10 |

## 5. Register operating rules

1. Do not fix an unexpected result before assigning an RMA defect ID and saving
   minimum reproduction evidence.
2. Do not convert a correct governed rejection into a defect merely because the
   requested operation did not execute.
3. Do not classify an official-source outage as product failure without proving
   the product violated its source/fallback contract.
4. A fix is not closed by a unit test alone; it must pass its named RMA retest.
5. Any fix affecting public contract, routing, source activation, schema,
   Security Master authority or transport-security policy requires explicit
   scope review before implementation.
6. Historical records are not rewritten to hide a defect discovered later.
7. No defect closure authorizes `VERSION=1.5.1`, commit, push, tag or release.
8. No RMA evidence or source file is deleted as part of closing an item.

## 6. Final release summary fields

Final RMA disposition counts as of 2026-11-03:

```text
OPEN_BLOCKERS                  0
OPEN_MAJORS                    0
DEFERRED_NON_BLOCKING          2   # RMA-D022, RMA-D025
NOT_A_BUG_GOVERNED_REJECTION   0
EXTERNAL_CONDITION             0
CLOSED_PASS                   25
TOTAL_REGISTERED              27
```

`OPEN_BLOCKERS` is zero. These counts satisfy the defect-disposition prerequisite for a later v1.5.1 release-candidate proposal, but do not by themselves make the current dirty working tree or any noncanonical diagnostic ZIP release-eligible. Final-byte assembly and the remaining release-gate checks are separate.

### RMA-D004 — RMA-2 GUI Automation Mis-click

RMA-2 attempt-01 used coordinate-based UI Automation fallback for daily Launcher controls. The run objectively passed the normal STOPPED and RUNNING_READY projections, loopback Workbench HTTP 200, close/reopen persistence and Restart path. However, Host WinCLI evidence shows the later control click triggered Security Master `Install` (`Updating...`) instead of the intended daily-operation control. The run then ended at `STOPPED_UI_TIMEOUT`; this final Stop observation is invalid as product evidence.

Evidence is retained under `C:\twmarket_temp\v1.5.1-rma-20261031\rma-2\attempt-01\`, including `output\result.json` and Host screenshots around 21:33–21:34 showing the unintended Security Master action and its fail-closed `official_acquisition_or_qualification_failed` result in the network-disabled Sandbox.

Classification: **test harness issue only**; no product-code repair is authorized. Release blocker: **No**. Attempt-04 replaced coordinate fallback with exact child-HWND / `BM_CLICK` invocation and passed the complete normal daily-operation matrix with `failed_checks=[]`, including Start, Stop, Refresh, Diagnose, Open Workbench, close/reopen persistence, Restart and final STOPPED projection. Attempts 05–14 then hardened the adverse-state harness without product-code change. Attempt-14 correctly projected `STARTING`, `RUNNING_UNHEALTHY`, `PORT_CONFLICT`, `STALE_OWNERSHIP`, `INSTALLATION_INCOMPLETE` and `STATUS_ERROR`, with package integrity preserved before and after fixtures. Its sole aggregate false negative, `status_error_actions`, was proven to be a duplicate-control selection error: the retained UI tree contains the disabled hidden-panel `Diagnose` and the enabled Daily View `Diagnose`; `Start`/`Stop`/`Open Workbench` are disabled and `Refresh` is enabled as required. The original result remains unchanged and the bounded adjudication is retained at `attempt-14\review\status-error-actions-adjudication.json`. Retest disposition: **CLOSED_PASS**. The separate RMA-2 requirement for explicit Restart after a successful Security Master update remains a cross-RMA3 acceptance dependency and does not keep RMA-D004 open.


### RMA-D005 — RMA-3 Harness Optional-Field / Rejection-Matcher Defect

RMA-3 attempt-01 successfully reached the real fresh Native Security Master strict acquisition and preserved the generated source evidence. The product-side acquisition itself completed with a governed source-probe rejection. The external RMA harness then failed while summarizing that preserved evidence because PowerShell `Set-StrictMode` treated direct access to absent optional probe fields (first observed at `http_status`) as a terminating `PropertyNotFoundException`.

The same attempt also produced a false negative for `unsafe_explicit_rejected`: the product correctly exited 2 and argparse rejected `unsafe-explicit` as an invalid `_select_security_master_ssl_policy` value, while the harness matcher accepted only narrower wording such as `invalid choice` / `not valid`.

Classification: **test harness only**. Product Security Master behavior is not implicated by either harness failure. Fix scope was restricted to preserved RMA-3 harness continuations: optional evidence fields were read through presence-safe accessors and the rejection matcher was widened to recognize the actual argparse rejection. Attempt-01 remains immutable evidence. Later preserved RMA-3 attempts completed the Security Master lifecycle without recurrence of this summarization/rejection-matcher failure, including the final `attempt-08-remaining-lifecycle` result with `failed_checks=[]`. Status: **CLOSED_PASS**; release blocker: **No**.

### RMA-D006 — Security Master Activation Leaves Launcher Restart Blocked

RMA-3 attempt-02 used the exact RMA-0 Native ZIP in a fresh network-enabled Windows Sandbox. Strict acquisition first produced the allowlisted `PYTHON_X509_STRICT_COMPATIBILITY` condition for both TWSE ISIN identity probes. The Launcher therefore offered the explicit compatibility retry with certificate verification and hostname verification still enabled. That compatibility retry succeeded: official-source materialization completed, the candidate qualified, Security Master became `ACTIVE`, and the Launcher returned `SECURITY_MASTER_UPDATE_COMPLETE` with `restart_required=true` for release `security-master-20261101T033334Z`.

Immediately afterwards, the real Native Launcher `Restart` action returned `ACTION_BLOCKED / RESTART_NOT_ALLOWED_FROM_STATUS_ERROR`. This prevents the exact RMA-3 / RMA-2 cross-gate that the successful update declared necessary. The current root cause is unknown. The next bounded reproduction must capture Launcher `Status`, lifecycle raw status / Doctor evidence and ownership/service state immediately after activation and before Restart. No product-code repair is authorized until that state transition is reproduced and localized.

Classification: **preliminary product integration blocker candidate**. Release blocker: **Pending confirmation**. Evidence root: `C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\attempt-02\`. Sandbox/JIT cleanup returned `PASS_RESTORED`; no host state or product source was mutated.

Targeted attempt-03 used a fresh exact-ZIP Sandbox but could not reach the post-activation state: the same two TWSE ISIN strict probes were classified on that run as generic `TLS_CERTIFICATE_VERIFICATION_FAILED`, so the Launcher correctly did not offer compatibility and the run ended `BLOCKED` before activation. This does **not** count as a D006 non-reproduction because the required `ACTIVE + restart_required` precondition never existed. It does demonstrate live-source / TLS diagnostic variability across fresh Sandboxes. Attempt-03 cleanup also returned `PASS_RESTORED` with no residual Sandbox/JIT state.


Subsequent deterministic reproduction closed the localization gap without relying on live TLS. A host-side diagnostic used the preserved successful attempt-02 official-acquisition snapshot (`d42522b7...fa467`, 54,842 records) to build and qualify an isolated ACTIVE Security Master root at current HEAD `b84f9fc8...`; the build produced 2,204 execution-eligible records and passed qualification. That root was packaged as diagnostic input and injected only into a fresh Sandbox installation-local `Home\state\security-master` after the service had already reached `RUNNING_READY` with `NOT_INITIALIZED` identity. No product module was imported inside the built package and the replay recorded `package_pycache_count=0`.

The deterministic replay is retained under `C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\diagnostics\d006-prebuilt-replay-01\`. It reproduced D006 with networking disabled. SecurityStatus successfully read the ACTIVE 54,842-record release. A direct lifecycle Status could complete in about 22.5 seconds, but a following lifecycle invocation hit the hard-coded Security Master subprocess timeout at about 10.09 seconds and returned `FAIL / CHECK_TIMEOUT`; Launcher Status projected that payload as `STATUS_ERROR / CHECK_TIMEOUT`. Direct Doctor independently reproduced `FAIL / CHECK_TIMEOUT`. Two seconds later another Status completed successfully, confirming timing sensitivity rather than release corruption. The immediately requested Launcher Restart again returned `ACTION_BLOCKED / RESTART_NOT_ALLOWED_FROM_STATUS_ERROR`. Ownership metadata retained the same healthy managed-service PID across the transition.

Root cause is therefore **proven**: `scripts/tw_market_lifecycle.py::_sm_status()` imposes a fixed 10-second subprocess budget on `manage_security_master.py status`. Loading and validating the full ACTIVE 54,842-record identity release is close enough to that boundary in Windows Sandbox that status becomes intermittently `CHECK_TIMEOUT`; Launcher then correctly maps the incomplete lifecycle payload to `STATUS_ERROR`, which in turn prevents the explicitly required Restart. Host timing with the same release (~6.3 seconds) explains why the defect is environment/timing-sensitive rather than universal.

Classification is upgraded to **confirmed product integration BLOCKER**. Release blocker: **Yes**. Any repair must preserve fail-closed identity validation and may not weaken Security Master authority, package integrity, TLS verification, or hostname verification. A fix is not closed until a fresh bounded RMA-3 retest reaches ACTIVE and proves explicit Restart returns to `RUNNING_READY`.

### RMA-D007 — Launcher Doctor Masks Lifecycle Failure as DOCTOR_COMPLETE

The same deterministic D006 replay exposed a separate Launcher projection defect. Direct lifecycle Doctor returned exit code 1 with `status=FAIL` and `reason_code=CHECK_TIMEOUT`, but `Invoke-DoctorAction` only checks whether a payload exists and therefore returned `DOCTOR_COMPLETE` containing that failed payload. This makes the top-level Launcher result claim completion even when the underlying diagnostic operation failed.

Evidence is retained in `C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\diagnostics\d006-prebuilt-replay-01\output\result.json`. Classification: **product UX/integration MAJOR**; status **OPEN / REPRODUCED**. Repair must make Launcher Doctor reflect lifecycle failure without rewriting or hiding the underlying diagnostic payload. Release-blocker status remains pending RMA-3 adjudication; it must at minimum receive regression coverage before RMA-3 closure.

Bounded implementation scope selected for the confirmed D006/D007 repair: D006 may modify only `scripts/tw_market_lifecycle.py` plus lifecycle regression tests to replace the accidental 10-second Security Master status literal with a named bounded budget large enough for a qualified full ACTIVE release. Timeout behavior must remain fail-closed as `CHECK_TIMEOUT`; no Security Master acquisition, identity authority, TLS policy, routing, schema or public MCP contract may change. D007 may modify only `packaging_native/launchers/tw-market-launcher.ps1` plus Launcher regression tests so an underlying lifecycle Doctor failure is projected as `DOCTOR_FAILED` while preserving the original diagnostic payload/reason. No version, release, commit, push or tag authority is implied.

D006/D007 closure retest evidence is retained under `C:\twmarket_temp\v1.5.1-rma-20261031\rma-3\attempt-06-fix-retest-60s\`. Before Sandbox execution, the bounded gate passed the two targeted regression tests (2/2) and both directly affected unit-test files (56/56). The noncanonical diagnostic candidate ZIP SHA-256 is `905fef6ea830f318a6cc786416b4e68f9e1f2676949b5208f955c13a2c77a374`; it is explicitly not release-eligible.

The fresh network-disabled Sandbox retest used the preserved qualified ACTIVE 54,842-record Security Master root. With `SECURITY_MASTER_STATUS_TIMEOUT_SECONDS = 60`, post-ACTIVE direct Status, Launcher Status and normal Doctor all completed without `CHECK_TIMEOUT`; Launcher Status remained `RUNNING_READY`. Explicit Restart returned `RESTART_COMPLETE`, the managed-service PID changed from 4680 to 7124, and the first post-Restart Launcher Status returned successfully as `RUNNING_READY`. The controlled Doctor failure case returned direct lifecycle `FAIL / INVALID_PORT`, while Launcher correctly projected `DOCTOR_FAILED / INVALID_PORT` and preserved the underlying failure payload.

This closes RMA-D006 and RMA-D007 for the validated candidate. The 60-second budget remains bounded and fail-closed: `subprocess.TimeoutExpired` still maps to `CHECK_TIMEOUT`; Security Master authority, qualification, package-integrity checks, TLS certificate verification, hostname verification, routing, schema and public MCP contract were not weakened. Closure does not authorize `VERSION=1.5.1`, commit, push, tag or release. The remaining RMA-3 lifecycle scenarios subsequently passed under `attempt-08-remaining-lifecycle`; overall RMA-3 closure is recorded in `POST_V1_5_V1_5_1_RMA_3_SECURITY_MASTER_LIFECYCLE_2026-11-01.md`.

### RMA-D008 — RMA-4 Local Service Contract Negotiation Harness Assumption

RMA-4 attempt-01 directly queried `/api/unified/capabilities` without the
`X-TW-Market-Service-Contract` header, so the service correctly negotiated its
backward-compatible v1 projection. The harness incorrectly required v2 and
reported one aggregate false negative even though the MCP adapter itself already
negotiated v2 and passed its complete stdio probe.

This was a **test-harness defect only**. No product repair was selected. Attempt-02
used the same candidate bytes and isolated fixture, added the explicit v2 contract
header, and passed the complete Local Service/MCP matrix with `failed_checks=[]`.
Evidence: `C:\twmarket_temp\v1.5.1-rma-20261031\rma-4\attempt-02-native-local-service-mcp\`.
Status: **CLOSED_PASS**. Release blocker: **No**.

### RMA-D013 — Result V3 Typed Evidence Can Misreport Full Success

RMA-6D attempt-01 executed `trading_status_context` for `TPEX:5227` through the real production transport path in a fresh network-enabled Sandbox. All three governed TPEx source acquisitions (`tpex_trading_warning_information`, `tpex_disposal_information`, `tpex_cmode`) raised `URLError`; each component evidence object reported `source_failed`, aggregate covered status types were empty, and source-attempt governance recorded failed outcomes. Despite this, the canonical Result V3 and AI handoff reported `full_success`.

Static localization proves the mechanism in `scripts/m8r_05c/result_builder.py`. In the V3 typed-capability coverage branch, `is_provided` is set solely from the presence of a non-null typed evidence object. The branch does not require a usable typed evidence status. Therefore a `source_failed` typed object can be counted in `provided_needs`, suppress required-evidence failure, and allow `_compute_result_status()` to return `full_success`.

This contradicts the builder's own deterministic status contract: `full_success` means all required evidence is present with no failures. Classification: **product Result-integrity BLOCKER**. Status: **OPEN / ROOT_CAUSE_PROVEN**. Release blocker: **Yes**. Evidence root: `C:\twmarket_temp\v1.5.1-rma-20261031\rma-6\6D-live-execution\attempt-01\`; forensic adjudication: `POST_LIVE_FORENSIC_ADJUDICATION_2026-11-01.md`.

No product repair is authorized by this record. Any repair must preserve valid `available`, `partial`, `no_evidence_in_covered_scope`, and other governed typed statuses while ensuring `source_failed` / unusable required evidence cannot become `provided_needs` or `full_success`. RMA-8 must later revalidate Result/Audit truthfulness after repair.

### RMA-D013 — Result V3 Typed Evidence False Success

RMA-6D attempt-01 reproduced the defect on live TPEx `trading_status_context`: all three governed source components were `source_failed`, covered status types were empty, yet Result V3 and AI handoff reported `full_success`. Root cause was the V3 coverage branch in `scripts/m8r_05c/result_builder.py`, which treated any non-null typed evidence object as satisfying the requested need regardless of failure status.

The authorized bounded repair adds explicit typed-evidence usability semantics. Failure-like states (`source_failed`, `binding_failed`, `unavailable`, `unsupported`, `insufficient`, or unknown) no longer satisfy required coverage merely because an artifact exists; governed usable states such as `available`, `partial`, `no_evidence_in_covered_scope`, and contract-valid equivalents remain eligible.

Validation evidence is retained under `C:\twmarket_temp\v1.5.1-rma-20261031\rma-6\6F-d013-bounded-repair\`. The directly affected V3/Phase-H suite passed 118/118 and the cross-version V2/legacy suite passed 26/26. The diagnostic Native candidate ZIP SHA-256 is `8de69ad1be8aaa4fe2fd63df2abccf0e457facd69c091fc5c40a0d6c123d3f17`; it is explicitly noncanonical and not release-eligible.

Fresh network-enabled targeted Sandbox retest reproduced the same source-failure condition: all three TPEx components remained `source_failed`. With the repair, `provided_needs=[]`, `missing_needs=[trading_status_context]`, canonical Result became `failed`, the handoff no longer claimed full success, Result/Audit/Handoff integrity checks passed, and JIT cleanup returned `PASS_RESTORED`. Status: **CLOSED_PASS**. No TLS, source acquisition, routing, MCP contract, version, commit, tag, or release behavior was changed.

### RMA-D020 — Advanced Unified Request JSON obscures the primary operator path

Current state: **REPRODUCED / MAJOR / PENDING ADJUDICATION**. Release blocker: **Pending adjudication**.

RMA-11 owner-driven operator acceptance reached the normal Workbench without developer instructions. The Owner successfully created a watchlist and accepted the separate mutation-confirmation boundary as mildly inconvenient but acceptable. The next major comprehension failure occurred at the large `Advanced Unified Request JSON` panel: the Owner described it as being like a password lock and did not know what should be entered.

Static inspection confirms the intended product design is different from the observed operator interpretation. `UnifiedMarketEvidenceWorkbench.html` labels the upper `Persistent Watchlist & Request Builder` as the primary path, while `watchlist-workbench.js::composeRequest()` builds the governed request from selected targets/evidence needs and automatically populates `request-textarea` after `Compose Frozen Request`. Manual JSON entry is therefore an advanced override/import path, not a required normal step.

The defect is UX discoverability / information hierarchy: technical JSON remains visually prominent enough to be mistaken for a mandatory gate. This conflicts with the RMA-11 acceptance goal that normal operators complete the primary workflow without needing implementation-level request internals, while technical detail remains available without becoming the main workflow. No code repair is authorized by this registration. Exact repair scope and release disposition require a separate Owner decision after the remaining RMA-11 operator flow is completed.

### RMA-D021 — Workbench Builder / Selection Schema Drift

Current state: **BLOCKER / ROOT_CAUSE_PROVEN**. Release blocker: **Yes**.

RMA-11 owner-driven acceptance followed the intended primary Builder path and pressed `Compose Frozen Request`. The live product returned `WATCHLIST_SELECTION_SCHEMA_INVALID`, naming `watchlist_evidence_selection_request.v3.schema.json`; no Unified Request was composed.

Root cause is a contract-version drift. The live `/api/unified/capabilities` authority currently exposes 14 capability IDs, and `schemas/unified_market_evidence_request.v3.schema.json` accepts the same 14. The Workbench renders the live authority dynamically. However, `docs/contracts/schemas/watchlist_evidence_selection_request.v3.schema.json` still limits `data_needs` to `maxItems: 11` and omits `market_state_context`, `index_futures_context`, and `cash_institutional_flow_context` from its enum.

The v3 capability catalog bounds are not the blocker (`default_operation_limit=30`, `hard_operation_limit=100`). Therefore a normal operator selecting any of those three currently advertised capabilities can construct a UI-valid selection that the stale selection schema deterministically rejects.

No product repair is authorized by this record. A bounded repair should align the v3 watchlist-selection schema with the already-authoritative 14-capability Unified Request v3 contract and add regression coverage proving the Builder can compose requests containing each newly admitted capability and the full advertised set without weakening existing validation bounds.

### RMA-11 owner-retest disposition update — 2026-11-02

**RMA-D021 — CLOSED_PASS. Release blocker: No.** The authorized bounded repair aligned the v3 watchlist-selection schema with the already-authoritative 14-capability Unified Request v3 contract. Targeted regression, composer/integration coverage, diagnostic Native package validation, and Owner E2E all passed. The Owner successfully composed a Unified Request v3 containing all 14 advertised capabilities; the prior `WATCHLIST_SELECTION_SCHEMA_INVALID` did not recur. No release authority is implied.

**RMA-D020 — OPEN / OWNER RETEST FAILED. Release blocker: Pending RMA-11 adjudication.** The bounded UX repair reduced some JSON framing, but Owner retest still exposed a large raw generated Unified Request JSON payload in the normal post-Compose operator path. This does not yet satisfy the intended normal-operator information hierarchy; further repair is not authorized by this update.

**RMA-D023 — CLOSED_PASS. Release blocker: No.** The blocked-preview recovery UX now explains that the preview cannot be authorized, identifies each blocking capability in operator-readable language, states the available recovery choices, and provides `Review Evidence Needs`. Owner E2E used that guidance to deselect blocked items and successfully reached `Preview status: ready_for_confirmation` without external procedural instruction.

### RMA-D024 — Authorization recovery UX exposes internal reason code without operator recovery path

Current state: **REPRODUCED / MAJOR / PENDING ADJUDICATION**. Release blocker: **Pending RMA-11 adjudication**.

After the D023 recovery path succeeded, Owner E2E reached `Preview status: ready_for_confirmation`. The authorization surface then displayed `Authorization unavailable: i3_source_date_binding_missing`. The fail-closed authorization behavior itself is not being challenged here. The UX defect candidate is that the operator-facing surface exposes an internal reason code without explaining what it means, whether the operator can resolve it, or where to go next. No product repair is authorized by this registration.

### RMA-11 resume adjudication update — 2026-11-03

**RMA-D020 — OPEN / ROOT CAUSE CLARIFIED.** The previous Owner retest did not prove that the optional `Advanced: View or edit Unified Request JSON` disclosure remained open; current HTML correctly keeps that textarea inside a collapsed `<details>` element. The large raw JSON observed in the primary Builder path is instead `selection-provenance-view`, populated unconditionally by `watchlist-workbench.js` immediately after composition. The acceptance defect therefore remains valid as an information-hierarchy failure: implementation/provenance payload is still exposed in the normal operator path. Release disposition remains pending; no further repair is authorized by this update.

**RMA-D024 — BLOCKER / ROOT_CAUSE_PROVEN. Release blocker: Yes.** Owner E2E reached `Preview status: ready_for_confirmation` with executable TWSE `cash_institutional_flow_context`, then Workbench authorization failed with `i3_source_date_binding_missing`. Static localization shows `build_mode_b2_authorization()` rebuilds the B1 plan and passes it directly to `_materialize_execution_ticket()` / `build_execution_authorization()` without invoking the existing canonical pre-authorization I3 governed source-date resolver/binder. The authorization layer explicitly rejects TWSE I3 plans lacking `resolved_source_trade_date` + `source_date_binding`. The existing canonical binding capability is implemented in `scripts/phase_i_i3_execution_date.py` and used by `scripts/phase_i_i3_execution_pipeline.py`, but is absent from the Workbench/Mode-B2 path. Existing watchlist/B2 acceptance coverage exercises `current_observation`, so it does not cover this integration boundary.

D024 is therefore not merely an operator-message defect. The current product can truthfully preview the selected operation as confirmable but cannot materialize authorization for it through the normal Workbench B2 path. Any repair must preserve fail-closed date authority, must not invent calendar/weekday fallbacks, and must either integrate the existing governed date-binding authority before authorization or truthfully prevent the operation from being presented as authorizable. Separate Owner repair authorization is required.

### RMA-11 bounded repair authorization — 2026-11-03

**RMA-D020 residual — FIX_AUTHORIZED.** Authorized scope is limited to the remaining primary-path information-hierarchy defect: `selection-provenance-view` must no longer expose raw provenance JSON by default. Provenance content and integrity semantics must remain unchanged and available through an explicit advanced disclosure. Direct UX/state regression coverage is required.

**RMA-D024 — FIX_AUTHORIZED.** Authorized scope is limited to the Workbench/Mode-B2 pre-authorization integration gap for TWSE `cash_institutional_flow_context`, reusing the existing canonical governed source-date resolver/binder. The repair must preserve fail-closed date authority and may not invent calendar dates, weekday fallbacks, or manual defaults. Regression coverage must prove a TWSE I3 request cannot be authorized without governed date authority and can be authorized only after canonical binding succeeds.

No version mutation, commit, push, tag, release, Stable mutation, Phase M work, or unrelated backend change is authorized.
### RMA-D020 residual / RMA-D024 bounded repair candidate — 2026-11-03

**RMA-D020 residual — FIXED_PENDING_OWNER_RETEST.** `selection-provenance-view` is now preserved behind the default-collapsed `Advanced: View selection provenance` disclosure. Generated request JSON remains separately default-collapsed. Provenance bytes and semantics are unchanged.

**RMA-D024 — FIXED_PENDING_OWNER_RETEST.** Generic Workbench B1 now projects `authorization_readiness`. An executable TWSE `cash_institutional_flow_context` plan without an already-canonical `resolved_source_trade_date` + matching `source_date_binding` is reported as blocked with `i3_governed_source_date_authority_required`; Workbench disables Authorize and gives an operator-readable recovery path. No date is guessed and no historical acceptance authority is promoted. B2 independently enforces the same prerequisite before ticket materialization. Existing specialized I3 canonical resolver/binder remains unchanged.

Validation: affected suites passed 60/60 with 1 skipped, composer/readiness follow-up passed 23/23, final UI/B2/API gate passed 52/52 with 1 skipped, JS syntax/Python compile/git diff --check passed. Diagnostic Native ZIP SHA-256: `61049661a0ed3502079a402085a9f3d196357714bad9e95a00b4dfd5b8d0ad7c`; package integrity PASS; `release_eligible=false`. Closure requires Owner E2E.
### RMA-D025 — Normal Workbench validation can surface resource concurrency gate

Current state: **REPRODUCED / PENDING ADJUDICATION**. Release blocker: **Pending RMA-11 adjudication**.

RMA-11 Owner E2E successfully used the repaired D024 recovery path, returned to Evidence Needs, recomposed a request, and then pressed `Validate`. The Workbench returned `resource_concurrency_limit` / `{"error":"resource_concurrency_limit"}` instead of a validation result.

The underlying Local Service resource boundary is intentional: `server/resource_boundaries.py` enforces a process-local fail-fast ceiling of one in-flight resource-intensive or bounded-offline-planning request. The defect question is whether the normal single-operator Workbench flow is causing an unintended overlap, and independently whether a transient busy condition is being exposed as an internal reason code with no operator recovery guidance.

No repair is authorized by this registration. Before any product change, reproduce whether a retry after the prior request has fully completed succeeds, inspect the request-classification/admission path, and determine whether this is a frontend overlap defect, a gate-lifecycle defect, or only an operator-message/retry UX defect.

### RMA-11 Owner retest update — 2026-11-03 (D020/D024/D025)

**RMA-D020 residual — CLOSED_PASS. Release blocker: No.** Owner E2E confirmed the normal post-Compose path now shows only the generated-request summary and `Validate`; both `Advanced: View selection provenance` and `Advanced: View or edit Unified Request JSON (optional)` remain default-collapsed. Raw provenance/request payloads remain available without occupying the primary operator path.

**RMA-D024 — OWNER RECOVERY INTENT PASS / FULL E2E PENDING.** The repaired Preview correctly states that planning is valid but authorization is unavailable, explains that TWSE institutional flow requires current governed source-date authority, states that Workbench will not guess a date, and provides `Review Evidence Needs`. The Owner independently chose that recovery action and returned to the Builder without procedural instruction. Full closure remains pending recomposition/validation/preview after recovery.

**RMA-D025 — REPRODUCED / TRANSIENT_CONCURRENCY UX DEFECT / PENDING ADJUDICATION.** During the recovered D024 path, the next `Validate` returned `resource_concurrency_limit`. A subsequent direct probe to the same running Sandbox `/api/unified/validate-request` returned HTTP 200, proving the process-local gate was not stuck. Current evidence therefore supports a short-lived request overlap/race rather than persistent gate leakage. Product semantics remain fail-fast by design; operator handling of this transient busy state is still inadequate because the Workbench exposes the internal reason code without retry guidance. No repair is authorized by this update.

### RMA-11 Owner E2E update — 2026-11-03

**RMA-D020 residual — CLOSED_PASS. Release blocker: No.** Owner E2E confirmed both implementation-heavy surfaces are now outside the normal path: `selection-provenance-view` is behind the default-collapsed `Advanced: View selection provenance` disclosure, and the Unified Request JSON editor is behind `Advanced: View or edit Unified Request JSON (optional)`. The primary operator path presents `Generated request ready` and `Validate` without requiring JSON/provenance inspection.

**RMA-D024 — CLOSED_PASS. Release blocker: No.** Owner E2E first reached the new authorization-readiness recovery for TWSE institutional flow, independently chose `Review Evidence Needs`, adjusted the selection without external procedural instruction, recomposed and revalidated, and reached a new Preview with `status=ready_for_confirmation`, `coverage=full_possible`, six planned operations, and enabled `Authorize`. The product did not guess a source date and did not expose `i3_source_date_binding_missing` as the recovery surface.

**RMA-D025 — REPRODUCED / TRANSIENT / NON-BLOCKING OBSERVATION.** During the D024 recovery retest, one `Validate` attempt received `resource_concurrency_limit`. A subsequent direct probe against the same running Sandbox and `/api/unified/validate-request` returned HTTP 200, and the Owner immediately retried the normal flow successfully through `ready_for_confirmation`. This is currently classified as transient overlap / operator-message UX debt, not a persistent resource-gate failure. No repair is authorized by this record.

### RMA-D026 — Execute Once confirmation UX / network-confirmation state mismatch

Current state: **REPRODUCED / BLOCKER / PENDING REPAIR AUTHORIZATION**. Release blocker: **Yes**.

RMA-11 Owner E2E successfully reached a valid single-use authorization whose current control-package preflight has `network_required=true` and `network_authorized=true`. The Workbench nevertheless presented `I explicitly confirm network execution` as non-interactive/disabled while leaving `Execute Once` available. Pressing `Execute Once` then exposed an unexplained browser prompt, `Operator confirmation reference`, which the Owner reasonably interpreted as an unknown passphrase.

Static localization shows the execution API contract requires a non-empty `operator_confirmation_reference` for audit provenance, and the Workbench currently gathers it through a raw `window.prompt()` with no operator semantics. The backend remains fail-closed: because the accepted preflight requires network, an execution request without `confirm_network_execution=true` is rejected with `network_execution_confirmation_required` before authorization claim/dispatch. No market execution occurred in this finding.

Repair must preserve explicit human execution confirmation, network confirmation, single-use authorization, audit provenance, and fail-closed dispatch. It must not weaken or auto-confirm network authority. Separate Owner authorization is required before any product-code change.

### RMA-D026 bounded repair authorization — 2026-11-03

**RMA-D026 — FIX_AUTHORIZED. Release blocker: Yes until Owner E2E closure.** Authorized scope is limited to Workbench execution-confirmation UI/state, truthful projection of `network_required`, operator-readable presentation of the required audit `operator_confirmation_reference`, and direct regression coverage. Backend execution/claim contracts, single-use semantics, explicit network confirmation, authorization TTL, and Stable remain unchanged. No commit, push, tag, release, version mutation, or unrelated repair is authorized.

### RMA-D026 bounded repair candidate — 2026-11-03

**RMA-D026 — FIXED_PENDING_OWNER_RETEST.** Workbench now presents the required `operator_confirmation_reference` as an inline, editable **Audit reference (not a password)** with a bounded auto-filled value. `Execute Once` remains disabled after authorization until the audit reference is valid and, when `network_required=true`, the operator explicitly checks network execution confirmation. The backend execution/claim contract is unchanged. Targeted D026 tests passed 3/3; affected Workbench/B2/API suite passed 45/45 with 1 skipped; JS syntax and `git diff --check` passed. Diagnostic Native ZIP SHA-256: `274283fb4879ccf5ed628ca5157fa743e2b7eee632df3473e02ca0ef39d027a5`; `release_eligible=false`. Closure requires Owner E2E.

### RMA-D026 Owner E2E closure — 2026-11-03

**RMA-D026 — CLOSED_PASS. Release blocker: No.** Fresh Windows Sandbox Owner E2E on diagnostic candidate SHA-256 `274283fb4879ccf5ed628ca5157fa743e2b7eee632df3473e02ca0ef39d027a5` confirmed all required repaired behaviors: network confirmation was interactive, the inline `Audit reference (not a password)` was visible/editable/pre-populated, and `Execute Once` was gated by the confirmation state. Owner then completed the one-shot execution; Workbench reported `EXECUTION ATTEMPTED — succeeded; authorization consumed = YES.` Backend execution/claim semantics, single-use authorization, explicit network confirmation, authorization TTL, Stable, and release state remain unchanged. Diagnostic candidate remains noncanonical and `release_eligible=false`.

### RMA-D027 — Mode C result / AI handoff semantic inconsistency — 2026-11-03

**Current state: REPRODUCED / BLOCKER / PENDING REPAIR AUTHORIZATION. Release blocker: Yes.** Mode C successfully exported AI-ready Markdown, Canonical Result JSON, and Audit JSON for request `m8r10-workbench-61ffbae7-5c8c-4733-963d-b6ad54d51318`; execution receipt is 6/6 succeeded and all audit integrity verifications are true. However, the canonical result contains `recent_performance.coverage_status=complete` with a 5-trading-day baseline `recent_return_pct=-4.375`, while `derived_metrics` simultaneously reports `recent_return_pct` as `unavailable` / `required_fields_absent_in_artifact`. The AI-ready Markdown also renders Recent Performance twice, first as `unknown` and later as `complete`.

Root-cause localization for the derived-metric half is proven: `scripts/m8r_05c/derived_metrics.py` still expects legacy `period_return_pct` or `close_start`/`close_end` fields and does not consume the current `recent_performance_evidence.v1` `baselines[].recent_return_pct` shape. Duplicate Markdown rendering is reproduced but not yet fully localized. This is a projector/handoff truthfulness defect, not an execution or audit-integrity failure. No product repair is authorized by this registration.
### RMA-D027 bounded repair authorization — 2026-11-03

**RMA-D027 — FIX_AUTHORIZED. Release blocker: Yes until bounded repair and retest closure.** Authorized scope is limited to Mode C result-projector / AI-ready Markdown semantic consistency and direct regression coverage: adapt derived recent-return projection to the current `recent_performance_evidence.v1` `baselines[].recent_return_pct` shape, remove duplicate/contradictory Recent Performance rendering, and preserve existing execution/audit truth. Launcher, authorization, execution, audit chain, Stable, commit/push/tag/release/version state, and unrelated product behavior are out of scope.

### RMA-D027 bounded repair closure — 2026-11-03

**RMA-D027 — CLOSED_PASS. Release blocker: No.** `recent_performance_evidence.v1` baseline projection now consumes governed `baselines[].recent_return_pct`, and V3 AI-ready Markdown renders Recent Performance exactly once. The D027 diagnostic candidate reprojected the same previously executed 6/6 governed predecessor package locally with `external_market_network_executed=false`; the repaired result reports `recent_return_pct=-4.375`, `status=available`, `window=5td`. Request/result/audit identities remain consistent, receipt remains 6 succeeded / 0 failed, and all audit integrity verification flags remain true. Targeted regression passed; affected non-historical suite passed 127/127 with 6 deselected; package integrity and `git diff --check` passed. Diagnostic ZIP SHA-256: `5b115a255844f816dbe4239177778c70c21ce980596e99bddc30508618de4bfa`; candidate remains noncanonical and `release_eligible=false`.
