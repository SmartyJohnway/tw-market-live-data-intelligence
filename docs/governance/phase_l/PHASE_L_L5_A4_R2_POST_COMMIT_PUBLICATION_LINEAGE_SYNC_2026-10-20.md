# L5-A4-R2 — Post-Commit Derived Publication Lineage Synchronization

## Authority and scope

This is a bounded derived-publication repair within the existing L5-A4 authorization. Entry is branch `phase-l/l5-a4-publication-integration-conformance`, HEAD `8fc37608889fd11ea865827a3cf9e20524457271`, tree `3f0bd468d797c8a4e57687a60436263a57fb0097`; the A4 authorized base remains `91458d203ac28fe4ab00c89229ed1320bcb64753`.

The A4-R1 compatibility repair itself was correct. Independent review found that committing the Catalog/Route publication-prose changes changed their Git lineage after derived publication was generated. The R2 changes no canonical Catalog/Route authority and no runtime semantics; they only synchronize the portable catalog and Quick Guide to the now-committed authority.

## Preserved evidence

The primary A4 run `l5-a4-20261020T071416Z` remains HOLD evidence with its 48-artifact manifest and canonical SHA-256 `7e76b0db1a2d99bc14903ad79124dd630e3f5aaeda47518c68303f44c3399769`. A4-R1 `l5-a4-r1-20261020T074329Z` remains its pre-commit PASS evidence with 51 artifacts and canonical SHA-256 `dd83ba9ab1d353993d2220d3e699bb0ed815bf54e0ee91d2e3435161459869e9`. Neither run is rewritten as post-commit validation.

## Canonical authority and derived publication

Catalog last-change commit is `8fc37608889fd11ea865827a3cf9e20524457271`, blob `b9591b030037416333a73fc6c294a161f7c16ef0`. Routing last-change commit is the same R1 commit, blob `0f47162035e7870b98cca28cc47568abc2c9034e`. These are the only canonical sources; R2 does not edit them.

The only allowed R2 files are `skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json` and `skills/tw-market-evidence-agent/references/capability_quick_guide.md`. Their diffs contain only generated lineage values. The portable catalog binds to the Catalog commit/blob; Quick Guide routing lineage binds to the Routing commit/blob. The generator is not hard-coded to these SHAs.

## Validation and boundary

The amended dirty-entry exception contained exactly these two modified files, with zero untracked and zero staged paths at preflight. Both review-time raw SHA-256 values were independently reproduced. Running `python scripts/generate_portable_catalog.py` was idempotent: both file hashes remained unchanged and the diff still contained exactly those two paths.

The inherited portable-catalog, runtime Skill/guide, and A4 publication validators passed. Required focused tests, validators, and default-ci comparison are recorded in the R2 evidence run. The accepted historical default-ci failure set remains 41 nodes; these failures are not repaired or reported as passing. Provider requests, live acquisition, and production state mutations are zero. External socket attempts are not measured.

Final R2 disposition is `L5_A4_R2_POST_COMMIT_PUBLICATION_LINEAGE_SYNC_PASS` only after post-sync-commit and final committed-state publication validations pass. L5-A5+, L6-L7, push, PR, and merge remain unauthorized. L5-A4 Owner acceptance remains pending.

## Pre-commit results

Dirty-entry lineage and generator idempotence passed. Pre-commit portable catalog, runtime Skill/guide, and A4 publication validators passed. Focused results: A4 publication 23 passed, R1 negative guard 18 passed, and I3 preflight 6 passed. All 14 required validators passed. Default-ci reported 1,248 passed, 41 failed, four skipped, and five deselected; the 41 failed nodes exactly match the accepted R1 historical set, with zero candidate-only failures. These 41 remain failures. Post-commit validation is still required before final disposition.
