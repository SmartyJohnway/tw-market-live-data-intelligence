# J-B03-A2.2 — Representative H1 Composition Design

**Disposition:** `J_B03_A2_2_SELECT_RESULT_LEVEL_COMPONENT_COMPOSITION`

This is a static architecture decision. It performs no market request and changes no contract or runtime code.

## Current constraints

The active TPEx attention route is the only executable H1 route and emits H1 v1. H1 v1/v2 artifacts each retain one top-level source. Current lineage stores one binding per `(canonical_target_id, data_need)`, rejects a second binding as `duplicate_binding`, and rejects a second H1 typed artifact in that binding as `duplicate_phase_h_typed_artifact`. The Result target has one `trading_status_context` object. There is no existing multi-source composition path.

## Source readiness

| Component | Current state | Readiness |
|---|---|---|
| TPEx attention | Active executor `phase_h_h1_tpex_attention_executor`; accepted H1 v1 path | `READY_FOR_INTEGRATION` |
| TPEx disposition | Dataset 11396 / ODGL 1.0 and dormant normalizer exist; live source contract not verified; route not executable | `NEEDS_SOURCE_CONTRACT_VERIFICATION` |
| TPEx `tpex_cmode` | Dataset 11736 / ODGL 1.0 and payload shape accepted; `SuspensionOfTrading=Ｙ` semantics remain unresolved; H1 v2 native representation accepted; no adapter/route | `NEEDS_ADAPTER_IMPLEMENTATION` |
| TPEx suspend/resume history | Bounded historical events only; A1R remains semantic HOLD; not proof of current tradeability | `OPTIONAL_ONLY` |
| `tpex_spendi_today` | H0-SRC-01E remains open; current-day event detail is optional for J-B03 | `OPTIONAL_ONLY` |

## Composition decision

Keep each source's evidence artifact source-specific and compose above those artifacts. The future design should use one explicitly selected composite executor/operation for the one public `trading_status_context` need, with a predeclared source set and a Result-level `trading_status_context_composite.v1` representation. The composite is not itself a source artifact. It must preserve each component's H1 version, source, target binding, status, coverage, record/observation dates, items or native observations, citations, and artifact hash/reference.

Do not allow multiple ordinary bindings or multiple H1 artifacts to pass the existing duplicate checks. A future composition-aware lineage path must select only the preauthorized components of the composite operation and reject duplicate source components, duplicate artifact identity, or target mismatch.

The aggregate canonical coverage is the union of validated canonical component coverage. A native unresolved `SuspensionOfTrading=Ｙ` observation does not cover `suspension`. Component outcomes remain separate, so one source failure cannot erase successful evidence from another. Keep the composition partial whenever representative or canonical H1 scope remains incomplete; never derive normal trading, suspension, resumption, or complete H1 scope from component absence or unresolved native facts.

The attention-only Result plus disposition/cmode evidence hidden in Audit or handoff is insufficient: the canonical Result/readback surface must retain the representative evidence. A multi-source H1 artifact is rejected because it conflicts with the accepted one-source-per-artifact contract.

## Contract and integration impact

- **Result V3:** an additive composition branch is required; this tranche does not modify Result V3. No evidence requires Result V4.
- **Audit V3:** its generic arrays of artifact references and source attempts can retain per-component schema versions, paths, hashes, source contracts, citations, and outcomes. Future builder/resolver mappings and consistency validation still need changes.
- **Lineage and operation bundle:** future work must explicitly carry component artifacts and source attempts under the single composite operation. Current operation-result v2's single primary evidence contract and canonical item count need an explicit composition model; do not relabel source artifacts or redefine `result_item_count` / `total_item_count` to include native observations.
- **AI handoff:** render attention, disposition, and native `tpex_cmode` evidence separately. Preserve raw `Ｙ`, date, citation, unresolved status, and caveat; do not translate it into a trading-state conclusion.
- **MCP:** existing Result and handoff tools suffice; keep exactly six tools.

The future authorization must bind the exact ordered source-contract set, endpoint per source, target, TLS policy, byte/time bounds, per-source request budget, retry and redirect/fallback policy, and expected artifact contracts. It must not permit dynamic source or URL selection.

## Static fixtures

An ephemeral in-memory model passed C1–C7: successful components compose while remaining partial; independent component failures and component-local no-match are retained; duplicate source, target mismatch, native-to-suspension promotion, and duplicate artifact identity are rejected. C3 keeps the H1 component status `partial`; it does not use `no_evidence_in_covered_scope`, which requires complete five-type H1 coverage. No fixture files were committed.

## Recommended next gates

1. **J-B03-A2.3:** author the composition contract and offline operation-bundle, lineage, Result V3, Audit, handoff, validator, and fixture support. No acquisition or activation.
2. **J-B03-A2.4:** separately verify the TPEx disposition source contract; its dormant normalizer is not live contract acceptance.
3. **J-B03-A2.5:** implement deterministic `tpex_cmode` native H1 v2 and disposition component adapters after their respective gates. Implementation does not activate either route.
4. **J-B03-A2.6:** integrated offline acceptance; live acceptance and route activation require separate explicit authorities.

## State and boundary

Market GET/HEAD/POST = `0/0/0`. Production code, schema, Result, lineage/runtime, catalog, routing, registry, activation, and preferred-version state are unchanged. `data/` is untouched. H0-SRC-01E and H0-SRC-02 remain OPEN; J-B03 remains HOLD; J-B04 remains BLOCKING; Phase J remains NOT STARTED; MCP remains 6. PR #316 is MERGED/CLOSED.
