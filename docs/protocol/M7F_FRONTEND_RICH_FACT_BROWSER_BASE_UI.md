# M7F-02 Frontend Rich Fact Browser Base UI

Status:
- base_ui_defined

Purpose:
- Add the first read-only frontend rich fact browser.
- Render governed rich facts according to the M7F display catalog policy.
- Confirm M7F is not summary-only.
- Confirm no trading advice and no raw payload exposure.

Implemented UI sections:
- Operator status header
- Rich fact browser table
- Per-symbol governed field details
- Governance/caveat panel
- Raw forbidden omission notice

Data policy:
- Static/read-only.
- Demo safe projection is not live data.
- No live probe.
- No auto refresh.
- No hidden fetch.
- No FastAPI/MCP changes.
- No raw payload exposure.

Rendering policy:
- DOM API / textContent only.
- No unsafe innerHTML.
- Raw forbidden fields are not rendered.
- Displayable project-validated/source-observed fields are shown with provenance/confidence/caveats where available.

Next task:
- M7F-03-04-FIELD-BADGES-CURRENTNESS-AND-CALENDAR-INTEGRATION
