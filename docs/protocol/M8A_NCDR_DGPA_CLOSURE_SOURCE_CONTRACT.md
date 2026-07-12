# M8A NCDR/DGPA closure source contract

`NCDR_DGPA_CLOSURE_CAP` is a bounded official dynamic-event evidence source for market-day currentness resolution only. It uses `https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33` by explicit operator-triggered execution when an apparent official EOD trade-date mismatch requires emergency closure evidence.

It is not market price data, not a primary M8A market-data source, and not polled or scheduled. Normal artifacts retain only compact event provenance: source ID, event ID, target date, area, decision status, closure scope, and publication time. Raw XML is not retained by default.
