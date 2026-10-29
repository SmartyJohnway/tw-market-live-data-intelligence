# Post-v1.5 P1-A3-R2 — Bounded Correction and R5 Recertification

Date: 2026-10-29

Status: **R2_CORRECTION_COMPLETE — R5_PASS — INDEPENDENT_RE_REVIEW_PENDING**

Baseline development HEAD: `430d320784d5249508c37bbd6e8272732bf63ee8`.
Stable v1.5.0 release authority remains frozen at source commit `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`.

P1-A3-R2 is limited to the two defects preserved by the P1-A3-R1 independent re-review disposition. It does not authorize P2–P5, release mutation, Registry mutation, or Phase M.

## Bounded corrections

1. `Get-LauncherSnapshot` now accepts `-PreserveTechnicalDetails`. When used for a post-action/UI refresh, canonical status truth is refreshed without overwriting the action result already stored for Technical Details.
2. GUI render forwards its `PreserveTechnicalDetails` intent into a newly acquired snapshot instead of protecting only the final render assignment.
3. Start and Stop now perform the required single post-action status refresh before testing whether the lifecycle payload parsed successfully. Malformed/non-JSON Start/Stop responses therefore return failure while caching the actual post-command state rather than the pre-action state.
4. No new polling, service manager, downloader, network acquisition, MCP surface, P2 behavior, or release authority was introduced.

Current R2 launcher SHA-256: `96f9cbaeaf61d7292aa5ff0e783e32e8d17689056ce8dfdbfa60eedf1e299aa5`.
Current CMD SHA-256: `8cdfad2f8e86e9c91b9aac89216b8e5bd817dbf3476407de2e8269fdcb5914ca`.
## Executable regression coverage

The launcher unit file now contains 19 tests. New executable probes verify:

- Setup failure followed by a status refresh preserves the serialized `SETUP_BLOCKED` action result in Technical Details.
- malformed/non-JSON Start still performs pre-action + exactly one post-action status observation, returns `START_FAILED`, and caches the actual post-command state;
- malformed/non-JSON Stop does the same and returns `STOP_FAILED`.

The full P1-A3/lifecycle/package deterministic set is now **97 passed**. PowerShell parser validation, CR-at-EOL-aware `git diff --check`, front-door, public-contract, runtime-skill-guide sync, Portable Catalog sync, product-version consistency, and L5 publication-conformance validators all pass.

## R5 exact-current acceptance identity

R5 acceptance overlay classification remains `NOT_RELEASE_ARTIFACT` over frozen v1.5.0.

- working-tree snapshot SHA-256: `8c25fc1ee788b8221057f618ed4df9aac632a504e9bd69a4a2f3abd7dd9d8f7b`
- launcher SHA-256: `96f9cbaeaf61d7292aa5ff0e783e32e8d17689056ce8dfdbfa60eedf1e299aa5`
- acceptance provenance SHA-256: `df03c5159851ab0bc63f983868d85151302e9ba5aeee90189b021dab1f0728fa`

R5 exact-current Sandbox recertification passed on the current launcher digest. The combined run independently self-computed source/executed launcher and CMD digests, blocked missing/wrong Python and tampered/stale cases, completed Setup and repeated Setup, preserved existing business state, reached `RUNNING_READY`, returned Workbench HTTP 200, completed Doctor, stopped cleanly, and finished `STOPPED`. Its interactive fresh-install GUI probe also passed on the same launcher digest.

A separate interactive R5 failure-path probe then warmed the package runtime, switched to an existing-state transfer-conflict root, clicked **Set Up TW-Market**, observed the Setup failure modal, opened **Technical Details**, and verified the displayed action JSON remained `SETUP_BLOCKED / EXISTING_STATE_REQUIRES_EXPLICIT_TRANSFER`. The business sentinel remained unchanged and the GUI process remained alive. Both successful R5 Sandbox runs finished with JIT `PASS_RESTORED`, zero running sandboxes, and no active marker.

Historical R4 evidence and the earlier R5 harness-only failures remain preserved and are not rewritten as R5 authority. The harness-only failures were an `ExistingLogin` timing failure and two probe implementation/readout issues; none required a product-code change.

```text
P1_A3_R2_CORRECTION = COMPLETE
P1_A3_R5_HEADLESS_ACCEPTANCE = PASS
P1_A3_R5_GUI_ACCEPTANCE = PASS
P1_A3_R5_GUI_FAILURE_DETAILS = PASS
INDEPENDENT_RE_REVIEW = PENDING
OWNER_COMMIT_GATE = NOT_REACHED
COMMIT = NOT_PERFORMED
PUSH = NOT_PERFORMED
P2 = NOT_STARTED
PHASE_M = NOT_AUTHORIZED
```


## Preserved R5 evidence

Successful repository evidence under `docs/acceptance_runs/post_v1_5/p1_a3/`:

- `P1_A3_ACCEPTANCE_OVERLAY_R5_PROVENANCE_2026-10-29.json`
- `P1_A3_SANDBOX_R5_GUEST_RESULT_PASS_2026-10-29.json`
- `P1_A3_SANDBOX_R5_GUI_RESULT_PASS_2026-10-29.json`
- `P1_A3_SANDBOX_R5_ORCHESTRATOR_PASS_2026-10-29.json`
- `P1_A3_SANDBOX_R5_JIT_RESULT_PASS_RESTORED_2026-10-29.json`
- `P1_A3_SANDBOX_R5_GUI_FAILURE_DETAILS_RESULT_PASS_2026-10-29.json`
- `P1_A3_SANDBOX_R5_GUI_FAILURE_DETAILS_ORCHESTRATOR_PASS_2026-10-29.json`
- `P1_A3_SANDBOX_R5_GUI_FAILURE_DETAILS_JIT_PASS_RESTORED_2026-10-29.json`

The successful combined run completed in 846.939 seconds; the successful targeted GUI failure-details run completed in 136.72 seconds. Their orchestrators each recorded `post_running_sandboxes = 0` and `post_active_marker = false`.
