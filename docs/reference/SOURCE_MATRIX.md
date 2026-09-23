# Current Source / Evidence Role Matrix

This page is a concise navigation aid. Exact runtime route selection is governed
by the current V3 routing matrix and executor registry.

| Source / family | Role | Current use | Authority / caveat |
|---|---|---|---|
| Installation-local Security Master | Taiwan Market Identity Service | target identity, eligibility, routing projection | local qualified release; `NOT_INITIALIZED` is legal |
| TWSE / TPEx current-observation routes | bounded market observation | `current_observation` | route-specific; not a realtime guarantee |
| TWSE / TPEx official EOD sources | official reference | `official_eod_reference` | official source; publication/timing semantics apply |
| MOPS material disclosure open data | official research evidence | Phase G `material_disclosures` | latest completed official daily batch; bounded target evidence |
| MOPS monthly revenue open data | official periodic evidence | Phase G `monthly_revenue` | latest available reporting period; TWD/thousand semantics |
| TPEx trading warning information OpenAPI | official trading-status evidence | active H1 TPEx attention route | exact-code binding; current H1 coverage is partial |
| V1/V2/V3 governed Result/Audit artifacts | local derived evidence | read/replay/audit/handoff | persisted version is preserved |
| Persistent Watchlists | local durable user state | target selection/composition | not an external market source |

## Not current production authority

Earlier M5F/M5K/M5N/M5Q packages remain engineering history and may still be
used by compatibility tests, but they are not the current product source model.

Third-party or credential-gated providers remain optional until separately
governed. They must not silently override official/current route authority.

For exact capability/source status use:

- `docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json`
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json`
