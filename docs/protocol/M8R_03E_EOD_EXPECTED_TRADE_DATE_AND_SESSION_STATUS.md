# M8R EOD Expected Trade Date and Session Status Protocol

## 1. Objectives and Scope

This protocol establishes the rules for determining the **expected latest completed trade date** and **current market session status** for Taiwan financial markets (TWSE, TPEX, TAIFEX). 

Instead of relying on heuristic assumptions or hardcoded trading dates, this protocol introduces a timezone-aware, rule-based state machine that combines:
1. Official trading calendars.
2. Taipei City emergency work-suspension (natural disaster closure) status.
3. Specific market close times and publication grace periods.

---

## 2. Timezone and Reference Clock Governance

- **Clock standard**: All internal evaluations and clock math are bound strictly to the `Asia/Taipei` timezone.
- **Fail-closed policy**: Any naive (timezone-unaware) datetime inputs are forbidden and will cause immediate failure to prevent ambiguous date interpretation across boundaries.

---

## 3. Market Session Status Determination

For a given reference timestamp \(T\) in `Asia/Taipei`, the status of the session is classified as:
- **`regular_trading_day`**: The day is a scheduled trading day, and no emergency closure is active.
- **`weekend` / `official_holiday`**: The day is a weekend or scheduled holiday based on the TWSE official calendar.
- **`market_closed_no_session`**: The day is an active trading day but has been closed due to emergency work-suspension (typhoon closure) or special exchange announcement.
- **`calendar_status_unresolved`**: The calendar metadata is missing or query fails.

---

## 4. Emergency Closure Mappings (Taipei City)

Natural disaster closures are parsed from the NCDR/DGPA emergency broadcast CAP feed:
- Region criteria: Area name must match `臺北市` or `台北市`, with area level as `municipality`.
- Scope mappings:
  - `full_day` closure: Entire day's session is cancelled -> `market_closed_no_session`.
  - `morning` closure: Morning trading is cancelled -> Entire day's session is cancelled -> `market_closed_no_session`.
  - `afternoon` closure: Afternoon trading is cancelled -> The morning trading session has already taken place -> Day remains a valid trading day.

---

## 5. EOD Publication Grace and Staleness Logic

When comparing the reported trade date from a data source against the expected latest trade date:
1. **`official_latest_completed_eod`**: Actual matches expected, and the market session is complete.
2. **`official_previous_session_eod_before_close`**: Actual matches expected (which is the previous day), and we are currently mid-market or pre-market.
3. **`not_yet_published_after_close`**: We are within the 60-minute publication grace period immediately following market close, and the source is still returning the previous trade date.
4. **`unexpected_stale_eod`**: We are past the grace period, but the source is still returning the previous trade date.
5. **`future_trade_date_invalid`**: Actual trade date is newer than the calculated expected trade date.

---

## 6. Fallback Policy

If the official calendar or closure feed is unresolved, the evaluator falls back to a **provisional bounded-age check**:
- `fallback_policy_used = true`
- `fallback_policy = "provisional_bounded_age"`
- Freshness is determined strictly via elapsed age since the reported trade date's expected close time (max age 3 days).

---

## 7. Legacy Compatibility Layer

To prevent regressions in existing Watchlist, Executor, and Context Builder modules, the legacy `resolve_market_day_currentness` wrapper translates the detailed states into legacy compatibility strings (e.g. `current_official_eod`, `matches_expected_latest_trade_date_after_emergency_closure`, `delayed_one_trading_day`, `stale_official_eod`).
