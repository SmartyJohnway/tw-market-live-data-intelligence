# Phase H H3-R1 — Free Official OpenAPI Decision

Status: **OWNER-RESEARCHED / DECISION COMPLETE**

Date: 2026-09-23  
Project: tw-market-live-data-intelligence  
Baseline: e033302fa78b81b7644f0de059d20c1c91321d31

## 1. Question

Can the existing free official TWSE / TPEx OpenAPI lanes satisfy H3 \`recent_performance\` for a fresh installation by retrieving 1..20 completed official trading sessions plus one governed end observation on demand?

## 2. TWSE decision

Selected endpoint:

\`\`\`text
https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
\`\`\`

Existing repository probe evidence from 2026-07-11 established:

- GET without parameters returned HTTP 200;
- response was a full latest-market array;
- all observed rows reported the same latest trade date;
- Swagger documented no request-date parameter;
- adding \`date=invalid&response=json\` still returned HTTP 200 and the same row count / same reported trade date;
- the probe explicitly concluded the extra date/query parameters were ignored.

Independent current public evidence from data.gov.tw also states that the currently available public dataset provides the dataset's updated single-day stock information, and a user request for date/code historical lookup remains a separate requested dataset capability.

Decision:

\`\`\`text
TWSE STOCK_DAY_ALL
official authority          = PASS
automation/open-data use    = PASS
latest EOD evidence         = PASS
requested-date history      = NOT SUPPORTED
fresh-install 1..20 H3      = FAIL
H3 default route            = NOT ELIGIBLE
\`\`\`

## 3. TPEx decision

Selected endpoint:

\`\`\`text
https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes
\`\`\`

Existing repository probe evidence from 2026-07-11 established:

- GET without parameters returned HTTP 200;
- response was a latest mainboard daily-close array;
- all observed rows reported the same latest trade date;
- Swagger documented no request-date parameter for this endpoint;
- adding \`date=invalid&response=json\` still returned HTTP 200 and the same latest trade date;
- the probe explicitly concluded the extra parameters were ignored.

The current TPEx Swagger inventory exposes many historical/statistical endpoints, but it does not expose a historical per-security daily OHLCV endpoint equivalent to the human-facing individual-stock history query.

Decision:

\`\`\`text
TPEx tpex_mainboard_daily_close_quotes
official authority          = PASS
automation/open-data use    = PASS
latest EOD evidence         = PASS
requested-date history      = NOT SUPPORTED
fresh-install 1..20 H3      = FAIL
H3 default route            = NOT ELIGIBLE
\`\`\`

## 4. H0-SRC consequence

This closes the free-OpenAPI question:

\`\`\`text
H0-SRC-09 TWSE free default bounded-history route
= NOT SATISFIED BY STOCK_DAY_ALL

H0-SRC-10 TPEx free default bounded-history route
= NOT SATISFIED BY tpex_mainboard_daily_close_quotes
\`\`\`

The sources remain valid and important for official latest EOD evidence. They simply do not implement H3 bounded history.

## 5. Human-facing history surfaces

Official human-facing history surfaces prove the data exists and can provide date/month history.

Owner internal authorization now permits bounded technical programmatic acquisition in principle.

However, current TWSE / TPEx website terms still do not establish unattended production automation authority for those human-facing surfaces.

Therefore:

\`\`\`text
technical feasibility research         = allowed by Owner
provider-approved production route     = not proven
portable/default H3 route              = not approved
\`\`\`

No scraper workaround is authorized by this decision.

## 6. Optional official provider findings

### TWSE Data E-Shop

Current official Data E-Shop facts:

- Daily Quotes includes security code, OHLC, closing price, trading volume, transactions and trading value;
- start date shown as 1992-01-04;
- period is daily;
- subscription unit is month;
- delivery supports download and the E-Shop generally advertises URL/API delivery services;
- internal-use price currently shown for Daily Quotes is NT$1,000/month;
- exact fresh-install historical continuity / historical API contract for an arbitrary recent 20-session request is not proven by the public product page.

Disposition:

\`\`\`text
TWSE E-Shop
= OPTIONAL_PROVIDER_CANDIDATE
fresh-install H3 fit
= REQUIRES PROVIDER-CONTRACT CONFIRMATION
\`\`\`

### TPEx E-Data Shop

Current official E-Data Shop facts:

- End-of-Day products are daily;
- history can be subscribed for the previous month and earlier;
- subscription can cover data after the subscription start;
- subscription/member terms apply;
- this split does not publicly prove that a new subscriber in the middle of a month can immediately obtain the missing earlier sessions of the same current month.

Disposition:

\`\`\`text
TPEx E-Data Shop
= OPTIONAL_PROVIDER_CANDIDATE
fresh-install arbitrary 20D continuity
= NOT PROVEN
\`\`\`

## 7. H3-R1 final decision

\`\`\`text
TWSE FREE OFFICIAL OPENAPI
NO_GOVERNED_H3_HISTORY_ROUTE

TPEX FREE OFFICIAL OPENAPI
NO_GOVERNED_H3_HISTORY_ROUTE

H3-I
NOT AUTHORIZED BY H3-R1

LOCAL ACCUMULATION
PROHIBITED

BACKGROUND COLLECTION
PROHIBITED
\`\`\`

This is a source capability result, not an architecture failure.

## 8. Next H3-R work

H3-R2 remains:

1. determine whether TWSE Data E-Shop has an approved delivery contract that can immediately provide a continuous last-20-session window to a new installation;
2. determine whether TPEx E-Data Shop can bridge current-month prior sessions plus subscription data on day one;
3. if neither can satisfy portable fresh-install semantics, decide whether Phase H closes market-specifically, remains open, or requires a separately accepted product-scope adjustment.

## 9. Evidence

Repository evidence:

- research/probe_runs/m8a_official_eod_contract_preflight/m8a_twse_official_eod_probe_summary_20260711T102435Z.json
- research/probe_runs/m8a_official_eod_contract_preflight/m8a_tpex_official_eod_probe_summary_20260711T102435Z.json
- docs/protocol/M8A_OFFICIAL_EOD_ADAPTER_SCOPE_AND_CONTRACT_PREFLIGHT.md

Current official references reviewed:

- TWSE OpenAPI Swagger
- TPEx OpenAPI Swagger
- data.gov.tw dataset 11549
- data.gov.tw datasets 11370 / 11371
- TWSE Data E-Shop Daily Quotes
- TPEx E-Data Shop End-of-Day / subscription pages
