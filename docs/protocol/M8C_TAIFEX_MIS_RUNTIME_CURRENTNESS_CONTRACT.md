# M8C TAIFEX MIS runtime currentness contract

Currentness axes: transport state, session alignment, market phase, source timestamp state, quote age state, calendar evidence, confidence, and overall AI currentness.

Fresh promotion requires an accepted `mode=1` quote, safely resolved source timestamp, regular-session identity alignment, evaluation time within a validated active session window, directly supported market phase, quote age <= 90 seconds, and no reliance on retrieved-at alone. Aging is <= 300 seconds; stale is > 300 seconds. These are project policy thresholds, not an exchange SLA.

If market phase is unresolved, M8C-01 does not emit `active_session_fresh_liveish`. After-hours remains disabled; without authoritative after-hours calendar evidence, source timestamp state is `ambiguous_after_hours` and overall currentness is `session_alignment_unresolved`. Cross-midnight semantics remain unresolved and no implementation subtracts one day from trade date.
