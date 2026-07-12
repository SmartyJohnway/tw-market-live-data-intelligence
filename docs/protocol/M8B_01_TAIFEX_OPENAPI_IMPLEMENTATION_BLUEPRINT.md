# M8B-01 TAIFEX OpenAPI implementation blueprint

Next PR: `M8B-01-TAIFEX-OPENAPI-OFFICIAL-DERIVATIVES-EOD-ADAPTERS-AND-CONTEXT-INTEGRATION`.

Implement `scripts/m8b_taifex_derivatives_observation.py`, `scripts/m8b_taifex_openapi_futures_adapter.py`, `scripts/m8b_taifex_openapi_options_adapter.py`, `scripts/m8b_taifex_openapi_execution.py`, and `scripts/validate_m8b_taifex_openapi_live.py`. A unified low-level fetch helper is acceptable, but futures/options parsers should stay separate because option identity requires strike and call/put.

Required behavior: explicit operator confirmation; selected products/contracts; bounded retained scope; no full raw payload retention; no scheduler, polling, startup fetch, or DB write; normalized derivatives observations; futures context projection; options context projection only when identity is robust; source-specific currentness; conversation projection; README/source registry update; final acceptance.

Suggested commits: (1) derivatives observation and parser helpers, (2) futures/options adapters and fixtures, (3) controlled execution and M8 context integration, (4) conversation projection, README, live validation, final acceptance.
