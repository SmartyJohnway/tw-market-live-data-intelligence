# Phase H H3-R4 — Portable Production Source Closure

Status: **OWNER-RESEARCHED / SOURCE CLOSURE COMPLETE / NO PORTABLE PRODUCTION H3 ROUTE AUTHORIZED**

Date: 2026-09-24  
Project: tw-market-live-data-intelligence  
Baseline main: `ca81969b4ebf8b5390816c8ebb0be00ba90a2c5c`

## 1. Question

Under the frozen Owner product boundary, can TWSE or TPEx provide a production H3 `recent_performance` route that is:

- official;
- free/public;
- portable;
- non-credential-dependent;
- unattended-automation-authorized;
- fresh-install capable;
- target-scoped and request-time bounded;
- sufficient for 1..20 completed-session lookback observations plus one governed end observation;
- compatible with the no-local-accumulation / no-background-history rule?

This record also evaluates whether an explicitly user-supplied official historical export should be promoted into the current production product path.

## 2. TWSE public-history findings

The official TWSE historical individual-stock surface provides:

- stock-code query;
- month/date query;
- daily trade volume;
- trade value;
- OHLC;
- close;
- transaction count;
- CSV download;
- official monthly historical records.

The historical data clearly exists and is usable for manual verification.

However, the TWSE website Terms of Use prohibit automated downloading through automated devices, scripts, crawlers, scrapers, or similar tools unless the method has been approved by TWSE or prior consent has been obtained.

Therefore:

```text
TWSE official historical data exists
= YES

TWSE official browser/manual CSV export
= YES

TWSE unattended production automation authority
= NOT PROVEN / PROHIBITED BY DEFAULT TERMS

TWSE portable unattended H3 production route
= NO
```

The human-facing `STOCK_DAY` / historical query surface remains `manual_verification`, not a production API.

## 3. TWSE Government Open Data / OpenAPI

Government Open Data dataset 11549 is:

- official;
- free;
- ODGL-1.0;
- daily updated;
- machine-readable;
- automation-authorized through the OpenAPI/Open Data lane.

It does not provide arbitrary stock/date bounded history for fresh-install H3.

The Government Open Data Platform separately records a request asking for historical stock/day lookup by date and code because the existing public dataset exposes only the currently updated stock information rather than the requested historical-query capability.

Therefore:

```text
TWSE latest EOD machine evidence
= AVAILABLE

TWSE free official bounded recent-history retrieval
= NOT AVAILABLE

H0-SRC-09
= REMAINS UNSATISFIED
```

## 4. TPEx public-history findings

The official TPEx individual-stock daily-trading history surface provides:

- security-code or keyword query;
- year/month selection;
- daily historical records;
- HTML export;
- CSV export;
- UTF-8 CSV export;
- historical coverage published from ROC year 83 (1994).

The data clearly exists and is usable for manual verification.

However, TPEx website Terms of Use prohibit automated downloading through automated devices, scripts, crawlers, scrapers, or similar tools unless the method has been approved by TPEx or prior consent has been obtained.

Therefore:

```text
TPEx official historical data exists
= YES

TPEx official browser/manual CSV export
= YES

TPEx unattended production automation authority
= NOT PROVEN / PROHIBITED BY DEFAULT TERMS

TPEx portable unattended H3 production route
= NO
```

The human-facing historical surface remains `manual_verification`, not a production API.

## 5. TPEx free OpenAPI

The previously accepted H3-R1 decision remains unchanged:

```text
tpex_mainboard_daily_close_quotes
= official latest EOD source
= not arbitrary requested-date history
= insufficient for fresh-install 1..20 H3
```

No newly identified free TPEx OpenAPI endpoint closes H0-SRC-10.

Therefore:

```text
H0-SRC-10
= REMAINS UNSATISFIED
```

## 6. E-Data Shop consequence

The Owner Product Source Boundary dated 2026-09-24 is controlling:

```text
TPEx E-Data Shop / EDIS
= RESEARCH_ONLY
= NOT A PRODUCTION ROUTE
= NOT A PRODUCT FALLBACK
= NOT A PORTABLE INSTALL DEPENDENCY
```

H3-I1A and H3-I1B remain accepted dormant research/reference assets.

No EDIS credentials, subscription, authenticated probe, provider continuity, or production integration is required for Phase H product work.

EDIS cannot be used to close the H3 production source gap.

## 7. Explicitly user-supplied official export evaluation

A user may manually download an official TWSE/TPEx historical CSV through the exchange-provided browser export surfaces.

Local parsing of an explicitly supplied file would avoid unattended exchange-site automation.

However, the current production contracts do not provide a truthful sufficient authority model for promoting such a file into an H3 production source.

Current gaps include:

1. `recent_performance_evidence.v1` records source family, source contract, retrieval time, and citations but does not distinguish:
   - system-retrieved official evidence;
   - Owner/operator-supplied evidence claimed to originate from an official export.

2. A user-supplied CSV is not cryptographically signed by the exchange. The runtime can validate structure, target, dates, values, and file hash, but cannot independently prove that the supplied bytes originated from the claimed official website.

3. Request V3 and the six-tool MCP workflow do not currently define a governed file-import binding for H3.

4. Treating user-supplied bytes as fully verified official production evidence would overstate provenance.

Decision:

```text
USER-SUPPLIED OFFICIAL HISTORICAL EXPORT

research/manual verification candidate
= YES

future operator-assisted import candidate
= YES

current production H3 route
= NO

current default fallback
= NO

current Phase H closure route
= NO
```

A future separately authorized tranche MAY design an operator-assisted import contract with explicit acquisition/provenance state.

That future design MUST distinguish operator-supplied evidence from independently acquired official evidence and MUST NOT silently label user-provided bytes as independently verified official source retrieval.

This future option is DEFERRED and is not required for the current H3-R4 source decision.

## 8. H3-R4 production-source conclusion

Under the current Owner product boundary:

| Market | Free official latest EOD | Official manual history | Unattended public history authorized | Portable production H3 route |
|---|---|---|---|---|
| TWSE | YES | YES | NO | **NONE** |
| TPEx | YES | YES | NO | **NONE** |

Therefore:

```text
APPROVED_PORTABLE_H3_PRODUCTION_ROUTE
= NONE

TWSE H3 runtime
= BLOCKED / INACTIVE

TPEx H3 runtime
= BLOCKED / INACTIVE

recent_performance.runtime_executable
= false

local history accumulation
= PROHIBITED

browser scraper promotion
= PROHIBITED

credential-gated provider workaround
= PROHIBITED BY OWNER PRODUCT BOUNDARY
```

## 9. Phase H completion consequence

The frozen Safety-Belt Completion Contract requires:

- at least one active governed H3 production route for every market claimed H3 safety-complete;
- bounded-live H3;
- mandatory H10 Full 20D Reference acceptance;
- real H2/H3 upstream evidence reaching H4/H5.

It also explicitly states that if no governed portable default H3 route can be proven for a market, that market MUST NOT be represented as H3 safety-complete.

Therefore, after H3-R4:

```text
TWSE H3 safety-complete
= NO

TPEx H3 safety-complete
= NO

Roadmap Phase H closure under current frozen completion scope
= NOT YET AVAILABLE
```

This is not an implementation failure.

The deterministic H3 core remains valid and can prove H10/H11 semantics through governed fixtures, but deterministic fixtures do not satisfy the separate production-route and bounded-live-H3 closure requirements.

## 10. Owner decision space after H3-R4

The frozen completion contract already permits three choices when no governed portable H3 route exists:

1. keep Phase H open for the affected market;
2. approve a narrower market-specific Phase H closure;
3. separately change Roadmap scope.

H3-R4 does NOT make that Owner decision.

No market is silently removed from the Phase H claim.

No Roadmap checkbox is changed.

## 11. Recommended next work

Do NOT spend additional implementation effort on another historical-data adapter unless new official source authority appears.

The next work should be an explicit Phase H scope/closure decision:

### Path A — preserve current completion contract

Keep Phase H open while the H3 source gap remains.

### Path B — Owner-approved narrower safety-belt closure

Define Phase H product truthfully as:

- H2/H4/H5 interpretation-safety where governed evidence exists;
- H3 deterministic semantics implemented;
- H3 live recent-history unavailable in portable default runtime;
- ordinary interpretation blocked when H3 coverage is unavailable;
- no claim of TWSE/TPEx H3 safety-complete.

This requires an explicit Owner amendment to the frozen completion scope before Roadmap closure.

### Path C — future operator-assisted import

Separately design a provenance-aware user-supplied official CSV import lane.

This is optional and must not be used as an implicit substitute for Path A/B.

## 12. No runtime mutation

This decision changes no:

- schema;
- Catalog;
- Routing;
- executor registry;
- source activation;
- MCP tool;
- Request/Result/Audit behavior;
- Phase I state;
- Roadmap checkbox.

Current required runtime state remains:

```text
H2 activation = false
H3 activation = false
recent_performance.runtime_executable = false
routing_status = blocked
MCP tool count = 6
Phase I = NOT_STARTED
```

## 13. Research basis

Current official public evidence reviewed:

- TWSE historical individual-stock query / CSV export;
- TWSE Terms of Use;
- Government Open Data dataset 11549;
- Government Open Data historical-query request 136936;
- TPEx historical individual-stock daily-trading query / CSV export;
- TPEx Terms of Use;
- current TWSE/TPEx OpenAPI conclusions from H3-R1;
- Owner EDIS product-source boundary from 2026-09-24.

This record is additive and does not rewrite H3-R1, H3-R2, H3-R3, H3-I1A, or H3-I1B historical evidence.
