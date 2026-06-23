# M3G Source Recovery Plan

## 1. Source Recovery Principles

1. **Safety First**: No live probes or network requests are executed without explicit prior authorization in a dedicated milestone.
2. **Offline Resilience**: Generators must remain fully functional in offline environments. If inputs are missing, they should gracefully produce empty valid contracts rather than crashing.
3. **Deterministic Testing**: Recovery of sources must begin with deterministic, local mock fixtures to prove parsing and contract normalization logic before any live endpoint is queried.
4. **Iterative Authorization**: Live probes will be re-enabled through a strictly governed authorization ladder, moving from mock tests to bounded live probes, to broader refresh automation.

## 2. Strict No-Investment-Advice Boundary

The recovery of market data sources must adhere to a strict "no investment advice" boundary:
- This system is an operational and research workbench.
- No trading signals, recommendations (buy/sell/hold), rankings, or target prices may be generated or implied.
- The data fetched is strictly raw material to evaluate AI interpretability, not to inform trading strategies.

## 3. Bounded Watchlist-Only Boundary

- Market data retrieval and generation are strictly bounded to the explicitly configured watchlist in `config/market_targets.json`.
- Full-market sweeps are explicitly prohibited in the current phase to minimize risk, rate-limit exposure, and resource consumption.

## 4. Official vs. Unofficial vs. Third-Party Authority Rules

- **Official Public Exchange EOD**: `TWSE_OpenAPI`, `TPEx_OpenAPI`. These are the highest authority but only provide End-Of-Day (EOD) data. They must never be labeled as real-time.
- **Unofficial Frontend Endpoint**: `TWSE_MIS`. This provides candidate intraday live data but is unofficial, fragile, and prone to breaking. It requires strict rate limiting and error handling.
- **Third-Party API**: `Yahoo_Finance`, `FinMind`. These sources provide additional context but carry third-party risk. They are not official exchange authorities and must carry appropriate caveats.
- **Broker Authenticated**: `Fugle`, `Fubon`. These are completely deferred in the current scope as they require authentication or broker execution logic, which violates current project boundaries.

## 5. EOD vs. Live Candidate Labeling Rules

- A source is only a **live_candidate** if it has the potential to provide intraday updates (e.g., `TWSE_MIS`).
- A source must be explicitly labeled as **eod_reference** if it operates on daily batch updates (e.g., `TWSE_OpenAPI`, `TPEx_OpenAPI`).
- EOD sources must never have their `freshness_status` marked as anything implying intraday freshness (e.g., `realtime`).

## 6. Mock Fixture Recovery Plan

To safely recover the pipeline without violating network boundaries, a mock fixture strategy is required:

- **Location**: Mock files will reside in `tests/fixtures/market_sources/`.
- **Target Subsets**: Minimum initial coverage must include: `2330`, `0050`, `00929`, `8069`, `TAIEX` (mapped to specific source formats).
- **Generator Integration**: Production generator scripts will remain unchanged by default. For testing, specific function parameters or test-only configuration (e.g., `pytest monkeypatch`) will be used to inject the mock fixtures. Automatic environment-variable-driven changes in production are discouraged.
- **Validation**: Test suites must run entirely offline, validating that the parsed output against these fixtures correctly populates the final contract schemas without producing empty arrays (unless intentionally testing failures).
- **Frontend Revalidation**: To use mock-generated artifacts in the frontend without committing fake production artifacts, mock artifacts should be generated into a temporary directory during automated tests, or served directly via the backend API during tests, leaving `research/generated/` strictly for true production snapshots.

## 7. Controlled Live Probe Preflight Requirements

For future controlled live probes, the following policies apply to the candidates (`TWSE_MIS`, `Yahoo_Finance`, `TWSE_OpenAPI`, `TPEx_OpenAPI`):

1. **endpoint family**: REST/HTTP GET endpoints specific to the target source.
2. **expected request shape**: Standard HTTP GET requests with necessary query parameters (e.g., symbols, timestamps).
3. **expected response shape**: JSON (or CSV/HTML for legacy) corresponding to the source's protocol documentation.
4. **target symbol subset**: Strictly limited to the configured watchlist (e.g., `2330`, `0050`, `00929`, `8069`, `TAIEX`).
5. **timeout policy**: Strict short timeouts (e.g., 5-10 seconds) to prevent hanging requests.
6. **retry policy**: Minimal retries (1-2) with exponential backoff to respect rate limits.
7. **rate limit policy**: Mandatory delays between requests to unofficial endpoints (e.g., `TWSE_MIS`).
8. **local raw payload storage policy**: Optional caching during tests, but production probes should not persist raw payloads unless debugging.
9. **redaction policy**: Remove any IP addresses or API keys from logs and generated artifacts.
10. **failure classification**: Network errors must map to specific failure reasons (e.g., `connection_error`, `timeout`) and correctly set `offline_mode` or similar caveats.
11. **allowed generated outputs**: Valid capability matrix artifacts, snapshots, and context packs populated with observed data.
12. **prohibited outputs**: Trading signals, recommendations, rankings, target prices, broker actions, full-market claims, or official realtime guarantee claims.

## 8. Controlled Live Probe Authorization Ladder

The recovery of active network probes follows a strict authorization ladder:

- **LEVEL_0**: Preflight planning only. (Current milestone: M3G-02)
- **LEVEL_1**: Mock fixture creation and parser contract repair. Tests run entirely locally.
- **LEVEL_2**: Bounded controlled live probes for selected watchlist targets only.
- **LEVEL_3**: Broader source recovery, expanding source coverage but staying within the bounded watchlist.
- **LEVEL_4**: Production refresh automation and scheduled CI/CD runs.

*The next milestone, M3G-03, is explicitly restricted to LEVEL_1.*

## 8. Per-Source Recovery Table

| Source ID | Source Type | Authority Level | Current Artifact Status | Error Type | Caveats | Attempted | Live Probe Needed | Local Mock Supports | Priority | Risk | Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| TWSE_MIS | unofficial_frontend_endpoint | unofficial_frontend | offline_mode_no_data | offline_mode_no_local_input | offline_mode, unofficial_source_risk | false | yes (in LEVEL_2) | yes | P1 | medium | Recover via mock fixtures in LEVEL_1 |
| Yahoo_Finance | third_party_api | third_party | offline_mode_no_data | offline_mode_no_local_input | offline_mode, third_party_coverage_caveats | false | yes (in LEVEL_2) | yes | P2 | low | Recover via mock fixtures in LEVEL_1 |
| TWSE_OpenAPI | official_openapi | official_public_exchange_eod | offline_mode_no_data | offline_mode_no_local_input | offline_mode, official_eod_reference_only | false | yes (in LEVEL_2) | yes | P1 | low | Recover via mock fixtures in LEVEL_1 |
| TPEx_OpenAPI | official_openapi | official_public_exchange_eod | offline_mode_no_data | offline_mode_no_local_input | offline_mode, official_eod_reference_only | false | yes (in LEVEL_2) | yes | P1 | low | Recover via mock fixtures in LEVEL_1 |
| FinMind | third_party_api | third_party | not_attempted | not_attempted_offline_default | offline_mode | false | yes | no | deferred | blocked | Keep deferred until M3G-04 or later |
| Fugle | broker_api | broker_authenticated | skipped | auth_required_doc_only_skipped | broker_api_not_eligible | false | yes | no | deferred | blocked | Out of scope. Maintain doc-only |
| Fubon | broker_api | broker_authenticated | skipped | auth_required_doc_only_skipped | broker_api_not_eligible | false | yes | no | deferred | blocked | Out of scope. Maintain doc-only |

## 10. M3G-03 Recommended Sequence

The recommended execution for the next milestone (M3G-03-CONTROLLED-MARKET-SOURCE-PROBE-REPAIR) is strictly **LEVEL_1 mock fixture and parser contract repair first**.

1. Create static JSON/HTML mock files for `TWSE_MIS`, `TWSE_OpenAPI`, `TPEx_OpenAPI`, and `Yahoo_Finance` in `tests/fixtures/market_sources/`.
2. Ensure the mocks cover the required minimum bounded symbols (`2330`, `0050`, `00929`, `8069`, `TAIEX`/`t00`).
3. Update unit tests to patch generators/probes to use these local fixtures instead of making live network calls.
4. Verify that generator scripts produce non-empty valid artifacts (`latest_market_snapshot.json`, etc.) using these mocks.
5. Do not run any live probes or enable network traffic.

## 11. Stop Conditions

The recovery process must halt immediately if:
- Any live network request is executed outside of the explicitly authorized ladder level.
- Generators crash or fail to produce valid (even if empty) output schemas.
- Trading advice or signals begin appearing in generated context.
- The pipeline breaches the bounded watchlist constraints.

## 12. What Must Remain Deferred

- **Live Probes**: Deferred until LEVEL_2 authorization.
- **Broker Auth**: `Fugle` and `Fubon` remain deferred indefinitely.
- **Full Market Scans**: Strictly deferred. All processing must adhere to the bounded watchlist.
- **FinMind Integration**: Deferred until primary sources are fully validated.