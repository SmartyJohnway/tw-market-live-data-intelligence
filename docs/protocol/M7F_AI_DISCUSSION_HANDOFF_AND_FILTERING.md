# M7F-05/06 AI Discussion Handoff, Rich Fact Selection, Search, and Filters

Status:
- ai_handoff_selection_search_filters_defined

Purpose:
- Add operator-controlled rich fact selection.
- Add search, filters, and field grouping to the rich fact browser.
- Generate safe AI discussion handoff previews from selected displayable fields.
- Preserve raw-forbidden and no-trading-advice boundaries.

Implemented UI additions:
- Symbol/name search
- Field group filter
- Confidence filter
- Exposure filter
- Currentness filter
- Show/hide caveated fields toggle
- Field selection controls
- Safe Markdown handoff preview
- Safe JSON projection preview
- Explicit copy buttons
- Field grouping display

Data policy:
- Static/read-only in this PR.
- Uses static safe demo projection only.
- No live data loading.
- No real artifact loading.
- No manual refresh.
- No auto refresh.
- No hidden fetch.
- No FastAPI/MCP changes.
- No backend API changes.
- No AI/model call.

Selection policy:
- Only fields with display_allowed=true, ai_handoff_allowed=true, raw_forbidden=false may enter AI handoff.
- Raw forbidden fields are never selectable.
- Raw forbidden values are never copied.
- Handoff includes currentness/calendar caveats and governance guardrails.

Semantic policy:
- Handoff is for AI discussion context only.
- Handoff is not trading advice.
- Handoff is not a recommendation.
- Handoff is not a trading signal.
- Handoff is not a market prediction.
- No full-market breadth, capital flow, sector rotation, support/resistance, or target-price claims.

Rendering policy:
- DOM API / textContent only.
- No unsafe innerHTML.
- Copy buttons require explicit user action.

Next task:
- M7F-07-08-FRONTEND-SECURITY-SEMANTIC-REGRESSION-AND-FINAL-ACCEPTANCE
