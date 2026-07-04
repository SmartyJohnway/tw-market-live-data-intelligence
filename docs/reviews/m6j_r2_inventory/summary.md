# M6J-R2 Test Risk Inventory Summary

Static analysis is advisory and does not prove semantic equivalence by itself.

- Test functions detected: 636
- Duplicate clusters detected: 620
- safe_to_auto_retire clusters: 0
- manual_review_required clusters: 11

## Risk tag distribution
- mcp_fail_closed: 209
- invalid_ssl_fail_closed: 203
- frontend_static_contract: 181
- frontend_public_write: 142
- m5b_staging: 130
- snapshot_schema: 112
- observation_not_canonical: 93
- unknown: 85
- bounded_watchlist: 81
- fastapi_execute_confirmation: 75
- m5c_staging: 63
- m5e_publication: 63
- ai_context_pack: 57
- production_prod_write: 54
- governance_path: 53
- m5f_canonical: 51
- ssl_policy: 30
- conversation_context: 27
- research_generated_write: 26
- no_trading_semantics: 24
- briefing_render: 23
- source_health: 15
- no_full_market_scan: 15
- raw_payload_leakage: 12
- m6g_browser_e2e: 11
- m6e_acceptance: 7
- forbidden_behavior: 7

## Largest duplicate-risk clusters
- invalid_ssl_fail_closed:assert:8b0002c9c02c (5): static cluster overlap needs human semantic review
- fastapi_execute_confirmation:assert:8b0002c9c02c (3): static cluster overlap needs human semantic review
- unknown:no_assert:_assert_probe_envelope_first_row_freshness (3): static cluster overlap needs human semantic review
- bounded_watchlist:assert:fce22b4b2569 (2): static cluster overlap needs human semantic review
- frontend_public_write:assert:40c836ea8217 (2): static cluster overlap needs human semantic review
- m5c_staging:assert:924bf332c236 (2): static cluster overlap needs human semantic review
- m5f_canonical:no_assert:Path;build_package;pytest.raises;write_package (2): static cluster overlap needs human semantic review
- snapshot_schema:no_assert:Draft202012Validator.check_schema;load (2): static cluster overlap needs human semantic review
- unknown:assert:4c09a7f74a0c (2): static cluster overlap needs human semantic review
- unknown:assert:4c56f6835c0a (2): static cluster overlap needs human semantic review
