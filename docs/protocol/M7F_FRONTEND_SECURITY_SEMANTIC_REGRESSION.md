# M7F-07 Frontend Security and Semantic Regression

Status:
- frontend_security_semantic_regression_pass_with_caveats

Purpose:
- Verify M7F frontend security boundaries.
- Verify M7F semantic guardrails.
- Verify rich fact browser / operator workbench / AI discussion handoff remains static, governed, and non-trading.

Security regression coverage:
- No unsafe innerHTML in M7F section.
- No insertAdjacentHTML in M7F section.
- No document.write.
- No eval.
- No new Function.
- No external scripts/CDN dependencies.
- No JS framework/build step.
- No hidden fetch.
- No auto refresh.
- No polling.
- No WebSocket/EventSource/XMLHttpRequest.
- No backend/API/MCP hook in M7F section.
- Clipboard write only occurs through explicit operator click.

Raw exposure regression coverage:
- raw_payload values are not rendered.
- twse_mis_rich_facts raw object is not rendered.
- raw_unknown_facts are not rendered.
- full_ladder values are not rendered.
- bid_prices / ask_prices arrays are not rendered.
- source_investigation_notes values are not rendered.
- raw forbidden fields are not selectable.
- raw forbidden values are not copied.

Semantic regression coverage:
- No trading advice.
- No buy/sell/hold recommendation.
- No target price.
- No support/resistance.
- No capital flow.
- No sector rotation.
- No full-market breadth.
- No bullish/bearish language.
- No ranking/top movers/strongest/weakest UI.
- No frontend-side trading-day inference.
- No AI/model call.

Known caveats:
- Static safe demo projection only.
- No real artifact loading.
- No manual refresh.
- No browser screenshot captured in this environment.
- browser_e2e_screenshot_captured = false
- reason = Playwright/browser not available in current environment
- not_blocking_because = static DOM/security/unit regression coverage is present
- No Python 3.11 optional run if interpreter/dependencies are unavailable.

Result:
- pass_with_caveats
