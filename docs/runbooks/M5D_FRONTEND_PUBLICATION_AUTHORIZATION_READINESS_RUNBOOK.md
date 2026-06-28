# M5D frontend publication authorization readiness runbook

This package is a request-only, hash-bound release candidate for a future explicit user authorization decision. It does not authorize or perform publication to `frontend/public/market-context.json`.

## Preflight

Run safe, offline checks only:

```bash
python scripts/validate_m5d_publication_candidate.py --candidate-dir research/staging/m5d/m5d_frontend_publication_candidate_01
python scripts/run_m5d_frontend_publication_preflight.py --check-only
python scripts/simulate_m5d_frontend_publication_transaction.py --check-only
python scripts/simulate_m5d_frontend_publication_rollback.py --check-only
```

## Evidence interpretation

The candidate is derived only from the reviewed M5C `frontend_readonly_context_package.json`, bound to the M5C package manifest, supplemental audit, run-summary destination correction, PR #57 merge SHA, source `TWSE_OpenAPI`, and targets `2330`, `0050`, and `00929`.

The preview must display stale/historical status, official TWSE_OpenAPI authority, source date/freshness fields, and caveats that it is not realtime guaranteed, not production current state, and not a trading signal.

## Future execution prerequisites

Actual frontend publication remains blocked until a separate user authorization decision and single-use token exist. Executable publication mode intentionally fails closed in this bundle.

## Rollback drill

Use the rollback simulator with temporary paths only. Future authorized execution must preserve the destination hash before replacement and restore that exact hash if rollback is required.
