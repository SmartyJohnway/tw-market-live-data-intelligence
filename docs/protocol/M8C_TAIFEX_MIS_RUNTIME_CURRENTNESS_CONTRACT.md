# M8C TAIFEX MIS runtime currentness contract

Currentness axes: transport state, session alignment, market phase, source timestamp state, quote age state, calendar evidence, confidence, and overall AI currentness.

Fresh promotion requires all of: an accepted `mode=1` quote, safely resolved non-future source timestamp, regular-session identity/suffix alignment, evaluation time inside the validated regular session window, directly verified active market phase, quote age <= 90 seconds, and no reliance on retrieved-at alone. Aging is <= 300 seconds; stale is > 300 seconds. These are project policy thresholds, not an exchange SLA.

Raw TAIFEX `Status` is not exposed as normalized market phase. Only directly mapped status codes may produce `active_regular_trading`; unknown status codes produce `market_phase_unresolved` and prevent fresh promotion.

If market phase is unresolved, M8C-01 does not emit `active_session_fresh_liveish`. After-hours remains disabled; without authoritative after-hours calendar evidence, source timestamp state is `ambiguous_after_hours` and overall currentness is `session_alignment_unresolved`. Cross-midnight semantics remain unresolved and no implementation subtracts one day from trade date.
