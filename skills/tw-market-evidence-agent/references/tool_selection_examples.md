# Prompt-neutral tool-selection examples

| User intent | Selected capabilities | Sufficiency | Important semantics | Next evidence step |
|---|---|---|---|---|
| 台積電現在多少？ | `resolve_market_targets`, `get_current_market_evidence` | sufficient_with_caveats | live-ish/retrieved observation; not guaranteed zero-latency realtime | Add EOD reference if comparing with prior close. |
| 台積電今天跟昨日收盤相比如何？ | `resolve_market_targets`, `get_current_market_evidence`, `get_official_eod_reference` | sufficient_with_caveats | align intraday snapshot with official prior close | disclose retrieval time and source time if available. |
| 台積電近20日漲多少？ | `resolve_market_targets`, `get_price_performance_evidence` | sufficient_with_caveats | unadjusted price return, not total return | dividend-adjusted evidence for total return. |
| 台積電為什麼今天跌？ | `get_current_market_evidence`, `identify_required_additional_evidence` | requires_additional_evidence | price movement can be established; cause needs event evidence | MOPS, issuer announcement, timestamped news. |
| Based on the evidence, should I buy? | current/EOD/performance evidence plus `identify_required_additional_evidence` | sufficient_with_caveats or requires_additional_evidence | recommendation is not globally prohibited; disclose evidence, horizon, uncertainty, missing fundamentals/news | valuation, financial statements, portfolio suitability, risk evidence. |
