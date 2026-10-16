# Phase L L3-A6-P0-R2 — DGPA Daily Parser Repair and Re-observation

**Authority:** `USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_R2_DGPA_DAILY_PARSER_REPAIR_AND_REOBSERVATION`\
**Entry HEAD:** `a9986572f6803ea8d56a06586488499ac10a8e1b`\
**Canonical base:** `origin/main@7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`\
**Branch:** `phase-l/l3-a6-bounded-live-source-drift-recertification`\
**Run:** `l3-a6-p0-r2-20261016T055915Z`\
**Status:** candidate; live re-observation pending the pre-network commit and independent post-run review.

## Chronology and root cause

P0 materialized the 2026 TWSE calendar but the NCDR dynamic feed did not prove
historical closure completeness. R1 selected official DGPA current and archive
authority. Its single daily request succeeded at HTTP 200, but the parser
reported `dgpa_daily_displayed_date_mismatch`; R1 correctly stopped before
archive access and remains immutable with disposition `INCOMPLETE_AUTHORITY`.

The parser had required the displayed date to occur in `h1`/`h2`/`h3`. That
unsupported DOM-shape assumption did not cover a visible status title whose date
and subject are in adjacent non-heading elements. The repair binds the exact
status date to a unique recognized daily-status subject block and, when needed,
an immediately adjacent date-only block. It excludes navigation/footer/script
text and linked text from semantic date binding; timestamp dates and unrelated
page dates cannot supply the status date. It separately requires an explicit
update timestamp, DGPA attribution, and either explicit no-notice text or one
adjudicable locality table set. Conflicting dates and no-notice/table closure
contradictions fail closed.

The original R1 heading form `停止上班上課情形` remains a recognized bounded
equivalent. No resolver, calendar, NCDR parser, production market source, public
schema, Catalog, or Route code is changed.

## Fixed R2 window and request bound

R2 reuses the immutable P0 calendar artifact at
`acceptance_runs/l3-a6-p0-20261016T033822Z/twse_trading_calendar_2026.json`,
normalized SHA-256
`28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8`. The
evaluation time remains `2026-10-16T11:38:22+08:00`; the only closure dates are
`2026-10-16` and `2026-10-15`. The existing I3 resolver SHA-256 is
`075abdbb9a5cb961cb7054583eebbe3f8722bb9c570577037396db85dc0f010`.

The pre-network R2 plan fixes official DGPA daily/archive URLs and limits of one
daily GET, four sequential archive-index GETs, one discovered-detail GET, and
six total. A failed single daily observation stops the run without refetch or
archive call. P01-P18, B01-B05 and T86 remain disabled; A6 market authority is
not consumed. No retry, sleep, polling, scheduler, or production state mutation
is permitted.

## Offline parser evidence

The new realistic fixture
`tests/fixtures/phase_l/dgpa_daily_20261016_non_heading.html` puts the target date
and subject in a non-heading status block, includes an explicit update time and
DGPA attribution, and includes a footer date that must not bind. Tests also
retain the old R1 heading form and exercise wrong/missing/ambiguous dates,
timestamp mismatch, missing subject/attribution/status, conflicting no-notice
and locality status, malformed UTF-8, normal work, morning closure, full-day
closure, and the R2 request ceilings.

Focused R2/R1 parser and authority tests passed 44 tests. The integrated guarded
offline gate passed 266 tests across R2/R1/P0/I3, DGPA/NCDR, A5 and L3-A1 through A4;
the global external socket guard recorded zero attempts. Five validators,
`py_compile`, and `git diff --check` passed. Detailed machine-readable results
are in the R2 run's `offline_review.json`.

## Pending live observation and disposition

No R2 live response is yet asserted by this pre-network record. The plan and
authority reservation must be bound to the exact pre-network implementation
commit before any external DGPA request. After the authorized run, this record
will be updated with observed request counts, response hashes, bounded daily
and archive facts, completeness decision, resolver result if justified, and the
final R2 disposition. P0 and R1 evidence will not be rewritten.

Regardless of R2 result, no P01-P18/B01-B05 recertification or T86 request is
authorized here; the A6 market live authority must remain unconsumed.
