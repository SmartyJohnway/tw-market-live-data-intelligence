# Current Capability Matrix

This page is a human-readable summary. The machine authority is
`docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json`
plus the V3 routing matrix and executor registry.

| Capability | Contract status | Current execution summary | Markets | Key limitation |
|---|---|---|---|---|
| `identity` | contract_supported | resolved by installation-local Security Master, not a standalone source operation | TWSE / TPEX / TAIFEX | known identity != executable capability |
| `current_observation` | runtime_executable | governed bounded route(s) | TWSE / TPEX | not guaranteed realtime; TAIFEX current observation not implemented |
| `official_eod_reference` | runtime_executable | governed bounded official reference | TWSE / TPEX | publication-grace semantics apply |
| `session_status` | runtime_executable | governed deterministic/session authority | TWSE / TPEX | TAIFEX session authority remains limited/provisional |
| `material_disclosures` | runtime_executable | Phase G G1 | TWSE / TPEX eligible common shares | latest completed official daily batch; no arbitrary history |
| `monthly_revenue` | runtime_executable | Phase G G2 | TWSE / TPEX eligible common shares | latest available reporting period; no arbitrary history |
| `trading_status_context` | runtime_executable, partial | **TPEx attention route only** | semantic scope TWSE / TPEX; active route TPEX | broader H1 types/routes are uncovered/inactive |
| `corporate_action_context` | contract_supported | not currently route-executable | TWSE / TPEX | no H2 route activated |
| `recent_performance` | contract_supported | not currently route-executable | TWSE / TPEX | H3 default 5D/20D route not proven/activated |
| `source_currentness` | contract_supported | projected/derived where governed | TWSE / TPEX / TAIFEX | not a promise of realtime data |
| `evidence_quality` | contract_supported | projected/derived where governed | TWSE / TPEX / TAIFEX | depends on underlying evidence coverage |

## Contract versions

- accepted Request: V1 / V2 / V3
- preferred Request: V3
- new Result/Audit: V3
- V1/V2 compatibility retained

Always consult the machine Catalog/Route authority before claiming a route is
executable.
