# Current Capability Matrix

This page is a human-readable summary. The machine authority is
`docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json`
plus the V3 routing matrix and executor registry. Catalog support can be broader
than selected-route executability; the route-scope column below describes the
currently selected executable route where one exists.

| Capability | Catalog status | Current execution summary | Current route scope | Key limitation |
|---|---|---|---|---|
| `identity` | contract_supported | installation-local Security Master resolution; route is plan-only with no standalone source executor | local identity service | known identity != executable evidence capability |
| `current_observation` | runtime_executable | selected bounded executor route | TWSE / TPEX | latest available snapshot; not guaranteed realtime; TAIFEX not implemented |
| `official_eod_reference` | runtime_executable | selected bounded official-reference route | TWSE / TPEX | TAIFEX remains provisional; publication-grace semantics apply |
| `session_status` | runtime_executable | **blocked**; no selected approved executor binds the complete authoritative session/closure evidence set | none | Catalog support does not clear the current route blocker; TAIFEX remains provisional |
| `material_disclosures` | runtime_executable | selected Phase G official-research route | TWSE / TPEX eligible common shares | latest completed official daily batch only; no arbitrary history |
| `monthly_revenue` | runtime_executable | selected Phase G official-research route | TWSE / TPEX eligible common shares | latest available reporting period only; no arbitrary history |
| `trading_status_context` | runtime_executable | selected TPEx composite with partial coverage: attention + disposition + source-native `cmode` | TPEX common shares | `cmode` semantics unresolved; suspension/resumption and broader H1 coverage remain incomplete |
| `corporate_action_context` | runtime_executable | selected bounded TWSE TWT48U_ALL pre-announcement route | TWSE common shares | TPEx not executable; final/capital-reduction/par/split/consolidation coverage remains inactive, manual, or blocked |
| `recent_performance` | runtime_executable | selected bounded TWSE lookback route (`1..20` completed sessions) | TWSE common shares | TPEx remains blocked; no persistent history accumulation/backfill |
| `market_state_context` | runtime_executable | selected I1 production routes | TWSE / TPEX common shares | market-level context does not establish target-specific causation; no historical lookup |
| `index_futures_context` | runtime_executable | selected I2 TAIFEX-backed TX regular-session route | TWSE common-share targets | standard monthly outright TX only; no TPEx targets/night session/weekly/options/continuous contract |
| `cash_institutional_flow_context` | runtime_executable | selected I3 production routes | TWSE / TPEX common shares | descriptive only; no history/polling/retry; source-date/currentness caveats remain explicit |
| `source_currentness` | contract_supported | derived/plan-only; no independent executor | derived from governed upstream evidence | not a promise of realtime data |
| `evidence_quality` | contract_supported | derived/plan-only; no independent executor | derived from governed evidence bundle | depends on underlying evidence coverage |

## Contract versions

- accepted Request: V1 / V2 / V3
- preferred Request: V3
- new Result/Audit: V3
- V1/V2 compatibility retained

Always consult the machine Catalog/Route authority before claiming a route is
executable.
