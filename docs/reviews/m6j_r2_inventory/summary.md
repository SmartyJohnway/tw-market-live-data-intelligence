# M6J-R2 Test Risk Inventory Summary

Static analysis is advisory and does not prove semantic equivalence by itself.

- Test functions detected: 637
- Duplicate clusters detected: 439
- safe_to_auto_retire clusters: 0
- manual_review_required clusters: 101
- P0 clusters: 11
- P1 clusters: 47
- P2 clusters: 23
- P3 clusters: 358

## Risk tag distribution
- unknown: 257
- frontend_static_contract: 79
- frontend_public_write: 65
- ai_context_pack: 57
- conversation_context: 56
- research_generated_write: 44
- m5f_canonical: 43
- m5c_staging: 43
- m5b_staging: 36
- mcp_fail_closed: 33
- m5e_publication: 29
- production_prod_write: 27
- snapshot_schema: 24
- bounded_watchlist: 21
- governance_path: 21
- source_health: 19
- ssl_policy: 18
- no_trading_semantics: 16
- no_full_market_scan: 13
- fastapi_execute_confirmation: 11
- m6g_browser_e2e: 11
- briefing_render: 9
- raw_payload_leakage: 9
- m6e_acceptance: 7
- invalid_ssl_fail_closed: 7
- forbidden_behavior: 7
- observation_not_canonical: 3

## Largest duplicate-risk clusters
- mcp_fail_closed:asyncio_run:equals (14): static cluster overlap needs human semantic review
- unknown:generate_symbol_observations:contains (7): static cluster overlap needs human semantic review
- unknown:load:equals (7): static cluster overlap needs human semantic review
- unknown:any:contains+equals (6): static cluster overlap needs human semantic review
- unknown:copy_candidate:contains (6): static cluster overlap needs human semantic review
- unknown:datetime:contains+equals (6): static cluster overlap needs human semantic review
- unknown:datetime_now:contains+truthy (6): static cluster overlap needs human semantic review
- frontend_static_contract:read_text:contains (5): static cluster overlap needs human semantic review
- m5b_staging:codes:contains (5): static cluster overlap needs human semantic review
- research_generated_write:any:equals (5): static cluster overlap needs human semantic review
