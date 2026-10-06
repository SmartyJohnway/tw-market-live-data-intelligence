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

Keep the history layers separate. The H0-G manifest was frozen at `286ef3dbb0acfffca10d35b0b13463c6b7357102` on 2026-09-21. It is immutable historical evidence and must not be edited. H1 v1 was introduced in that freeze commit and has no later modifying commit, so `trading_status_context_evidence.v1` remains unchanged.

The Result V3 hash difference is `HISTORICAL_FREEZE_HASH_DIFFERS_FROM_LATER_GOVERNED_CURRENT_ADDITIVE_SCHEMA`, not corruption. The manifest records the historical Result V3 SHA-256 `dae35eaa…`; the current schema path hashes to `e20a5456…`. Git history shows later Result V3 changes on 2026-09-29, 2026-09-30, and 2026-10-04. I0 explicitly left the exact Request/Result V3 additive schema shape for later bounded decisions. The current V3 validator lists Request/Result/Audit V3 schemas in `activation_mutable` and separately verifies later additive hashes. Historical snapshot immutability therefore does not prohibit governed additive evolution of the current V3 contract family.

| Surface | Authority category | A2.0-R2 finding |
| --- | --- | --- |
| H0-G V3 freeze manifest | A: historical snapshot immutable | Preserve unchanged, including its historical hashes. |
| H1 v1 | B: versioned contract immutable | Preserve unchanged; history shows no post-freeze edit. |
| H1 v2 | New contract | Add `native_observations[]` outside canonical `items[]`. |
| Result V3 H0-G snapshot | A: historical snapshot immutable | Keep as historical evidence; do not rewrite old artifacts. |
| Current Result V3 schema path | C: additive-mutable under later explicit authority | H1 v1-or-v2 additive support is `CANDIDATE_ALLOWED_FOR_A2_1_DECISION`; not selected here. |
| Result V4 | Optional versioning alternative | Use only if additive V3 is incompatible with current guarantees, strict consumers cannot safely accept it, or current versioning governance requires a new outer version. The old manifest alone does not require V4. |
| Audit V3 H0-G snapshot / current path | A / C | Preserve historical snapshot. Current schema has later additive authority; no Audit schema change is currently required because generic references carry capability, schema version, relative path, hash and lineage/citations. |
| Handoff renderer; loaders, lineage, builders, validators | D: current implementation/projection mutable | Future changes must carry H1 v2 and the chosen Result contract safely. |

A2.1 must create a new dated/current acceptance authority recording the accepted H1 v2 hash and either the current additive Result V3 hash or Result V4 hash, plus relevant projection, handoff, validator and acceptance evidence. The original H0-G manifest remains untouched.

No Request V3 change is required: this is an output/evidence representation change and the existing `trading_status_context` request can request the capability. Future AI handoff must include the source-native label, exact value, source record date, unresolved caveat and citation; MCP remains six tools. Preserve the item-count finding: A2.1 must separately define canonical status item count, native observation count and operation/result evidence count without breaking aggregation invariants.

Existing H1 v1 fixtures, Result V3 artifacts, Audit V3 packages, routes and MCP consumers must remain valid; additive evolution must not rewrite historical artifacts. A2.1 must explicitly test compatibility with strict consumers before selecting V3 or V4.

## Next gate and state

Recommend **J-B03-A2.1 — Minimal Native-Evidence Contract Amendment** under separate Owner authorization. Its first design decision is `RESULT_VERSIONING_DECISION`: choose `ADDITIVE_RESULT_V3` or `NEW_RESULT_V4` after compatibility and strict-consumer analysis. Then author H1 v2, support it in the chosen Result contract, create a new dated/current acceptance authority, add Audit V3 mapping support, handoff rendering, validators, fixtures and tests. Preserve H1 v1 and the H0-G manifest; do not assume Result V4 solely because the historical manifest exists. Define separate canonical-item, native-observation and operation/result evidence counts. No `tpex_cmode` acquisition adapter or route activation is authorized. J-B03 remains HOLD pending implementation and representative acceptance. `H0-SRC-01E` and `H0-SRC-02` remain OPEN; `tpex_spendi_today` remains `OPTIONAL_CURRENT_EVENT_DETAIL_NOT_J_B03_BLOCKING`.

- Market-data GET/HEAD/POST = **0**; no source acquisition.
- No production code, schema, contract, catalog, routing, registry, activation or MCP change; MCP remains 6.
- J-B04 = BLOCKING; Phase J = NOT STARTED.
- `data/` and frozen historical records were untouched.
- Temporary fixture checks passed both required JSON schema and semantic validator checks for Paths A and C; 60 existing focused H1 V3 projection/freeze tests passed.

See the companion JSON for detailed propagation, freeze-surface impacts, compatibility analysis and test evidence.
