# Current Limits and Governed Boundaries

The Unified MCP and Local Service are available through their six registered
tools. Availability does not authorize every request: validation, preview,
capability authority, explicit execution confirmation, and execute-once control
remain mandatory.

- Supported cash execution is bounded to governed TWSE/TPEX routes and eligible
  `common_share`/`etf` instruments.
- TAIFEX capability support is provisional; no provisional or blocked route may
  be represented as an executable market retrieval.
- `recent_performance` is plan-only and session-state semantics remain bounded
  by the capability authority.
- Current observation is not realtime guaranteed. EOD is reference data for a
  completed session.
- A fresh installation may be `NOT_INITIALIZED`; operators explicitly update
  the installation-local Security Master. There is no Candidate B fallback,
  scheduler, polling, startup acquisition, raw-payload exposure, trading, or
  order routing.
