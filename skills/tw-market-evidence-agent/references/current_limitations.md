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
  every Phase H route. `trading_status_context` currently executes only through
  the explicitly active TPEx attention route; the broader H1 declared scope
  remains partial.
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
