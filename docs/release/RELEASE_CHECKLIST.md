# Release Checklist

## Deterministic release-blocking gate

- [ ] `release-blocking-ci` v1 passes with zero selected failures and zero unexpected guard denials: `python scripts/run_test_profile.py release-blocking-ci --json --output-root ../ci-runs/UNIQUE-RUN-ID`.
- [ ] Existing Python dependencies, Git and Node prerequisites are available before the test window. `TW_MARKET_CI_NODE` may select an existing Node executable; this command does not install dependencies.
- [ ] Retain exact collected members, excluded historical-node reasons/current equivalents, JUnit results and Python/Node subprocess guard evidence under the fresh output root.
- [ ] Record FAST / DEFAULT_CI / FULL_NON_NETWORK diagnostic results honestly; never convert their overall FAIL into PASS. They are not substitutes for the canonical blocking gate.
- [ ] Retain the original historical assertions and legacy acceptance migration matrix at `docs/reviews/m6k_ci_gate_migration_matrix.csv`. A1's explicit classification lives in `config/release_blocking_ci.v1.json`; future selection changes require governance.

`DEFAULT_CI` is the preserved current/historical mixture. `FULL_NON_NETWORK` is
the broader diagnostic composite; on the A1 Windows baseline it stops during
collection because the historical Phase J A6 session helper imports Unix-only
`fcntl`. No FULL_NON_NETWORK PASS is implied. The canonical profile preserves
all DEFAULT_CI current invariants, adds current Phase L boundaries and explicitly
replaces frozen historical scope/readiness assertions with current blocking
coverage. Its process-local guard does not claim OS-level egress isolation.

## Additional release acceptance (separately governed)

The following proofs remain applicable release work for later authorized
tranches. A1's local CI result does not accept them or authorize publication.

- [ ] OPERATOR_PREFLIGHT passes: `python scripts/run_test_profile.py operator-preflight --json`.
- [ ] MCP startup safe: `python server/mcp_server.py --startup-check`.
- [ ] Windows Compatibility Smoke is run through its actual manual trigger; A2 owns fresh-clone / Windows 11 x64 Native / Docker release integration. No label trigger exists in current YAML.
- [ ] Browser E2E dependencies installed only for browser validation: `python -m pip install -r requirements-browser-e2e.txt` and `python -m playwright install --with-deps chromium`.
- [ ] BROWSER_E2E passes when release validation requires real browser evidence: `python scripts/run_test_profile.py browser-e2e --json`.
- [ ] L7-A5 bounded-live release acceptance has separate exact Owner authorization and source/target/request/time/retry budgets. The runner confirmation flag alone is insufficient authority; A1 authorizes no live execution.
- [ ] M5F validator passes.
- [ ] M5Q source-health check-only passes.
- [ ] Conversation Package builds.
- [ ] FastAPI startup remains safe: no startup network calls.
- [ ] Frontend readonly workbench documented.
- [ ] No forbidden path writes.
- [ ] No trading output.
- [ ] No raw payload leakage.
- [ ] No production-ready claim; status remains Local Release Candidate / Not Production Ready.

Commands and change-type routing are listed in [Testing Guide](../contributor/TESTING_GUIDE.md).
The canonical local deterministic gate is defined by
`config/release_blocking_ci.v1.json`; GitHub workflow integration and required
checks/protection remain later separately authorized work.
