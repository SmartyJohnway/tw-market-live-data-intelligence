# Release Readiness

Current status: local-first staging and readonly preview are ready for non-network CI acceptance.

CI readiness: non-network workflow runs compileall, pytest excluding network tests, and local delivery acceptance check-only.

Test readiness: fixture, validator, governance, PR-body, CI-wrapper, and frontend static tests are included.

Fixture readiness: local-only fixtures and golden readonly packages are validation examples only.

Frontend readonly local preview readiness: source files exist outside frontend/public and display caveats.

Not production-ready blockers: no production refresh authorization, no production/generated/frontend publication promotion, no production current state.

Not live-ready blockers: no additional live probe authorization in this bundle, not realtime guaranteed, no current-market-state claim.

Not frontend/public-ready blockers: no frontend/public publication is authorized.

Next authorization ladder: review the M5C staging package, then issue a separate M5D frontend-publication authorization only if frontend/public publication is desired.


## M4 Omega

Adds local-only fixture-only governed platform skeleton: governance policy, source registry, evidence ledger, fixture replay, readonly observability, release gates, authorization ladder, and operator checks.

## M5A readiness note

M5A adds a check-only authorization request schema and validator for a future bounded single-source M5B live probe. A passing M5A request means `ready_for_user_authorization_review`; it does not authorize live probing, token issuance, production writes, frontend publication, generated artifact writes, full-market scans, or trading outputs.

## M5B bounded live evidence gate

M5B adds a single-use bounded TWSE_OpenAPI evidence gate. It is staging-only and does not authorize production promotion, generated artifact refresh, frontend publication, or trading signals.

## M5C/M5D bundle 01

- M5C durable staging promotion is local-only, single-use, historical evidence only, and not production-ready.
- M5D frontend publication remains request-only; the next action is separate user authorization.

## M5D frontend publication authorization readiness bundle 02

- `ready_for_user_authorization_review=true`
- `frontend_publication_authorized=false`
- `publication_performed=false`
- `production_ready=false`
- Candidate directory: `research/staging/m5d/m5d_frontend_publication_candidate_01`
- Proposed destination for a future authorization only: `frontend/public/market-context.json`
- No frontend/public write is authorized or performed by this bundle.

## M5E controlled frontend publication gate

M5E adds a check-only, fail-closed release gate for a future explicitly authorized frontend publication. Required status is `ready_for_explicit_user_authorization_review=true`, `frontend_publication_authorized=false`, `publication_performed=false`, `execute_mode_available=false`, and `production_ready=false`. No actual authorization, token, or frontend/public write is included.

## M5FGH product convergence status

PR #59 / M5E is treated as merged upstream. M5FGH converges the reviewed M5C/M5D historical evidence into the current canonical local product line: `research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json` is the only source-of-truth payload for browser preview, FastAPI readonly endpoints, MCP readonly tools, and AI briefing artifacts.

North Star: a local-first, bounded-watchlist, explicit manual-refresh Taiwan market context center shared by browser and AI Agents. The package is historical/stale reviewed evidence for 0050, 00929, and 2330 from TWSE_OpenAPI source date 2026-06-26; it is not realtime, not production current state, not full-market coverage, and not a trading signal.

Historical M3 generated artifacts under `research/generated/` remain legacy generated artifacts. M5F is the current canonical consumer package. Bounded live evidence exists in prior governed evidence, so the repo is not fixture-only, but M5FGH does not run new live probes. The only remaining main bundle after this closure is M5IJ for future explicitly authorized refresh execution and final release hardening.
