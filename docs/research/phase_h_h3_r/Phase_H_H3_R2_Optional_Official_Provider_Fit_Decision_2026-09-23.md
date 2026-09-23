# Phase H H3-R2 — Optional Official Provider Fit Decision

Status: **PARTIAL DECISION COMPLETE / NO PORTABLE DEFAULT ROUTE / H3-I STILL NOT AUTHORIZED**

Date: 2026-09-23  
Project: tw-market-live-data-intelligence  
Baseline: ac8a3a8620c61b3636ab806bb71643b0fdaa632f

## 1. Question

Can an official exchange-operated optional provider satisfy the H3 fresh-install requirement:

> On installation day, obtain enough governed official completed-session close and volume evidence to form up to a 20-session lookback plus one governed end observation, without local historical accumulation?

This research covers provider/public-contract fit only. It does not authorize subscription purchase, credentials, production integration, or H3-I.

## 2. TWSE Data E-Shop — Daily Quotes

Current official product evidence establishes:

- product: Daily Quotes / 每日收盤行情;
- daily production;
- securities code;
- OHLC;
- closing price;
- trading volume;
- transaction count;
- trading value;
- data start date extends back decades;
- data may be ordered from the product's data start date according to the desired date range;
- one online order may cover up to five years;
- internal-use subscription currently NT$1,000/month;
- external-use subscription currently NT$1,500/month.

This resolves an important H3-R question:

~~~text
TWSE E-Shop historical continuity
= PUBLICLY PROVEN
~~~

A fresh operator can order past Daily Quotes data instead of waiting for future accumulation.

### Remaining automation question

The Daily Quotes product page explicitly lists shipment methods such as download and email.

The E-Shop home page states that the platform provides delivery mechanisms including email, URL and API download.

The public pages reviewed do not prove that the Daily Quotes product itself exposes a documented unattended API/URL contract suitable for direct H3 runtime execution.

Therefore:

~~~text
TWSE E-Shop data depth / continuity
= PASS

TWSE E-Shop official provider role
= PASS

TWSE E-Shop product-specific automated runtime transport
= NOT PROVEN FROM PUBLIC CONTRACT

TWSE H3 optional-provider disposition
= OPTIONAL_PROVIDER_CAPABLE_DATA
  / AUTOMATION_TRANSPORT_PENDING
~~~

This is materially stronger than the earlier generic provider-pending state, but it is not yet production activation authority.

## 3. TPEx E-Data Shop — End-of-Day

Current official product evidence establishes:

- daily End-of-Day products;
- account/subscription terms;
- downloadable/API-document product surface;
- historical data can be subscribed for the previous month and earlier;
- subscription can cover data after the subscription start/current day;
- some cited API-document product surfaces currently show NT$0/month external use, subject to member subscription terms.

However, the published date-range model creates a fresh-install continuity gap.

Example:

~~~text
installation / subscription date = middle of current month

history purchase
= previous month and earlier

subscription
= today forward

missing
= earlier sessions in the current month
~~~

Those missing current-month prior sessions may be required to form the last 20 completed trading sessions.

The public contract reviewed does not establish a mechanism to retrieve that gap immediately on day one.

Therefore:

~~~text
TPEx E-Data Shop official provider role
= PASS

historical older-month availability
= PASS

future subscription availability
= PASS

arbitrary fresh-install last-20-session continuity
= NOT PROVEN

TPEx H3 optional-provider disposition
= OPTIONAL_PROVIDER_ONLY
  / FRESH_INSTALL_CONTINUITY_GAP
~~~

## 4. Portability consequence

Neither optional provider becomes a mandatory fresh-install dependency.

The H0 rule remains:

~~~text
portable installation must remain valid without paid/account provider
~~~

Provider absence must yield provider_unavailable / route inactive / partial or unsupported evidence as applicable.

## 5. H3-R status after R1 + R2

### TWSE

~~~text
free OpenAPI bounded history
= NO

human-facing history
= official data exists
= provider automation authority unresolved

E-Shop historical Daily Quotes
= sufficient historical depth publicly proven
= automated product-specific delivery contract not yet proven

current disposition
= OPTIONAL_PROVIDER_CAPABLE_DATA
  / AUTOMATION_TRANSPORT_PENDING
~~~

### TPEx

~~~text
free OpenAPI bounded history
= NO

human-facing history
= official data exists
= provider automation authority unresolved

E-Data Shop
= official provider
= older history + forward subscription
= fresh-install current-month continuity gap

current disposition
= OPTIONAL_PROVIDER_ONLY
  / FRESH_INSTALL_CONTINUITY_GAP
~~~

## 6. H3-I decision

H3-I remains NOT AUTHORIZED.

Reason:

- no free portable default bounded-history route has been proven for either market;
- TWSE optional provider still lacks a product-specific public automation contract;
- TPEx optional provider does not publicly prove arbitrary fresh-install last-20-session continuity.

## 7. Remaining bounded research

### TWSE provider clarification

One question now matters:

> Does the Daily Quotes subscription expose an exchange-approved programmatic URL/API retrieval method for arbitrary subscribed historical dates, or is delivery limited to manual/account download and email for this product?

A positive official answer would make TWSE a strong optional-provider H3 implementation candidate.

### TPEx provider clarification

One question now matters:

> Can a new subscriber obtain earlier completed sessions from the current month immediately, through the End-of-Day product/API or another official product, so that previous-month history plus current-month data forms a continuous last-20-session window?

Without that, TPEx cannot satisfy fresh-install H3 through E-Data Shop alone.

## 8. Current H3 conclusion

~~~text
APPROVED_DEFAULT_ROUTE          none
APPROVED_WITH_CAVEATS           none yet

TWSE optional provider          promising / transport clarification required
TPEx optional provider          continuity gap

H3-I                            NOT AUTHORIZED
local accumulation              prohibited
background collection           prohibited
human-page scraper promotion    not approved
~~~

## 9. Official references reviewed

TWSE:
- Data E-Shop Daily Quotes / 每日收盤行情
- Data E-Shop home page delivery description
- Data E-Shop historical information category

TPEx:
- E-Data Shop End-of-Day API document/product surface
- E-Data Shop subscription terms
- E-Data Shop historical/subscription date-range rules
