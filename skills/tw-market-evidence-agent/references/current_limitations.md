# Current Limits and Governed Boundaries

The Unified MCP and Local Service are available through their six registered
tools. Availability does not authorize every request: validation, preview,
capability authority, explicit execution confirmation, and execute-once control
remain mandatory.

- Supported cash execution is bounded to governed TWSE/TPEX routes and eligible
  `common_share`/`etf` instruments.
- TAIFEX capability support is provisional; no provisional or blocked route may
  be represented as an executable market retrieval.
- V3 is the preferred request/result authority, but promotion does not activate
  every Phase H route. `trading_status_context` executes through the selected TPEx H1 composite
  (attention/disposition); cmode marker semantics remain unresolved with zero
  canonical coverage. The broader H1 scope remains partial.
- `corporate_action_context` and `recent_performance` remain plan-only or
  blocked where current routing says so; session-state semantics remain bounded
  by the capability authority.
- `material_disclosures` is executable only for eligible TWSE/TPEX common
  shares and covers the latest completed official daily batch; it is not a
  historical or realtime disclosure search.
- `monthly_revenue` is executable only for eligible TWSE/TPEX common shares and
  covers the latest available reporting period; arbitrary history and
  `financial_summary` are not supported.
- Research acquisition is execute-once, official CSV first, with an explicit
  governed official JSON OpenAPI fallback. `no_evidence_in_covered_scope` and
  `not_yet_available` must not be interpreted as no historical event or zero.
- Current observation is not realtime guaranteed. EOD is reference data for a
  completed session.
- A fresh installation may be `NOT_INITIALIZED`; operators explicitly update
  the installation-local Security Master. There is no Candidate B fallback,
  scheduler, polling, startup acquisition, raw-payload exposure, trading, or
  order routing.

## Catalog and selected-route publication boundary

Catalog support != selected route executability. Effective executability requires
runtime-compatible support AND a resolved selected executable route for the requested
market/target scope. Unsupported, blocked, plan-only and provisional are distinct;
none authorizes retrieval. Consult the canonical Catalog and canonical Routing,
then validate/preview the request; guides are derived usage guidance only.

- `session_status`: Catalog `runtime_executable`, but the current Unified 05B route
  is blocked with no selected approved executor; NOT currently executable.
- `market_state_context`: selected active TWSE/TPEX route, bounded descriptive context.
- `index_futures_context`: final Owner production activation accepted; selected active
  TWSE route for TAIFEX TX regular-session standard monthly outright context. TPEx
  targets and provisional TAIFEX target support remain non-executable. Authority:
  `docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json`
  and `docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json`.
- `cash_institutional_flow_context`: selected active TWSE/TPEX route; descriptive only.
- `corporate_action_context` and `recent_performance`: selected bounded TWSE routes;
  TPEx restrictions remain explicit. Preserve `CORPORATE_ACTION_COVERAGE_INCOMPLETE`,
  H4 discontinuity-safety caveats, missing/source-failed distinctions, citations and
  all existing A3 typed timing/currentness semantics in Result/Audit/AI-ready handoff.

Runtime truth → publication projection. Publication does not activate routes.
Historical AI guides/source-capability registries are not current capability authority.
