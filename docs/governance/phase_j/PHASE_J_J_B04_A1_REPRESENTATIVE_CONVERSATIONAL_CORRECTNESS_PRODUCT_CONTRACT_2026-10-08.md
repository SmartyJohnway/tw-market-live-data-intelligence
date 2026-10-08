# J-B04-A1 — Representative Conversational Correctness Product Contract

Status: **PRODUCT CONTRACT FROZEN; J-B04 REMAINS BLOCKING**
Date: 2026-10-08
Baseline main: `a9346c0609aadf01c179981d5c1653c3efe3eb3c`

## Decision

J-B04 exits at **bounded conversational correctness**, not complete H2
corporate-action coverage and not Phase H completion. The product must avoid
presenting a mechanical price-basis reset as an ordinary economic collapse.
When relevant evidence is unsupported, incomplete, failed, or cannot be bound
to the H3 comparison window, the correct result is an explicit H4
`coverage_incomplete` state with ordinary raw-return interpretation blocked.

This is a successful safety outcome. It does not claim that an event did or did
not occur. Empty H2 events and no-row results cannot establish no event.

## Authority reconciliation

The Phase-J readiness preflight identifies J-B04 as the remaining
conversational blocker: contract-only H2 cannot provide event evidence through
the normal governed runtime. Its minimum scope is the J event set on one
explicit representative market, with H4 fail-closed behavior and explicit
caveats for unselected markets.

The frozen H2/H4 contracts and H-SB0 completion contract define broader Phase-H
requirements, including a production H2 route, a real H2/H3/H4 chain, bounded
live acceptance, and coverage discipline. Those remain necessary for Phase H
completion. They do not require complete H2 subtype coverage to close the
narrower J-B04 conversational gate. A1 does not waive any H2 per-window
coverage rule or Phase-H completion requirement.

The earlier H-SB1 TPEx pre/final pair is a historical candidate, not a current
J-B04 market mandate. The currently selected H3 route is TWSE and H4 takes its
comparison window from the actual H3 baseline. TPEx H3 remains blocked. A
TWSE-first J-B04 chain is therefore the smallest currently governable
cross-layer slice. The frozen H2 contract already permits a later TWSE first
slice; TWSE TWT49U remains optional and inactive.

## Required conversational behavior

- Surface only official, governed event facts: exact target and market, source
  and source stage, dates actually supported, official reference context only
  when supplied, citations, provenance, and coverage caveats.
- Preserve `scheduled`/preannouncement separately from effective or final
  official reference evidence. Do not upgrade event lifecycle without source
  authority.
- For relevant unsupported, source-gap, manual-only, failed, binding-failed,
  timing-unresolved, or historically uncovered evidence, preserve its state
  and return H4 `coverage_incomplete`.
- When H4 is not `no_material_discontinuity_detected`, block ordinary
  raw-return interpretation. Raw values may remain available as facts.
- `no_material_discontinuity_detected` remains legal only under the frozen H4
  complete relevant-coverage and timing conditions. Empty H2 event lists and
  current-source no-row results do not satisfy those conditions.

The H3 evidence owns the window:

```text
H3 available baseline
  -> actual start/end observation dates
  -> governed H2 window binding
  -> deterministic H4 safety
```

H2 must not invent a historical window. Plan-time calendar guessing and
event-derived windows are prohibited. No public H2 request parameter is
required merely to carry this internal safety binding.

## J scenario acceptance matrix

| Scenario | Positive evidence behavior | Safe incomplete behavior |
|---|---|---|
| J1-13 ex-dividend | Report supported facts and stage. Scheduled evidence remains scheduled. If an effective event is confirmed, distinguish reference available from unavailable. | If timing, window relation, or relevant coverage is unresolved, use `coverage_incomplete`; block ordinary return interpretation. |
| J1-14 ex-right | Same stage and reference rules as ex-dividend; retain preannouncement and final evidence independently. | Unresolved timing/window/coverage uses `coverage_incomplete`; block ordinary return interpretation. |
| J1-15 capital reduction | Positive automated runtime evidence is not required while the sources remain manual/inactive. | State unavailable/unsupported/uncovered with caveat; never infer absence; guard ordinary interpretation when relevant. No browser/CSV scraping. |
| J1-16 reference-price discontinuity | Preserve a confirmed in-window event with official reference available or unavailable. | Relevant incomplete coverage or timing uses `coverage_incomplete`; block ordinary interpretation. A no-discontinuity result is not required to be generally reachable. |

For a confirmed in-window event with no official reference, H4 uses
`discontinuity_detected_reference_unavailable`. Missing reference is never
replaced with a local formula, adjustment factor, adjusted series, total return,
or guessed price.

## J-B04 closure acceptance required after A1

J-B04 remains BLOCKING after this product decision. A later implementation and
acceptance gate must demonstrate a normal, explicitly approved TWSE H2 route
and bounded live source acceptance, bind its evidence to the actual TWSE H3
baseline window, and pass the deterministic H4 guard through Result, Audit,
and AI handoff. Positive event facts and their source stage must be tested;
scheduled evidence cannot be promoted to effective. Representative acceptance
must exercise confirmed discontinuity with reference available, confirmed
discontinuity without reference, and `coverage_incomplete`, with ordinary
return interpretation blocked for all non-normal states. The reference-available
and reference-unavailable H4 branches may each be proved with deterministic
fixtures validated against the frozen H2/H4 schemas and semantics. Such fixtures
are test evidence only and must never be represented as live source evidence.
`coverage_incomplete` should be exercised through real integrated behavior where
appropriate. Bounded-live H2 acceptance proves source transport, authorization
and call bounds, target binding, source-contract validation, normalization,
lifecycle/stage preservation, coverage/no-row/failure semantics, and
citation/provenance; it does not require the live observation to contain an
effective event. Scheduled/preannouncement evidence must retain its stage.
Unselected markets and uncovered source families remain explicit. This does not
require complete H2 coverage, a generally reachable no-discontinuity result, a
live final-reference provider, or Phase H completion. A1 does not select the
exact source adapter or execution plumbing.

## Coverage boundaries

Capital-reduction sources remain manual verification/inactive; no unattended
production automation authority is established. This gap is not closed by A1.
Par-value changes, splits, reverse splits, and share consolidations remain
source gaps and uncovered whenever relevant. A1 makes no complete H2 claim.

## Current runtime snapshot

- H2 `corporate_action_context`: contract-supported, runtime inactive.
- H3 TWSE: active through `phase_h_h3_twse_recent_performance_executor`.
- H3 TPEx: blocked/non-executable.
- H4: existing deterministic zero-network implementation; derived contract,
  no selected executor.
- TWSE H2 pre OpenAPI: eligible/inactive; TWT49U: optional licensed provider,
  inactive; capital reduction: manual/inactive; par/split/consolidation:
  source gap/blocked.
- TPEx pre/final OpenAPI: eligible/inactive; capital reduction:
  manual/inactive; par/split/consolidation: source gap/blocked.

## State after A1

```text
J-B01 = CLOSED
J-B02 = CLOSED
J-B03 = CLOSED
J-B04 = BLOCKING
J-B04-A0 = REVIEW COMPLETE
J-B04-A1 = PRODUCT CONTRACT / EXIT CRITERIA FROZEN
Phase J = NOT_STARTED
MCP = 6
H2 runtime = INACTIVE
H3 TWSE = ACTIVE
H3 TPEX = BLOCKED / NON-EXECUTABLE
H4 deterministic implementation = EXISTING / UNCHANGED
```

A1 freezes product semantics only. It does not activate H2, start Phase J,
complete J-B04, or complete Phase H. No market GET/HEAD/POST was performed.
The machine-readable contract and repository cross-checks are in the paired
JSON and validator.
