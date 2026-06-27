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
