# M8R-06-01C1B Compact Runtime Identity Index — Final Closure

Task: `M8R-06-01C1B-COMPACT-RUNTIME-IDENTITY-INDEX-IMPLEMENTATION`
Baseline: `78bb7ec582ec7d94eef49332a0b1b773dd4e5f33`
Starting PR head: `99d0c97b0333c5e1f292ea41401631b33e82a3ba`
Authorized bundle: `m8r06-01b-20260807T053540Z`

## Decision

Status: **PASS_WITH_CAVEATS**
Principal decision: **READY_FOR_M8R_06_01C2_AUTHORIZATION_REVIEW**

This closes C1B only. M8R-06-01C2, M8R-06-01C Post-Activation Acceptance, and M8R-06-02 remain **NOT_AUTHORIZED**. Production runtime and the production pointer were not modified.

## Source and candidate binding

- The original sealed 01B bundle was copied without modification and independently verified against the committed 01B immutable manifest, including every declared component and raw payload hash and count.
- Semantic source snapshot ID: `dryrun-m8r06-01b-20260807T053540Z`.
- Snapshot artifact filename: `dryrun_snapshot.json`. The filename is recorded separately and is not used as the snapshot identity.
- Source snapshot SHA-256: `a851aa664727a02df87e88b086d956467ce9348aa8a9d9ef9dfc33cc415dc2b8`.
- Compact index SHA-256: `ad467f077c76d9c7462545fcf322d4960cbd485d09d34463e26dfefea8c1c455`.
- Compact manifest SHA-256: `01857224d025bd9342402917c140050f0fb40b385a65103702c856037dfc93db`.
- The committed immutable seal is `docs/reviews/m8r06-01c1b-runtime-index-manifest/immutable_manifest.json`. The candidate itself remains Git-ignored.

## Canonical resolver equivalence

The compact lookup now exposes the canonical five-key contract: `snapshot`, `by_canonical`, `by_isin`, `by_code`, and `by_name`. It preserves every field read or returned by the protected canonical resolver. The canonical adapter itself was not changed.

The local sealed-bundle test built both lookups from the same 43,070-record snapshot and called the same `resolve_verified_security_identity()` implementation. Exact result dictionaries were compared for 86,160 deterministic queries:

- all 43,070 canonical target IDs;
- all collision groups present in the sealed population (zero ISIN and zero unscoped-code groups);
- all 43,070 unique normalized Chinese/English name queries;
- all 40,746 known non-runtime-eligible identities through exhaustive canonical-ID coverage;
- 16 market-mismatch cases;
- not-found sentinels;
- `2330 / TWSE` and a real TPEx identity.

The sealed population contains no quarantined identities or `fixture_observation_only` records. Synthetic CI fixtures therefore exercise collision, quarantine, ambiguous-code, and fixture-rejection behavior that is absent from this sealed population. Full-vs-compact semantic equivalence passed exactly.

## Coverage and determinism

Coverage was computed from source semantics, not placeholders:

- knowledge universe: 43,070;
- runtime eligible: 2,324;
- quarantined identities: 0.

The historical runtime-candidate estimate of approximately 2,327 was only a cross-check. The authoritative sealed snapshot currently marks 2,324 records as `allowed` or `allowed_with_caveat`; the implementation does not force the historical estimate.

Two independent temporary-directory materializations produced identical bytes:

- index hashes: `ad467f...c455`, `ad467f...c455`;
- manifest hashes: `018572...3db`, `018572...3db`.

Canonical artifact metadata is source-derived. Wall-clock execution time does not affect either artifact hash.

## Executable validation

- C1B focused tests: 23 passed, including synthetic CI and the non-skipped sealed-bundle gate.
- Canonical Security Master regressions: 18 passed.
- C1R regressions: 9 passed.
- Mode A regressions: 42 passed.
- Workbench/API regressions: 8 passed (one upstream deprecation warning).
- Repository workflow compile step: passed.
- Repository `default-ci` profile: 768 passed, zero failed, no network; the C1B test module is included in the profile.

The strict loader's executable negative cases cover missing/invalid artifacts, both schema versions and schemas, all authorized lineage fields, record counts, duplicate canonical IDs, index/schema hash bindings, and invalid compact records.

## Accepted caveats

- Resolver compatibility requires more retained data: the compact index is 68,256,184 bytes, a 17.13% reduction from the 82,362,814-byte source snapshot.
- Real sealed-bundle collision, quarantine, and fixture-only counts are zero; deterministic synthetic tests cover those branches.
- The candidate is local-only and reproduction requires the exact original sealed 01B bundle. A fresh network reprobe is not equivalent and was not used.
