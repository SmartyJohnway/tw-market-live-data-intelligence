# L7-A1 — Deterministic Required CI & Historical Failure Classification

Technical disposition:
`L7_A1_DETERMINISTIC_REQUIRED_CI_AND_HISTORICAL_FAILURE_CLASSIFICATION_PASS`.
**OWNER ACCEPTANCE PENDING**. Merge/auto-merge, L7-A2+, stable publication and
Phase M remain unauthorized. L6 is CLOSED; L7-A0 is Owner-accepted and merged;
Phase L remains NOT CLOSED.

Authority:
`USER_CHAT_2026-10-24_PHASE_L_L7_A1_DETERMINISTIC_REQUIRED_CI_AND_HISTORICAL_FAILURE_CLASSIFICATION_AUTHORIZATION`.

## Exact entry and result

PR #409 was verified merged through GitHub. Its normal merge is
`405bf16f5f82f4d37062d036ca6815eba27f7c4d`, with exact parents
`37b6a836fd80addfd6a8cf03c3c6f19848b3e143` and
`f29f053336773b093c9cda819922cd1ee8f5fc65`, tree
`cf6db19544705fa83a55e17377489116b9ebcdc7`. origin/main equalled this merge.
The clean isolated branch is `phase-l/l7-a1-deterministic-required-ci`.

[A1 evidence manifest](acceptance_runs/l7-a1-20261024T003128Z/manifest.json)
binds the records and exact test input hashes. The containing Git commit/tree
and PR record bind the final candidate without circular embedded commit hashes.

| Execution | Result | Interpretation |
| --- | --- | --- |
| Entry DEFAULT_CI | 1245 passed / 45 failed / 4 skipped / 5 deselected | FAIL; exact A0 45-node set reproduced |
| Candidate DEFAULT_CI | 1277 passed / 13 failed / 4 skipped / 5 deselected | FAIL retained; 32 resolved, 12 historical + one legacy Node prerequisite remain |
| Entry FULL_NON_NETWORK | 5357 collected / 56 deselected; one collection error | FAIL before test execution; Unix `fcntl` in historical Phase J A6 helper |
| Candidate FULL_NON_NETWORK | same collection-error module | FAIL retained; exact candidate collection count is in its record; no complete suite PASS claimed |
| Canonical release-blocking-ci v1 | 1895 passed / 0 failed / 4 named optional artifact witnesses skipped | PASS; 1899 selected, zero unexpected skip/xfail |
| Preserved historical replay | two expanded L5 assertions + post-J/K boundary assertion fail | Expected diagnostic FAIL, retained verbatim |

The four optional witnesses need an original Git-ignored sealed/developer bundle
or initialized inherited active release. Fresh deterministic CI must not inherit
that state. Their exact IDs, reasons and required current equivalents are frozen
in the contract. The current equivalents include offline qualification/activation,
synthetic resolver tests, fresh-install lifecycle tests and a real localhost HTTP
identity validation using an explicitly initialized, qualified test release.
Any other skip/xfail, changed reason, collection error or selected test failure
blocks the canonical gate.

An early harness run used Windows backslashes in PYTEST_ADDOPTS and placed temp
output inside the checkout. It was terminated, its own untracked output moved
within the task root, and the clean baseline rerun with forward slashes. That
invalid run supplies no acceptance or failure-comparison authority.

## Canonical required contract

`config/release_blocking_ci.v1.json` is the versioned selection/network/state
authority. `config/test_execution_profiles.json` exposes it through
`python scripts/run_test_profile.py release-blocking-ci --json --output-root ../ci-runs/UNIQUE-RUN-ID`.
The output directory must be fresh, outside APP_ROOT and under the isolated
workspace parent. Existing Python/Git/Node prerequisites are required; no setup
downloads or machine-wide installation occur in the test window.

The profile includes the existing DEFAULT_CI current selection plus explicit
current L3–L6 boundaries, identity-release and current-equivalent tests. The exact
final collected nodes are recorded after pytest selection and match the JUnit set.
Fifteen explicit historical diagnostic nodes are excluded: the original 14 A0
historical failures and one additionally sampled post-J closure assertion. Every
exclusion names its historical intent, superseding authority and executed current
equivalent. There is no runtime failing-node discovery, blanket file exclusion,
xfail or test deletion.

The runner has a 3600-second supervising deadline; timeout is FAIL. Individual
process tests retain their shorter bounds. FAST is inner-loop feedback. DEFAULT_CI
and FULL_NON_NETWORK remain honest mixed/broad diagnostics. Operator/browser and
live acceptance remain separately governed; current deterministic JS state
semantics execute in Node and remain blocking. Selection or boundary changes
require explicit governance; A2–A7 must not silently redefine the contract.

## Final 47-node adjudication

`failure_adjudication_47.json` has exactly 47 unique rows and **DECISION_REQUIRED=0**.
Each row retains its A0 classification, final classification, blocking role, root
cause, repair, exact node/current equivalent, historical evidence and final result.

| Final classification | Count | Resolution |
| --- | ---: | --- |
| TEST_INFRASTRUCTURE_DEFECT | 32 | 28 isolated identity fixture/root bindings; two launcher init setups; one localhost init setup; one fake-client trace_id seam |
| ENVIRONMENT_PREREQUISITE | 1 | Existing Node explicitly selected in guarded canonical execution; all JS assertions preserved |
| HISTORICAL_GOVERNANCE_ASSERTION | 14 | Frozen I3 call-shape/catalog projection, Phase-J-not-started and L5 no-later-change assertions retained with current blocking equivalents |

The I2 acceptance-only helper now honors its explicit selected Security Master
root. Tests build synthetic records, qualify and activate through the existing
offline APIs in per-test directories. There is no runtime fixture fallback or live
Security Master update. The launcher tests explicitly initialize before exercising
preload-before-bind/failure behavior. The passive MCP fake accepts the current
trace_id keyword and asserts a nonempty trace; the real dispatcher is unchanged.

All fourteen historical test nodes and their modules are byte-identical to the entry. Current
equivalents freeze accepted public/source/executor authorities and detect mutations,
exercise H3 transport and L4 boundaries, preserve all 72 family dimensions and
identity/lineage failure controls, and validate accepted J closure with subsequent
accepted K continuation. The additional post-J test still demands K NOT_STARTED;
the immutable K Owner closure from 2026-10-13 and checked Roadmap prove why that
frozen continuation condition no longer governs current release CI. Its original
test and validator also remain untouched. This extra node is recorded separately
from the required 47-row ledger.

No product/server/public-contract repair was required. The changed proof helper
is acceptance-only, not a runtime root resolver. No valid current 45-node failure
was demoted: all 33 nonhistorical baseline nodes pass in canonical execution.
There are zero new DEFAULT_CI failures and the FULL_NON_NETWORK collection error
is unchanged. Its Unix-only historical helper receives no shim/dependency change;
it remains a platform/manual diagnostic with current budget/authorization coverage
in the deterministic profile.

## Affirmative network and subprocess boundary

The canonical window records **385 guard events, zero denials**. External
DNS/connect/sendto is denied through Python audit hooks. Python children receive
guard bootstrap, including `-I`, `-S` and `-X utf8`; normal children install it
before site startup. Node executes only the explicit state-contract mode with
network, workers and child processes denied. Git is restricted to local reviewed
operations; other native children and raw process escape APIs fail closed. Proxy
environment is stripped. Explicit controlled localhost service/readiness traffic
is permitted. This is process-local instrumentation, not an OS firewall claim.

Nine separate negative controls prove denial of DNS, connect_ex, urllib,
requests, httpx, isolated Python child, native child, Node HTTPS and Node worker
paths. They intentionally trigger nine denials before dispatch, with zero real
external dispatches. Their logs are distinct from the zero-denial product-test
window. The archived negative-control harness records the original task-root
invocation; it is an evidence snapshot, not an installed product entrypoint.

Actual live provider requests, market acquisition attempts, Security Master live
updates, background market polling, production-state mutations and D-drive access
commands are **0**. Synthetic source delegates remain explicitly test data.
No host firewall/security settings changed. No Node/Python/dependency installation
occurred. The observed environment is Windows/Python 3.13.7, MCP 1.29.0, pytest
9.0.2, existing Node 26.7.0 and Git 2.56.0.windows.2. This does not decide A3/A4
release dependency or Python/SDK support policy.

## Gate reconciliation and bounded progress

The release checklist adopts Model B: the new green deterministic profile is the
canonical gate; DEFAULT_CI/FULL_NON_NETWORK outcomes are retained diagnostics,
with no misleading PASS. Current testing guidance names the same hierarchy.
Windows workflow invocation reflects its actual manual trigger; no YAML changed.
Additional fresh-release/operator/browser/live/publication proofs remain later
authorized work. A1's local gate does not waive them.

Only L7-GAP-01/02/03/04 are CLOSED. Only L7-EXIT-01/02/03/27 are PASS. The other
17 A0 gaps and 25 final release criteria remain unaccepted by A1. The canonical
29-item wording and accepted Windows 11 x64-only Native policy remain unchanged.

Eight governance/front-door/version/hygiene/forbidden-path validators, Python/Node
static checks, historical A0/A5/A6 manifest verification, exact scope and evidence
manifest checks pass. Historical evidence is unchanged. Requirements, VERSION,
SDK pin, workflows, GitHub settings, packaging policies, public Request/Result/Audit
contracts, exact-six MCP, L2 authority and L6 install/state contracts are preserved.
After opening the PR, stop for independent review and Owner acceptance.
