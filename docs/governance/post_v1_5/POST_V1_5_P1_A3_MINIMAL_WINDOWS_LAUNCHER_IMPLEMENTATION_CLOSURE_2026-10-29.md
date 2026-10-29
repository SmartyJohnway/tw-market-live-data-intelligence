# Post-v1.5 P1-A3 — Minimal Windows Launcher Implementation Closure

Date: 2026-10-29

Status: **CLOSURE_CANDIDATE_COMPLETE — INDEPENDENT_REVIEW_PENDING**

## Authority and scope

P1-A3 implements the Owner-frozen P1-A1 First-run / Setup UX Contract and P1-A2 Daily Main Launcher / Runtime Control UX Contract. It does not reopen Phase L, redefine v1.5.0, authorize P2–P5, or start Phase M.

Baseline development HEAD for this tranche is `430d320784d5249508c37bbd6e8272732bf63ee8`. The stable v1.5.0 release remains frozen at source commit `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`, tree `d44f66dc154c21326ac8b105d2f15fd793f6071b`.

## Implementation result

P1-A3 adds a thin Windows operator facade over existing canonical bootstrap and lifecycle authority:

```text
Launch-TW-Market.cmd
  -> launcher/tw-market-launcher.ps1
  -> existing bootstrap.ps1 / tw-market.cmd JSON lifecycle
```

No new service manager, market-data executor, Security Master lifecycle, MCP daemon, scheduler, polling loop, or release authority is introduced.

## Implementation artifacts

The current candidate implementation is:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `packaging_native/launchers/Launch-TW-Market.cmd` | 238 | `8cdfad2f8e86e9c91b9aac89216b8e5bd817dbf3476407de2e8269fdcb5914ca` |
| `packaging_native/launchers/tw-market-launcher.ps1` | 26052 | `04be1dfd090b6509584ff41d0c247a9ccdbaf165d4098c5c347ddccd1f0b8389` |
| `packaging_native/README-PACKAGE.md` | 2354 | `fdf0851d7bf327ea5d41009accb60dc7bc4d0d18dd5e38c8ecd0e2e72d489fb4` |
| `packaging_native/resource-policy.json` | 77230 | `91415ef107721904ce5d4824c62359f98c980dbb5852d51ab1c8edc4f67bdcdb` |
| `tests/unit/test_p1_a3_windows_launcher.py` | 5880 | `4ad3a4d3cc23a0ae08c2f79509202a6fe7926f6f547b7a7b517aacb718aaa637` |

The launcher exposes GUI operation and a deterministic headless action surface for acceptance. Both paths reuse the same internal functions and canonical bootstrap/lifecycle commands.

The package resource policy adds only the human launcher entry and its PowerShell facade. Existing `tw-market.cmd`, `tw-market-security-master.cmd`, and `tw-market-mcp.cmd` remain canonical specialized entry points.

## Deterministic validation

The exact current working tree passed the focused launcher/package/lifecycle regression set:

```text
97 passed in 57.91s
```

The following validators also passed after the current launcher byte identity was established:

```text
git -c core.whitespace=cr-at-eol diff --check       PASS
validate_v1_front_door                              PASS
validate_v1_public_contracts                        PASS
validate_runtime_skill_guide_sync                   PASS
validate_portable_catalog_sync                      PASS
validate_product_version_consistency                PASS
validate_l5_extension_publication_conformance       PASS
```

The public contract remained product version `1.5.0` with exactly six MCP tools. Catalog and portable Skill synchronization remained deep-equality PASS.

## Windows Sandbox acceptance chronology

### R1 — harness prerequisite failure

R1 correctly proved the missing-Python fail-closed state, but the test harness then attempted a per-user CPython install while executing as `SYSTEM`. The Python installer returned `PYTHON_INSTALL_EXIT_3`; Launcher lifecycle acceptance did not proceed. The R1 failure is preserved as historical evidence and is not reclassified as a product defect.

### R2 — functional PASS before byte-identity drift was discovered

R2 corrected only the harness prerequisite provisioning (`InstallAllUsers=1`) and completed the intended Sandbox E2E with PASS. The tested launcher had SHA-256 `56153c64c1a9151661cc2103e8ebc8af7d3a60d5564973f7ee3fcbc75bc82624`.

During closure preparation, the current working-tree launcher was found to have a later modified identity (`04be1dfd...`). R2 therefore remains useful functional evidence but is not the final exact-current acceptance authority.

### R3 — exact-current recertification

R3 rebuilt an acceptance-only overlay using the current working-tree launcher and re-ran the complete fresh Windows Sandbox E2E. The overlay is explicitly classified `NOT_RELEASE_ARTIFACT`; it does not redefine or republish v1.5.0.

R3 working-tree snapshot SHA-256: `94ecd54444d911e2abb0154590b6063cc370c57260b5d55925410c2d13fd921e`.
R3 launcher SHA-256: `04be1dfd090b6509584ff41d0c247a9ccdbaf165d4098c5c347ddccd1f0b8389`.

## R3 observed acceptance

Fresh Sandbox R3 observed:

- missing Python -> `PREREQUISITE_BLOCKED` / `CPYTHON_3_13_X64_REQUIRED`, with no package runtime or HOME created;
- official CPython 3.13 x64 prerequisite accepted by the harness;
- external Sandbox network adapters disabled before Launcher lifecycle actions;
- Setup -> `SETUP_COMPLETE` with installation `READY` and Security Master `NOT_INITIALIZED`;
- repeated Setup -> `SETUP_COMPLETE` with the same installation ID;
- Start -> `START_COMPLETE` and normalized state `RUNNING_READY`;
- Workbench -> validated `http://127.0.0.1:8000/workbench/`, HTTP 200;
- Doctor -> `DOCTOR_COMPLETE`, canonical status `WARN`, 15 checks;
- Stop -> `STOP_COMPLETE`;
- final state -> `STOPPED`, service not alive;
- wrong Python remained blocked;
- tampered package did not create a runtime;
- stale runtime probe was preserved rather than auto-deleted;
- existing business-state sentinel was preserved.

The `WARN` diagnosis is compatible with the accepted fresh-install Security Master `NOT_INITIALIZED` state and does not convert that state into product corruption.

## Sandbox/JIT cleanup

R3 orchestration completed with:

```text
guest_exec_exit       0
guest_result_found     true
orchestrator status    PASS
JIT status             PASS_RESTORED
JIT cleanup_action     RESTORED_BEFORE
post_running_sandboxes 0
post_active_marker     false
```

The Sandbox-JIT temporary `SeServiceLogonRight` mutation was restored to its pre-run state. No active Sandbox or JIT marker remained after acceptance.

## Durable acceptance evidence

Core evidence is preserved under `docs/acceptance_runs/post_v1_5/p1_a3/`.

Final exact-current R3 authority:

- `P1_A3_ACCEPTANCE_OVERLAY_R3_PROVENANCE_2026-10-29.json` — SHA-256 `1d760eab6b09c52515641e65bf8bf1112590d154c0853389072d13b954594da5`;
- `P1_A3_SANDBOX_R3_GUEST_RESULT_PASS_2026-10-29.json` — SHA-256 `e0c010431113b3b4134cd4ff3b5ee40e5a7383b9141ff0b80ccc1fa3cc2d9391`;
- `P1_A3_SANDBOX_R3_ORCHESTRATOR_PASS_2026-10-29.json` — SHA-256 `6baf8ac2633d0c2c9552ccebb894d151355aa719b786560619f385a4c77ab3ca`;
- `P1_A3_SANDBOX_R3_JIT_RESULT_PASS_RESTORED_2026-10-29.json` — SHA-256 `48149ff2f86be9e1092fda235493f1a5f4b7b68e8a929b48b3e11a71477c5e77`.

Earlier R1/R2 evidence is preserved alongside R3 rather than overwritten. R1 records the harness prerequisite failure; R2 records the pre-drift functional PASS. Neither supersedes R3 exact-current acceptance.

## Boundary preservation

P1-A3 preserves the frozen A1/A2 boundaries:

- external CPython 3.13 x64 remains a prerequisite; the Launcher does not install or download Python;
- Setup performs no automatic market/provider acquisition and does not initialize Security Master;
- Setup does not automatically start Local Runtime or open Workbench;
- no automatic runtime/business-state deletion, repair, adoption, or overwrite;
- Start/Stop/Status/Doctor reuse existing lifecycle JSON authority;
- Workbench opening is explicit and loopback-only;
- Security Master remains status-only in P1;
- MCP remains readiness-only; no persistent MCP daemon is introduced;
- no timer polling, tray daemon, scheduler, updater, service install, or hidden background agent is introduced.

The protected Catalog V3 summary debt remains deferred and untouched.

## Release and roadmap disposition

The acceptance overlay is test-only and explicitly has `release_authority=false`. P1-A3 does not mutate the v1.5.0 tag, release assets, MCP Registry metadata, Docker registry state, Catalog/Route machine authority, or Phase M authority.

P2–P5 remain NOT_STARTED / not authorized by this closure. Phase M remains **NOT_AUTHORIZED**.

## Review gate

Implementation and exact-current Sandbox acceptance are complete. Independent review is the remaining P1-A3 closure gate before commit authorization.

```text
P1_A3_IMPLEMENTATION = CANDIDATE_COMPLETE
P1_A3_EXACT_CURRENT_SANDBOX_ACCEPTANCE = PASS_R3
P1_A3_CLOSURE = CANDIDATE_COMPLETE
INDEPENDENT_REVIEW = PENDING
COMMIT = NOT_PERFORMED
PUSH = NOT_PERFORMED
P1_A4 = NOT_STARTED
P2 = NOT_STARTED
PHASE_M = NOT_AUTHORIZED
```
