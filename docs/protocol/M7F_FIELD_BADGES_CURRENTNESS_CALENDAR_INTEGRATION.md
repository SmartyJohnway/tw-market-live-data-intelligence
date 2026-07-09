# M7F-03/04 Field Badges, Currentness, and Calendar Integration

Status:
- field_badges_currentness_calendar_integrated

Purpose:
- Add field-level confidence / exposure / caveat badges to the rich fact browser.
- Add currentness and trading-calendar authority displays.
- Clarify how to interpret rich facts without turning them into trading signals.

Implemented UI additions:
- Field confidence badges
- Exposure class badges
- Caveat badges
- Currentness status panel
- Trading-calendar authority panel
- Badge legend

Currentness labels:
- live_candidate
- recent_but_unverified
- reference_only
- not_current
- degraded_unknown

Calendar authority labels:
- controlled_twse_holiday_schedule_artifact
- weekday_heuristic_only
- artifact_missing_date
- trading_day
- non_trading_day
- unknown

Data policy:
- Static/read-only in this PR.
- No live data loading.
- No manual refresh.
- No auto refresh.
- No hidden fetch.
- No FastAPI/MCP changes.
- No frontend-side trading-day inference.

Semantic policy:
- Badges describe data state and field confidence.
- Badges are not trading signals.
- Badges are not recommendations.
- Badges are not market predictions.
- No full-market breadth, capital flow, sector rotation, support/resistance, or target-price claims.

Rendering policy:
- DOM API / textContent only.
- No unsafe innerHTML.
- Raw forbidden fields are not rendered.

Next task:
- M7F-05-06-AI-DISCUSSION-HANDOFF-RICH-FACT-SELECTION-SEARCH-AND-FILTERS
