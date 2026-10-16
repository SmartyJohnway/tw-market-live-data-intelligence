# Phase L L3-A6-P0-R4 — DGPA Table Status Semantics Repair

## Status

Candidate implementation and bounded re-observation record. Independent review
and Owner acceptance are not recorded here. R4 does not authorize A6 market
recertification.

## Authority and lineage

- R4 entry HEAD: `4739ac519a5505089df920db78037345e106f2c6`.
- Canonical `origin/main`: `7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`.
- R4 authority: `USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_R4_DGPA_TABLE_STATUS_SEMANTICS_REPAIR`.
- Reused P0 calendar normalized SHA-256:
  `28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8`.
- Frozen resolver evaluation time: `2026-10-16T11:38:22+08:00`.
- Resolver window: `2026-10-16`, `2026-10-15`.

## Prior observations

The earlier evidence remains immutable. P0 materialized the calendar but did
not establish historical closure completeness using the NCDR current feed. R1
then stopped because its parser assumed the date had to be in a heading. R2
repaired that assumption but used whole-page subject multiplicity in a way that
could not distinguish presentation duplication. R3 added semantic candidate
diagnostics; independent review accepted its final disposition
`R3_PARSER_CONTRACT_INSUFFICIENT`, not the initial runner's
`DGPA_SOURCE_DRIFT_OBSERVED`.

R3 diagnostics identified the false conflict: an official table header,
`是否停止上班上課情形`, matched the substring `停止上班` and was treated as a
closure fact alongside `無停班停課訊息`. R3 also exposed a larger ancestor
presentation container that repeated descendant status text. These facts did
not establish conflicting provider status.

## R4 contract change

The R1/R2/R3-scoped HTML parser now keeps a structured row representation with
cell tags and bounded text while preserving the legacy text-only `rows` view.
Daily status adjudication uses the structured representation:

- schema/header vocabulary and `th` cells without locality identity classify as
  `TABLE_SCHEMA_HEADER`;
- a locality status requires locality identity and a non-header decision cell;
- affirmative closure semantics require a locality row plus a decision phrase
  and a resolvable day-part scope;
- no-notice plus a schema header is valid;
- no-notice plus an actual locality closure row remains a conflict;
- mutually inconsistent Taipei locality statuses remain fail closed;
- nested presentation candidates are collapsed while retaining the specific
  bound subject candidate; schema header cells are excluded as subject facts.

Bounded `table_semantic_diagnostics.json` records row count and, per row, cell
tags, normalized cell texts, classification, locality, and normalized status.
No raw HTML is retained. Subject diagnostics remain bounded and are preserved.

## Live authority and limits

R4 has an independent one-run DGPA authority. It permits at most one daily GET,
four sequential archive index GETs, one discovered detail GET, and six total.
There is no daily refetch. First actual GET consumes only R4 authority. The A6
market-source authority remains unconsumed. The runner must verify its
pre-network plan/reservation, resolver SHA, and retained P0 calendar SHA before
dispatch. It will not dispatch P01-P18, B01-B05, or T86.

The daily page must adjudicate before archive traversal. Historical negative
evidence requires the existing official archive ordering/pagination and target
crossing proof. The existing I3 resolver is called only if both dates are
adjudicated, and the returned date is not hard-coded.

## Verification and observation

The bounded deterministic gate passed 309 tests across R4, R3, R2, R1, P0,
I3, DGPA/NCDR, A5, L3-A1 through A4, and the relevant Phase G runtime and
projection regressions. All five required validators passed; exact-six MCP
validation reported six tools. `python -m compileall -q scripts server tests`
and `git diff --check` passed. The R4 global socket sentinel recorded zero
external attempts. Before network execution, resolver and retained P0 calendar
SHA-256 values were independently rechecked against the frozen values above.

The bounded live observation, if reached after the committed preflight plan,
will record exact request counts, response hashes, diagnostics, closure
completeness, resolver result, manifest SHA-256, and mutation checks in its
separate R4 run directory. If daily adjudication fails, R4 stops without
archive requests or refetch and retains both subject and table diagnostics.

## Non-goals

No P01-P18 or B01-B05 recertification, T86 request, market-source runtime
change, I3 resolver/calendar change, Security Master update, Catalog/Route or
public schema change, retry, daily refetch, sleep/backoff, polling, scheduler,
or background monitoring is permitted. A6 market recertification, A7, and
L4-L7 remain unstarted.
