# Phase H H4 Discontinuity Safety Contract

Status: **FROZEN**
Freeze date: 2026-09-21
Contract role: deterministic cross-evidence interpretation-safety gate
Repository baseline: `85a61cd8dc14c37832f7702c9e0a529b3f27ee0f`
Upstream H0-A–H0-D merge: `85a61cd8dc14c37832f7702c9e0a529b3f27ee0f`
Owner instruction: `H0-02B FORMAL CONTRACT FREEZE`

## 1. Purpose and boundary

H4 determines whether raw recent price comparisons may be interpreted as ordinary close-to-close returns when an official price-basis discontinuity may exist.

H4 is deterministic safety logic. It is not an external data need, network capability, price-adjustment engine, investment conclusion, or human-facing AI answer layer.

H4 MUST NOT fetch the network, activate a source, invent missing corporate-action evidence, or substitute unofficial evidence.

## 2. Governed inputs

H4 consumes normalized governed evidence already supplied by:

- H2 `corporate_action_context` evidence and coverage;
- H3 `recent_performance` observations, baselines, and raw metrics;
- current or official EOD price evidence where the comparison requires it;
- the existing canonical target identity;
- the explicit comparison window.

H4 MUST fail closed when required identity, timing, binding, coverage, or source evidence is missing or invalid.

## 3. Comparison window and event timing

The comparison window MUST identify the official trading dates and price bases of the start and end observations.

For a completed-session comparison, a price-basis event is inside the comparison interval when governed official evidence establishes that its effective basis change occurred after the start observation's price basis and on or before the end observation's price basis. Conceptually this is the interval `(start_observation_date, end_observation_date]`, subject to the official event contract.

Announcement date alone MUST NOT prove that the price basis changed inside the interval. H4 MUST use official effective date, official reference stage, or another explicitly governed basis-change field.

If the effective timing cannot be resolved well enough to determine whether the basis changed between the observations, H4 MUST return `coverage_incomplete`.

## 4. Relevant event subtype

An H2 event subtype is relevant when, for the resolved target, market, and comparison window, an occurrence could invalidate ordinary comparison of the beginning and ending price bases.

Relevance MUST consider:

- target instrument applicability;
- market;
- comparison start and end;
- whether the subtype can change the official price-comparison basis.

H4 MUST NOT treat every taxonomy value as globally applicable. It also MUST NOT declare a subtype irrelevant merely because no source exists for it.

An applicable price-basis subtype with no sufficient governed source remains relevant and uncovered.

Relevance MUST be determined before evaluating source coverage. Source availability or coverage MUST NOT be used to remove a subtype from the relevant set. After relevance is fixed, H2 coverage determines whether H4 may conclude complete coverage or MUST return `coverage_incomplete`.

## 5. Required H2 coverage evidence

H4 MUST consume explicit coverage evidence capable of representing:

```text
coverage_status
covered_event_subtypes
uncovered_event_subtypes
failed_source_families
requested_window.start
requested_window.end
```

An empty event list does not prove complete coverage. H4 MUST NOT infer coverage completeness from event count or source success for only a subset of relevant subtypes.

## 6. Frozen H4 state model

The canonical conceptual H4 states are:

- `no_material_discontinuity_detected`;
- `discontinuity_detected_reference_available`;
- `discontinuity_detected_reference_unavailable`;
- `coverage_incomplete`.

These states describe interpretation safety. They do not describe investment significance, direction, sentiment, or causality.

Exact V3 schema syntax is DEFERRED to H0-G.

## 7. Strict legality of no-discontinuity state

H4 MAY emit `no_material_discontinuity_detected` only when all of the following are true:

1. canonical target identity and market binding are valid;
2. the comparison start and end observations and their price bases are known;
3. every event subtype relevant to the target, market, and comparison window has sufficient governed coverage;
4. all required source retrievals and source-contract validations succeeded;
5. exact target binding succeeded;
6. revision or lifecycle uncertainty does not prevent a deterministic conclusion;
7. no covered official event indicates an effective material price-basis discontinuity in the comparison interval.

If any relevant subtype is unsupported, uncovered, source-failed, binding-failed, or lifecycle-unresolved, H4 MUST NOT emit this state.

The word `material` does not authorize a locally invented numeric threshold. A governed event is material to H4 when it changes the official comparison basis.

The current frozen H2 source matrix does not prove complete historical corporate-action coverage for every arbitrary H3 comparison window. Therefore `no_material_discontinuity_detected` is not a generally reachable fresh-install default. It MAY be emitted only for a particular target and window whose complete relevant-subtype coverage is affirmatively established by governed evidence.

## 8. Unsupported subtype rule

An unsupported or uncovered relevant subtype does not prove that an event occurred. It also does not prove that no event occurred.

```text
unknown != event occurred
unknown != event did not occur
```

The deterministic safe state is `coverage_incomplete` when an unsupported or uncovered subtype is relevant to the comparison window.

The H2 source gaps for `par_value_change_resume`, `split`, `reverse_split`, and `share_consolidation` therefore prevent a no-discontinuity claim whenever those subtypes are applicable and relevant but uncovered.

## 9. Confirmed event with official reference

When governed H2 evidence confirms that an event became effective in the comparison window and supplies an official reference-price context, H4 MUST emit:

```text
discontinuity_detected_reference_available
```

The raw close comparison MAY remain as factual evidence. The official reference context MUST be retained separately. H4 MUST preserve that the two facts use different comparison bases.

Ordinary raw-return interpretation is not allowed under this state. A later Result composition MAY provide an explicitly reference-aware comparison while preserving both source bases and citations.

H4 MUST NOT overwrite, rebase, or mutate raw historical prices.

## 10. Confirmed event without official reference

When an effective event is confirmed in the comparison window but the official reference context is unavailable, H4 MUST emit:

```text
discontinuity_detected_reference_unavailable
```

Raw prices and raw return MAY remain factual evidence. Ordinary return interpretation MUST be blocked with the conceptual guard:

```text
NOT_COMPARABLE_AS_ORDINARY_RETURN
```

Missing reference evidence MUST NOT be replaced by a locally calculated adjustment factor.

## 11. Incomplete coverage and failures

H4 MUST emit `coverage_incomplete` when a relevant price-basis subtype has any of these conditions:

- partial or unknown coverage;
- unsupported subtype;
- source failure;
- binding failure;
- unresolved effective timing;
- unresolved revision/correction/cancellation relationship;
- missing required target or comparison-window evidence.

The upstream failure details MUST be preserved. `coverage_incomplete` MUST NOT erase source-failed or binding-failed provenance.

Raw metrics MAY remain available, but ordinary interpretation MUST be blocked with an appropriate conceptual guard such as:

```text
CORPORATE_ACTION_COVERAGE_INCOMPLETE
```

## 12. Raw metric and interpretation permission are separate

H4 MUST preserve independent concepts equivalent to:

```text
raw_metric_status:
  available | unavailable

ordinary_return_interpretation:
  allowed | blocked

interpretation_guard:
  none
  NOT_COMPARABLE_AS_ORDINARY_RETURN
  CORPORATE_ACTION_COVERAGE_INCOMPLETE
  PRICE_BASIS_DISCONTINUITY_REFERENCE_AVAILABLE
```

Ordinary raw-return interpretation MAY be allowed only when H4 state is `no_material_discontinuity_detected` and all other timing and coverage requirements are satisfied.

This permission means only that the comparison is not known or unresolved to cross a material price-basis discontinuity. It does not turn the raw metric into an adjusted return, total return, economic return, shareholder return, or causal explanation.

## 13. Preannouncements and future events

A preannouncement MAY prove that a future price-basis event is known or scheduled. It does not prove that the basis has already changed.

A future event whose effective basis change occurs after the historical comparison end MUST NOT be treated as an already-effective discontinuity for that completed comparison.

An effective event inside the comparison interval MUST remain a discontinuity even when final reference evidence is unavailable.

## 14. Revision uncertainty

H4 MUST NOT infer `corrected`, `amended`, `cancelled`, `supersedes`, or same-event relationships from target, date, text similarity, local record hash, or snapshot difference.

When official linkage is absent and revision uncertainty prevents a reliable effective-event determination, H4 MUST emit `coverage_incomplete` and preserve the unresolved evidence.

## 15. Multiple events

H4 MUST support multiple relevant H2 events within one comparison window. Each event MUST remain individually traceable to its evidence, source, lifecycle, and citations.

Events MUST NOT be overwritten into a single boolean. One confirmed effective price-basis discontinuity is sufficient to block ordinary raw-return interpretation. Multiple reference contexts MUST remain distinct.

## 16. No price adjustment, investment inference, or causality

H4 MUST NOT:

- generate adjustment factors;
- forward-adjust or backward-adjust prices;
- rebase a price series;
- reinvest dividends;
- model rights subscription economics;
- construct a total-return index;
- invent a materiality percentage threshold;
- create technical-analysis indicators or signals;
- rank securities;
- attribute a price move to a trading status or corporate action;
- emit bullish, bearish, buy, sell, hold, target-price, or strategy conclusions.

H4 determines comparison safety only.

## 17. Determinism and auditability

Given identical normalized H2 evidence, H2 coverage, H3 observations, current/EOD evidence, target identity, and comparison window, H4 MUST produce the same state and guards.

No LLM judgment belongs in H4 canonical derivation.

A later Audit V3 MUST be able to show:

- input evidence identifiers;
- target and comparison window;
- coverage status and covered/uncovered subtypes;
- failed source families;
- event evidence and citations;
- deterministic rule applied;
- derived H4 state;
- raw metric status;
- interpretation permission and guard.

This requirement freezes audit semantics, not Audit V3 schema bytes.

## 18. H4 and H5 boundary

H4 is a deterministic safety state. H5 `quote_interpretation_context` is the later deterministic Result composition layer.

H4 MAY provide states and guards to H5. It MUST NOT become the human-facing AI conclusion layer. H5 exact semantics remain outside this H0-02B tranche.

## 19. Normative acceptance examples

| ID | Governed inputs | Required result |
|---|---|---|
| F1 | Relevant H2 coverage complete; no relevant effective event | `no_material_discontinuity_detected`; ordinary raw-return interpretation may be allowed |
| F2 | Event effective in window; official reference available | `discontinuity_detected_reference_available`; retain raw and reference contexts separately |
| F3 | Event effective in window; official reference unavailable | `discontinuity_detected_reference_unavailable`; raw facts retained; ordinary interpretation blocked |
| F4 | Relevant subtype unsupported or uncovered | `coverage_incomplete`; no no-discontinuity claim |
| F5 | Required H2 source failed | `coverage_incomplete`; preserve source failure |
| F6 | Exact target binding failed | `coverage_incomplete`; preserve binding failure |
| F7 | Future event announced but not effective in completed window | Do not treat it as an already-effective discontinuity |
| F8 | Multiple effective events in window | Preserve every event and citation; do not overwrite |
| F9 | Correction/cancellation relation unresolved | Do not guess; emit guarded `coverage_incomplete` when resolution affects the result |
| F10 | Raw return available but H4 state is not `no_material_discontinuity_detected` | Raw metric remains factual; ordinary interpretation blocked or guarded |

## 20. Freeze decision

```text
H4 semantic contract = FROZEN
H4 network capability = NONE
H4 deterministic safety = READY
Price adjustment engine = NONE
Contract-freeze blockers = 0
Runtime activation = NOT AUTHORIZED
```

Inherited H2 source and coverage gates remain visible:

- `H0-SRC-03`: unresolved correction/cancellation linkage may force `coverage_incomplete`;
- `H0-SRC-04`: TWT49U optional-provider contract affects official-reference availability, not whether an event occurred;
- `H0-SRC-05` and `H0-SRC-06`: capital-reduction routes remain manual-only/inactive and may prevent complete window coverage;
- `H0-SRC-07` and `H0-SRC-08`: par-value/split/consolidation source gaps prevent complete coverage when relevant.

These are implementation, provider, or per-window coverage gates. They are not H4 semantic-contract blockers.

This document does not create V3 schema bytes, runtime implementation, MCP behavior, Workbench behavior, source activation, or H5 Result projection.

## 21. Provenance

Normative upstream authority:

- `docs/governance/phase_h/Phase_H_Product_Boundary_and_Anti_Scope_Creep_FROZEN.md`;
- `docs/governance/phase_h/Phase_H_Official_Source_and_Automation_Authority_Matrix_FROZEN.md`;
- `docs/governance/phase_h/Phase_H_Official_Source_and_Automation_Authority_Matrix_FROZEN.json`;
- `docs/governance/phase_h/Phase_H_H2_Price_Basis_Corporate_Action_Contract_FROZEN.md`;
- `docs/governance/phase_h/PHASE_H_H0_A_D_FREEZE_MANIFEST.json`.

H3 input semantics:

- `docs/governance/phase_h/Phase_H_H3_Bounded_Recent_Reference_Contract_FROZEN.md`.

This file's SHA-256 and byte size are recorded in `PHASE_H_H0_E_F_FREEZE_MANIFEST.json`.
