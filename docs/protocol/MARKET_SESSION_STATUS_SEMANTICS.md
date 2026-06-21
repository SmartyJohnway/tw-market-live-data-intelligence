# Market Session Status Semantics

## 1. Purpose
This document defines a conservative, strictly metadata-driven vocabulary for describing the overall or per-symbol market session status within the Latest Market Snapshot. Session status informs human operators and AI agents about the temporal context of the data, but it strictly **must never** be used to generate trading signals or automated execution triggers.

## 2. Default M3A-01 Behavior
In the current design-only phase (M3A-01), no session detection logic is implemented. The default session status output must always be:

```json
{
  "market_session_status": {
    "status": "unknown",
    "as_of_taipei": null,
    "evidence": [],
    "caveats": [
      "session_detection_not_implemented_in_m3a_01"
    ]
  }
}
```

## 3. Allowed Status Labels

The following is the authorized vocabulary for describing the market session.

### `unknown`
* **Meaning:** The system cannot determine the session status due to lack of evidence, source failures, or because session detection logic is not implemented.
* **Evidence Requirement:** None.
* **Live Candidate Usage:** Permitted, but must carry high staleness/delay caveats as freshness is uncertain.
* **EOD Source Usage:** Permitted.
* **Required Caveats:** `session_status_unknown`

### `pre_market`
* **Meaning:** Current system time or source explicit signals indicate the market is in the pre-open matching phase.
* **Evidence Requirement:** Explicit clock time matches (e.g., Taipei time 08:30 - 09:00) AND source confirmation (e.g., pre-market indicators from TWSE MIS).
* **Live Candidate Usage:** Permitted for pre-market quote data.
* **EOD Source Usage:** EOD data refers to the previous trading day.
* **Required Caveats:** `pre_market_data_subject_to_change`

### `regular_trading`
* **Meaning:** The core intraday trading session is actively ongoing.
* **Evidence Requirement:** Current system time falls within regular hours AND source timestamps continually update without excessive staleness.
* **Live Candidate Usage:** Fully permitted for live-style summaries.
* **EOD Source Usage:** EOD sources must not be presented as reflecting current regular trading activity.
* **Required Caveats:** `unofficial_live_data_risk` (if using unofficial sources).

### `post_market`
* **Meaning:** The regular session has ended, but after-hours / odd-lot matching may be occurring.
* **Evidence Requirement:** Time is immediately following market close (e.g., 13:30 - 14:30 Taipei) and source data reflects closing phases.
* **Live Candidate Usage:** Permitted, but quotes reflect closing or post-market auctions.
* **EOD Source Usage:** EOD sources may not yet be published until batch processing completes later in the afternoon.
* **Required Caveats:** `post_market_auction_phase`

### `closed`
* **Meaning:** All trading sessions for the day have concluded, and the market is formally closed.
* **Evidence Requirement:** Late afternoon/evening Taipei time, or explicit API `is_open = false` flags.
* **Live Candidate Usage:** May be used, but prices are functionally EOD/stale until the next pre-market session.
* **EOD Source Usage:** Fully permitted and preferred for canonical end-of-day reference.
* **Required Caveats:** `market_closed`

### `holiday_or_no_session`
* **Meaning:** A scheduled weekend, national holiday, or emergency closure (e.g., typhoon day).
* **Evidence Requirement:** Explicit calendar lookup or exchange API signals indicating no trading today.
* **Live Candidate Usage:** Values will be extremely stale (from the last active day). Must not be presented as "live".
* **EOD Source Usage:** Represents the close of the last active trading day.
* **Required Caveats:** `no_trading_session_today`

### `source_time_inconsistent`
* **Meaning:** Different data sources or multiple targets within the same source report highly divergent timestamps, making a unified session status impossible to verify.
* **Evidence Requirement:** `staleness_seconds` varies wildly across the snapshot or contradicts the system clock significantly.
* **Live Candidate Usage:** High risk. Must explicitly mark individual symbols as `unknown` freshness or `stale`.
* **EOD Source Usage:** Permitted as reference, as EOD batch data is disconnected from intraday clocks.
* **Required Caveats:** `conflicting_source_clocks`

## 4. General Implementation Rules (Future M3A-02)

1. **Inference Limits:** Future M3A-02 implementations may infer session status only from explicit clock, calendar, or source evidence. Do not guess.
2. **Fallback to Unknown:** If the session status cannot be confidently verified, the snapshot must default to `unknown`.
3. **EOD Limitations:** End-of-Day (EOD) batch sources (like OpenAPI) cannot determine intraday session states by themselves.
4. **Stale Clocks:** Significantly stale source timestamps must force the session status to `source_time_inconsistent` or `unknown`.
5. **No Trading Semantics:** The market session status is strictly for contextual awareness and AI reading comprehension. It **must never** be wired into logic that executes buy/sell orders or generates automated trading signals.
