# M8B-01 TAIFEX OpenAPI official derivatives EOD final acceptance

## 1. Purpose
Implement controlled, source-governed TAIFEX OpenAPI derivatives EOD/statistical/reference context for AI conversation.

## 2. Accepted upstream
M8 source governance, M8 context builders, M8A official EOD currentness, emergency closure evidence, and M8B-00 endpoint preflight contracts.

## 3. Implemented endpoints
DailyMarketReportFut, DailyMarketReportOpt, FinalSettlementPrice, OpenInterestOfLargeTradersFutures, OpenInterestOfLargeTradersOptions, PutCallRatio, and BlockTrade.

## 4. Runtime execution contract
Execution requires explicit operator confirmation, requested contexts, bounded products/contracts where required, and no scheduler, polling, startup fetch, DB write, persistent cache, model call, credentials, cookies, or browser automation.

## 5. Futures EOD adapter
DailyMarketReportFut normalizes official futures daily rows with price, activity, open-interest, session, provenance, currentness, and bounded retention.

## 6. Options EOD adapter
DailyMarketReportOpt normalizes bounded option identities using product, contract month/week, strike, option type, session, and trade date. Source Close maps to `price.close`; SettlementPrice maps to `price.settlement`.

## 7. Final settlement adapter
FinalSettlementPrice is projected as official final settlement reference, not daily settlement and not current market price.

## 8. Large-trader futures OI adapter
OpenInterestOfLargeTradersFutures is normalized as large trader open-interest concentration with top-5/top-10 and market OI fields.

## 9. Large-trader options OI adapter
OpenInterestOfLargeTradersOptions adds strict option CallPut identity mapping and preserves concentration semantics.

## 10. Put/Call Ratio adapter
PutCallRatio preserves source-reported percentage strings and integer counts. Ratios are not divided by 100 and are not sentiment labels.

## 11. BlockTrade adapter
BlockTrade supports factual aggregate row context. Futures `-` strike/call-put is not applicable; options require strike and option type.

## 12. Normalized observation families
Implemented families: official_derivatives_futures_eod_reference, official_derivatives_options_eod_reference, official_derivatives_final_settlement_reference, official_derivatives_large_trader_open_interest_reference, official_derivatives_put_call_ratio_reference, and official_derivatives_block_trade_reference.

## 13. Contract identity rules
Futures identity is trade date, product, contract month/week, and session. Options identity also includes strike and option type. Final settlement identity uses final settlement day, delivery month, and product. Put/Call Ratio identity is aggregate source/context/trade date. BlockTrade identity is aggregate row identity, not transaction ID.

## 14. Price/settlement/close semantics
Futures Last remains last. Options Close remains close and is not fabricated as last. Daily SettlementPrice remains daily settlement. FinalSettlementPrice remains expiry final settlement reference.

## 15. Quotation-unit handling
Quotation unit remains `product_specific_quote_unit`; settlement currency and contract multiplier remain null until product-level metadata is validated.

## 16. Volume/open-interest semantics
Volume and open-interest values are non-negative integer counts. Zero values may be valid when identity and date are valid.

## 17. Session handling
Validated `一般` maps to regular. Unknown labels are retained as source labels with `session_semantics_unresolved` caveat.

## 18. Currentness behavior
Daily/statistical rows now use source-specific TAIFEX derivatives currentness evaluation from the operator-supplied `evaluation_time_asia_taipei`, with weekend/closure-aware expected-date resolution where evidence is valid. TAIFEX dates are not forced to match TWSE/TPEX dates. Final settlement records use final-settlement reference currentness.

## 19. Emergency closure behavior
NCDR/DGPA evidence may support expected-date explanation, but the implementation does not assume TAIFEX closures are identical without source-specific evidence.

## 20. Bounded retention
Whole endpoints may be fetched where no filters exist, but retained observations are bounded to requested scopes.

## 21. Raw payload policy
Full raw endpoint payloads are not retained or projected.

## 22. Context integration
TAIFEX_OPENAPI observations coexist with TWSE_MIS, TWSE_OPENAPI, and TPEX_OPENAPI in M8 multi-source context without source ID collision.

## 23. Conversation projection
Conversation context has TAIFEX-family factual projections for futures, options, final settlement, large-trader OI concentration, Put/Call Ratio, and BlockTrade. It preserves source labels and factual fields, prevents realtime wording for official EOD/reference data, and includes no recommendation or trading signal output.

## 24. Manual live validation
`scripts/validate_m8b_taifex_openapi_live.py` performs explicit `--confirm` bounded validation and prints compact sanitized summaries.

## 25. Test coverage
Deterministic no-network tests cover observation helpers, seven adapter families, source-specific currentness, schema drift versus no-match behavior, completion rules, exception-safe execution, context integration, conversation projection, and acceptance.

## 26. Source registry/inventory closure
TAIFEX_OPENAPI is marked controlled runtime executable with bounded retained scope, no raw payload exposure, and no trading signal/recommendation permission.

## 27. Boundary preservation
No TAIFEX_MIS, Yahoo, FinMind, scheduler, polling, startup fetch, DB write, persistent cache, model call, frontend expansion, MCP expansion, backtesting, strategy, or recommendation logic was added.

## 28. Caveats
Product-level quotation units remain unresolved; session/night-session labels may be incomplete; options Close remains close semantics; TAIFEX trading calendar OpenAPI remains unresolved; ContractAdj/productsExemptedAH are not implemented; no TAIFEX_MIS, historical backfill, automated refresh, DB persistence, institutional-investor endpoint, or recommendation engine is added.

## 29. Final result
m8b_01_taifex_openapi_official_derivatives_eod_context_pass_with_caveats

## 30. Next recommended track
Add product metadata/quotation-unit validation and TAIFEX-specific trading calendar evidence before expanding currentness precision or derivative product labeling.
