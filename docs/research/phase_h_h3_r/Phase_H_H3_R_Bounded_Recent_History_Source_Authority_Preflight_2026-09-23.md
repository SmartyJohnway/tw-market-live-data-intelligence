
# Phase H H3-R — Bounded Recent-History Source Authority Preflight

Status: **RESEARCH PREFLIGHT — DEFAULT PORTABLE ROUTE STILL NOT PROVEN**

Research date: **2026-09-23**

Project baseline: 976930aa2255c0baac847d860eb1198858bd2325

Capability: recent_performance

Scope: source-authority research only. This document does **not** authorize H3 adapter implementation, source activation, website scraping, licensed-provider integration, background accumulation, or bounded-live production execution.

## 1. Research question

H3 does not need a historical database.

The source question is narrowly:

> Can a fresh installation, for one exact TWSE or TPEx common-share target and one explicitly authorized request, obtain up to 20 prior valid completed official trading-session observations plus one governed end observation using an authorized machine-readable source?

The required evidence must support:

- exact market/security-code binding;
- official trade date;
- official close;
- completed-session volume;
- N+1 endpoint proof;
- 1..20 lookback;
- request-time bounded acquisition;
- explicit partial/missing/failure semantics;
- source provenance and citation;
- no local history accumulation.

## 2. Existing frozen H3 source state

The frozen H3 contract currently classifies:

~~~text
TWSE default fresh-install bounded route     NOT PROVEN
TPEx default fresh-install bounded route     NOT PROVEN
TWSE optional provider                        CONTRACT PENDING
TPEx optional provider                        CONTRACT PENDING
~~~

This preflight rechecks that conclusion against current official surfaces.

## 3. TWSE findings

### 3.1 Official OpenAPI / Government Open Data

Official TWSE OpenAPI documents STOCK_DAY_ALL and STOCK_DAY_AVG_ALL as public securities-trading datasets.

Government Open Data dataset 11549 — 個股日成交資訊 confirms official TWSE/FSC provenance, daily update, Government Data Open License v1, and fields including trade date, code, OHLC, volume, value and transactions.

The current open-data lane establishes a strong official latest-session source, but does not establish a fresh-install parameterized 1..20-session history contract.

Disposition:

~~~text
SOURCE AUTHORITY: strong
AUTOMATION AUTHORITY: approved for the open-data surface
H3 20D DEPTH: not proven
DEFAULT H3 ROUTE: not eligible yet
~~~

### 3.2 TWSE historical website query

The official TWSE STOCK_DAY website query exposes per-stock monthly daily trading history with trade date, volume, OHLC and close. Current and explicitly selected historical months are available through the human-facing query.

This proves the historical data exists on an official surface.

However, TWSE website terms state that, unless using a TWSE-approved method or with TWSE consent, automated devices, scripts, robots, spiders, crawlers or extraction programs may not download website data.

Therefore:

~~~text
DATA EXISTENCE: proven
HUMAN / MANUAL RESEARCH AUTHORITY: yes
UNATTENDED PRODUCTION AUTOMATION AUTHORITY: no
unless separately approved by TWSE
H3 DEFAULT ROUTE: NOT ELIGIBLE
~~~

The existence of a JSON-shaped response or downloadable result does not override this terms boundary.

### 3.3 TWSE Data E-Shop

TWSE Data E-Shop provides official subscription data services and states that delivery can include download, URL and API mechanisms.

The current Daily Quotes product provides daily OHLC, close, volume and value under paid internal/external-use subscription terms. Historical trading products also exist.

Disposition:

~~~text
ROLE: OPTIONAL_LICENSED_PROVIDER candidate
PORTABILITY: subscription/config dependent
H3-R STATUS: provider-fit research still required
DEFAULT PORTABLE ROUTE: NO
~~~

## 4. TPEx findings

### 4.1 Official TPEx OpenAPI / Government Open Data

TPEx official OpenAPI publishes tpex_mainboard_daily_close_quotes for mainboard daily closing quotes.

Government Open Data datasets 11370 — 上櫃股票行情 and 11371 — 上櫃股票收盤行情 confirm official TPEx/FSC origin, daily update, Government Data Open License v1 and close/OHLC/volume/value fields.

The documented open-data surface does not currently establish an arbitrary 1..20 prior-session query contract for one target.

Disposition:

~~~text
SOURCE AUTHORITY: strong
AUTOMATION AUTHORITY: approved for the open-data surface
H3 20D DEPTH: not proven
DEFAULT H3 ROUTE: not eligible yet
~~~

### 4.2 TPEx historical website query

TPEx provides an official 個股日成交資訊 history query and states that data is available from ROC year 83 (1994) onward, with HTML and CSV export.

This proves substantial official history exists.

But TPEx website terms likewise prohibit automated downloading through scripts, crawlers, extraction programs and similar mechanisms unless using a TPEx-approved method or with TPEx consent.

Therefore:

~~~text
DATA EXISTENCE: proven
HUMAN / MANUAL RESEARCH AUTHORITY: yes
UNATTENDED PRODUCTION AUTOMATION AUTHORITY: no
unless separately approved by TPEx
H3 DEFAULT ROUTE: NOT ELIGIBLE
~~~

A CSV-download button is not, by itself, production automation authority.

### 4.3 TPEx E-Data Shop

TPEx E-Data Shop provides official End-of-Day products under an account/subscription contract.

The currently published End-of-Day product page distinguishes:

- historical data: previous month and earlier;
- subscription: data from the subscription period forward.

The cited page currently displays an external-use price of NT$0/month, but account/subscription terms still apply.

This does not yet prove a fresh-install immediate recent-20-session route because current-month prior-session continuity for a new subscription is not established.

Disposition:

~~~text
ROLE: OPTIONAL_LICENSED_PROVIDER candidate
PORTABILITY: account/subscription dependent
FRESH-INSTALL 20D CONTINUITY: not proven
H3-R STATUS: provider-fit / acquisition-window research required
DEFAULT PORTABLE ROUTE: NO
~~~

## 5. Licensing conclusion

H3-R must keep three different questions separate:

~~~text
official data exists
!=
machine-readable response exists
!=
authorized unattended production automation
~~~

The TWSE and TPEx public historical query pages prove official data availability. Their website terms prevent treating those human-facing query/export surfaces as production scraping APIs without a separately approved method or consent.

This confirms the original H0 stop rule.

## 6. Current source-authority matrix

| Market | Candidate | Authority | Automation | Fresh-install 20D | Current H3 disposition |
|---|---|---|---|---|---|
| TWSE | OpenAPI / Government Open Data daily snapshot | official / ODGL | approved open-data use | not proven | PARTIAL_ONLY / NOT_H3_ROUTE |
| TWSE | public STOCK_DAY history query | official website | automated extraction not approved by site terms | data exists | MANUAL_RESEARCH_ONLY |
| TWSE | Data E-Shop daily/historical products | official licensed provider | contract-dependent | plausible, not proven | OPTIONAL_PROVIDER_RESEARCH |
| TPEx | OpenAPI / Government Open Data daily snapshot | official / ODGL | approved open-data use | not proven | PARTIAL_ONLY / NOT_H3_ROUTE |
| TPEx | public stock-pricing history query | official website | automated extraction not approved by site terms | data exists | MANUAL_RESEARCH_ONLY |
| TPEx | E-Data Shop End-of-Day | official subscription provider | account/contract-dependent | current-month continuity not proven | OPTIONAL_PROVIDER_RESEARCH |

## 7. Preliminary H3-R decision

The H0-SRC-09 / H0-SRC-10 blockers remain valid.

As of this preflight:

~~~text
TWSE default portable H3 route:
NO_GOVERNED_ROUTE PROVEN

TPEx default portable H3 route:
NO_GOVERNED_ROUTE PROVEN

Browser-history scraper workaround:
PROHIBITED

Local daily accumulation workaround:
PROHIBITED

H3-I implementation:
NOT AUTHORIZED YET
~~~

This is not an architecture failure. It is a truthful source-authority result.

## 8. Remaining H3-R work before final Owner decision

### H3-R1 — Open-data endpoint behavior proof

For TWSE and TPEx:

- issue a small fixed set of controlled requests against the official OpenAPI endpoint;
- prove exact response trade-date behavior;
- prove whether any documented query parameter can select earlier dates;
- record row count, unique trade-date count and exact target binding;
- record current schema fields;
- prove completed-session volume semantics;
- record call bound and response size.

### H3-R2 — Optional-provider fit

TWSE E-Shop:

- identify the minimal Daily Quotes / historical product combination capable of satisfying N+1 20D;
- confirm API/URL delivery semantics;
- confirm historical/current continuity for a new subscriber;
- confirm allowed internal/external software use;
- confirm credentials/config requirements;
- confirm whether acquisition is target-level or whole-market file download;
- estimate bounded request/file size.

TPEx E-Data Shop:

- identify the exact EOD product/file needed for close + volume;
- determine whether a new account can immediately obtain current-month prior sessions;
- determine whether history + subscription can form continuous last-20-session evidence on day one;
- confirm API authentication/delivery and use rights;
- determine whether acquisition is target-level or whole-market.

### H3-R3 — Product-boundary fit

Reject a provider candidate as a Phase H default if it requires:

- persistent local accumulation;
- unbounded multi-year download;
- full-market warehousing;
- mandatory paid credentials for every installation;
- redistribution terms incompatible with a portable public product.

## 9. Final H3-R outcomes

The final Owner-reviewed decision may classify each market as:

~~~text
APPROVED_DEFAULT_ROUTE
APPROVED_WITH_CAVEATS
OPTIONAL_PROVIDER_ONLY
PARTIAL_ONLY
NO_GOVERNED_ROUTE
~~~

If both markets remain NO_GOVERNED_ROUTE, Phase H safety-belt closure remains open unless the Owner separately changes the Roadmap/product scope.

## 10. Official references checked

TWSE:

- https://openapi.twse.com.tw/
- https://www.twse.com.tw/exchangeReport/STOCK_DAY
- https://wwwc.twse.com.tw/zh/terms/use.html
- https://data.gov.tw/dataset/11549
- https://data.gov.tw/dataset/11548
- https://eshop.twse.com.tw/en/
- https://eshop.twse.com.tw/en/product/detail/ef7b7785e2cb4793baca3644c8a74d4e

TPEx:

- https://www.tpex.org.tw/openapi/
- https://www.tpex.org.tw/zh-tw/mainboard/trading/info/stock-pricing.html
- https://www.tpex.org.tw/zh-tw/gtsm_disclaimer.html?l=zh-tw
- https://data.gov.tw/dataset/11370
- https://data.gov.tw/dataset/11371
- https://eshop.tpex.org.tw/en/product/detail/2c92e01394fcf4c7019518bffe06000c

## 11. Stop rule

Until H3-R1/R2 close enough source-authority questions for an Owner decision:

~~~text
recent_performance.runtime_executable = false
H3 route = blocked
H3-I = NOT STARTED
~~~

No workaround through website scraping, daily collection, or unofficial history is authorized.
