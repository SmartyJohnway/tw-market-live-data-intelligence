# M7B AI-safe market context final acceptance

Status:
- pass_with_caveats

Completed tasks:
- M7B-00 readiness / scope / policy
- M7B-01 AI-safe projection schema
- M7B-02 pure projection builder
- M7B-03 fixtures and safety tests
- M7B-04 controlled exposure integration
- M7B-05 compatibility hardening
- M7B-06 final acceptance / closure

Merged PR references:
- PR #95
- PR #96
- this PR

Dependency:
- M7A completed as pass_with_caveats

Runtime behavior:
- M7A TWSE_MIS observations continue to include twse_mis_rich_facts.
- Raw twse_mis_rich_facts remain not safe for AI context.
- M7B controlled projection is exposed only through policy-gated conversation context.
- Latest observation payload is not mutated by M7B exposure.
- Watchlist rows are not changed by M7B exposure.
- Source-health behavior is not changed by M7B exposure.

AI exposure:
- M7B projection safe_for_ai_context=true only after controlled promotion.
- M7A rich facts safe_for_ai_context=false.
- raw_rich_facts_exposed=false.
- full_ladder_exposed=false.
- not_trading_signal=true.
- not_recommendation=true.

Compatibility:
- FastAPI conversation context checked.
- MCP conversation context checked.
- frontend/watchlist checked.
- source-health checked.
- latest observation checked.
- non-TWSE sources checked.

Caveats:
- no official public TWSE MIS API field dictionary
- no realtime SLA
- quantity units remain unverified
- displayed depth remains displayed-depth snapshot only
- not full order book
- not true liquidity
- not support/resistance
- not trading signal
- not recommendation
- odd-lot semantics not fully runtime-integrated

No-go confirmations:
- no live probe in M7B-04/M7B-05/M7B-06
- no new probe output committed
- no latest_summary.json committed
- no cookies/headers/session tokens committed
- no raw browser payload committed
- no buy/sell/hold/target-price language introduced

Final decision:
- M7B accepted as pass_with_caveats

Recommended next track:
- M7C-DETERMINISTIC-METRICS-LAYER
- Scope: deterministic calculations such as change, change_percent, intraday_range, displayed_spread, and displayed bid/ask depth ratios.

Note:
- Future source timing / authority governance belongs to a later M8 preflight or M8 official-reference-source workstream, not immediate M7C.
