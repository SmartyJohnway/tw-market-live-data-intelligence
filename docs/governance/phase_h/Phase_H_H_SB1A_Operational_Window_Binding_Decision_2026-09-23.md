# Phase H H-SB1A — H2 Operational Window Binding Decision

Status: **CONTRACT INCOMPATIBILITY CONFIRMED / PRODUCTION WIRING PAUSED / SOURCE-LIVE PROBE MAY PROCEED**

Date: 2026-09-23  
Project: tw-market-live-data-intelligence  
Baseline: ac8a3a8620c61b3636ab806bb71643b0fdaa632f

## 1. Decision summary

H-SB1 selected the paired TPEx corporate-action source slice:

~~~text
H2-TPEX-EXRIGHT-PRE-OPENAPI
H2-TPEX-EXRIGHT-FINAL-OPENAPI
~~~

Source authority and dormant normalization are ready.

However, production executor wiring MUST NOT proceed yet because the currently materialized 05B execution request does not carry the H2 interpretation window required by the frozen H2/H4 contracts.

This is a real operational-contract incompatibility, not an implementation convenience issue.

## 2. Frozen contract facts

The frozen Request V3 contract intentionally gives H1/H2 empty public parameters.

Only H3 recent_performance has the public parameter:

~~~text
lookback_trading_days = 1..20
~~~

The frozen H2 evidence contract requires:

~~~text
coverage.requested_window.start
coverage.requested_window.end
~~~

The frozen H4 contract requires H2 coverage to be checked against the actual H3 comparison window.

H4 may emit no_material_discontinuity_detected only when relevant H2 scope has sufficient governed coverage for the exact comparison window.

## 3. Current 05B projection gap

The current execution request contract is:

~~~text
unified_market_evidence_execution_request.v1
~~~

The planner operation may contain parameters, but 05B-03 request projection currently preserves only:

- requested_fields;
- currentness_requirement.

It does not carry generic governed operation parameters or an H2 comparison/requested window.

Therefore a production H2 executor currently cannot obtain a plan-bound, authorization-bound H2 requested_window.

## 4. Why the executor MUST NOT invent the window

The following shortcuts are rejected:

~~~text
requested_window = today
requested_window = observed_at date
requested_window = arbitrary last 20 calendar days
requested_window = min/max event dates returned by source
requested_window = hard-coded fixture range
~~~

Reason:

- H2 public parameters are intentionally empty;
- H4 compares H2 coverage with H3 actual official start/end observations;
- H3 trading-session dates are not known until governed H3 evidence exists;
- a locally invented H2 window would appear auditable while not being bound to the authorized comparison being protected.

That would violate the H0 requirements for explicit, time-bounded, authorized and auditable interpretation evidence.

## 5. Additional source limitation

The selected TPEx H2 sources are current/daily surfaces, not historical event-query APIs:

### H2-TPEX-EXRIGHT-PRE-OPENAPI

~~~text
coverage_mode = daily preannouncement table
historical_records_exist = false
bounded_historical_retrieval_supported = false
~~~

### H2-TPEX-EXRIGHT-FINAL-OPENAPI

~~~text
coverage_mode = daily next-business-day final reference table
historical_records_exist = false
bounded_historical_retrieval_supported = false
~~~

Therefore activation of these routes can provide real current event/reference evidence, but MUST NOT be represented as complete corporate-action coverage for an arbitrary H3 20-session comparison window.

## 6. Safe interpretation of the selected H2 slice

The selected H2 routes remain valuable.

They can prove:

- a current/scheduled ex-right or ex-dividend event is present;
- a final official reference calculation is present when the final route supplies it;
- the exact target and source stage;
- explicit source failure / binding failure / no-row within that source slice.

They cannot prove:

~~~text
no price-basis event occurred anywhere in an arbitrary recent H3 window
~~~

Therefore:

~~~text
current event detected + reference available
→ event/reference facts may be surfaced
→ ordinary raw-gap interpretation remains blocked

no row in selected current H2 sources
→ MUST NOT become proved no-event for an H3 historical window
~~~

H4 coverage_incomplete remains the correct safe result whenever the upstream coverage cannot cover the required comparison window and relevant subtype scope.

## 7. H-SB1 sequencing amendment

The earlier H-SB1 activation preflight remains historical evidence. Its implementation-ready statement is narrowed by this newly discovered incompatibility.

Revised sequence:

~~~text
H-SB1-A0
source-level bounded-live proof
TPEx pre + final
route remains inactive
no production planner claim

H-SB1-A1
operational window-binding contract resolution
must be separately frozen

H-SB1-A2
production executor + registry wiring
only after A1

H-SB1-B
network-free production integration acceptance

H-SB1-C
production-path bounded-live acceptance

H-SB1-D
rollback rehearsal

H-SB1-E
Owner activation approval

H-SB1-F
Catalog / Routing / Skill current-authority update
~~~

## 8. Permitted work now

H-SB1-A0 MAY proceed because route-level source proof does not require pretending that a production H2 evidence window has already been bound through 05B.

The bounded-live source proof may validate:

- exact official endpoints;
- maximum two calls;
- HTTP/transport;
- payload contract;
- exact target binding;
- pre/final normalizers;
- no-row semantics;
- source-contract drift behavior;
- source dates / effective dates;
- citation/source metadata;
- no raw full-market persistence.

It MUST NOT mark the H2 capability runtime executable or active.

## 9. Candidate A1 solutions to evaluate

No solution is selected by this record.

The separately reviewed A1 decision should compare at least:

### Option A — additive execution-request version

Carry a plan-bound internal comparison/window binding through a new execution-request contract version.

Pros:
- explicit and auditable.

Risk:
- must not invent a user parameter that Request V3 intentionally excluded;
- H3 actual official start/end may still not exist at planning time.

### Option B — dependent H3→H2 execution binding

H3 executes first, establishes actual official comparison-window dates, then a governed downstream H2 operation is authorized/bound to exactly that window.

Pros:
- semantically strongest H4 alignment.

Risk:
- introduces dependent operation sequencing not currently represented by the simple independent 05B plan.

### Option C — current-context H2 evidence separated from historical-window H4 coverage

Activate H2 as truthful current event/reference evidence while treating it as insufficient for historical no-discontinuity proof.

Pros:
- minimal and immediately useful.

Risk:
- does not by itself close the full H2→H4 historical safety chain.

The decision MUST favor semantic truth over implementation convenience.

## 10. No mutation authority

This decision does not authorize:

- editing frozen Request/Result/Audit V3 schema bytes;
- silently editing execution-request v1 semantics;
- source activation;
- H3 implementation;
- Phase I;
- a new MCP tool;
- persistent history collection.

## 11. Decision

~~~text
H2 selected source readiness         PASS
H2 source-level live proof           READY
H2 production window binding         BLOCKED / CONTRACT DECISION REQUIRED
H2 production executor wiring        PAUSED
H2 runtime activation                NOT EFFECTIVE
H3 state                             unchanged / blocked
~~~
