# Phase L L3-A6-P0-R1 — DGPA Historical Closure Completeness

**Disposition:** `INCOMPLETE_AUTHORITY`
**Authority:** `USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_R1_DGPA_HISTORICAL_CLOSURE_COMPLETENESS_AUTHORIZATION`
**Canonical base:** `origin/main@7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`
**Parent P0 HEAD:** `4f840f424e45b7836b78ab6e8c09f79282df78dd`
**Branch:** `phase-l/l3-a6-bounded-live-source-drift-recertification`
**Run:** `l3-a6-p0-r1-20261016T042447Z`

## Purpose and boundary

P0 correctly ended `INCOMPLETE_AUTHORITY`: its NCDR/DGPA dynamic CAP feed
provided no authority for historical closure completeness. R1 was separately
authorized to inspect the official DGPA daily status page and historical archive
for exactly `2026-10-16` and `2026-10-15`. It does not repeat the P0 TWSE
calendar acquisition, perform P01-P18/B01-B05 recertification, request T86, or
consume the one-shot A6 market-source authority.

The existing `scripts/phase_i_i3_execution_date.py::resolve_i3_twse_source_trade_date`
and calendar resolver were not modified. Their completeness gate and no-weekday-
fallback behavior remain unchanged. The retained P0 calendar was revalidated
read-only against normalized SHA-256
`28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8`.

## R1 pre-network authority

The R1 plan fixes the P0 evaluation time at
`2026-10-16T11:38:22+08:00`, the two-date coverage window, official DGPA
endpoints, and ceilings of 2 daily / 6 archive-index / 2 archive-detail / 10
total GETs. It explicitly prohibits P01-P18, B01-B05, T86 and consuming A6
market authority. The offline implementation and tests were committed before
network access at `96fc89efeaad0f36e6cd4716208d54628c327bb9` (tree
`7c12102c364c045c6b1b6784c0f5b9fc3fc273d8`); reservation binding was committed
at `314f0b1f501a0f1398c599eb7ca93bb69edab03e`. Runner `--preflight-only`
passed with zero external requests.

## Acquisition and adjudication

Exactly one authorized request was attempted:

| Sequence | Purpose | Endpoint | HTTP | Bytes | Response SHA-256 |
|---:|---|---|---:|---:|---|
| 1 | `INITIAL_DAILY_STATUS` | `https://www.dgpa.gov.tw/typh/daily/nds.html?uid=31` | 200 | 15,037 | `db8fc2c63a0334069400d9532402b31d0f5cc8d87c17e51ef35887fbf256f879` |

The bounded parser could not establish that the displayed heading represented
exactly `2026-10-16` (`dgpa_daily_displayed_date_mismatch`). No raw HTML was
retained. This is recorded as unresolved authority, not as a claim that the
provider is permanently unavailable or that the source was removed. Under the
stop rule, R1 made no archive-index or detail request and did not refetch the
daily page. Consequently, the `2026-10-15` archive condition was not inspected.

The exact request counts are:

```text
daily status = 1 / 2
archive index = 0 / 6
archive detail = 0 / 2
total = 1 / 10
```

No `closure_authority_complete=true` claim is made. The I3 resolver was not
called, P17 remains unresolved, and no weekday/manual fallback was used.

## Retained evidence

Run artifacts are under
`docs/governance/phase_l/acceptance_runs/l3-a6-p0-r1-20261016T042447Z/`.
`daily_adjudication_failure.json` binds the bounded parser outcome to the
response hash without retaining provider content. `authority_reservation.json`
and `authority_consumed.json` show that R1 authority was consumed while A6
market authority remained unconsumed. `manifest.json` binds seven retained JSON
artifacts; manifest SHA-256 is
`4ad4d9f66fd5c49187234beea8313077045de656e91a42a44484acb6bb9d71cb`.

## Offline verification

With the external-network socket guard active:

```text
R1 + P0 authority tests + existing I3 execution-date tests: 43 passed
external socket attempts in offline gate: 0
```

The source registry, Portable Catalog sync, runtime/Skill exact-six,
V1 public-contract and Phase H V3 validators passed. `py_compile` and
`git diff --check` passed. The implementation adds no resolver/calendar or
production source runtime changes. MCP remains exactly six tools.

## Stop boundary

R1 ends `INCOMPLETE_AUTHORITY`. Do not repeat the daily request or start archive
inspection under this consumed run. Any further DGPA inspection requires fresh
Owner direction. The original A6 market-source authority remains
`AUTHORIZED / NOT CONSUMED`; market recertification has not started. No
Security Master, Watchlist, Result/Audit, Catalog, Route or production-state
mutation occurred. No retry loop, sleep/backoff, polling, scheduler or
background monitor was added. A6 market recertification, A7, L4-L7 remain
unstarted.
