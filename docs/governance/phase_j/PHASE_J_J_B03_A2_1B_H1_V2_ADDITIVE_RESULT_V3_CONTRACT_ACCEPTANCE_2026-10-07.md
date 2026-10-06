# J-B03-A2.1B — H1 v2 and Additive Result V3 Contract Acceptance

**Disposition:** `J_B03_A2_1B_H1_V2_ADDITIVE_RESULT_V3_CONTRACT_ACCEPTED`
**Record state:** contract acceptance on the implementation branch, pending Draft PR review
**Authority:** `USER_CHAT_2026-10-06_J_B03_A2_1B_CONTRACT_AMENDMENT_AUTHORIZATION`

## Decision

H1 v1 remains unchanged. H1 v2 adds `native_observations[]` beside canonical
`items[]`; Result V3 now accepts either H1 version through a disjoint `oneOf`
selected by the exact `schema_version` constant. Result V4 was not selected.
The historical H0-G freeze manifest and its recorded hashes remain unchanged.

The v2 native observation records the source-native field and label, exact JSON
scalar value and type, source record date, `semantic_status=unresolved`, a
non-empty caveat, and citations. It inherits target, source, observation time,
and coverage from its one-source H1 artifact. A native observation does not
establish a canonical subtype or add canonical coverage. In particular,
`SuspensionOfTrading=Ｙ` cannot become a canonical suspension, `stopped=true`,
or a current-tradeability conclusion. Blank values and absent rows remain
non-evidence for normal trading.

Native-only H1 v2 is `partial`, has no canonical items or covered status types,
keeps every declared canonical type uncovered, records successful retrieval
and exact-target search, and cannot claim complete scope or
`no_evidence_in_covered_scope`. Canonical item coverage is validated: every
canonical item's type must be in `covered_status_types`. Same-source mixed
canonical and native evidence is allowed; one H1 artifact still represents
only one top-level source contract.

`source_contract_validated=true` records only transport, payload, field, JSON
type, and date-grammar validation. It does not mean that the business meaning
of a source-native marker has been resolved.

## Compatibility and propagation

- **H1 v1:** unchanged schema hash `638200509cde05613d17bd4158d1676c3c086d2b10aa2f50fb85d52febe30ecf`; the existing attention route remains on v1.
- **H1 v2:** [schema](../../../schemas/trading_status_context_evidence.v2.schema.json), SHA-256 `818de1e9c501b4c4d0bb06d6a1503dafba7b63dc60977791f7842cd8b5a31d38`.
- **Result V3:** prior current hash `e20a54563c9bf1454e705ccdaed8f002aed0cc4692e74eaaaa81568ac4278872`; additive current hash `a8519bc4c444f59b24e74de702667c5570ed15f816a841b509e24b2f3bc788d5`.
- **Request V3:** unchanged. **Audit V3 schema:** unchanged; its generic artifact reference carries H1 v2 schema identity, path, hash, and lineage.
- Loader and lineage accept H1 v1 or v2 and reject duplicate typed artifacts for one operation/binding. Result projection preserves the validated artifact. The Audit V3 reference and citation lineage are tested.
- AI handoff renders the native label/value/date, unresolved status and caveat, and citation. Its wording prohibits treating the marker as proof of suspension or tradeability.
- Legacy `item_count`, `result_item_count`, and `total_item_count` meanings are unchanged. H1 v2 adds `native_observation_count`; evidence presence recognizes canonical items or native observations.
- The six MCP tools and their public input contracts are unchanged. Preferred Result V3 remains as configured; no promotion occurred.

## Historical Phase I containment

The first post-amendment `default-ci` run exposed eight I3 containment failures:
the historical comparison treated the authorized Result V3 H1 v1/v2 union as
unrelated drift. The containment comparison now recognizes only that exact
version-discriminated H1 union and compares its H1 v1 branch against the
historical snapshot. Other authority remains compared, and the current Result
V3 hash is independently pinned by the current Phase H validator. No frozen
Phase I ledger or H0-G manifest was rewritten.

## Baseline repair and validation

The exact baseline group initially produced 24 passes and one stale failure:
the Local Service test expected `recent_performance.routing_disposition` to be
`blocked`, while current accepted authority says `resolved`. That single test
expectation was corrected in its own commit, `a207c32f1af4884d1bcca4b8e721f4970f880891`;
the group then passed 25 tests.

- `python scripts/validate_phase_h_v3_contracts.py` — PASS.
- `python -m compileall -q scripts server tests` — PASS.
- Required focused suite — **107 passed**.
- `python scripts/run_test_profile.py default-ci --json` — **PASS**, 1,266 passed, 1 skipped, 5 deselected, 0 failed; `network_may_have_occurred=false`.
- Stored Result V3 readback remains pinned to V3 when a different output version is requested; focused rollback/readback test — PASS.

## Boundaries

This tranche adds internal contract support only. It adds no tpex_cmode
acquisition adapter and changes no source, route, catalog, routing, executor
registry, activation, or MCP tool. It performs no market GET, HEAD, or POST.
No route was promoted, the accepted attention route remains on H1 v1, and no
historical artifact was migrated or rewritten.

```text
H0-SRC-01E = OPEN
H0-SRC-02  = OPEN
J-B03      = HOLD
J-B04      = BLOCKING
Phase J    = NOT STARTED
MCP        = 6 tools
```

The next candidate gate is **J-B03-A2.2 — Representative H1 Composition / Adapter
Integration Design**, subject to separate authorization. The existing one-binding,
one-typed-artifact model is preserved, and this tranche did not establish a
governed composition path for the representative attention + disposition +
native current-status bundle. Design that composition before implementing the
tpex_cmode adapter. Live/source activation remains outside this contract
amendment.
