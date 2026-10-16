# Phase L L3-A6-P0-R5 — DGPA Archive List-Item Grammar Repair

**Status:** bounded R5 candidate; live archive observation pending the committed pre-network reservation.

## Authority and boundary

R5 continues the authorized P0 prerequisite on branch
`phase-l/l3-a6-bounded-live-source-drift-recertification`, from entry HEAD
`3adaafb866967f0f146858ccc8a995e97e31866d`, against canonical base
`7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`. It does not consume the separate
A6 market-source authority.

Scope is limited to the existing R1-scoped DGPA archive index parser, bounded
archive diagnostics, deterministic tests, reuse of R4 daily authority, and one
archive-only observation within the new R5 request ceiling. Daily GETs are
prohibited in R5. P01-P18, B01-B05, T86, Security Master, production state,
public schemas, the I3 resolver, and the P0 calendar are out of scope.

## Accepted prior evidence and root cause

P0 materialized the accepted 2026 TWSE calendar. R1-R3 repaired and diagnosed
the daily-page contract. R4 (`l3-a6-p0-r4-20261016T065039Z`) established the
current-day fact `2026-10-16 / NO_CLOSURE_NOTICE`; its daily artifact SHA-256 is
`059e9bbc5bc1c31d06a7d182c27c4dce4d0e01deef8a0a9b30b2cdf430b5574c`, response
SHA-256 is `b1bdcdee51ae9513a094c5de4107c05f9fff2025cdd82a4052a7fbfd9c0c156e`,
and R4 manifest records `f46287dbe950e0af0575569862e3dffa8d416d13dc67e4e394ba2a8f8e643e13`.
R4's single archive response was HTTP 200 but could not be parsed because the
implementation assumed the publication date must be in the `<tr>` containing
the anchor. That assumption is not a reliable archive item contract. A second
date-role defect used the first date in anchor text as the event date, although
a compact leading date can be the archive publication date.

## R5 parser contract

Each archive item now records publication date and target event date
independently. Publication date is taken only from a leading compact ROC date
in the same anchor or an unambiguous date-only cell in that item's structured
row. A conflicting same-item candidate fails closed. The recognized publication
prefix is removed before event-title validation and event-date extraction. The
event title must match the natural-disaster stop-work/stop-school status family;
its own ROC date supplies `target_event_date`. Ordinary page dates, navigation,
footer text, and other items cannot supply either role.

The parser supports anchor-only list items and preserves legacy structured rows.
Returned records retain the title, detail URL, bounded item excerpt (at most
300 characters), and date-role provenance. `archive_index_diagnostics.json`
records per-item candidates, selected values, parse status, and bounded source
excerpt, including when an item fails. Archive page semantic identity is
required; a rendered `第 N/M 頁` marker, when present, must match the requested
page. Target chronology remains based on event dates, not publication dates.

R5 has no daily request allowance, at most four sequential archive-index GETs,
at most one discovered detail GET, and at most five total. If page 1's newest
event date is older than the target and no target record exists, page 2 is
required as bounded cross-page ordering confirmation. This is a one-time
predeclared confirmation, not a retry. A target detail that requires an
additional attachment surface remains incomplete; R5 will not fetch it.

## Frozen inputs

- Reused R4 current-day authority: `2026-10-16 / NO_CLOSURE_NOTICE`; R5 daily
  GET count is zero.
- P0 calendar normalized SHA-256:
  `28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8`.
- I3 resolver SHA-256:
  `075abdbb9a5cb961cb7054583aeebbe3f8722bb9c570577037396db85dc0f010`.
- Evaluation time: `2026-10-16T11:38:22+08:00`; coverage dates:
  `2026-10-16`, `2026-10-15`.

## Verification and observation

The guarded offline gate passed 149 tests across the R1/P0 authority parser,
R2-R4 DGPA regressions, I3 resolver/calendar authority coverage, and A5 source
drift contract tests. The global external socket sentinel recorded zero
attempts. `validate_source_registry.py`, Portable Catalog sync,
runtime/Skill exact-six, V1 public contracts, and Phase H V3 validators all
passed. `python -m compileall -q scripts server tests` and `git diff --check`
passed. Exact commands and outputs are bound in the committed
`offline_review.json` and R5 evidence. No live archive response or result is
asserted by this candidate text before execution.

After the one bounded archive observation, R5 will either combine verified
historical evidence with the immutable R4 daily fact and call the unchanged I3
resolver, or remain `INCOMPLETE_AUTHORITY` / parser-inconclusive. No outcome is
preselected. No market-source recertification will be performed; the A6 market
authority remains unconsumed, and A6 market recertification, A7, and L4-L7
remain unstarted/not authorized.
