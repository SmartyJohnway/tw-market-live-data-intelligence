# M8R-03E-R2 combined final acceptance

Baseline SHA: `1c2144498b524e52b2bf21fce8ed00683d9eb3a7`.

- R2-F0: **GO_WITH_CAVEATS**
- R2: **GO_WITH_CAVEATS_PENDING_WINDOWS_WORKFLOW_CONFIRMATION**
- Combined PR: **REQUEST_CHANGES_PENDING_MANUAL_OR_RELEASE_WINDOWS_EVIDENCE**. Under CI_POLICY_V1 this NO_GITHUB_CI PR does not dispatch runners; unexecuted workflows are not recorded as passed.
- Recommended next task after closure: `M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP`, because the AI behavior/evidence schema decoupling P1 remains before Phase C.

Acceptance evidence is separated into `docs/acceptance_runs/` rather than embedded as permanent capability pass-count state. R2 authorization composition is tested at the nearest controlled-execution boundary: the M8R-03D watchlist controlled executor, because the M8R-03E handoff writer consumes already-authorized upstream artifacts rather than an authorization token directly.

Windows junction/reparse protection remains best-effort/follow-up. Windows Compatibility Smoke remains a complete manual-only compatibility workflow (M5F, M5I, M5IJ, FastAPI, MCP, M6D, package validation, and MCP startup); Release Validation runs that same complete set on published releases. No GitHub runner execution was performed for this PR under NO_GITHUB_CI.
