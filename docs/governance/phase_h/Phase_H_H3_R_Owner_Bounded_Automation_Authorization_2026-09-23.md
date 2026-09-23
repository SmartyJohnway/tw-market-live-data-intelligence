
# Phase H H3-R — Owner Bounded Automation Authorization

Status: **OWNER AUTHORIZED — INTERNAL EXECUTION AUTHORITY ONLY**

Date: **2026-09-23**

Project: tw-market-live-data-intelligence  
Baseline main: e78bf2d103057b5a935128237005766483ff1168

## 1. Owner decision

The Owner explicitly authorizes programmatic acquisition for Phase H H3 research and future local-first execution when all of the following are true:

- exact target scoped;
- explicit user/Owner initiated request;
- lookback bounded to the H3 contract;
- one-shot or low-frequency request-time acquisition;
- no continuous crawler;
- no background polling;
- no startup acquisition;
- no full-market crawl for accumulation;
- no durable market-wide history warehouse;
- no automatic daily backfill.

The purpose is to obtain only the recent official reference evidence required for the current AI conversation.

## 2. Product rationale

This authorization follows the frozen H0 product boundary:

~~~text
20D = request scope
20D != storage requirement
~~~

and:

~~~text
local-first
+
target-scoped
+
time-bounded
+
explicit authorization
+
execute-once
~~~

The Owner does not require browser-only/manual interaction merely because the project is local-first. Programmatic acquisition is acceptable inside the project when source authority and source-use requirements permit it.

## 3. Critical authority separation

Owner authorization and upstream provider authorization are independent.

~~~text
Owner permits programmatic retrieval
!=
TWSE/TPEx has approved automated retrieval from every website surface
~~~

Current official TWSE and TPEx general website terms state that automated devices, scripts, crawlers, scrapers, or extraction programs may not download website data unless using a method approved by the exchange or with exchange consent.

Therefore this Owner authorization:

- removes an **internal project-policy objection** to bounded programmatic acquisition;
- does not convert a human-facing history page into an exchange-approved production API;
- does not override external terms, license, contract, authentication, or redistribution requirements;
- does not by itself close H0-SRC-09 or H0-SRC-10.

## 4. H3-R impact

H3-R shall now evaluate candidate sources on two independent axes.

### Axis A — Technical / product fit

Can the source, with bounded programmatic access, provide:

- exact target binding;
- official trade dates;
- completed-session close;
- completed-session volume;
- N+1 observation proof;
- 1..20 lookback;
- bounded request count and response size;
- truthful no-row/failure semantics?

Owner authorization for this technical evaluation is **YES**.

### Axis B — Source-use / automation authority

Is the exact programmatic access method:

- an official OpenAPI;
- Government Open Data / ODGL-authorized machine surface;
- an exchange-approved download/API mechanism;
- covered by an applicable provider/subscription agreement;
- or separately consented to by TWSE/TPEx?

Only a positive Axis B result may promote a route to portable/default production authority.

## 5. Human-facing history pages

For TWSE STOCK_DAY and the TPEx individual-stock history query:

~~~text
technical bounded-access investigation:
OWNER AUTHORIZED

portable/default production activation:
NOT AUTHORIZED BY THIS RECORD

provider automation authority:
NOT PROVEN
~~~

No repository documentation may represent these surfaces as approved unattended production APIs unless a later H3-R source-authority record establishes the exchange/provider approval basis.

## 6. Permitted H3-R research

The Owner authorizes research to determine:

- request/response behavior;
- date-selection behavior;
- exact target binding;
- row/session counts;
- field semantics;
- payload size;
- whether one or a bounded number of requests can form 1..20 completed-session evidence.

Where direct programmatic probing of a website surface would conflict with the provider's published terms, research should use documentation, manual inspection, approved OpenAPI/open-data surfaces, or separately approved provider access instead.

## 7. No change to anti-scope-creep contract

Still prohibited:

~~~text
continuous crawling
background polling
daily accumulation
full-market historical warehouse
automatic backfill
unbounded history download
unofficial fallback
contract weakening merely to fit a source
~~~

## 8. Governance effect

This record changes only the project's Owner authorization state:

~~~text
OWNER_BOUNDED_PROGRAMMATIC_ACQUISITION
false / unspecified
→
true
~~~

It does not change:

- recent_performance runtime_executable=false;
- H3 routing blocked;
- H3-I not started;
- any source activation state;
- any external license or provider authority;
- the six-tool MCP surface;
- Phase I state.

H3-R remains responsible for finding and proving the exact source-use authority needed for a production route.
