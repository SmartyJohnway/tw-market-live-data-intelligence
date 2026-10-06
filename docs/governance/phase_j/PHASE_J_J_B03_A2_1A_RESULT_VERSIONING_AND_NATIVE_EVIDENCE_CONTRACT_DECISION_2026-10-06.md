# J-B03-A2.1A — Result Versioning & Native-Evidence Contract Decision

**Disposition:** `J_B03_A2_1A_SELECT_ADDITIVE_RESULT_V3`

**Starting main:** `1bdedf97d939a7d99e9bc8e03069f9693e4952fb`

**Starting tree:** `567f0c1a883d7dc9e587616b966b73b5c3a5bcc7`

**Owner authority:** `USER_CHAT_2026-10-06_J_B03_A2_1A_RESULT_VERSIONING_DECISION_AUTHORIZATION`

## Decision

Select **additive Result V3** for the future H1 v1-or-v2 nested contract. The current Result V3 path has later governed additive authority. A schema-version constant makes the existing H1 v1 branch and proposed H1 v2 branch disjoint. Existing Result V3 documents remain on the unchanged v1 branch, and the change can remain behind the existing six MCP tools.

This selects only the versioning strategy. It does not authorize modifying schemas, promoting runtime output, implementing an adapter, or activating a route. A2.1B must produce a new dated/current acceptance authority recording the updated Result V3 hash and evidence.

## H1 v2 candidate

Keep H1 v1 byte-, schema-, and semantics-unchanged. Existing attention output remains H1 v1 unless separately authorized. H1 v2 should mirror v1 and add required `native_observations[]` outside canonical `items[]`; retain the current one-source-per-artifact source model.

Minimum native-observation fields:

- `source_native_field`, `source_native_label`: non-empty strings;
- `source_native_value`: JSON scalar with exact type preserved (`string`, `number`, `boolean`, or `null`);
- `source_native_value_type`: matching scalar-type discriminator;
- `source_record_date`: required date;
- `semantic_status`: `unresolved` only for this contract;
- `semantic_caveat`: non-empty text;
- `citation_ids`: non-empty citation list.

For the accepted TPEx fact, preserve `SuspensionOfTrading = "Ｙ"` as a string. An unresolved observation cannot add `suspension` to `covered_status_types`, cannot become a canonical item, and cannot support stopped/tradeable wording. No lifecycle field is needed on a native observation.

The native-only case uses `status=partial`, `items=[]`, an observation, no covered canonical types, all five canonical types uncovered, and `declared_scope_complete=false`. Retrieval and exact target search may be true when proven. `no_evidence_in_covered_scope` is invalid because the native fact is evidence, while native evidence still does not establish canonical scope completeness.

`semantic_status` stays limited to `unresolved`. A future authoritative interpretation can be represented through the canonical item model under its own semantic authority; this decision does not add speculative native-observation states.

## Source and Result cardinality

H1 v1 has one top-level `source` object. Result V3 has one `trading_status_context` object per target. `TargetEvidenceProjection` likewise stores one object, while lineage maps one operation per `(canonical_target_id, data_need)`, rejects duplicate bindings, and rejects more than one typed H1 artifact for that binding.

H1 v2 should remain one-source-per-artifact. Canonical items and native observations may coexist only when the same top-level source supports both and each canonical item is independently semantically established and covered. Do not combine attention from one source and a `tpex_cmode` observation from another in one single-source H1 artifact.

The current Result path does not aggregate separate attention, disposition, and `tpex_cmode` operations for the same target/data need. A2.1B must resolve that multi-source composition boundary before claiming the J-B03 representative bundle is fully projected. It is an orthogonal composition issue; it does not make additive Result V3 incompatible or imply that Result V4 would solve aggregation.

## Versioning comparison

| Dimension | Additive Result V3 | Result V4 |
| --- | --- | --- |
| Existing Result V3 validity | Keep the existing H1 v1 branch unchanged. | Keep old V3 artifacts readable; add separate V4 read support. |
| H1 v1 compatibility | Unchanged. | Can remain supported in the new outer version. |
| H1 v2 support | Add disjoint H1 v2 branch in Result V3. | Embed H1 v2 in new outer schema. |
| Strict consumers | Update current Result V3 schema hash and mutable internal maps/validators; no MCP tool or input-schema change. | Add outer V4 schema/version dispatch and consumer support. |
| Persistence/readback | Keep outer V3 stored path; use nested schema version to validate H1 v1/v2. | Add distinct V4 persistence/readback path. |
| Mode C and MCP | Keep current V3 path and existing read/export tools; extend nested projection and rendering. | Add V4 output/readback behavior; same tools can carry it. |
| Rollback | Current preferred-version rollback remains server-owned; stored V3 packages remain read under V3. Test V3-to-V2 rollback. | Add V4-to-older-version transitions and retain V3/V4 readback. |
| Governance | Matches the later additive V3 authority model; new current hash gets a new dated acceptance record. | Clear new outer boundary, but adds a version without a current incompatibility requiring it. |

### Why the historical hash difference does not require V4

The H0-G manifest is the immutable 2026-09-21 snapshot, not a ban on later additive changes. Phase I I0 explicitly left the exact Request/Result V3 additive schema shape to later bounded decisions. The current validator lists Request, Result, and Audit V3 schema paths as `activation_mutable` and separately checks their later additive hashes. The current Result V3 hash is `e20a54563c9bf1454e705ccdaed8f002aed0cc4692e74eaaaa81568ac4278872`.

The Result V3 property can be expressed as `oneOf` the existing H1 v1 shape and the H1 v2 shape. Their `schema_version` constants differ, so instances cannot match both. The H0-G manifest and historical Result bytes/hashes remain untouched. Result V4 is only an alternative if A2.1B finds a concrete incompatibility: a strict supported consumer that cannot be updated safely, an H1 v1 pin in current Result semantics, a versioning rule requiring a new outer major version, or ambiguity in stored readback. The historical manifest alone is not such a reason.

The in-repository strict consumers are updateable: artifact loader, lineage maps, Result builder, Audit builder/maps, current Result schema validator, handoff renderer, and focused tests. The Local Service and MCP clients forward JSON without a fixed nested H1 response schema; no seventh tool or public input-schema change is needed. No frozen external strict response-schema consumer is declared by repository authority; A2.1B must test any supported external consumer before release.

## Audit, request, and handoff

- **Request V3:** no change required. It already requests `trading_status_context`.
- **Audit V3 schema:** no change required. Its Phase H evidence reference carries capability, string schema version, relative path, and SHA-256; source attempts and citation lineage are represented separately. The Audit builder, loader, and maps still need H1 v2 support.
- **AI handoff:** change required. Render source-native label, raw scalar, source record date, `semantic_status=unresolved`, caveat, and citation. Never turn `停止交易 = Ｙ` into “stopped”, “suspended”, or “cannot trade” without independent governed evidence.
- **MCP:** exactly six tools; no new tool or surface expansion.

## Counts and semantic validation

Keep three concepts separate:

- `canonical_status_item_count = len(items)`;
- `native_observation_count = len(native_observations)`;
- `operation_result_evidence_count`: an explicit operation-level count that accounts for both categories.

The current aggregation sums primary artifact `item_count` into operation `result_item_count` and bundle `total_item_count`. Keep `item_count` canonical-only and add a native count. Do not silently redefine legacy result or bundle counts by summing arrays. Evidence is present when canonical count **or** native count is positive. A2.1B must define operation-level accounting and test existing aggregation invariants before changing those fields.

A2.1B must strengthen semantic validation so every canonical item's `status_type` is covered and supported by governed semantics. A native observation never counts as canonical coverage. An unresolved `SuspensionOfTrading=Ｙ` cannot stand in for a suspension item. Validate required date, citations, caveat, and exact scalar type; disallow no-evidence status when a native observation exists.

## In-memory candidate checks

Temporary copies of the current schemas were tested in memory; no schema/code/test fixture was changed or committed.

- A — existing Result V3 with H1 v1 under candidate oneOf: **PASS**.
- B — H1 v2 native-only partial fixture: **PASS**.
- C — Result V3 with H1 v2 under candidate oneOf: **PASS**.
- D — unresolved marker used as canonical suspension shortcut: **rejected by proposed semantic policy**; A2.1B must implement this check.
- E — native observation claiming suspension coverage: **rejected by proposed semantic policy**; A2.1B must implement this check.
- F — missing source date, citation, or semantic caveat: **rejected by candidate schema**.
- oneOf ambiguity: **none**, because v1 and v2 schema-version constants are disjoint.

## Next gate and state

Recommend **J-B03-A2.1B — Implement H1 v2 + Additive Result V3 Contract Amendment**. First author H1 v2 and additive Result V3 under a new current acceptance authority. Before acceptance, test strict consumers and rollback, resolve the one-source/multi-operation composition boundary, define count semantics, strengthen semantic validation, add Audit V3 mapping, and verify guarded AI handoff. No source adapter, market execution, route activation, or preferred-version promotion is authorized here.

## Validation

- JSON parse, `git diff --check`, and `python scripts/validate_phase_h_v3_contracts.py`: **PASS**.
- Required focused tests: **60 passed**.
- Additional Local Service/MCP/promotion tests: **24 passed, 1 failed**. The failing existing assertion expects `recent_performance.routing_disposition=blocked`, while the current capability response returns `resolved`. No product-code change was made in this governance-only tranche.

- Market-data GET/HEAD/POST = **0 / 0 / 0**.
- No production, schema, runtime, catalog, routing, registry, activation, or MCP change in A2.1A.
- H0-SRC-01E = OPEN; H0-SRC-02 = OPEN.
- J-B03 = HOLD; J-B04 = BLOCKING; Phase J = NOT STARTED.
- `data/` untouched.

See the companion JSON for consumer-by-consumer classification and the full comparison matrix.
