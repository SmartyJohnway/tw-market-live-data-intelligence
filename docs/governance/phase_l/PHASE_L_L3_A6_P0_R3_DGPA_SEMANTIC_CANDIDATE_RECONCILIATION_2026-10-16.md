# Phase L L3-A6-P0-R3 — DGPA Semantic Candidate Reconciliation

**Authority:** `USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_R3_SEMANTIC_CANDIDATE_RECONCILIATION`
**Entry HEAD:** `3c633c6f36d79bd431eafa568c2ab4c1882b91b3`
**Canonical base:** `origin/main@7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`
**Status:** candidate record; independent review and Owner acceptance are pending.

## Chronology and review finding

P0 successfully materialized the 2026 TWSE calendar but the NCDR dynamic feed
did not prove historical closure completeness. R1 then used a separate DGPA
daily/archive authority. R1 stopped after one daily GET because its parser
assumed that the displayed date must be inside an `h1`/`h2`/`h3` element. R2
repaired that DOM-shape assumption and made one daily GET. Its parser selected a
small semantic subject container, then rejected the page whenever the subject
phrase appeared more than once across all visible page text. Independent review
did not accept R2's `DGPA_SOURCE_DRIFT_OBSERVED` provider disposition: the
evidence established an unadjudicated semantic presentation duplication, not a
provider contract violation.

R3 replaces the page-wide phrase-count gate with bounded semantic candidates.
Each candidate carries source block sequence, tag/depth, normalized subject
identity, bound status date, normalized status signal, link/exclusion flags,
and an excerpt limited to 300 characters. Nested duplicate blocks are collapsed
only when their visible text is contained by a shallower presentation block.
Independent candidates must bind to the same date and equivalent status; date
or status disagreement fails closed. Unbound independent presentations remain
ambiguous. Candidate diagnostics are retained separately from daily adjudication
so a failure can be reviewed without retaining page HTML.

The canonical status vocabulary is `NO_CLOSURE_NOTICE`, `TAIPEI_NORMAL`,
`TAIPEI_MORNING_CLOSURE`, `TAIPEI_FULL_DAY_CLOSURE`,
`TAIPEI_AFTERNOON_CLOSURE`, or unresolved. No majority selection is used.
Existing attribution, explicit update timestamp, target-date, and Taipei
closure mapping checks remain in force. The existing I3 resolver and P0
calendar are not modified or refreshed.

## R3 bounded re-observation

R3 is a separate one-run DGPA authority. Its only permitted requests are one
daily GET, up to four sequential official archive-index GETs, and up to one
discovered official archive-detail GET, six total. A failed/ambiguous daily
adjudication stops before archive access; there is no daily refetch. Archive
negative evidence remains valid only after continuous chronological traversal
crosses 2026-10-15. Closure completeness is scoped only to
`complete_for_i3_resolution_window`; the resolver is called only when both
2026-10-16 and 2026-10-15 have been adjudicated.

The run directory, exact pre-network commits, evidence hashes, request counts,
candidate diagnostics, disposition, and offline verification results are
recorded in the corresponding `acceptance_runs/l3-a6-p0-r3-*` artifacts. This
candidate does not authorize market-source recertification. A6 market authority
remains unconsumed; P01-P18, B01-B05 and T86 remain outside this run.

## Containment

No P0/R1/R2 evidence is rewritten. No TWSE calendar refetch, I3 resolver change,
market-source request, Security Master/Watchlist/Result/Audit write,
Catalog/Route mutation, retry, sleep, polling, or scheduler is authorized or
performed by the R3 implementation. Candidate disposition and evidence are
completed after the single authorized R3 observation; no second run is allowed
under this authority.
