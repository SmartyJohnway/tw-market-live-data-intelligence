# Phase H H3 — Owner Official-Web Automation Product Inclusion Decision

Status: **OWNER DECISION / SUPERSEDING PRODUCT BOUNDARY**

Date: 2026-09-24  
Project: tw-market-live-data-intelligence  
Baseline main: `57dc676faa4689804c9a015c99ef650022650367`

## 1. Owner decision

The Owner explicitly authorizes the TW-Market product to use bounded automated retrieval from official TWSE and TPEx historical web surfaces as a production-source candidate for H3 `recent_performance`.

This decision supersedes the product exclusion recorded by:

- `Phase_H_H3_R4_Portable_Production_Source_Closure_2026-09-24.md` for the question of whether official historical web automation may enter the product;
- any earlier planning language that limited these official historical web surfaces to manual verification only.

Historical records remain historically correct and MUST NOT be rewritten as if this Owner decision existed earlier.

## 2. Important authority distinction

This is an Owner product authorization.

It is NOT a statement that TWSE or TPEx has granted crawler/scraper/automated-download permission.

Current official website terms state that automated downloading with crawlers, scrapers, instruction code, scripts, or similar automated tools is prohibited unless the exchange has agreed to the method or prior consent has been obtained.

Therefore the product MUST preserve these two facts separately:

```text
official_source_authority
= official exchange website

owner_product_authorization
= approved

provider_automation_permission
= not established / terms-conflicted
```

No implementation, Catalog entry, Route, Result, Audit, documentation, or acceptance record may misstate Owner approval as exchange permission.

## 3. Product inclusion

The following source families MAY now be implemented as H3 production candidates:

### TWSE

Official individual-stock historical daily trading report:

```text
TWSE STOCK_DAY
```

Observed public report behavior supports:

- exact stock code;
- requested month/date;
- daily trade volume;
- trade value;
- open;
- high;
- low;
- close;
- change;
- transaction count;
- official historical month retrieval.

### TPEx

Official individual-stock daily-trading history surface:

```text
TPEx 個股日成交資訊
```

The official surface exposes:

- exact security-code/keyword query;
- requested year/month;
- historical daily trading records;
- HTML export;
- CSV export;
- UTF-8 CSV export;
- published history beginning in 1994/01.

The exact unattended request contract for TPEx MUST be separately source-probed and frozen before production implementation. The UI existence of CSV export does not by itself authorize guessing an endpoint.

## 4. Bounded crawler contract

Any H3 official-web automation implementation MUST remain:

- explicit;
- request-triggered;
- exact-target-scoped;
- lookback-bounded to the H3 request;
- month-bounded at transport level;
- execute-once;
- low-frequency;
- auditable;
- missing-aware;
- source-contract-validated.

A 1..20 trading-session request MAY require a small bounded number of month queries sufficient to obtain the requested observations plus the governed end observation.

The implementation MUST calculate the minimum necessary request window and MUST NOT fetch arbitrary full history.

## 5. Explicitly prohibited crawler behavior

Owner authorization does NOT authorize anti-bot or access-control circumvention.

TW-Market MUST NOT implement:

- CAPTCHA bypass;
- authentication bypass;
- access-control bypass;
- IP rotation to evade blocking;
- proxy rotation to evade blocking;
- user-agent spoofing intended to evade detection;
- stealth-browser or fingerprint evasion;
- rate-limit bypass;
- deliberate robots/technical-control evasion;
- concurrent market-wide harvesting;
- hidden background collection;
- scheduled daily scraping;
- automatic historical accumulation;
- full-market archive creation;
- retry storms;
- scraping after an explicit provider block;
- fallback to unofficial mirrors solely to bypass the official site.

If the official site blocks the bounded request, returns an anti-bot challenge, changes contract, or requires access not available to the product:

```text
STOP
FAIL CLOSED
SOURCE_FAILED / COVERAGE_INCOMPLETE
```

Do not evade the control.

## 6. Request-budget policy

A future implementation MUST define a hard maximum operation budget.

The default design target is:

```text
one target
+
one authorized H3 request
+
minimum month slices required for N<=20
```

Because 20 valid trading-session lookback observations plus one governed end observation may cross a month boundary, the adapter may retrieve more than one month only when required by the explicit request.

It MUST stop as soon as sufficient governed observations are obtained or the hard request bound is reached.

No reusable history cache may be introduced merely to reduce future requests.

## 7. Source identity and provenance

Official web automation evidence MUST preserve:

- exchange identity;
- source surface;
- exact target;
- requested month/date;
- retrieval timestamp;
- source-contract identifier;
- response hash where appropriate;
- citation/source URL in sanitized non-secret form;
- parser/normalizer version;
- coverage and missing semantics.

The product must distinguish:

```text
source is official
```

from:

```text
provider permits automated retrieval
```

These are not equivalent.

## 8. H3 evidence semantics remain unchanged

This Owner decision does NOT weaken the frozen H3 evidence contract.

Still required:

- `lookback_trading_days = 1..20`;
- N+1 distinct close proof for N-day raw return;
- exact completed-session dates;
- no interpolation;
- no forward fill;
- no fabricated sessions;
- exact target identity;
- raw unadjusted return only;
- completed-session volume semantics;
- explicit partial / insufficient / unavailable / source_failed behavior.

H3-I0 remains the deterministic derivation authority.

## 9. Existing EDIS boundary remains

This decision does NOT reopen TPEx E-Data Shop / EDIS.

EDIS remains:

```text
RESEARCH_ONLY
NOT A PRODUCTION ROUTE
NOT A PRODUCT FALLBACK
NOT A PORTABLE INSTALL DEPENDENCY
```

The new production candidate is the public official historical web surface, not EDIS.

## 10. User-supplied CSV lane

The future user-supplied official CSV import candidate remains separate and deferred.

Official-web automation is now the preferred H3 source-development direction.

No operator-supplied provenance contract is created by this decision.

## 11. Runtime status at this decision

This decision authorizes implementation work; it does not activate a route by itself.

Current runtime remains:

```text
recent_performance.runtime_executable = false
routing_status = blocked
phase_h_activation_state = inactive

H3 production web adapters = not yet implemented/accepted
H3 bounded-live web proof = not yet accepted

H2 activation = false
MCP tool count = 6
Phase I = NOT_STARTED
```

## 12. Implementation order

Implementation SHOULD proceed in bounded tranches:

### H3-I2A — TWSE STOCK_DAY bounded web adapter

Because the public request contract and historical month behavior are already sufficiently observable, implement and test the TWSE path first.

### H3-R5 / H3-I2B — TPEx exact web transport contract and adapter

First freeze the exact request/response/CSV contract through a bounded source probe.

Then implement the TPEx adapter.

### H3-I2C — governed H3 production orchestration

Only after one or both adapters are accepted:

- bind exact H3 request window;
- enforce request budgets;
- register approved route(s);
- wire Result/Audit provenance;
- perform bounded-live acceptance;
- then consider activation.

## 13. Reopening / external permission

If TWSE or TPEx later publishes an explicit automation permission, API, OpenAPI route, or written approval covering these historical surfaces, source governance SHOULD be updated to record that stronger authority.

If the provider explicitly blocks the implementation or sends a cease/request-not-to-automate instruction, the route MUST be disabled pending Owner review.

## 14. Decision summary

```text
OFFICIAL HISTORICAL WEB AUTOMATION
= FORMALLY INCLUDED IN PRODUCT DEVELOPMENT

TWSE STOCK_DAY
= APPROVED FOR BOUNDED ADAPTER IMPLEMENTATION

TPEx INDIVIDUAL DAILY HISTORY
= APPROVED FOR SOURCE-CONTRACT PROBE
  THEN BOUNDED ADAPTER IMPLEMENTATION

EXCHANGE AUTOMATION PERMISSION
= NOT ESTABLISHED

ANTI-BOT / ACCESS-CONTROL EVASION
= PROHIBITED

BACKGROUND HISTORY COLLECTION
= PROHIBITED

LOCAL HISTORY WAREHOUSE
= PROHIBITED

EDIS
= RESEARCH_ONLY
```
