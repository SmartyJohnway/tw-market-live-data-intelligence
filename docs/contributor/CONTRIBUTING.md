# Contributing

- Do not create parallel contracts.
- Search the repo before implementing.
- Reuse existing schemas and artifacts.
- Do not weaken governance tests.
- Do not add live behavior to startup.
- Do not introduce trading outputs.
- Do not modify M5F lightly.
- Never commit credentials, cookies, tokens, `.env`, broker/auth material, or raw private payloads.

## Test execution profile selection

Run `python scripts/run_test_profile.py fast --json` for small helper-only changes. Run `python scripts/run_test_profile.py default-ci --json` before opening a normal PR. Use `python scripts/run_test_profile.py full-non-network --json` for large refactors, source-normalization sweeps, M5F/canonical changes, or release preparation. Use `python scripts/run_test_profile.py operator-preflight --json` when operator execution paths change. Use `python scripts/run_test_profile.py browser-e2e --json` only after installing browser dependencies. Never run `bounded-live` unless live execution is explicitly intended and confirmed with `--confirm-bounded-live`.
