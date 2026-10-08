# J-B04-A2 — TWSE H2 Production Implementation Preflight

Status: **READY FOR NETWORK-FREE IMPLEMENTATION; H2 REMAINS INACTIVE**
Date: 2026-10-08
Baseline `main`: `7c48336e78d7461a3a83ef599b945c7c65542ba8`

## Decision

`J_B04_A2_READY_FOR_NETWORK_FREE_IMPLEMENTATION`

The existing official TWSE `TWT48U_ALL` source is sufficient for a bounded,
partial, fail-closed J-B04 route. Its preannouncement snapshot does not prove
complete historical event coverage for an H3 comparison window. The decision
permits a later network-free implementation tranche only. It does not authorize
source execution, bounded-live acceptance, activation, or J-B04 closure.

## Source and binding contract

The selected source is `H2-TWSE-EXRIGHT-PRE-OPENAPI` / `TWT48U_ALL`, from the
TWSE official OpenAPI under ODGL 1.0 / data.gov.tw dataset 89748. Its evidence
stage remains `preannouncement`; the existing normalizer emits `scheduled`
events. Neither a passed date nor the later H3 window may promote that stage to
`effective`. The source supplies no final reference price. No local reference
price, adjustment factor, adjusted series, or total return may be calculated.

The future executor ID is `phase_h_h2_twse_exright_pre_executor`: one explicit
TWSE target, exact security-code binding, at most one official GET, zero retry,
no name fallback, no persistence, no backfill, no scheduler, and no polling.
The currently eligible source descriptor and non-executable H2 route remain
unchanged in A2.

Current authority does not establish that one security code has at most one
relevant TWT48U_ALL row. A2 therefore retains the normalizer's existing
`binding_failed:ambiguous_exact_target_rows` behavior. A later implementation
must not select, merge, or deduplicate multiple exact rows without a separately
governed source-grain rule.

## H3 window and temporal coverage

H3 owns the comparison window. After exactly one usable available H3 baseline
exists, orchestration may bind that baseline's actual start/end observation
dates to H2 assembly. The H2 network request itself does not use those dates.
This binding supports H4 interpretation; it does not prove that a current
TWT48U_ALL table covered every relevant event in the historical interval.

The current authority records both `historical_records_exist = false` and
`bounded_historical_retrieval_supported = false` for TWT48U_ALL. Accordingly,
the default source must keep `declared_scope_complete = false` and partial
coverage. A successful no-row result means only that the exact target was
absent from the retrieved current source slice. It cannot establish that no
event occurred during the H3 comparison window. No local cache accumulation,
calendar inference, event-derived window, browser-history scrape, or future
background collection may fill that gap.

## Explicit plan, authorization, and execution order

The user/AI request must explicitly include both `recent_performance` and
`corporate_action_context` for the same resolved TWSE target when H4 comparison
is requested. Both operations and their network estimates must be visible in
the preview and included in the approved plan before execution. H2 is never
silently added because H3 or quote evidence was requested. A combined package
retains H3's existing limit of at most three unique STOCK_DAY month GETs with
zero retry, plus one TWT48U_ALL GET with zero retry.

The future plan must carry an H2 `dependency_operation_ids` reference to the
same-target H3 operation. The approved plan hash binds that dependency; the
internal dispatcher must execute H3 first and make only its exact completed
artifact available to the dependent H2 assembly. H2 does not fetch H3 itself,
and no public H2 window parameter or new MCP tool is needed. Current planner
dependency IDs exist, but H2 dependency planning, topological dispatch, and
artifact binding are not implemented; those are explicit A3 work.

The required order is:

```text
explicit request with H3 + H2
→ validate / plan / preview
→ explicit authorization of the complete bounded plan
→ execute H3
→ require exactly one available H3 baseline
→ derive its actual comparison dates
→ execute the single bounded TWT48U_ALL GET
→ exact-target normalize and assemble H2 with those dates, still partial
→ derive deterministic zero-network H4
→ include verified H2/H3/H4 artifacts in Result V3 and Audit V3
→ render source facts and H4 guard in AI handoff
```

If H3 has no usable available baseline, or has ambiguous multiple available
baselines, do not invent dates, issue an H2 request that cannot be assembled to
the required window, or invoke H4. Preserve H3's actual outcome; record H2 as
dependency-not-attempted/blocked with a stable reason; return a governed
partial/failed outcome and explicit no-comparison guard. Do not fabricate an
H4 artifact without its required window. No usable baseline means no valid
ordinary comparison return; any other raw values remain facts and cannot be
presented as that comparison. The frozen H4 precondition remains exactly one
available baseline for the same target.

## Existing H4, Result, Audit, and handoff behavior

`server/services/phase_h_discontinuity_safety.py` is a pure deterministic
zero-network derivation. It validates H2/H3 schemas and semantics, requires
matching target identity and exactly one available H3 baseline, then evaluates
window alignment, source/binding failures, declared-scope completeness,
uncovered subtypes, and event timing. Any failure or uncovered subtype takes
precedence and yields `coverage_incomplete`. An in-window scheduled event
produces unresolved-effective-timing failure and also yields
`coverage_incomplete`. Only with no failures/uncovered types can a confirmed
effective event lead to reference-unavailable or reference-available state;
otherwise the frozen complete-coverage rules govern the no-material state.
Source-supported event facts may still be surfaced while H4 blocks ordinary
return interpretation.

The existing Result V3 contains H2, H3, and H4 evidence slots. The Result
builder projects H2 and H3 by operation lineage and accepts a separately
verified H4 artifact from the bundle inventory; it does not invoke H4 itself.
Audit V3 already records H2/H3 source attempts and evidence references, H2
requested window, and H4 references, inputs, state, and guard. The AI renderer
shows H2 coverage, H3 observation dates, and H4's ordinary-return state and
interpretation guard. A3 must connect the existing pure H4 derivation to this
verified artifact path and retain upstream dependency failures in the Result,
Audit, and handoff. Raw numeric observation and permission to interpret it as
an ordinary return remain separate facts.

## Acceptance split

Bounded-live source acceptance must prove the real official endpoint, visible
authorization and call bounds, exact target binding, payload validation,
normalization, preannouncement/scheduled-stage preservation, no-row and failure
semantics, caveats, citation, and provenance. It need not encounter an
effective event. A1 permits governed deterministic fixtures, validated against
the frozen H2/H4 schemas and semantics, to exercise reference-available and
reference-unavailable H4 states; they must never be represented as live source
evidence. The integrated real path should exercise `coverage_incomplete` where
the actual source evidence warrants it. No first live run is promised to reach
any positive H4 state or a no-material state.

## A3 implementation inventory

The machine-readable record gives the file-level CREATE/MODIFY/MUST NOT MODIFY
map. Principal work is: create the source executor; add explicit same-target
H3 dependency planning and dependency-aware dispatch; add executor metadata and
a still-inactive route/catalog preparation; and connect H4 derivation to the
existing verified Result/Audit/handoff path. Do not change the H3 executor,
H2/H3/H4/Result/Audit/Execution Request schemas, or H4 semantics. Skill
guidance changes only after a later route-activation decision.

## Validation performed

- A2 validator: PASS.
- A2 + A1 + Phase-J readiness focused tests: 61 passed.
- Phase-H V3, Phase-J A1/readiness, portable catalog sync, and runtime
  skill-guide sync validators: PASS; MCP tool count remains 6.
- `default-ci`: 1282 passed, 1 skipped, 5 deselected, 0 failed.
- An additional H2/H3/H4/projection-focused run had 155 passed and one
  unchanged M8R-05C lineage test failure: its assertion expects
  `operation_artifact_hash_mismatch`, while the current path returns
  `artifact_hash_mismatch`.
- An additional M8R-05C Result/Audit/handoff run had 42 passed and five
  failures, all reporting `artifact_hash_mismatch` against committed fixture
  packages. These tests and runtime files are outside A2's four-file scope;
  no implementation or fixture repair was made here.
- No live market tests or requests were run. Market GET/HEAD/POST: 0/0/0.

## Remaining gates

```text
J-B04-A3  network-free implementation; H2 remains inactive
J-B04-A4  independent exact-head review and merge
J-B04-A5  separately authorized bounded-live source acceptance
J-B04-A6  separate activation, integrated acceptance, and J-B04 closure review
```

Each gate preserves its own authority. A2 does not perform source acquisition,
activate a route, start Phase J, or close J-B04.

## State after A2

```text
H2-TWSE-EXRIGHT-PRE-OPENAPI = eligible / runtime_executable=false
H2 runtime = INACTIVE
H3 TWSE = ACTIVE
H3 TPEX = BLOCKED / NON-EXECUTABLE
H4 = existing deterministic zero-network implementation
J-B04 = BLOCKING
Phase J = NOT_STARTED
MCP = 6
market GET / HEAD / POST = 0 / 0 / 0
```

The JSON companion and `scripts/validate_phase_j_b04_a2_twse_h2_preflight.py`
provide machine-checkable assertions and current repository cross-checks.
