# M6E Operator Acceptance Test and Release Preflight

M6E is the operator acceptance layer for the local-first M6 workflow. It proves that a new maintainer can start from a clone-like repository state, run diagnostics, inspect Mode A, plan Mode B without network, build Mode C, verify FastAPI/MCP/frontend readonly contracts, and receive one final acceptance report.

## Command

Default check-only mode is non-network and does not execute live observation:

```bash
python scripts/run_m6e_operator_acceptance.py --check-only
```

The script writes only the M6E report files in check-only mode:

```text
research/live_observation_runs/m6e_operator_acceptance/latest_operator_acceptance_report.json
research/live_observation_runs/m6e_operator_acceptance/latest_operator_acceptance_report.md
```

## Status interpretation

- `pass` means all acceptance checks passed with no caveats.
- `pass_with_caveats` means required checks passed, but the operator should read caveats such as missing optional latest observation evidence.
- `fail` means at least one acceptance check failed and the repository should not be treated as release-preflight ready until corrected.

## Modes covered

- Mode A validates and reads the canonical M5F Level 1 package. M5F remains unchanged.
- Mode B validates default watchlist planning and source-health/source-contract check-only readiness. Observation remains non-canonical.
- Mode C builds the M5N Conversation Package for safe ChatGPT handoff without raw endpoint payload fields or trading output fields.

## Live mode

`--execute-bounded-live-check --ssl-policy strict` is recognized as an explicit operator mode, but M6E does not implement live aggregation. Existing bounded live commands remain the controlled surfaces for live observation or source-contract probing. There is no silent TLS fallback; strict remains default, compatibility is explicit, and unsafe-explicit is explicit only.

## Forbidden behavior remains forbidden

M6E does not add trading output, recommendations, ranking, target price, buy/sell/hold, broker/auth, polling, scheduler, startup network calls, full-market scans, M5F mutation, frontend/public writes, research/generated writes, production/prod writes, raw payload leakage, or TLS verification bypass.
