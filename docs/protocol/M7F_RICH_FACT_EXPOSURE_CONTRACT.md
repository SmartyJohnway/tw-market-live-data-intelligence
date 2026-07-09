# M7F Rich Fact Exposure Contract

Status:
- exposure_contract_defined

Exposure classes:
- operator_display_allowed
- ai_handoff_allowed
- operator_only
- caveated_display_allowed
- structured_display_candidate
- raw_forbidden
- future_review_required

Confidence levels:
- official_source_field
- project_validated
- source_observed
- semantic_inferred
- unit_caveat
- currentness_dependent
- calendar_authority_dependent
- unknown_or_unclassified
- raw_forbidden

Display scopes:
- operator_browser
- ai_handoff
- governance_panel
- source_health_panel
- currentness_panel
- hidden_raw

Field groups:
- identity
- source
- timestamp
- price_quote
- price_change
- volume_trading
- market_state
- rich_observation
- deterministic_metrics
- bounded_watchlist_context
- market_clock_currentness
- trading_calendar_authority
- source_health
- caveats_governance
- raw_forbidden

Rules:
- operator_display_allowed fields may appear in the rich fact browser.
- ai_handoff_allowed fields may be copied into AI discussion summaries.
- operator_only fields may be displayed to humans but excluded from AI handoff.
- caveated_display_allowed fields must show caveats inline.
- structured_display_candidate fields require future controlled rendering before display.
- raw_forbidden fields must not be displayed or copied.
- unknown_or_unclassified fields must not be silently hidden forever; they should be routed to future review.
- Do not mark all uncertain fields raw_forbidden. Unknown fields should be future_review_required unless they are raw payloads.
