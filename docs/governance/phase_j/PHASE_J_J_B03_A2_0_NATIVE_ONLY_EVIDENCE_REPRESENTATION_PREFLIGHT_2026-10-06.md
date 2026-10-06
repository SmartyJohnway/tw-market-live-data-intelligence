# J-B03-A2.0 — Native-Only Evidence Representation Preflight

**Disposition:** `J_B03_A2_0_MINIMAL_CONTRACT_AMENDMENT_REQUIRED`

## Finding

No existing H1 → Result V3 → Audit V3 → AI handoff path safely represents the S3-approved native fact `SuspensionOfTrading = \uff39` with unresolved semantics and no canonical status subtype.

The H1 v1 item requires `status_type`, whose frozen enum contains only canonical types. `status_lifecycle=unresolved` does not undo `status_type=suspension`. A mechanical fixture with that shape passes the H1 schema, Result V3 H1 schema fragment and current semantic validator, but it remains semantically false: the validator checks the five-type coverage partition and no-evidence conditions, not source marker meaning or item/coverage consistency.

An empty `items` list with `status=partial` is schema- and validator-valid. It can preserve the raw marker only if the value is embedded in free-text `caveats`; the frozen contract does not define caveats as structured source facts. The typed Result projector copies the H1 artifact unchanged, but this does not create a native fact slot. Audit V3 keeps source attempts, citations and the evidence artifact path/hash, not a self-contained raw fact. AI handoff structured content carries the canonical Result, while its Markdown formatter omits H1 source, record date, items and native provenance.

## Paths and fixtures

| Path | Mechanical result | Contract decision |
| --- | --- | --- |
| A: `status_type=suspension`, lifecycle unresolved | Schema PASS; semantic validator PASS; Result V3 H1 fragment PASS; projector preserves fields | **Unsafe.** The subtype itself asserts canonical suspension. |
| B: empty items, native fact elsewhere | No structured top-level native fact slot; raw text can fit only in caveat | Insufficient; prose caveat is not a typed source fact. |
| C: `partial` with empty items | Schema PASS; semantic validator PASS; Result projection preserves caveat | `partial` is the truthful status after amendment, but caveat-only value is insufficient. |
| D: another native/untyped structure | None found for H1 across Result/Audit/Handoff | No safe existing path. |
| E: no safe representation | Confirmed by A–D | Minimal additive amendment required. |

For a future native-only H1 result, keep `status=partial`; declare all five canonical types, cover none from this native-only source, leave all five uncovered, set `declared_scope_complete=false`, and do not emit `no_evidence_in_covered_scope`. Retrieval, raw source-shape validation and exact-target search may be true; `source_contract_validated` must not imply marker business semantics are known.

## Minimal amendment and versioning

Add `native_observations[]` to a new `trading_status_context_evidence.v2`, outside canonical `items[]`. Each observation should retain the exact source-native field, official label, raw value/type, source record date, `semantic_status=unresolved`, caveat and governed citation. The parent H1 target, source and observation time supply the exact binding. Do not add `status_type=unknown`, `native_only` or `unresolved`.

Preserve H1 v1. Formally amend the frozen H1 concept to distinguish native observations from canonical items. Reopen the frozen Result V3 contract additively so its H1 property accepts an explicit v1-or-v2 union; update the freeze manifest without rewriting historical artifacts. Keep the Audit V3 schema shape and outer versions if the generic path/hash reference remains sufficient, while updating artifact/audit maps and acceptance tests for v2. Update H1 Markdown rendering so the actual AI handoff text includes label, exact value, date, unresolved caveat and citation. MCP remains six tools.

The implementation gate must also define how `native_observations` contribute to `item_count`/`result_item_count`; the current loader counts `len(items)` and would otherwise report zero for a native-only artifact.

## Next gate and state

Recommend **J-B03-A2.1 — Minimal Native-Evidence Contract Amendment** under separate Owner authorization, before adapter implementation. J-B03 remains HOLD pending representation, implementation and representative acceptance. `H0-SRC-01E` and `H0-SRC-02` remain OPEN; `tpex_spendi_today` remains `OPTIONAL_CURRENT_EVENT_DETAIL_NOT_J_B03_BLOCKING`.

- Market-data GET/HEAD/POST = **0**; no source acquisition.
- No production code, schema, contract, catalog, routing, registry, activation or MCP change; MCP remains 6.
- J-B04 = BLOCKING; Phase J = NOT STARTED.
- `data/` and frozen historical records were untouched.
- Temporary fixture checks passed both required JSON schema and semantic validator checks for Paths A and C; 60 existing focused H1 V3 projection/freeze tests passed.

See the companion JSON for detailed propagation, freeze-surface impacts, compatibility analysis and test evidence.
