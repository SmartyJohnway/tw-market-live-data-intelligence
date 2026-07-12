# M8B TAIFEX OpenAPI official derivatives EOD preflight acceptance

Final status: `m8b_taifex_openapi_official_derivatives_eod_preflight_pass_with_caveats`.

## 1. Purpose
Define official TAIFEX OpenAPI derivatives EOD endpoint contracts for M8B-01 implementation.

## 2. Accepted upstream
M8A official TWSE/TPEx EOD context and M8 governance are accepted upstream.

## 3. Official source entrypoint
`https://openapi.taifex.com.tw/` and `https://openapi.taifex.com.tw/swagger.json`.

## 4. Endpoint discovery summary
Swagger/OAS and bounded probes identify daily futures, daily options, and final settlement endpoints.

## 5. Selected endpoints
`DailyMarketReportFut`, `DailyMarketReportOpt`, and `FinalSettlementPrice`.

## 6. Rejected/deferred endpoints
Time-and-sales is rejected as non-EOD. Large-trader open-interest statistics are deferred because they are not contract-level daily quote core.

## 7. Futures identity contract
Use market, instrument_type, product_id, contract_month, session, and trade_date.

## 8. Options identity contract
Use market, instrument_type, product_id, contract_month, strike_price, option_type, session, and trade_date.

## 9. Price semantics
Open/high/low, last, settlement, reference, change, and final settlement are separate.

## 10. Settlement/reference/last distinction
Daily settlement price is not last price. Final settlement price is expiry settlement. Reference price is not inferred unless source-reported.

## 11. Activity/open-interest semantics
Volume and open interest are contract counts; unresolved units must remain caveated.

## 12. Trade-date/currentness contract
`Date` is market trade date; retrieved time is not freshness.

## 13. Session/night-session caveats
`TradingSession` is present but label mapping and night-session behavior require adapter validation.

## 14. Non-trading-day/emergency closure behavior
Weekend and emergency closure handling uses expected latest TAIFEX trade date without forcing equality to TWSE/TPEx.

## 15. Normalized schema decision
`m8b_taifex_derivatives_eod_observation.v1` is accepted with caveats.

## 16. Fixture/test strategy
Compact sanitized fixtures cover normal, partial, duplicate, mixed-date, invalid numeric, invalid identity, empty, and schema drift cases.

## 17. Boundary preservation
No production adapter, runtime fetch, scheduler, polling, startup fetch, DB write, server/frontend/MCP change, TAIFEX_MIS, Yahoo, FinMind, model call, or recommendation wording is added.

## 18. Readiness decision
Futures daily EOD is `go`; options daily EOD and final settlement are `conditional_go` pending parser validation of identity/session labels.

## 19. Caveats
Endpoint semantics depend on observed official fields; options identity requires additional validation; session semantics may be endpoint-specific; no production adapter in M8B-00; no TAIFEX_MIS; no historical backfill; no recommendation engine.

## 20. Next PR blueprint
Proceed to M8B-01 adapters and context integration using `docs/protocol/M8B_01_TAIFEX_OPENAPI_IMPLEMENTATION_BLUEPRINT.md`.
