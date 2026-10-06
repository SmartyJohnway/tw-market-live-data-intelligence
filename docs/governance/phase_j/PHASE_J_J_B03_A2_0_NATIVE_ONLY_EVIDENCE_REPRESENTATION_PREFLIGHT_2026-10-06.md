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

Preserve the frozen H1 v1 and Result V3 schemas byte-for-byte. A native H1 v2 must be structurally present in the canonical Result, so the future contract requires a new Result version; `unified_market_evidence_result.v4` is the current candidate. Do not reopen or amend Result V3 and do not call a modified Result V3 backward-compatible. Keep Audit V3 schema unchanged: its generic artifact reference carries capability, schema version, path, hash, lineage and citations. Future builders, loaders and audit acceptance maps still need explicit H1 v2 / Result V4 support.

The H0-G V3 schema freeze manifest is immutable historical authority. Do not update it. A2.1 must author a new dated/versioned freeze and acceptance authority for H1 v2, Result V4 if accepted, and related projection and handoff changes. This follows the existing V3 promotion inventory rule that frozen schemas and historical artifacts remain immutable while current promotion/activation projections are mutable. The frozen V3 manifest and exact-contract record remain unchanged.

No Request V3 change is required by this output-representation decision: the existing `trading_status_context` request can request the capability. Future AI handoff must include the source-native label, exact value, source record date, unresolved caveat and citation; MCP remains six tools. Define separate canonical status item count, native observation count and operation/result evidence count, and preserve aggregation invariants rather than mechanically summing arrays.

| Surface | A2.0 recommendation |
| --- | --- |
| H1 conceptual contract | New addendum or superseding current-state authority; leave historical frozen record unchanged. |
| H1 v1 schema | Immutable. |
| H1 v2 schema | New contract with `native_observations[]`. |
| Result V3 schema | Immutable; no reopening or amendment. |
| Result V4 | New Result contract version required; V4 is the current candidate. |
| Audit V3 schema | No change currently required; implementation maps/builders/loaders may need extension. |
| H0-G V3 freeze manifest | Immutable historical authority; do not update. |
| A2.1 freeze/acceptance authority | New dated/versioned record required. |
| Request V3 | No change required. |
| AI handoff | Projection and acceptance change required; no new MCP tool. |

The existing H1 v1 fixtures, Result V3 artifacts, Audit V3 packages, active routes, and MCP consumers remain valid under their existing versions. Future Result V4 consumers must recognize the new version; no historical V3 artifact is rewritten.

## Next gate and state

Recommend **J-B03-A2.1 — Minimal Native-Evidence Contract Amendment** under separate Owner authorization, before adapter implementation. Its contract-authoring scope is H1 v2, a Result V4 candidate, a new dated/versioned freeze/acceptance authority, Result V4 projection, Audit V3 mapping support, AI handoff support, validators, fixtures and tests. It must not modify H1 v1, Result V3 or the original V3 freeze manifest. It must define separate canonical-item, native-observation and operation/result evidence counts. No route activation or `tpex_cmode` acquisition-adapter implementation is authorized by that gate without separate authority. J-B03 remains HOLD pending implementation and representative acceptance. `H0-SRC-01E` and `H0-SRC-02` remain OPEN; `tpex_spendi_today` remains `OPTIONAL_CURRENT_EVENT_DETAIL_NOT_J_B03_BLOCKING`.

- Market-data GET/HEAD/POST = **0**; no source acquisition.
- No production code, schema, contract, catalog, routing, registry, activation or MCP change; MCP remains 6.
- J-B04 = BLOCKING; Phase J = NOT STARTED.
- `data/` and frozen historical records were untouched.
- Temporary fixture checks passed both required JSON schema and semantic validator checks for Paths A and C; 60 existing focused H1 V3 projection/freeze tests passed.

See the companion JSON for detailed propagation, freeze-surface impacts, compatibility analysis and test evidence.
