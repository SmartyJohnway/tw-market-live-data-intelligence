# Release Readiness

Current status: local-first staging and readonly preview are ready for non-network CI acceptance.

CI readiness: non-network workflow runs compileall, pytest excluding network tests, and local delivery acceptance check-only.

Test readiness: fixture, validator, governance, PR-body, CI-wrapper, and frontend static tests are included.

Fixture readiness: local-only fixtures and golden readonly packages are validation examples only.

Frontend readonly local preview readiness: source files exist outside frontend/public and display caveats.

Not production-ready blockers: no production refresh authorization, no durable evidence promotion, no production current state.

Not live-ready blockers: no live probes, not realtime guaranteed, no source freshness verified by this bundle.

Not frontend/public-ready blockers: no frontend/public publication is authorized.

Next authorization ladder: approve limited fixture refresh, then controlled single-source live probe, then explicit durable promotion review.


## M4 Omega

Adds local-only fixture-only governed platform skeleton: governance policy, source registry, evidence ledger, fixture replay, readonly observability, release gates, authorization ladder, and operator checks.
