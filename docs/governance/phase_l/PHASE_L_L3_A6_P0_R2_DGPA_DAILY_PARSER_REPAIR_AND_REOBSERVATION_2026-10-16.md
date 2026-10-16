# Phase L L3-A6-P0-R2 — DGPA Daily Parser Repair and Re-observation

**Authority:** `USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_R2_DGPA_DAILY_PARSER_REPAIR_AND_REOBSERVATION`\
**Entry HEAD:** `a9986572f6803ea8d56a06586488499ac10a8e1b`\
**Canonical base:** `origin/main@7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`\
**Branch:** `phase-l/l3-a6-bounded-live-source-drift-recertification`\
**Run:** `l3-a6-p0-r2-20261016T055915Z`\
**Disposition:** `DGPA_SOURCE_DRIFT_OBSERVED`

**Status:** R2 candidate complete; independent review pending; Owner acceptance not recorded.

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

The offline implementation, tests, fixture and governance record were first
committed at `54c6e99da7ff4b52aea8d17d959fe0058434ca63`. The preflight then
exposed a resolver hash typo in the runner; after correcting and re-running all
gates, the final pre-network implementation commit is
`8840a4f53a190a5bce5a7a84ce54c5230ce27cd7` (tree
`0c12b813983a1da47b85a7bfd6aad8c793e5c309`). The R2 reservation binds this
corrected commit and exact plan hash before any request. The pre-network R2 plan fixes
official DGPA daily/archive URLs and limits of one
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

The first runner preflight attempt exposed a recorded resolver-hash typo before
network dispatch. A byte comparison against the R2 parent showed the resolver
was unchanged; the runner and plan hash were corrected and all offline gates
were rerun. No R2 external request occurred during either preflight attempt.

## R2 bounded live observation

The corrected preflight passed before the one authorized live run, binding the
run to the pre-network implementation commit/tree and confirming the existing
resolver/calendar hashes. Exactly one request was dispatched:

| Sequence | Purpose | URL | HTTP | Bytes | Response SHA-256 | Parser result |
|---:|---|---|---:|---:|---|---|
| 1 | `R2_DAILY_SINGLE_OBSERVATION` | `https://www.dgpa.gov.tw/typh/daily/nds.html?uid=31` | 200 | 15,037 | `1bcaf4cdd7620796e206fbaf0236c6ecbed9d4f7eb0a69c5b33be3d8e6476232` | `dgpa_daily_subject_ambiguous` |

Under the single-daily-request stop rule, R2 made no archive-index or detail
request. The page response was not retained; only the bounded response metadata
and hash remain. The parser could not bind one unique visible semantic subject
region, so the current-day status was not adjudicated. This is recorded as a
bounded contract ambiguity, not as permanent provider removal or an availability
claim. Historical 2026-10-15 status was not inspected.

Request totals were daily `1/1`, archive index `0/4`, detail `0/1`, total `1/6`.
`closure_authority_complete=false`; the resolver was not called; P17 remains
unresolved. A6 market authority remains unconsumed; P01-P18, B01-B05 and T86
were not requested. No source payload, Security Master, Watchlist, Result/Audit,
Catalog or Route mutation occurred.

The R2 `manifest.json` binds the retained run artifacts. R1 and P0 manifests
were independently rechecked and remain unchanged. R2's final outcome is
`DGPA_SOURCE_DRIFT_OBSERVED`; no Owner acceptance is recorded. The single R2
authority is consumed and cannot authorize another daily/archive observation.
R2 manifest SHA-256 is
`e7049145bcd13bf484229f2db0c2abb58b1808b60358370b510cf3c03704ed78`.

No P01-P18/B01-B05 recertification or T86 request is authorized here; the A6
market live authority remains unconsumed. No second R2 observation is authorized
by the consumed one-shot authority.
