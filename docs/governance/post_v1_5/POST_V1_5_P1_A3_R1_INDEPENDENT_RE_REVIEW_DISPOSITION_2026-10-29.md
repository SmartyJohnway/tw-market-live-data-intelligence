# Post-v1.5 P1-A3-R1 — Independent Re-review Disposition

Date: 2026-10-29

Status: **CHANGES_REQUIRED**

Baseline development HEAD reviewed: `430d320784d5249508c37bbd6e8272732bf63ee8`.
Local `main` equaled local `origin/main`; no staged changes were present.

The independent Codex re-review accepted four of the five original findings as closed and found original finding 2 still reproducible. It also identified one new bounded A2 failure-path defect. The reviewer made no source, test, governance, acceptance-evidence, commit, push, cleanup, or deletion changes.

## Original findings disposition

1. Fresh-install StrictMode crash — **CLOSED**.
2. Technical Details overwritten after action — **NOT_CLOSED**.
3. Setup final verification fail-open — **CLOSED**.
4. Start/Stop duplicate normal-path refresh — **CLOSED**.
5. Exact-current / GUI evidence insufficiency — **CLOSED**.

Finding 2 remained reproducible because a Setup failure can store the action result in `LastTechnicalDetails`, then a subsequent status refresh inside GUI render calls `Get-LauncherSnapshot`, which overwrites `LastTechnicalDetails` before the preserved render completes.
## New bounded finding

**MEDIUM — Start/Stop malformed-response branches skip required post-action status refresh.**

When canonical Start or Stop returns an unparseable/non-JSON payload, the current implementation returns `START_FAILED` / `STOP_FAILED` before refreshing status. The GUI then reuses the pre-action cached snapshot, which can present stale state and violates the frozen A2 requirement that Start/Stop completion be followed by one actual status refresh.

## Independent revalidation

The reviewer independently ran the specified P1-A3/lifecycle/package regression set: **94 passed**. PowerShell parser validation, CR-at-EOL-aware `git diff --check`, front-door, public-contract, runtime-skill-guide sync, Portable Catalog sync, product-version consistency, and L5 publication-conformance validators all passed.

Existing R4 provenance, guest self-digest, headless lifecycle, GUI acceptance, JIT restoration, and cleanup evidence were judged sufficient to close original finding 5. A new Sandbox run was not required to establish this `CHANGES_REQUIRED` disposition because the remaining source defects were reproducible without altering files.

## Gate disposition

```text
INDEPENDENT_RE_REVIEW = CHANGES_REQUIRED
OWNER_COMMIT_GATE = NOT_REACHED
COMMIT = NOT_PERFORMED
PUSH = NOT_PERFORMED
P2 = NOT_STARTED
PHASE_M = NOT_AUTHORIZED
```

The next authorized work unit is a bounded P1-A3-R2 correction limited to the two defects above, followed by exact-current R5 recertification and a new independent re-review. Historical R1/R4 evidence remains immutable evidence of the reviewed candidate and must not be overwritten.
