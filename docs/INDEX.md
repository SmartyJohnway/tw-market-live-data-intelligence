# Documentation Index

- [Delivery Index](DELIVERY_INDEX.md)
- [Release Readiness](RELEASE_READINESS.md)
- [Glossary](GLOSSARY.md)
- [Source Authority Manual](manuals/SOURCE_AUTHORITY_MANUAL.md)
- [Operator Staging Workflow Manual](manuals/OPERATOR_STAGING_WORKFLOW_MANUAL.md)
- [Frontend Caveat Display Manual](manuals/FRONTEND_CAVEAT_DISPLAY_MANUAL.md)
- [Troubleshooting Guide](manuals/TROUBLESHOOTING_GUIDE.md)
- [Local-First Architecture](architecture/LOCAL_FIRST_MARKET_CONTEXT_ARCHITECTURE.md)

Safe commands: `python -m compileall scripts tests`, `pytest -m "not network"`, and `python scripts/run_local_delivery_acceptance.py --check-only`. Boundaries: no live probes, no production refresh, no frontend/public writes, no trading signals, no realtime guarantee.


## M4 Omega

Adds local-only fixture-only governed platform skeleton: governance policy, source registry, evidence ledger, fixture replay, readonly observability, release gates, authorization ladder, and operator checks.

## M5FGH product convergence status

PR #59 / M5E is treated as merged upstream. M5FGH converges the reviewed M5C/M5D historical evidence into the current canonical local product line: `research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json` is the only source-of-truth payload for browser preview, FastAPI readonly endpoints, MCP readonly tools, and AI briefing artifacts.

North Star: a local-first, bounded-watchlist, explicit manual-refresh Taiwan market context center shared by browser and AI Agents. The package is historical/stale reviewed evidence for 0050, 00929, and 2330 from TWSE_OpenAPI source date 2026-06-26; it is not realtime, not production current state, not full-market coverage, and not a trading signal.

Historical M3 generated artifacts under `research/generated/` remain legacy generated artifacts. M5F is the current canonical consumer package. Bounded live evidence exists in prior governed evidence, so the repo is not fixture-only, but M5FGH does not run new live probes. The only remaining main bundle after this closure is M5IJ for future explicitly authorized refresh execution and final release hardening.
