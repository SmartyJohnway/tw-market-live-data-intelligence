# M6K CI Tiering and Test Execution Profile

## Decision

M6K preserves the broad non-network safety net and makes execution intent explicit. The repository problem is not test-count reduction; it is routing developers, Codex, CI, and operators to the smallest profile that answers the validation question.

## Profiles

| Profile | Command | Intent | Automatic CI |
|---|---|---|---|
| FAST | `python scripts/run_test_profile.py fast --json` | Inner-loop deterministic safety checks. | Yes, allowed as a local/developer profile. |
| DEFAULT_CI | `python scripts/run_test_profile.py default-ci --json` | Normal PR/push merge protection. | Yes, normal CI. |
| FULL_NON_NETWORK | `python scripts/run_test_profile.py full-non-network --json` | Broad no-network regression equivalent to `pytest -m "not network"`. | Manual or release-oriented only. |
| OPERATOR_PREFLIGHT | `python scripts/run_test_profile.py operator-preflight --json` | Release/operator readiness through existing authoritative runners. | Manual/release-oriented. |
| BROWSER_E2E | `python scripts/run_test_profile.py browser-e2e --json` | Actual browser/operator frontend validation through M6G check-only. | Manual. |
| BOUNDED_LIVE | `python scripts/run_test_profile.py bounded-live --confirm-bounded-live --ssl-policy compatibility` | Explicit operator-approved bounded live acceptance. | Never automatic. |

## Measurement

Baseline collected before implementation:

- `pytest --collect-only -q`: 712 tests collected.
- `pytest -m "not network" --collect-only -q`: 711 selected / 712 collected.

Post-implementation measurement is recorded from the runner JSON fields in validation output. The acceptance target is selected-count ordering: FAST < DEFAULT_CI < FULL_NON_NETWORK. Runtime should generally follow the same direction, but runtime is not manipulated solely to satisfy the graph.

## Safety ownership

DEFAULT_CI retains the core merge-protection owners in [`m6k_default_ci_risk_ownership.csv`](m6k_default_ci_risk_ownership.csv). FAST intentionally keeps the smallest safety-critical subset and excludes large historical milestone regression families, slow operator orchestration, browser E2E, network, and bounded live execution.

## CI routing

- Normal PR/push uses DEFAULT_CI and does not install Playwright or Chromium.
- FULL_NON_NETWORK is a separate workflow for manual or explicitly labeled validation.
- BROWSER_E2E is a separate manual workflow and installs browser dependencies only there.
- BOUNDED_LIVE is not scheduled and is not wired to automatic CI.

## Operator trial path

After M6K, the expected operator path is: fresh clone, install documented dependencies, run operator preflight, start FastAPI/frontend, use Mode A/B/C interactively, and run bounded live only by explicit operator choice.
