# L5-A4-R1 — Historical I3 Compatibility Guard Reconciliation

Authority: `USER_CHAT_2026-10-20_PHASE_L_L5_A4_PUBLICATION_INTEGRATION_AUTHORIZATION`; bounded repair within A4. Run: `l5-a4-r1-20261020T074329Z`.

## Entry and preserved HOLD

The worktree remains on `phase-l/l5-a4-publication-integration-conformance` at
entry HEAD `91458d203ac28fe4ab00c89229ed1320bcb64753`, tree
`91ecbb8dac58800f7f21cebf8e9657fed43ad2c6`. The A4 publication-only Catalog
and Routing changes remain the only changes to those production authorities;
all functional fields match the pinned A4 entry. Existing A4 uncommitted
publication files were preserved.

The primary A4 run `l5-a4-20261020T071416Z` remains historical HOLD. Its original
48-artifact manifest is unchanged, with canonical SHA-256
`7e76b0db1a2d99bc14903ad79124dd630e3f5aaeda47518c68303f44c3399769`. Its
recorded default-ci result remains 1,247 passed / 42 failed / 4 skipped /
5 deselected: 41 historical failures and one candidate-only failure. R1 does not
rewrite the original evidence.

## Reconciled compatibility boundary

The A4 publication content did not regress runtime behavior. The original A4 HOLD
was valid because default-ci had one candidate-only failure. The failure was caused
by the historical I3 compatibility comparison lacking an explicit projector for
the authorized L5-A4 I2 publication-only reconciliation.

`scripts/phase_i_i3_a4_compat.py` now pins the pre-A4 authority at
`91458d203ac28fe4ab00c89229ed1320bcb64753`. Current production authorities are
validated first by the existing I3 activation gate. For historical comparison only,
the projector locates `index_futures_context`, validates every field against the
pinned A4 entry except the exact A4-authorized descriptive fields, verifies the new
publication text against the established accepted wording, and restores only those
fields to their pinned A4-entry representation. It does not write or treat the old
Phase-I snapshot as current authority.

Catalog projection is limited to the I2 `description` and the one specified stale
activation sentence in `known_limitations`. Routing projection is limited to the
I2 `capability_status_source` and one specified stale activation sentence in
`known_limitations`. Every other field remains part of the historical comparison.
No global prose stripping or arbitrary hash bypass was added. Negative tests prove
that Catalog support/runtime/market drift, Routing status/runtime/executor/output
contract/other routing drift, unapproved I2 prose, and other-capability changes
remain rejected.

## Verification and disposition

The historical I3 test remains unchanged. R1 records the exact single-node and
complete-file results, A4 validator/focused tests, negative guard tests, required
validators, default-ci exact failure-set comparison, scope inventory, and manifest.

The historical guard remains fail closed for functional authority drift. No
runtime/source/route/executor/authorization behavior, Request/Result/Audit schema,
handoff envelope or public MCP tool changed. Provider requests, live market/source
acquisition and production state mutations are zero. External socket attempts are
`NOT_MEASURED`; no OS-wide claim is made.

The exact default-ci failure set matches the accepted 41-node historical baseline; candidate-only failures are zero. All R1 acceptance gates pass. The final technical disposition is `L5_A4_TEST_CATALOG_SKILL_GUIDE_PUBLICATION_INTEGRATION_PASS`; the original A4 run remains HOLD evidence. The four canonical front doors now state L5-A4 technical publication integration complete / Owner acceptance pending, with L5-A5+, L6-L7, and Phase M unauthorized. Owner acceptance remains pending.
