# M3F-02 Frontend Browser Smoke Test and Screenshot QA

## 1. Final Status
`M3F_02_COMPLETED_WITH_CAVEATS_READY_FOR_M3F_03`

## 2. Baseline Merge SHA
PR #29 merged SHA: `0bdd2f3e60e6d244fb95b26f90dd35c0044eaecc`

## 3. Files Changed
- `frontend/public/market-context.html` (Added CSS word-break rule for mobile layout).
- `docs/reviews/M3F_02_FRONTEND_BROWSER_SMOKE_TEST_AND_SCREENSHOT_QA.md` (This report).
- Added `docs/reviews/screenshots/m3f_02/m3f_02_desktop_top.png`
- Added `docs/reviews/screenshots/m3f_02/m3f_02_desktop_bottom.png`
- Added `docs/reviews/screenshots/m3f_02/m3f_02_mobile_top.png`
- Added `docs/reviews/screenshots/m3f_02/m3f_02_mobile_bottom.png`

## 4. Static Server Command Used
`python -m http.server 8000`

## 5. Browser / Automation Environment Used
Python Playwright (`playwright.sync_api` Chromium headless).

## 6. Viewports Tested
- Desktop: `1440x1000`
- Mobile: `390x844`

## 7. Console Error Summary
- No uncaught JavaScript exceptions occurred on normal load.
- Simulated missing artifact loads correctly threw standard "Failed to fetch" exceptions.

## 8. Network Request Summary
All network requests were correctly constrained to local serving:
- `http://localhost:8000/frontend/public/market-context.html`
- `http://localhost:8000/research/generated/ai_context_pack.json`
- `http://localhost:8000/research/generated/chatgpt_briefing.md`
No requests to TWSE, Yahoo, TPEx, external broker APIs, CDNs, or package registries were observed.

## 9. Screenshot QA Summary
Screenshots were captured successfully using Playwright for both desktop and mobile viewports.
The layout rendered gracefully, with panels aligning nicely under standard DOM constraints.
Screenshots demonstrate that all required artifact sections (Artifact Load Status, Health, Snapshot, Failed Sources/Targets, and AI Briefing) are visible without breaking out of bounds.

## 10. Functional QA Summary
- The `<details open>` help panel is open by default and can be closed/reopened.
- Copy AI Briefing button: Works locally with clipboard permissions, successfully updates status to "Copied." However, note that in restricted headless environments without granted clipboard permissions, it degrades safely with an internal error handler.
- Table layout: Failed sources and targets wrap gracefully, overflowing horizontally without clipping screen edges.
- Text overflow handling works successfully.
- Required explicit safety wording is visually rendered perfectly in the DOM.

## 11. Failure-Mode QA Summary
Failure modes were tested using Playwright's `route.abort()` route interception (simulating 404/failure) to maintain repo file cleanliness.

1. `ai_context_pack.json` missing:
   - A critical full-page error (`#error-container`) appears, properly rendering paths to the root and static serving command.
   - Normal page UI correctly hidden.
2. `chatgpt_briefing.md` missing:
   - Page loads normally but `#status-briefing` reads as `unavailable`.
   - `#briefing-content` preview renders: "Unavailable (../../research/generated/chatgpt_briefing.md failed: Failed to fetch)".

## 12. Frontend Repairs Made
- **Mobile Layout Fix:** I added `word-break: break-word;` to `ul.no-bullets li` and `#mandatory-caveats li` inside `market-context.html`. Without this, very long contiguous strings (like `official_openapi_sources_are_eod_reference_only`) in the mandatory caveats list ran horizontally past the panel container boundary on narrow mobile viewports.

## 13. Artifact Modification Confirmation
No generated artifacts in `research/generated/*` were modified or moved during the review.

## 14. Probe/Generator Confirmation
No live probes or generation scripts were run during the review.

## 15. Validation Commands and Results
```bash
$ python -m compileall scripts server tests && python -m pytest -m "not network" -v
```
**Results:** Compiled flawlessly. Pytest suite ran with 102 passed, successfully skipping network tests.

## 16. Static Grep Check Results
```bash
$ grep -nE "cdn|react|vue|tailwind|run_all_probes|generate_latest_market_snapshot|generate_ai_context_pack|innerHTML" frontend/public/market-context.html
```
**Results:** Returned entirely empty. No restricted frameworks, CDNs, Python CLI wrappers, or dangerous `innerHTML` functions were found.

## 17. Remaining Caveats
- Bounded Watchlist constraint applies; UI enforces strictly descriptive data.
- Headless copy capabilities behave differently than interactive GUI copying due to `navigator.clipboard` permissions, but failure pathways degrade predictably.

## 18. Recommended Next Milestone
`M3F-03-FRONTEND-READONLY-RELEASE-CANDIDATE-POLISH`
