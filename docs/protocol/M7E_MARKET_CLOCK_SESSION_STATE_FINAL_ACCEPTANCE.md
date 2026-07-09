# M7E Market Clock and Session State Final Acceptance

Status:
- pass_with_caveats

Completed tasks:
- M7E-00 policy/schema
- M7E-01 pure builder
- M7E-02 controlled promotion
- M7E-03 shared context integration
- M7E-04 final acceptance and inventory closure

Upstream baseline:
- PR #105 merge commit: bb95c3f47479394c4adf519b8aa7f964d8d76fbc

Final capability:
- M7E provides governed market-clock/session-state semantics for AI conversation context.
- M7E distinguishes live_candidate, recent_but_unverified, reference_only, not_current, and degraded_unknown cases.
- M7E prevents AI from treating stale/postclose/weekend/holiday/unknown observations as unconditional current intraday movement.

Accepted artifacts:
- docs/protocol/M7E_MARKET_CLOCK_SESSION_STATE_POLICY.md
- scripts/market_clock_session_state.py
- scripts/m5k_common.py shared context integration
- scripts/build_m5n_conversation_context.py deterministic pass-through support
- tests/unit/test_m7e_market_clock_session_state_*.py
- docs/data_capabilities/twse_mis_rich_field_inventory.json

Acceptance criteria:
- builder output remains not AI-safe
- controlled promotion output is AI-safe
- malformed candidates fail closed
- shared conversation context includes promoted market_clock_session_state
- markdown handoff includes Market Clock / Currentness
- AI guidance summary includes currentness guardrails
- M7B/M7C/M7D context remains preserved
- no raw payload/rich facts/full ladder arrays exposed
- no TWSE holidaySchedule runtime fetch
- no live probe
- no FastAPI/MCP/frontend changes
- no trading signal/recommendation/target/support/resistance/capital-flow/full-market-breadth claims

Known caveats:
- M7E is not an official full exchange calendar engine.
- If holiday schedule records are not supplied, M7E uses weekday heuristic and must preserve the holiday-confidence caveat.
- M7E does not provide real-time SLA.
- M7E does not fetch TWSE holidaySchedule at runtime.
- M7E does not validate all special trading sessions.
- M7E contextualizes currentness; it does not create observations.
- M7E contextualizes observations; it does not produce trading advice.

Final decision:
- pass_with_caveats

Next recommended task:
- M7F-FRONTEND-OPERATOR-PRESENTATION-AND-CONTEXT-WORKBENCH

## Post-acceptance M7E-05 insertion

After M7E-04 final acceptance, M7E-05 was inserted before M7F to establish a formal TWSE trading-calendar authority. This does not invalidate M7E-04; it strengthens the calendar-confidence layer before frontend/operator presentation.
