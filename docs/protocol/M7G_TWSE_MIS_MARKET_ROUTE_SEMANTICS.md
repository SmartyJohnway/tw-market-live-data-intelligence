# M7G TWSE MIS Market Route Semantics

Status: `twse_mis_market_route_semantics_defined`

## Correct live / reference source semantics

Live / Level 2 / bounded observation:
- 上市即時：TWSE_MIS / tse_{symbol}.tw
- 上櫃即時：TWSE_MIS / otc_{symbol}.tw
- 期貨即時：TAIFEX_MIS

Official reference / EOD / Level 1 or canonical-adjacent:
- 上市盤後/官方參考：TWSE_OPENAPI
- 上櫃盤後/官方參考：TPEX_OPENAPI
- 期交所盤後/官方參考：TAIFEX_OPENAPI

## Important constraints

- TPEx/OTC listed stock live quotes are TWSE_MIS otc_ channel routes.
- Do not introduce TPEX_MIS.
- TPEX_OPENAPI is not a Level 2 live quote source family.
- TAIFEX_MIS is Level 2 live observation family but not executable in M7G-10.
- TWSE_OPENAPI, TPEX_OPENAPI, TAIFEX_OPENAPI are official reference/EOD families, not M7G-10 executable live refresh families.
- ROTC / rotc_ must not be declared as supported or candidate in M7G.
- Emerging stock live route is not supported in M7G.

## M7G-10 source taxonomy

```json
{
  "level2_live_observation_source_families": ["TWSE_MIS", "TAIFEX_MIS"],
  "twse_mis_market_routes": {
    "twse_listed": "tse_{symbol}.tw",
    "tpex_otc_listed": "otc_{symbol}.tw"
  },
  "level1_reference_source_families": ["TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI"],
  "m7g09_execution_supported_source_families": ["TWSE_MIS"],
  "declared_but_not_yet_executable_source_families": ["TAIFEX_MIS", "TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI"],
  "not_declared_source_families": ["TPEX_MIS", "ROTC_MIS"],
  "emerging_stock_live_route_supported": false,
  "rotc_route_declared": false
}
```
