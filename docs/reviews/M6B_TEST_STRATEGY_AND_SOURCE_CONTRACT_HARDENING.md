# M6B Test Strategy and Source Contract Hardening

Task ID: `M6B-TEST-STRATEGY-AND-SOURCE-CONTRACT-HARDENING`.

## Test taxonomy

- `unit`: pure local logic, always safe, default CI.
- `mock`: simulated source envelopes and fail-closed behavior, default CI when non-network.
- `integration`: real bounded network checks, manual only, marked `network` and excluded from default CI.
- `release_preflight`: optional operator-run release checks.

## Default CI behavior

Default validation remains no-network:

```bash
pytest -m "not network" -v
python scripts/run_m6b_source_contract_preflight.py --check-only
```

## Manual integration behavior

Manual live checks are bounded and explicit:

```bash
pytest -m integration -v
python scripts/run_m6b_source_contract_preflight.py --execute-live-contract-check
```

## Source contract preflight command

- Script: `scripts/run_m6b_source_contract_preflight.py`.
- Check-only mode: `--check-only`; no network, no writes.
- Execute mode: `--execute-live-contract-check`; bounded live check and writes only under `research/live_observation_runs/m6b_source_contract/`.
- Report flag: `network_calls_may_have_occurred=true` once live execution starts.
- Raw payload policy: `raw_payload_included=false`; endpoint payloads are not stored in the report.

## Targets used

- `2330` through TWSE MIS listed-equity route.
- `0050` through TWSE MIS listed-ETF route.
- `TX` through TAIFEX MIS TX futures route.

## Assertions used

Checks assert request completion or governed failure, JSON parse success or fail-closed diagnostic, required-field presence or governed failure, normalized observation or governed failure, strict TLS policy reporting, no raw payload inclusion, and explicit network flagging.

## What is intentionally not asserted

No exact price, market direction, realtime guarantee, recommendation, ranking, target price, or buy/sell/hold output is asserted.

## TLS policy

Strict TLS is the default. M6B does not implement compatibility or unsafe TLS modes, does not disable TLS verification silently, and does not set a global unverified SSL context. Explicit compatibility policy, if needed for Windows/Python 3.13 environments, is an M6C follow-up.

## Known caveats

Live checks depend on source availability, endpoint contracts, local certificate stores, and current exchange/session behavior. A stale or closed-session observation is degraded rather than healthy, and `reference_only` is not treated as current price.

## Validation commands

```bash
python -m compileall scripts server tests
pytest -m "not network" -v
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python scripts/run_m5ij_end_to_end_acceptance.py --check-only
python scripts/run_m5k_postmerge_validation.py --check-only
python scripts/run_m5q_source_health_probe.py --check-only
python scripts/build_m5n_conversation_context.py
python scripts/governance_forbidden_path_guard.py
python scripts/forbidden_behavior_scanner.py
python server/mcp_server.py --startup-check
python scripts/run_m6b_source_contract_preflight.py --check-only
git diff --check
```

## Forbidden behavior confirmation

M6B does not mutate M5F, fork schemas/contracts, change observation/source-health/conversation semantics, write `frontend/public`, write `research/generated`, write production/prod, add broker/auth, add polling/scheduler/startup network calls, run a full-market scan, add trading recommendations/rankings/target prices/buy/sell/hold, expose raw payloads, or silently disable TLS.
