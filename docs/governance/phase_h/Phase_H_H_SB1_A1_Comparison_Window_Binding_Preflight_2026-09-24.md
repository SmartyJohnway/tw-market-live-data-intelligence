# Phase H H-SB1-A1 — Comparison-Window Binding Preflight

Status: **PREFLIGHT / RECOMMENDED ARCHITECTURE / OWNER FREEZE NOT YET RECORDED**

Date: 2026-09-24  
Project: tw-market-live-data-intelligence  
Baseline main: 97379a070fec641b3a41f77661d15b3bece4d9eb

## 1. Problem

H-SB1-A0 proved that the selected TPEx H2 source slices are reachable and normalize truthfully under a bounded two-call live probe.

However, production H2 evidence cannot yet be wired safely because:

- Request V3 intentionally gives H2 no public parameters;
- corporate_action_context_evidence.v1 requires coverage.requested_window.start/end;
- H4 derives the actual comparison window from the H3 available baseline;
- current execution-request v1 does not carry a governed H2 comparison window;
- the selected TPEx H2 sources are current/daily source slices, not arbitrary historical lookup routes.

Therefore production code MUST NOT invent an H2 requested_window.

## 2. Governing semantic facts

### H3

lookback_trading_days=N means N valid completed official trading-session lookback observations before one governed end observation.

The actual comparison start/end are therefore evidence-derived facts, not merely calendar estimates.

Partial or missing H3 observations may change the actual available baseline.

### H4

The current deterministic H4 implementation already:

1. selects the exactly one available H3 baseline;
2. reads start_observation_date and end_observation_date;
3. compares H2 coverage.requested_window against that actual H3 window;
4. returns coverage_incomplete when H2 does not truthfully cover the comparison window.

This existing direction is semantically correct and should be preserved.

## 3. Rejected approaches

### A. Executor-local today window

Rejected.

A today-only default is not the H3 comparison window and would make the evidence appear more strongly bound than it is.

### B. Arbitrary calendar lookback

Rejected.

20 trading observations are not 20 calendar days. Missing valid observations and exchange-calendar effects make plan-time calendar guessing non-authoritative.

### C. Event-derived window

Rejected.

The event returned by H2 cannot define the comparison window that H4 is supposed to evaluate.

### D. Change H2 public Request V3 parameters

Not recommended.

The frozen V3 contract intentionally keeps H2 public parameters empty. The product should not expose an internal safety-binding detail as a new user-facing parameter merely to simplify executor plumbing.

### E. Immediate execution-request schema/version change

Premature.

No H3 runtime route exists yet. Changing a lower-level execution contract before the H3 production shape is known would optimize for a hypothetical implementation.

## 4. Recommended architecture

The recommended semantic authority is:

~~~text
H3 governed evidence
        ↓
available baseline
        ↓
actual official
start_observation_date
end_observation_date
        ↓
comparison-window binding
        ↓
H2 governed evidence assembly
        ↓
H4 deterministic safety
~~~

In short:

> **H3 evidence owns the comparison window; H2 consumes that window for safety coverage.**

H2 MUST NOT be the authority that defines the historical comparison interval.

## 5. Source acquisition versus safety binding

H2 source acquisition and H2 safety-window binding are separate concerns.

### Source acquisition

The selected TPEx routes may retrieve current official source slices and produce governed source fragments:

- preannouncement;
- final reference calculation;
- target binding;
- source state;
- no-row/source-failure state;
- event/reference facts when present.

### Safety-window binding

Only after the actual H3 baseline is known may those H2 fragments be assembled/projected against the comparison window used by H4.

Because current TPEx H2 sources do not provide arbitrary historical coverage:

~~~text
H2 requested_window = H3 comparison window
does NOT imply
H2 declared_scope_complete = true
~~~

For the selected current-only source slices, H2 may still truthfully remain partial / coverage-incomplete for that historical window.

## 6. Important product consequence

A current TPEx H2 event may still be useful even when complete historical H2 coverage is unavailable.

Example:

~~~text
H3 raw comparison suggests -5%
+
H2 current/final source confirms an ex-dividend event
+
official reference is available
+
H2 historical coverage remains incomplete
~~~

The product may surface the confirmed event/reference facts and MUST block ordinary raw-return interpretation.

It does not need to pretend that all relevant H2 subtypes were historically covered.

Likewise:

~~~text
H2 current source no-row
+
H2 historical coverage incomplete
→
H4 coverage_incomplete
→
ordinary interpretation blocked
~~~

This is a successful safety behavior, not a failure.

## 7. Recommended implementation timing

Do NOT implement the binding plumbing yet.

First close enough H3 source authority to select the actual H3 runtime shape.

After H3-R / H3-I design is concrete, reopen A1 implementation and choose the smallest truthful internal mechanism.

Likely implementation families include:

### Option 1 — additive dependent execution binding

Represent H2 as dependent on H3 and carry a governed comparison-window binding through a new/additive internal execution-request contract.

### Option 2 — post-acquisition derived assembly

Persist governed H2 source fragments and, after H3 materialization, assemble corporate_action_context_evidence.v1 using the H3 baseline window before H4 derivation.

Either implementation MUST preserve:

- explicit authorization;
- execute-once semantics;
- immutable plan/authorization lineage;
- exact target identity;
- no hidden network after authorization;
- no background history collection;
- no user-facing H2 window parameter;
- no seventh MCP tool.

The choice between Option 1 and Option 2 is DEFERRED until H3-I shape is known.

## 8. Standalone H2 behavior

This preflight does not create a new standalone current-window semantic for H2.

Until separately defined, H2 production activation remains tied to the interpretation-safety chain rather than exposing an invented implicit today-window contract.

The H-SB1-A0 source runner remains valid source-contract evidence only.

## 9. Closure impact

H-SB1-A0 is complete.

H-SB1-A1 semantic recommendation is:

~~~text
comparison-window authority
= H3 available baseline

H2 self-defined historical window
= PROHIBITED

plan-time calendar guess
= PROHIBITED

immediate execution-request version change
= DEFERRED

production H2 activation
= WAIT FOR H3 SHAPE
~~~

Therefore the current critical path shifts to H3 source/runtime resolution.

## 10. Next gate

The next productive work is H3-R continuation:

1. close the TWSE optional-provider automation-transport question;
2. close the TPEx fresh-install current-month continuity question;
3. if no portable/default provider route emerges, decide the allowed Owner scope for an optional-provider or bounded owner-authorized route;
4. only then design H3-I and reopen H-SB1-A1 implementation plumbing.

## 11. No authority mutation

This preflight changes no:

- Request/Result/Audit schema;
- execution-request schema;
- Catalog;
- Routing;
- executor registry;
- source activation;
- MCP surface;
- Phase I state.

It records the recommended semantic direction only.
