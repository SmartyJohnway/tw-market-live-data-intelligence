# Post-v1.5 P1-A3-R1 — Bounded Correction and R4 Recertification

Date: 2026-10-29

Status: **R1_CORRECTION_COMPLETE — R4_PASS — INDEPENDENT_RE_REVIEW_PENDING**

Baseline development HEAD: `430d320784d5249508c37bbd6e8272732bf63ee8`.
Stable v1.5.0 release authority remains frozen at source commit `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`.

P1-A3-R1 is a bounded correction of the five findings from the first P1-A3 independent review. It does not authorize P2–P5, release mutation, Registry mutation, or Phase M.

## Corrections implemented for independent-review findings

1. Fresh-install GUI StrictMode safety: optional snapshot `data` is now guarded before access; fresh Sandbox GUI acceptance renders successfully.
2. Technical Details preservation: action results are retained across post-action render instead of being overwritten by a status snapshot.
3. Setup final verification: only explicit `STOPPED` is accepted as `SETUP_COMPLETE`; unexpected final states fail closed as `SETUP_BLOCKED`.
4. Start/Stop status refresh: the single post-action snapshot is reused by GUI render; the render no longer performs a second lifecycle status refresh.
5. Exact-artifact / GUI evidence: R4 guest records its own executed launcher digest, and a separate fresh-Sandbox GUI acceptance verifies the actual WinForms first-run surface.

Current corrected launcher:
- path: `packaging_native/launchers/tw-market-launcher.ps1`
- bytes: `27973`
- SHA-256: `7329e666c309f9d9768764feb492abff5feb6cd7d78f680adc335fbf847e2907`

## Deterministic revalidation

- PowerShell parser: PASS.
- P1-A3 + lifecycle/package regression set: `94 passed`.
- `git diff --check`: PASS.
- Front-door validator: PASS.
- Public-contract validator: PASS (`product_version=1.5.0`, `tool_count=6`).
- Runtime skill guide sync: PASS.
- Portable Catalog sync: PASS.
- Product-version consistency: PASS (`1.5.0`).
- Publication conformance: PASS; no network, runtime discovery, or writes.

## R4 exact-current Sandbox acceptance

Headless R4 guest acceptance is PASS. The guest independently verified the source and executed launcher SHA-256 against acceptance provenance before lifecycle execution. The executed SHA is `7329e666c309f9d9768764feb492abff5feb6cd7d78f680adc335fbf847e2907` and `self_digest_verified=true`.

The lifecycle then passed Setup → Start → Workbench HTTP 200 → Doctor → Stop. Final state is `STOPPED`; Security Master remains the valid fresh-install state `NOT_INITIALIZED`; wrong-Python, tampered-package, stale-runtime and existing-business-state preservation guards all passed.

A separate fresh Windows Sandbox interactive-session GUI acceptance also passed against the same launcher SHA. The `TW-Market` WinForms window rendered, remained alive after render, exposed 26 observed UI elements, and showed the expected fresh-install status and button states.

## Re-review gate

The first independent review disposition was `CHANGES_REQUIRED`. P1-A3-R1 implements bounded corrections and R4 recertification for those findings, but no second independent reviewer disposition is yet preserved as durable evidence. Therefore the independent re-review remains pending and the Owner commit gate has not been reached.

```text
P1_A3_R1_CORRECTION = COMPLETE
P1_A3_R4_HEADLESS_ACCEPTANCE = PASS
P1_A3_R4_GUI_ACCEPTANCE = PASS
INDEPENDENT_RE_REVIEW = PENDING
OWNER_COMMIT_GATE = NOT_REACHED
COMMIT = NOT_PERFORMED
PUSH = NOT_PERFORMED
P2 = NOT_STARTED
PHASE_M = NOT_AUTHORIZED
```