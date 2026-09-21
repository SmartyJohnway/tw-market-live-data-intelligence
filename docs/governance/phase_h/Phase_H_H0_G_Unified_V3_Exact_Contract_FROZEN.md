# Phase H H0-G Unified V3 Exact Contract Freeze

Status: **OWNER ACCEPTED / FROZEN**  
Freeze date: 2026-09-21  
Repository baseline: `59cedf7434afe54fc19a3517f20aa07b7411e455`  
Branch: `phase-h/h0-g-v3-contract-freeze`

Owner decision: **OWNER ACCEPTED / FROZEN**  
Accepted amendments: **A1, A2**  
Acceptance date: **2026-09-21**  
Contract-freeze blockers: **0**  
H0-H readiness: **READY_FOR_ACCEPTANCE_AND_IMPLEMENTATION_PLAN**

## 1. Normative role

H0-G translates the frozen H0-A through H0-F semantics into machine-readable V3 contracts. It does not activate V3, implement adapters or executors, alter the current preferred request version, or authorize H0-H.

The V3 family is a future contract candidate:

- V1 remains readable and accepted legacy authority;
- V2 remains readable, accepted, and the current production authority;
- V3 is exact but runtime-inactive pending later authorization.

Current production request preference remains `unified_market_evidence_request.v2`. Existing six MCP tools and runtime dispatch remain unchanged.

## 2. Exact artifacts

H0-G creates:

- `schemas/unified_market_evidence_request.v3.schema.json`;
- `schemas/unified_market_evidence_result.v3.schema.json`;
- `schemas/unified_market_evidence_audit_package.v3.schema.json`;
- `schemas/trading_status_context_evidence.v1.schema.json`;
- `schemas/corporate_action_context_evidence.v1.schema.json`;
- `schemas/recent_performance_evidence.v1.schema.json`;
- `schemas/discontinuity_safety_evidence.v1.schema.json`;
- `docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json`;
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json`.

Exact hashes and byte sizes are recorded in `PHASE_H_H0_G_V3_SCHEMA_FREEZE_MANIFEST.json`.

Amendment A1 closes endpoint identity, raw-return arithmetic, non-vacuous declared scope, comparison-window chronology, and traversal-safe artifact-reference gaps without changing V3 activation status.

## 3. Request V3

Request V3 preserves all V2 data needs and adds exactly:

- `trading_status_context`;
- `corporate_action_context`.

It reuses `recent_performance`. It does not add `historical_baseline`, `price_history`, `recent_history`, `discontinuity_safety`, or `quote_interpretation_context` as request needs.

`recent_performance.parameters.lookback_trading_days` remains required, integer, and bounded from 1 through 20. H1 and H2 have empty public parameters. Source/provider choice remains internal governance and routing authority.

## 4. Typed evidence

H1 through H4 do not rely on an unrestricted `observed_fields` map.

### H1

`trading_status_context_evidence.v1` fixes the five status subtypes, exact target identity, lifecycle, source authority, coverage proof, timing, source-native bounded provenance, and citations.

H1 declares all five canonical status types because Request V3 has no subtype selector. `declared_status_types` is non-empty and equals the disjoint union of covered and uncovered types. `no_evidence_in_covered_scope` is schema-valid only with empty items, complete declared scope, successful retrieval, successful source-contract validation, successful exact-target search, no uncovered subtype, and no failed source family.

### H2

`corporate_action_context_evidence.v1` keeps three independent concepts:

- source evidence stage: `preannouncement`, `official_reference_calculated`, or `unresolved`;
- event lifecycle: `announced`, `scheduled`, `effective`, `corrected`, `amended`, `cancelled`, or `unresolved`;
- revision relation: `unresolved` or `officially_linked`.

An officially linked relation requires a governed relation type and official reference. An unresolved relation requires both to be null.

Corporate-action numeric facts use `{state, value}`. This preserves blank, numeric zero, not announced, not applicable, unavailable, and source failed as distinct states.

H2 declares its target-applicable event subtype scope explicitly. `declared_event_subtypes` is non-empty and equals the disjoint union of covered and uncovered types; unavailable source routes remain declared and uncovered rather than being silently removed.

### H3

`recent_performance_evidence.v1` represents requested lookback observations separately from the governed end observation. For baseline N:

```text
required_distinct_close_count = N + 1
```

For an available baseline, the governed end observation is required; `end_observation_date` equals its trade date; `start_observation_date` equals `observations[-N].trade_date` in the governed ordered completed-session series; and the baseline-specific actual close proof equals exactly `N+1`. The raw return is recomputed as `(close_end - close_start) / abs(close_start) * 100`; zero start close fails closed. The deterministic serialized-number comparison uses absolute tolerance `1e-9` with no implicit rounding.

Draft-07 cannot express dynamic arithmetic between sibling fields. The exact schema constrains status-compatible shapes, while `scripts/validate_phase_h_v3_contracts.py` enforces observation accounting, mutually exclusive coverage precedence, endpoint identity, baseline-specific 1→2, 5→6, 20→21 proof, and raw-return arithmetic. This validator is a zero-network contract validator and is not runtime activation.

The V3 range decision is basis-qualified explicit naming:

```text
recent_close_high
recent_close_low
range_basis = completed_session_closing_price
```

Legacy `range_high` and `range_low` are not reused. V3 consumers therefore cannot confuse an intraday high/low envelope with the Phase H completed-session closing-price range.

H3 preserves `recent_return_pct` as raw, unadjusted, close-to-close evidence. It also records current-volume basis, completed-session historical-average basis, and alignment without producing volume-strength classifications.

### H4

`discontinuity_safety_evidence.v1` is typed derived evidence. It is not a request data need and has no network route.

It preserves relevant, covered, and uncovered subtype sets; failed sources; comparison window; input evidence; event/reference evidence; raw metric status; interpretation permission; guard; and deterministic rule version.

Only `no_material_discontinuity_detected` permits ordinary-return interpretation. The other states block it. Raw metric availability remains independent, so raw factual arithmetic can survive while ordinary interpretation is blocked.

The comparison window is ordered: its start observation date must precede its end observation date. The zero-network cross-evidence validator additionally verifies that an H4 window equals the referenced available H3 baseline window and that H4 covered/uncovered subtype claims do not exceed the governed H2 coverage claims. Runtime artifact loading remains deferred to H0-H.

The set invariant—relevant subtypes equal the disjoint union of covered and uncovered relevant subtypes—is enforced by `scripts/validate_phase_h_v3_contracts.py` because Draft-07 cannot compare arrays as sets. The schema independently requires an explicit coverage-incomplete reason and forbids no-material status when raw evidence is unavailable or any uncovered/source/upstream failure remains.

## 5. Result V3

Result V3 retains V2 canonical identity, citations, legacy evidence envelopes, official EOD evidence, material disclosures, monthly revenue, derived metrics, coverage, and audit reference roles.

It replaces the V2 generic `recent_performance` envelope in V3 with typed H3 evidence and adds typed H1, H2, and H4 evidence under each target. Historical V1/V2 results remain readable without migration or byte rewrite.

## 6. Audit V3

Audit V3 retains V2 request, target, Plan, Authorization, Claim, Receipt, Bundle, operation, artifact, citation, integrity, replay, and projector lineage. Those subordinate contracts remain at their truthful existing versions.

The V3-only `phase_h_governance` section records source attempts, source role, activation state, provider availability, license authority, target and window binding, coverage/failure result, and typed evidence artifacts. `h4_derivations` is a target-scoped array: every record binds canonical target, market, comparison window, input evidence, governed H4 artifact, deterministic rule, state, and guard. This preserves distinct lineage for multi-target Result V3 packages.

`source_role` and `activation_state` remain separate fields and vocabularies.

All V3 artifact filesystem references are canonical slash-separated, non-empty, artifact-root-relative paths. They reject URI, absolute, Windows-drive, UNC, and parent-directory traversal forms.

## 7. Catalog V3

Catalog V3 carries all existing capabilities forward and adds H1/H2. It preserves `recent_performance` rather than creating a history capability.

H1, H2, and H3 are `contract_supported`, runtime-inactive, and limited initially to TWSE/TPEX `company_share/common_share`. H4 appears only as derived zero-network evidence and is not a request capability.

Existing active Phase G capabilities remain truthfully inherited. Catalog V3 itself is not current authority. Its contract-version block explicitly records current runtime V2 and future candidate V3 separately.

## 8. Routing Matrix V3

Routing V3 carries inherited executable V2 capability routes without changing current runtime registration.

H1/H2/H3 have no executor ID, are not runtime executable, and retain explicit blocking/source gaps. Eligible source authority does not equal active runtime authority. Manual browser CSV remains manual verification and source gaps remain blocked.

H4 is recorded under derived contracts as zero-network and dependent on governed H2/H3 evidence. It is absent from request routes.

## 9. Compatibility and immutable authority

No V1 or V2 schema byte is changed. Existing Phase G exact freeze assets remain authoritative and readable. V3 does not require old Result/Audit packages to be rewritten.

No Plan, Authorization, Claim, Execution Request, Operation Result, Receipt, or Bundle version is changed. No new identity authority or planner is created.

## 10. Activation and source gates

At this freeze:

- V3 runtime: inactive;
- H1 runtime: inactive;
- H2 runtime: inactive;
- H3 runtime: inactive;
- H4: deterministic contract only;
- Phase H active source count: zero;
- preferred production request: V2;
- MCP tool count: six.

Open H0-SRC-03 through H0-SRC-12 gates remain visible. Schema existence does not close a license, provider, source-contract, automation, or coverage gate.

## 11. Scope boundary

H0-G introduces no source adapter, executor, network behavior, scheduler, polling, background refresh, automatic backfill, history warehouse, corporate-action warehouse, adjustment engine, technical-analysis engine, screening, ranking, backtesting, Workbench activation, MCP behavior change, or public capability activation.

## 12. H0-H readiness

The exact contract candidate is ready for Owner review and, after approval/checkpoint, H0-H acceptance and implementation planning. H0-H has not started.

```text
contract-freeze blockers = 0
H0-H readiness = READY_FOR_ACCEPTANCE_AND_IMPLEMENTATION_PLAN
```
