# Phase H H3 — Owner Product Source Boundary Decision

Status: **OWNER DECISION / PRODUCT BOUNDARY FROZEN**

Date: 2026-09-24  
Project: tw-market-live-data-intelligence  
Baseline main: `a095753ff2c1cf6aec867ee9452f500921b0ca98`

## 1. Owner decision

TPEx E-Data Shop / EDIS may be used for:

- source research;
- official contract study;
- format/parser validation;
- transport-security research;
- comparative provider analysis.

It MUST NOT become part of the TW-Market production product path.

This decision applies regardless of whether the provider is technically automatable.

## 2. Product baseline rule

The portable TW-Market product MUST NOT require:

- a TPEx E-Data Shop account;
- an API data-download account/password;
- a paid or subscribed EDIS product;
- EDIS credentials or secrets;
- EDIS entitlement;
- EDIS provider availability;

in order for a valid installation or normal product runtime to exist.

Absence of EDIS MUST NOT make installation invalid.

## 3. Existing H3-I1A / H3-I1B work

The accepted dormant components remain valid research/reference assets:

- H3-I1A — TPEx EDIS S37/S38 dormant file adapter;
- H3-I1B — TPEx EDIS dormant bounded authenticated transport.

They MAY remain in the repository as evidence of:

- official source-contract understanding;
- parser correctness research;
- bounded credential-bearing transport design;
- future source comparison.

They MUST remain dormant and MUST NOT be promoted into the product execution path.

Specifically, they MUST NOT be:

- registered as production executors;
- selected in the Capability Catalog;
- selected in the Routing Matrix;
- made a fresh-install dependency;
- made a runtime credential requirement;
- exposed as a seventh MCP tool;
- invoked automatically by startup, polling, scheduling, background refresh, or hidden fallback;
- used to justify a production H3 coverage claim.

No EDIS live authenticated probe is required for Phase H product completion.

## 4. Source-role consequence

For product purposes:

```text
TPEx E-Data Shop / EDIS
= RESEARCH_ONLY
= NOT A PRODUCTION ROUTE
= NOT A PRODUCT FALLBACK
= NOT A PORTABLE INSTALL DEPENDENCY
```

This Owner decision supersedes earlier planning language that treated TPEx EDIS as a possible future optional-provider production route.

Historical research records remain historically correct and MUST NOT be rewritten as though this decision had existed earlier.

## 5. H3 production-source policy

The production H3 search space is now limited to routes that are compatible with the product baseline, including:

- free official machine-readable sources with sufficient bounded semantics;
- official public routes whose unattended automation authority is explicitly established;
- explicitly user-supplied governed evidence where separately authorized and contract-compatible;
- other portable, non-credential-required official evidence lanes proven in future research.

Credential-gated or subscription-gated exchange data services may still be researched but are excluded from the default TW-Market product architecture unless the Owner explicitly reopens this decision.

## 6. Missing-data consequence

If no portable authorized official source can provide the requested recent-history coverage, TW-Market MUST report the limitation truthfully.

Allowed outcomes include:

- `partial`;
- `insufficient`;
- `unavailable`;
- `unsupported`;
- `provider_unavailable` only where a provider concept remains relevant to a non-product research path;
- H4 `coverage_incomplete`.

The product MUST NOT close the gap by:

- silently requiring EDIS;
- hidden local accumulation;
- automatic backfill;
- scraping browser-only pages;
- unofficial third-party substitution;
- inventing historical observations.

A blocked interpretation caused by incomplete H3 evidence is a valid Phase H safety outcome.

## 7. Phase H consequence

Phase H remains a market-interpretation safety system, not a promise that every requested historical baseline is always available.

Therefore:

```text
safe refusal / coverage_incomplete
>
credential-gated hidden dependency
```

Phase H closure MUST distinguish:

- scenarios where complete bounded H3 evidence is available;
- scenarios where coverage is incomplete and ordinary interpretation is correctly blocked.

It MUST NOT claim TPEx fresh-install 20D completeness through EDIS.

## 8. Current runtime authority

This decision does not mutate runtime authority.

Current required state remains:

```text
recent_performance.runtime_executable = false
routing_status = blocked
phase_h_activation_state = inactive

H2 activation = false
H3 activation = false
MCP tool count = 6
Phase I = NOT_STARTED
```

## 9. Next research direction

The next H3 work should focus on portable official evidence lanes, not EDIS integration.

Priority order:

1. reassess whether any official free/public TWSE or TPEx surface can satisfy bounded recent-history semantics without account credentials;
2. evaluate explicitly user-supplied official evidence as a governed manual/import lane if compatible with the product contract;
3. define the exact Phase H closure claim when complete recent history is unavailable;
4. keep EDIS research assets dormant unless the Owner explicitly reopens the boundary.

## 10. Reopening rule

This boundary may be changed only by a new explicit Owner decision.

Technical feasibility, provider availability, or existence of credentials does not by itself reopen the product boundary.
