# GitHub Actions execution policy

## CI_POLICY_V1

CI_POLICY_V1 separates mandatory Codex sandbox validation from optional GitHub
runner evidence.  It applies to repository testing workflows.

- Ordinary PR creation and updates do **not** schedule GitHub Actions.
- Pushes or merges to `main` do **not** schedule GitHub Actions.
- Every task must run applicable Codex sandbox validation and commit a
  machine-readable acceptance/validation artifact.
- The task authorization defaults to `NO_GITHUB_CI` unless the task explicitly
  says `LIGHTWEIGHT_CI_REQUIRED` or `RELEASE_CI_REQUIRED`.
- A workflow that was skipped or never run is **unexecuted**, never passed.

## Authorization modes

| Mode | GitHub runner behavior |
| --- | --- |
| `NO_GITHUB_CI` | No GitHub workflow is dispatched. Sandbox validation is the required evidence. |
| `LIGHTWEIGHT_CI_REQUIRED` | One final-head manual dispatch each of **Default CI** and/or **Windows Compatibility Smoke** when the task explicitly authorizes it. |
| `RELEASE_CI_REQUIRED` | **Release Validation** runs for a published release or is manually dispatched in release context. |

Historical acceptance, browser E2E, and performance remain manual. Performance
is not release-blocking under CI_POLICY_V1. The single **Release Validation**
workflow owns automatic release execution of the default, full-non-network, and
Windows compatibility checks; the corresponding standalone workflows are
manual-only to prevent duplicate release runs.

## Sandbox and release evidence

Sandbox validation is primary during ordinary development. GitHub runner
validation is independent environment evidence and is used only when explicitly
authorized or during release validation. Sandbox evidence records the tested
local generation, exact commands, and return codes; it cannot prove GitHub
runner, branch-protection, Windows junction/reparse, or release-environment
behavior.

`workflow_dispatch` is normally available once a workflow definition is on the
default branch. Therefore PR #151 remains `NO_GITHUB_CI`; future explicitly
authorized milestone tasks can manually dispatch approved workflows only after
this policy reaches `main`.
