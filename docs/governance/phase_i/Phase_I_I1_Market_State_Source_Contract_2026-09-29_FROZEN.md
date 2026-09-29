# Phase I I1 — Market State Source Contract
## Frozen Offline Authority

**Date:** 2026-09-29  
**Status:** `FROZEN / PASS`  
**Capability:** `market_state_context`  
**JSON contract SHA-256:** `0073c606f8319fdcb7a97b0330db2afd996b09038497a64c8d26cb613b0d2cf7`

## 1. Purpose

This record closes the source-row mapping blocker found at the start of I1 implementation.

It defines the exact offline row shapes and unit semantics that Codex may use to implement deterministic, zero-network I1 normalizers and fixtures.

It does **not** authorize live source probing, production executor registration, route activation, live acceptance, or merge.

## 2. I1 source set

### 2.1 TWSE FMTQIK

Official surface:

`https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK`

Exact JSON keys:

- `Date`
- `TradeVolume`
- `TradeValue`
- `Transaction`
- `TAIEX`
- `Change`

Official semantic mapping:

| Source key | Meaning | Unit | I1 normalized concept |
|---|---|---|---|
| `Date` | 日期 | ROC compact `YYYYMMDD` | `official_trade_date` |
| `TradeVolume` | 成交股數 | shares | `turnover.volume` |
| `TradeValue` | 成交金額 | TWD | `turnover.value` |
| `Transaction` | 成交筆數 | transactions | optional `turnover.transactions` |
| `TAIEX` | 發行量加權股價指數 | index points | `benchmark.close_index` |
| `Change` | 漲跌點數 | index points | `benchmark.change_points` |

`Change` is **not percentage return**.

### 2.2 TWSE breadth — twtazu_od

Official surface:

`https://openapi.twse.com.tw/v1/opendata/twtazu_od`

Exact JSON keys:

- `出表日期`
- `類型`
- `上漲`
- `漲停`
- `下跌`
- `跌停`
- `持平`
- `未成交`
- `無比價`

I1 MUST select only:

`類型 == 股票`

`整體市場` is not a permitted fallback.

Breadth values are security counts.

### 2.3 TPEx mainboard market highlight

Official surface:

`https://www.tpex.org.tw/openapi/v1/tpex_mainborad_highlight`

Exact Swagger keys:

- `Date`
- `ListedCompanyNumbers`
- `AuthorizedCapital`
- `MarketCapitalization`
- `DailyTradingValue`
- `DailyTradingVolume`
- `CloseIndex`
- `IndexChange`
- `PriceRiseCompanyNumbers`
- `LimitUpCompanyNumbers`
- `PriceDeclineCompanyNumbers`
- `LimitDownCompanyNumbers`
- `PriceFlatCompanyNumbers`
- `UnmatchedCompanyNumbersSuspensionStocksIncluded`

Official unit semantics:

| Source key | Unit |
|---|---|
| `AuthorizedCapital` | TWD million (`佰萬元`) |
| `MarketCapitalization` | TWD million (`佰萬元`) |
| `DailyTradingValue` | TWD million (`佰萬元`) |
| `DailyTradingVolume` | thousand shares (`仟股`) |
| `CloseIndex` | index points |
| `IndexChange` | index points |
| breadth company-number fields | company count |

`IndexChange` is **not percentage return**.

## 3. Date contract

All three I1 source families use ROC/Minguo compact dates in observed/API form.

Example:

`1150924 -> 2026-09-24`

Deterministic conversion:

`Gregorian year = ROC year + 1911`

Malformed dates fail closed.

Do not equate source date with local calendar today.

## 4. TWSE source alignment

A complete TWSE market-state evidence record requires:

1. a valid selected `FMTQIK` row;
2. an exact `類型=股票` breadth row;
3. equal normalized official dates.

If both source components are present but dates differ:

`status = partial`

The implementation must preserve both source dates and add a mismatch caveat.

It must not rewrite either date to force alignment.

## 5. TPEx completeness

A complete TPEx market-state evidence record may be assembled from one valid `tpex_mainborad_highlight` row.

No industry context is part of I1.

## 6. Unit policy

Do not convert units merely to make TWSE and TPEx look symmetric.

Examples:

- TWSE `TradeValue`: TWD
- TPEx `DailyTradingValue`: TWD million
- TWSE `TradeVolume`: shares
- TPEx `DailyTradingVolume`: thousand shares

The typed evidence must carry explicit unit metadata.

A future consumer may normalize units only under a separately governed derivation contract.

## 7. Fixture policy

Fixtures may be synthetic but must use the exact official source keys in this contract.

Do not commit full manually downloaded live payloads as fixtures.

Required fixture cases are enumerated in the companion JSON contract.

## 8. Authorization boundary

Owner decision: `OWNER_ACCEPTED_I1_SOURCE_CONTRACT`  
Owner decision ref: `USER_CHAT_2026-09-29_PHASE_I_I1_SOURCE_CONTRACT_ACCEPTANCE`

This frozen source contract authorizes only:

- offline I1 implementation;
- exact-key synthetic fixtures;
- pure zero-network normalizers;
- deterministic contract/result/audit tests.

It does not authorize:

- live source probing;
- live acceptance;
- production executor registration;
- runtime route activation;
- I2;
- I3;
- merge.

## 9. Companion machine-readable authority

Canonical machine-readable companion:

`PHASE_I_I1_MARKET_STATE_SOURCE_CONTRACT_2026-09-29_FROZEN.json`

SHA-256:

`892558ae7a9fd87f75d6ddecffb856a482c9a42de62911208d89c2d68342ded9`

When this MD and JSON disagree on a machine-checkable source mapping, the JSON companion is authoritative for I1 implementation.

## 10. Freeze decision

This contract is `FROZEN / PASS` under Owner decision `USER_CHAT_2026-09-29_PHASE_I_I1_SOURCE_CONTRACT_ACCEPTANCE`.

I1 offline implementation may resume. Live probing, live acceptance, production route activation, I2/I3 work, and merge remain unauthorized.
