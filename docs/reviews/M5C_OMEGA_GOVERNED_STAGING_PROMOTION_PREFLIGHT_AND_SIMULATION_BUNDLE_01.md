# M5C Omega Governed Staging Promotion Preflight and Simulation Bundle 01

## Completed tracks
1. M5B evidence intake gate verifies committed manifest hashes, required artifacts, receipt audit, source `TWSE_OpenAPI`, targets `2330/0050/00929`, and historical snapshot classification.
2. Staging promotion contract and request schema separate authorization request from authorization decision.
3. Authorization request package binds M5B manifest hash, candidate hash, merge commit, and exact target set without approval token.
4. Eligibility assessment returns only `eligible_for_user_authorization` or `blocked`.
5. Dry-run planner/simulator is check-only by default and reports `write_performed=false`.
6. Rollback simulator covers tamper, missing artifact, stale evidence, unauthorized target, contract failure, forbidden flags, and partial write simulation without deletion/overwrite.
7. Readonly compatibility gate adapts the historical candidate through the existing readonly package builder without frontend/public writes.
8. One-command preflight reports all M5C gates and leaves `actual_promotion_performed=false` with next action `user_authorization`.

## Boundaries
No live probe, network probe, M5B replay, new authorization consumption, actual promotion, generated write, frontend-public write, production write, broker/auth, or trading output is authorized or performed.

## Review hardening follow-up
- Evidence integrity now delegates to `scripts.verify_m5b_manifest.verify` and adds required-artifact/manifest-contract checks including `evidence_ledger.json`.
- Receipt audit now delegates to `validate_m5b_execution_authorization.validate_authorization(..., mode="receipt_audit")` instead of checking only `authorization_consumed`.
- Request validation now runs Draft 2020-12 schema validation with `additionalProperties:false`, exact ordered targets, canonical M5B run directory, required request-only field set, and strict false safety flags.
- Rollback simulation now copies M5B evidence into temporary directories, injects tamper/missing/target/contract/flag/partial-write scenarios, calls the evidence gate, and reports observed error codes without deleting or overwriting repository files.
- Blocked assessment/planning CLI outcomes now return non-zero.
- Forbidden path checks now cover `production/`, `prod/`, absolute paths, Windows separators, and traversal normalization.

## Second review rollback hardening
- Rollback CLI no longer accepts `--tmp-root`; formal CLI execution always uses an internal `TemporaryDirectory`.
- The Python-only rollback test interface rejects forbidden/durable tmp roots including `frontend/public`, `research/generated`, `production`, `prod`, and `research/live_probe_runs/m5b`.
- Evidence contract validation now requires `contract_status` consistency across candidate, summary, receipt, and manifest, and blocks statuses outside `normalized_pass`/`partial_pass` with `contract_status_blocked`.
- Rollback simulation now marks the overall status `simulation_failed` if any scenario does not observe its expected error code; partial write simulation is explicitly detected as `partial_write_detected`.
- Malformed request/evidence JSON is converted to structured blocked errors instead of tracebacks.
