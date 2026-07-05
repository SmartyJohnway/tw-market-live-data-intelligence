# Release Checklist

- [ ] FAST passes: `python scripts/run_test_profile.py fast --json`.
- [ ] DEFAULT_CI passes: `python scripts/run_test_profile.py default-ci --json`.
- [ ] FULL_NON_NETWORK passes: `python scripts/run_test_profile.py full-non-network --json`.
- [ ] Confirm FULL_NON_NETWORK legacy acceptance gates are preserved in `docs/reviews/m6k_ci_gate_migration_matrix.csv`.
- [ ] OPERATOR_PREFLIGHT passes: `python scripts/run_test_profile.py operator-preflight --json`.
- [ ] MCP startup safe: `python server/mcp_server.py --startup-check`.
- [ ] Windows Compatibility Smoke workflow is run manually or with the `windows-smoke` label before release when Windows/fresh-clone compatibility matters.
- [ ] Browser E2E dependencies installed only for browser validation: `python -m pip install -r requirements-browser-e2e.txt` and `python -m playwright install --with-deps chromium`.
- [ ] BROWSER_E2E passes when release validation requires real browser evidence: `python scripts/run_test_profile.py browser-e2e --json`.
- [ ] Optional BOUNDED_LIVE is run only with explicit operator intent: `python scripts/run_test_profile.py bounded-live --confirm-bounded-live --ssl-policy strict`.
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
