# M8A market-day currentness runtime contract

M8A resolves official EOD currentness from scheduled calendar status, optional emergency closure evidence, exchange-specific special status, and the reported official EOD trade date.

The accepted project rule is: confirmed Taipei City municipality full-day or morning work suspension closes TWSE and TPEx for the full market day. Annual schedule absence alone must not prove an actual trading day when emergency evidence is unresolved.

Statuses include `current_official_eod`, `matches_expected_latest_trade_date_after_emergency_closure`, `delayed_one_trading_day`, `stale_official_eod`, and `unresolved_date_mismatch`.
