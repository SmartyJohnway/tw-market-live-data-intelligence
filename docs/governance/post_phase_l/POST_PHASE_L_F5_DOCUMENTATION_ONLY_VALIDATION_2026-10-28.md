# Post-Phase-L F5 — Documentation-only Validation

Date: 2026-10-28

Status: **CANDIDATE_COMPLETE / SELF_REVIEW_PASS**

## Scope

F5 validates the cumulative Post-Phase-L F0–F4 documentation candidate without
reopening Phase L or redefining frozen `v1.5.0` release authority.

Frozen release identity remains:

- commit: `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`
- tree: `d44f66dc154c21326ac8b105d2f15fd793f6071b`
- GitHub release: `v1.5.0`

Phase M remains **NOT_AUTHORIZED**.

## Lifecycle validator realignment

Current `ProductVersion = 1.5.0` now validates as stable/published rather than
`selected_unpublished`. Historical `selected_unpublished` remains an explicit
supported validator state for frozen pre-publication evidence.

Updated validation-only surfaces:

- `scripts/validate_v1_front_door.py`
- `scripts/validate_v1_public_contracts.py`
- `scripts/run_m5ij_end_to_end_acceptance.py`
- their focused unit tests
## Validation results

- current-vs-historical contradiction scan: `0` current stale-status hits;
- current local Markdown links: `109 / 109` resolved before final F5 record;
- GitHub `v1.5.0` live release: stable, non-draft, non-prerelease;
- tag target: exact frozen commit `acaf726...`;
- six release asset names / states / server SHA-256 digests: exact match;
- README release/download URLs: exact live asset URLs;
- Native / MCPB documented hashes: exact frozen hashes;
- `validate_v1_front_door.py`: PASS;
- `validate_v1_public_contracts.py`: PASS;
- runtime Skill / guide sync: PASS, exactly six MCP tools;
- portable Catalog sync: PASS, deep equality verified;
- product-version consistency: PASS;
- `git diff --check`: PASS;
- cumulative scope containment: PASS; no runtime/product-authority paths changed.

Final focused regression used a fresh workspace-local pytest base directory and
completed **141 passed / 0 failed**.

## Preserved historical semantics

The first broad regression used the default Windows user temp directory. Two R1
publication-manifest synthetic tests failed because their asset paths were
outside the manifest builder's selected-workspace containment boundary. No
product code was changed. Re-running the complete R1 suite with a fresh
`C:\twmarket_temp\...` pytest base produced **37 passed / 0 failed**; the final
combined focused regression then produced 141/141 PASS.
## Boundary and disposition

F5 does not authorize or perform:

- modification of the governance-frozen `v1.5.0` tag or release assets;
- MCP Registry or Docker Registry publication;
- runtime/product behavior changes;
- Phase M entry;
- commit, push, or pull request creation.

The cumulative F0–F5 candidate is ready for independent review. A later
accepted documentation-only commit on `main` may advance beyond the frozen
release source without redefining `v1.5.0`.
