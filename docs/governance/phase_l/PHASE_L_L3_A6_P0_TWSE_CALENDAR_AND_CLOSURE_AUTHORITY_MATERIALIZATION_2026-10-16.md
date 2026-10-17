# Phase L L3-A6-P0 — TWSE Calendar & Closure Authority Materialization

**Disposition:** `INCOMPLETE_AUTHORITY`
**Authority:** `USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_CALENDAR_AND_CLOSURE_AUTHORITY_ACQUISITION`
**Base:** `origin/main@7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`
**Branch:** `phase-l/l3-a6-bounded-live-source-drift-recertification`
**P0 run:** `l3-a6-p0-20261016T033822Z`
**P0 code candidate commit:** `302d1d94ae8f839324857cd47a0c7428a31bb228`
**P0 reservation commit:** `812d8d57ded8cc5b1717006051b0cc0f04dedb4f`

## Purpose and boundary

This is the calendar/closure-authority prerequisite inside the existing L3-A6
boundary. It materializes only the current TWSE holiday schedule and the
existing `NCDR_DGPA_CLOSURE_CAP` feed for the purpose of determining whether
the already-authorized P17 date can be resolved. It does not execute P17 or any
other A6 market/bootstrap source.

The frozen M7E calendar authority, M8A closure source contract, existing
`scripts.twse_trading_calendar.build_twse_trading_calendar_from_holiday_schedule`,
existing `scripts.m8r_03d_watchlist_controlled_executor._load_production_calendar`
acquisition seam, existing
`scripts.m8a_ncdr_dgpa_closure_cap.fetch_and_parse_closure_feed` seam, and
`scripts.phase_i_i3_execution_date.resolve_i3_twse_source_trade_date` remain the
relevant authorities. No calendar resolver or closure parser semantics were
changed.

## Pre-network plan and bounded authority

The committed plan is
`acceptance_runs/l3-a6-p0-20261016T033822Z/p0_plan.json` (SHA-256
`903d58fd667be47346319477a8a9c73f5989e1b04a6cd626071d9a5a18dc5683`). It
froze evaluation time `2026-10-16T11:38:22+08:00`, both exact endpoints, the
existing source seams, 10-second current seam timeouts, and limits of three
calendar acquisitions, three closure acquisitions, six total. It explicitly
sets `P01_P18_execution_allowed=false`, `B01_B05_execution_allowed=false`, and
`market_source_recertification_authorized_here=false`.

Offline candidate commit `302d1d94ae8f839324857cd47a0c7428a31bb228` has tree
`49341fd9f0fb2b971e38bac2c98796006e1d9123`. The committed reservation binds
that SHA/tree and the plan digest. `authority_reservation.json` changed from
`RESERVED` to `CONSUMED` immediately before the first external dispatch, and
`authority_consumed.json` records the same authority/run. The A6 market-source
one-shot authority remains unconsumed.

The P0 runner allows only the two exact GET endpoints and rejects any other
URL/method before dispatch. It reserves budget before each request, performs no
retry, sleep, backoff, polling, or scheduler action, and uses only the existing
acquisition seams. TWSE cache writes were suppressed while the seam ran under
an isolated temporary root; no local production state was written.

## Acquisition ledger

Exactly two external acquisitions occurred; both were authorized P0 authority
acquisitions, not P01-P18 or B01-B05 recertification:

| Seq. | Authority | Outcome | HTTP | Bytes | Response SHA-256 | Normalized SHA-256 |
|---:|---|---|---:|---:|---|---|
| 1 | `TWSE_HOLIDAY_SCHEDULE` | success | 200 | 3,774 | `7644c1a8af784c09f54670fd7413f536b13eb76c54d658058e8873d1aee32117` | `28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8` |
| 2 | `NCDR_DGPA_CLOSURE_CAP` | success | 200 | 73 | `db96f13b8fc6d00cc7738f9ceff385d4ebba9a9dd4ce85f7e5f975df5e35e9b7` | `4dfc5ef02b2530531b2275c0a1e5d13ae7f7a10e4a761eb8d90ae1c15fc06ab1` |

No response body was retained. The ledger stores bounded status, content type,
timing, byte count, response hash, normalized hash, and decision after each
attempt. The response metadata is in
`acceptance_runs/l3-a6-p0-20261016T033822Z/acquisition_ledger.json`.

## TWSE calendar result

The existing builder produced `twse_trading_calendar.v1` for TWSE, year 2026,
`Asia/Taipei`, with the exact accepted `holidaySchedule` source URL and
`runtime_fetch=false`. The normalized artifact covers all 365 dates in 2026,
contains zero invalid records, and reports 243 trading days and 122 non-trading
days. Its normalized calendar SHA-256 is
`28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8`.
The retained artifact is
`acceptance_runs/l3-a6-p0-20261016T033822Z/twse_trading_calendar_2026.json`.

Only one successful calendar acquisition was needed; no consistency-confirmation
acquisition was made. The resolver inspection window was derived locally from
the frozen evaluation time and materialized calendar, not guessed:

```text
2026-10-16
2026-10-15
```

The first date is included because the resolver checks today's closure status;
the second is the first preceding calendar-declared trading-day candidate.

## Closure authority finding

NCDR returned HTTP 200 and parsed successfully. The current feed contained zero
events relevant to the two resolver coverage dates. Its existing accepted
contract defines a dynamic event feed for explicitly triggered market-day
currentness checks; it does not attest that the feed is exhaustive for
historical dates or for this resolver window. A successful query and an empty
event list therefore do not prove that no closure occurred on either date.
Repeated identical feed hashes would not supply that missing completeness
authority, so no further NCDR acquisition was made.

The retained `closure_authority_snapshot.json` records:

```text
coverage_basis = resolver_inspection_window_only
coverage_dates = [2026-10-16, 2026-10-15]
source_query_succeeded = true
events_relevant_to_coverage_dates = []
closure_authority_complete = false
```

Accordingly, the existing I3 resolver was not called, no manual/weekday date
fallback was used, and no P17 market data request was made. P17 remains
`A6_PREFLIGHT_TWSE_TRADE_DATE_UNRESOLVED`.

## Disposition and verification

P0 disposition is `INCOMPLETE_AUTHORITY`: the 2026 calendar artifact is valid,
but closure completeness for the exact resolver window is not established by
the current source authority. This is an authority limitation, not a claim of
source removal or closure-source failure.

Offline preflight ran with the repository external-network socket guard:

```text
P0 + A5 + A1-A3 + calendar/resolver/closure + A4 backup/restore/migration/
retention + Persistent Watchlist deterministic regressions:
287 passed, 0 failed, 393 warnings
```

All 393 warnings are the existing `jsonschema.RefResolver` deprecation warning
from `scripts/m8r_09_persistent_watchlists.py`; no behavior failure was
observed. The source registry, Portable Catalog sync, runtime/Skill exact-six,
V1 public contract, and Phase H V3 validators passed. Python compile checks,
reservation/plan/tree hash preflight, and `git diff --check` passed. No denied
external socket attempt was observed in offline tests.

The post-run manifest at
`acceptance_runs/l3-a6-p0-20261016T033822Z/manifest.json` SHA-256 binds the
retained plan, reservation/consumption proof, acquisition ledger, calendar,
closure snapshot, and result. No raw TWSE JSON or NCDR XML was committed.

The first invocation used a file-path launch and stopped at Python package
import resolution before reaching runner preflight or dispatch; it made zero
source requests and left the worktree unchanged. The committed runner was then
invoked as `python -m scripts.run_phase_l_l3_a6_p0_authority_materialization
--execute-authorized-p0`, which passed the reservation checks and performed the
single two-source P0 run recorded above.

```text
P0 calendar acquisitions = 1 / 3
P0 closure acquisitions = 1 / 3
P0 total acquisitions = 2 / 6
P01-P18 live recertification = not performed
B01-B05 live recertification = not performed
A6 market-source authority = not consumed
Security Master / Watchlist / Result / Audit / Catalog / Route mutation = 0
```

## Stop boundary

P0 ends with incomplete closure authority and an unresolved P17 date. Do not
start A6 market recertification, infer a date, fetch T86 to test a date, or make
additional closure requests under this run. Any future closure-completeness
authority or additional acquisition requires separate review/authority. A7 and
L4-L7 remain unstarted and unauthorized; L3 is not closed.
