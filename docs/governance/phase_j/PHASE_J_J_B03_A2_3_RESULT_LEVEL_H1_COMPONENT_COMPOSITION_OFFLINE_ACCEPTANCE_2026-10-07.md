# J-B03-A2.3 — Result-Level H1 Component Composition Offline Acceptance

**Disposition:** `J_B03_A2_3_RESULT_LEVEL_H1_COMPOSITION_OFFLINE_ACCEPTED`

**Owner authority:** `USER_CHAT_2026-10-07_J_B03_A2_3_OFFLINE_COMPOSITION_IMPLEMENTATION_AUTHORIZATION`

**Starting main:** `f915f57b91d77d08f9a8cb95d402bf6ec677cf6f` / `2b3e9f2b57a5abdb0f583f4cc4beedd59eb69f31`

**PR #317:** MERGED / CLOSED

## Accepted model

`J_B03_A2_2_SELECT_RESULT_LEVEL_COMPONENT_COMPOSITION` is implemented as one
logical operation with one Result `trading_status_context` value. H1 v1/v2
artifacts remain one-source-per-artifact. Composition is a separate Result
contract, `trading_status_context_composite.v1`, with an explicit component
artifact role carried through OperationResult v2, bundle, receipt, lineage,
Audit V3 and handoff. Component H1 records are not mislabeled as governance
artifacts. Ordinary duplicate binding and duplicate typed-artifact protections
remain in force outside the explicit composite operation.

## Contracts and compatibility

- OperationResult decision: `J_B03_A2_3_OPERATION_RESULT_V2_ADDITIVE`.
- Composite schema: [trading_status_context_composite.v1.schema.json](../../../schemas/trading_status_context_composite.v1.schema.json), SHA-256 `3d34a1cb2112716211e39536b221994952aabd1c2723d3ed5f61ee8b0f224106`.
- Component set/order is fixed to TPEx attention, TPEx disposition, and TPEx changed-trading (`tpex_cmode`); only H1 v1/v2 are accepted.
- H1 v1 remains byte-identical (`638200509cde05613d17bd4158d1676c3c086d2b10aa2f50fb85d52febe30ecf`). H1 v2 remains unchanged (`818de1e9c501b4c4d0bb06d6a1503dafba7b63dc60977791f7842cd8b5a31d38`).
- Result V3 adds one disjoint exact-version branch: prior `a8519bc4c444f59b24e74de702667c5570ed15f816a841b509e24b2f3bc788d5`; current `9269fc9e5e07884fa2de791eae902ee57b3d937dbb793318ca4aff1a93fc5bcb`.
- OperationResult v2: prior `a308263bfcaa1837133770321caa3f5e081588519cc96f607b27c3b97c578ab1`; current `9d6430254215ae0b4048e0352f6902c629e4069530b1c9a267f1ee50d4c5bd64`.
- Bundle v1 current SHA-256: `9eb901b99db3a7b56d251e70c00f83ebc99b0f0587fc77fee8aca573f9049aad`; execution receipt v1: `cd70b135e751214d467dbf7ca1924fc2ce8a61461b2276defae7bd30a23e4d26`.
- Audit V3 schema is unchanged (SHA-256 `94208ac6f4c13bcde294de1a8c7cf6be23245d738b5dcd36fffcac1ab134c4cc`). H0-G historical manifest is unchanged (SHA-256 `6c1f23ed12a0d3bffcb7b964197eda6ee6a36d8c95ef1a8c5d6106ef31ea89f6`).

## Composition semantics

The composite stores each component's stable identity, source and contract,
schema version, status, relative artifact reference and hash, and complete
validated H1 evidence. Exact target identity must match across all components.
Duplicate source contracts, component IDs, artifact identities, unsupported
schema versions, target mismatches, hash/reference mismatches and unapproved
sources fail closed.

Aggregate canonical coverage is the union of component canonical coverage
only after source-specific authority validation. The composite authority table
allows attention source coverage `{attention}`, disposition source coverage
`{disposition}`, and no canonical coverage for the accepted native-only cmode
path. The complement of the five canonical H1 types remains uncovered.
Native observations add no canonical coverage: unresolved
`SuspensionOfTrading=Ｙ` remains native evidence and does not establish
`suspension`. Usable incomplete evidence is `partial`; every component outcome
remains visible. If no usable evidence survives, failure precedence is
`binding_failed`, `source_failed`, `unsupported`, then `not_applicable` when
all components are not applicable. No-match, blank, absence, or historical
resumption is never promoted into normal/current tradeability.

Count meanings remain separate: H1 `item_count` counts canonical `items[]`;
H1 `native_observation_count` counts native observations; composite
`canonical_item_count` sums canonical items; `native_observation_count` sums
native facts; `component_count` counts components. Composite primary
`item_count` equals `canonical_item_count`. Legacy OperationResult
`result_item_count` and bundle `total_item_count` count primary artifact items
only; component artifacts and native observations do not silently alter them.

## Offline acceptance evidence

The deterministic fixtures C1–C10 pass: valid heterogeneous H1 v1/v2
composition; independent component failure; exact-target no-match; duplicate
source; target mismatch; attempted native-to-suspension coverage promotion;
reused artifact; unknown H1 version; hash/reference mismatch; and unapproved
source. Result V3 readback accepts H1 v1, H1 v2 and Composite v1 without
rewriting stored packages. Audit references and source lineage remain
traceable. The handoff renders components separately and preserves the native
label/value/date, unresolved caveat and citations without asserting suspension.
The existing attention route remains on H1 v1.

## Validation and boundaries

- `python scripts/validate_phase_h_v3_contracts.py`: PASS.
- `python -m compileall -q scripts server tests`: PASS.
- Focused A2.1B, operation/bundle/lineage and composition tests: 122 passed,
  0 failed.
- `default-ci`: 1268 passed, 0 failed, 1 skipped, 5 deselected, 18 warnings;
  `network_may_have_occurred=false`.
- `market GET / HEAD / POST = 0 / 0 / 0`.
- No acquisition adapter, source/route activation, catalog/routing/registry
  selection change, preferred-version promotion, attention-route behavior
  change, Request V3 change, Audit V3 schema change, or MCP change. MCP remains
  exactly 6 tools. `data/` was left untouched.

## State and next gate

H0-SRC-01E remains OPEN; H0-SRC-02 remains OPEN. J-B03 remains HOLD, J-B04
remains BLOCKING, and Phase J remains NOT STARTED. The next gate is
**J-B03-A2.4 — TPEx Disposition Source-Contract Verification**. A2.3 does not
authorize market acquisition, source activation, A2.4 work, or merge.

## R1 source-authority coverage repair

Independent review found `COMPOSITE_SOURCE_COVERAGE_AUTHORITY_NOT_FAIL_CLOSED`.
H1 v1 correctly preserves its frozen broad coverage semantics; the composite
had trusted the source-declared coverage set without a source-specific subtype
check. The repair is confined to the composite authority boundary and does not
tighten H1 v1.

The fixed mapping in `scripts/m8r_05c/trading_status_composer.py` is:

| Source ID | Source family | Contract | Allowed canonical coverage |
| --- | --- | --- | --- |
| `H1-TPEX-ATTENTION-OPENAPI` | `TPEX_ATTENTION_OPEN_DATA` | `tpex_trading_warning_information` | `attention` |
| `H1-TPEX-DISPOSITION-OPENAPI` | `TPEX_DISPOSITION_OPEN_DATA` | `tpex_disposal_information` | `disposition` |
| `H1-TPEX-CHANGED-TRADING-OPENAPI` | `TPEX_CHANGED_TRADING_OPEN_DATA` | `tpex_cmode` | none for the accepted native-only path |

Embedded `source_family` and `source_contract_id` must exactly match the fixed
mapping. Coverage is checked against that mapping before it can enter the
aggregate union. Identity mismatch fails with
`composite_component_source_identity_mismatch`; over-coverage fails with
`composite_component_source_coverage_mismatch`. Activation state is not part
of identity, and offline composition does not require active routes.

Regression tests prove schema-valid H1 v1 attention with extra suspension
coverage and H1 v1 disposition with extra resumption coverage are rejected at
the composite boundary; an embedded attention source-family mismatch is
rejected; and exact source families with attention/disposition coverage plus
native-only cmode still produce aggregate `[attention, disposition]` and
`partial`. Existing C1–C10 cases remain covered.

R1 changed no schema bytes: H1 v1/v2, Composite v1, Result V3,
OperationResult v2, and the H0-G manifest hashes remain at their accepted A2.3
values. H1 v1 semantics changed = false; H1 v2 semantics changed = false;
market GET/HEAD/POST = 0/0/0.

R1 validation: the A2.3 composition plus prior focused suite passed with 126
tests and 0 failures. `default-ci` passed with 1268 passed, 0 failed, 1
skipped, 5 deselected and 18 warnings; `network_may_have_occurred=false`.
The Phase H V3 contract validator, compileall, and `git diff --check` passed.
