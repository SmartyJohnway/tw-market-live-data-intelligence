# M2C-01 Completion Report

## 1. Final Status
**Status**: `M2C_01_COMPLETED`

## 2. Files Changed
* `scripts/probe_yahoo.py`: Added explicit known unsupported placeholders classification for HTTP 404s, added safety checks for missing `chart.result` objects.
* `tests/unit/test_yahoo_probe_classification.py`: Added comprehensive unit tests for offline verification of the Yahoo probe logic.
* `docs/protocol/YAHOO_FINANCE_CHART_PROTOCOL.md`: New file detailing protocol mechanics and source classification.
* `docs/protocol/YAHOO_FINANCE_SYMBOL_COVERAGE.md`: New file outlining expected target coverage.
* `docs/source_catalog.md`, `docs/capability_matrix.md`, `frontend/public/matrix.json`, `research/generated/ai_context_pack.md`, `research/generated/ai_context_pack.json`, `research/probe_log.md`: Auto-updated by probe generator.

## 3. Validation Commands Executed
* `python -m pip install -r requirements.txt` (to install requests, responses dependencies)
* `python -m compileall scripts server tests` (passed successfully)
* `python3 -m pytest -m "not network" -v` (passed successfully: 33 passed)
* `python3 scripts/run_all_probes.py` (passed successfully)

## 4. Terminal Output Summary
The local test suite (`pytest -m "not network"`) completed successfully with 33 passed tests, highlighting 6 new specific fixtures targeting the updated Yahoo probe behaviors for success, expected failures, known unsupported fallbacks, and boundary network errors. `run_all_probes.py` correctly identified `TX.TW` and `FUNDA.TW` as `unsupported_targets` rather than raising hard code errors, demonstrating that Yahoo probe coverage behavior handles missing proxy assets elegantly.

## 5. Yahoo Chart Protocol Summary
The underlying endpoint `query1.finance.yahoo.com/v8/finance/chart/{symbol}` has been thoroughly documented in `docs/protocol/YAHOO_FINANCE_CHART_PROTOCOL.md`. It highlights the necessity of HTTP 404 fallback handling, the standard output JSON structure containing `chart.result`, and standard usage caveats indicating that the API operates off delayed UTC epochs within an unofficial capacity.

## 6. Yahoo Source Semantics Summary
Yahoo Finance operates under a `third_party_public_chart_endpoint` classification acting as an `unofficial_api`. It must never be used to represent an official TWSE or TPEx source. Due to unpredictable latency, HTTP 429 rate limit triggers, and missing execution-grade integrity guarantees, it is uniquely suited only to provide supplementary historical watchlist and chart data.

## 7. Taiwan Symbol Coverage Summary
The `docs/protocol/YAHOO_FINANCE_SYMBOL_COVERAGE.md` file covers standard asset semantics. Explicit TWSE/TPEx suffix classifications (`.TW`, `.TWO`) are listed as successfully supported, indices map with a caret prefix (`^`), and proxy/fund assets (futures) have been classified correctly as explicitly unsupported to prevent error noise.

## 8. Failure Classification Summary
The implementation separates structural or logical failures from known unsupported coverage. A hardcoded set of placeholders (`KNOWN_UNSUPPORTED_YAHOO_PLACEHOLDERS = {"TX.TW", "FUNDA.TW"}`) now ensures that anticipated HTTP 404 targets transition cleanly into `unsupported_targets` instead of logging generic `failed_targets` or parser crashes. Broad structural errors, timeout exceptions, and unrecognized 404s still appropriately elevate to `failed_targets`.

## 9. Tests Added
The new suite at `tests/unit/test_yahoo_probe_classification.py` uses the `responses` package to cleanly mock network logic. Tests assert:
1. Valid chart response parses successfully.
2. Known unsupported placeholder (e.g., `TX.TW`) returns 404 and goes to `unsupported_targets`.
3. Expected supported symbol returning 404 goes to `failed_targets`.
4. Empty `chart.result` does not crash the parser.
5. Missing quote arrays evaluate without exceptions.
6. Network/request exceptions fall back gracefully to `failed_targets`.

## 10. Remaining Caveats
* The list of explicitly unsupported assets is statically defined (`TX.TW`, `FUNDA.TW`) within `probe_yahoo.py`. A dynamic config check could handle larger datasets but was restricted per scope directives.
* `.TWO` symbols require explicit mappings from `otc_` namespaces externally.

## 11. Deferred M3/M4 Items
The following M3/M4 scopes were correctly avoided:
**M3**:
* AI context pack v2
* `latest_market_snapshot.json`
* `chatgpt_briefing.md`
* Market-session-aware AI narrative

**M4**:
* MCP server refactor
* Schedulers, alerts, public proxy integrations, and active full-market scanning.

## 12. Recommendation For Next Milestone
The immediate next milestone should likely be `M2C-02-YAHOO-FINANCE-NORMALIZED-CHART-CONTRACT-AND-TESTS`, building upon the parsed protocol metadata to establish a hardened normalized data model for specific chart series components.
