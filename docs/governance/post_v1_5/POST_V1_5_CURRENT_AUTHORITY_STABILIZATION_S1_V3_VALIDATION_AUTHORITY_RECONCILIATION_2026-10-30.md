# S1 — Current V3 Validation Authority Reconciliation

Classification: CURRENT validation reconciliation / uncommitted review candidate.
Date: 2026-10-30 (Asia/Taipei; execution crossed midnight from 2026-10-29).
Authority: Owner's explicit S1-only implementation and deterministic-test authorization
in the task conversation. Independent review is pending. Commit/push are NOT AUTHORIZED.
Implementation disposition: READY_WITH_NOTES (S1 focused checks pass; default-ci
has out-of-scope historical/current authority failures described below).

## Baseline and scope

- Branch: `main`.
- Starting HEAD and local `origin/main`: `344a00689785387f9e6af37dde484b798736ce51`.
- Starting working tree: clean; staged changes: zero; untracked files: zero;
  ahead/behind: `0/0`. No fetch, stage, commit or push was performed.
- Stable product: `v1.5.0`; frozen source commit:
  `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`; frozen tree:
  `d44f66dc154c21326ac8b105d2f15fd793f6071b`.
- Phase L remains CLOSED; Phase M remains NOT_AUTHORIZED.
- P1 and S2/S3/S4/S5 are excluded. No runtime, schema, route, acquisition,
  installation, Security Master, Watchlist, release or publication change.

## Problem and authority analysis performed before editing

`python -B scripts/validate_phase_h_v3_contracts.py` reproduced
`phase_i_v3_additive_schema_drift:schemas/unified_market_evidence_result.v3.schema.json`.
The current validator still required Result V3 SHA-256
`9269fc9e5e07884fa2de791eae902ee57b3d937dbb793318ca4aff1a93fc5bcb`.
The actual accepted current schema SHA-256 is
`700e13779757300699e6cf4dd2c81768dbd56eb853befc9f9cf218102b6a7b3a`.
Current bytes equal `git show acaf726a:schemas/unified_market_evidence_result.v3.schema.json`
byte for byte. This is stale current validation authority, not an unauthorized schema.

The exact Result V3 schema diff in
`cf90c697665e24b8bd5700bf8c033b102f1364e0` (L7-A5-R5/R5.1) changes only
the embedded I3 retrieval semantics:

1. `retrieved_at` remains required, with base type string-or-null.
2. Complete body requires a date-time string; incomplete body requires null.
3. `complete`, `binding_failed`, and `unavailable` require a complete body.

The prior complete/failure payload restrictions remain. A complete-body normalization
failure can still be `source_failed` with a timestamp; this must not be confused with
an incomplete-body transport failure. No new status meaning is introduced here.

Acceptance chain inspected:

- `docs/governance/phase_l/PHASE_L_L7_A5_FINAL_GOVERNANCE_RECONCILIATION_2026-10-26.md`:
  accepted R5/R5.1 purpose and consolidated independent review PASS.
- `docs/governance/phase_l/PHASE_L_L7_A5_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-27.md`:
  accepted repair chain and PR #418 merge `a812e212cb710a869289a18b3e7a29c886a43512`.
- Existing `test_l7_a5_r5_temporal_provenance.py` and
  `test_l7_a5_r5_1_finalization_publication.py`, including semantic-drift negatives.

Search of scripts/tests found the other obsolete Result identity in
`scripts/validate_phase_j_b04_a3_network_free_implementation.py`.
That identity belongs to HISTORICAL J-B04-A3 replay. Its `BASELINE`
`a833a5728501d99b942928fdebb790a993a5e838` actually contains schema bytes with
the old hash. It is retained, not promoted to current schema authority.
The new test verifies that historical identity in its Git source context and
that the historical validator/acceptance record are unchanged.
No historical validator invocation was added to the current validator.

## Bounded correction and ownership

Changed files, exactly:

1. `scripts/validate_phase_h_v3_contracts.py`.
2. `tests/unit/test_current_v3_validation_authority.py` (new).
3. This record (new).

The current validator now checks an explicitly owned current Result V3 byte pin
separately from the unchanged Request/Audit Phase I pins and historical H0-G
manifest protection. It then runs full embedded-definition schema probes over
the accepted I3 status/body/timestamp combinations, including invalid dates,
timezone-less timestamps and missing timestamps. Synthetic probe objects are
never persisted or used as market evidence; they perform no acquisition.
The format checker follows the existing offline R5 test convention, avoiding a
dependency on optional jsonschema date-time extras.

Existing V1/V2 manifest checks and selected-source/route assertions remain active.
Strict JSON parsing rejects duplicate members, malformed JSON and invalid UTF-8.
New mutation tests exercise the semantic guard separately from the byte pin,
including a simulated repin of a weakened schema: changing a hash alone cannot
authorize removal of the retrieval-state restrictions.

Ownership: this S1 reconciliation binds `CURRENT_RESULT_V3_SHA256` to the already
accepted R5 repair and frozen release source. It does not authorize a new schema.
A future legitimate schema change requires explicit scope authorization, a reviewed
schema diff and semantic tests, a new acceptance/reconciliation record, and an
intentional current pin update. Frozen/historical identities remain unchanged.
Automatic hash recalculation or blessing the observed working tree is forbidden.
No additional fingerprint manifest or competing schema source of truth was added.

## Before/after invariants

All values below are identical before and after S1.

| Surface | SHA-256 / identity |
|---|---|
| Result V3 | `700e13779757300699e6cf4dd2c81768dbd56eb853befc9f9cf218102b6a7b3a` |
| Request V1 | `c56add4bdb200d7dc1a1e9c27d576fefbf434dc7a8658fd17000c4ae8ee84cac` |
| Request V2 | `757d864c3a00d296f8ebf2eccdbb47a1d39ca8a222e9d939f34ef854f4245e3b` |
| Result V1 | `58fe88d33bbc5f53639cd3b9896ad0cf6106e00ec6e9f93630a45339c545f05f` |
| Result V2 | `ed9928530be37fc4b2a4d1e386eb2ea8ff5dbe33e4c6598d0a8010c338dea444` |
| Audit V1 | `5877ad564e488c6d4d4c5ef6b405e3b8dde60f056327cc1babf16a5ec2364198` |
| Audit V2 | `a798e435168a185c00250f56bb88aa09fc57788fcd47048fdd42ae29c977b14e` |
| Routing V3 | `77198c96d92bffffe3ee0cdaca2dd2771b0bc42ef6ca63e5ded34cb290ede1e5` |
| Entire Catalog V3, stronger than executable-field equality | `53f90abd35bbbaf4eed97c7b19d27a2ba2dec3d2f99d26996bb75f096716cffa` |
| Executor registry metadata | `eb12b538687285b6c205fb613e1f16986e9f8cd2054383c43e179e0a6457501b` |
| All 39 `schemas/*.schema.json` files with `.v1.` or `.v2.` in name | manifest digest `1702a7ac98b12c24f17869faa94a05b05b1a8e9e2004c9847b267c9f19a9bc5c` |

The aggregate digest is SHA-256 of UTF-8 `json.dumps(path_to_sha256,
sort_keys=True, separators=(',', ':'))`, with repository-relative POSIX paths.
All 39 current files additionally match starting HEAD Git bytes exactly.
Frozen tag commit/tree are verified by `git rev-parse`; release assets were not
downloaded, regenerated, or mutated. No claim of fresh remote asset recertification.

PRODUCT SEMANTICS CHANGE = NONE.
ROUTE ACTIVATION CHANGE = NONE.
SCHEMA CHANGE = NONE.

## Validation and remaining notes

Environment: CPython 3.13.7, Windows x64. Python checks use `-B`;
pytest uses `-p no:cacheprovider` and disposable basetemp under `C:/twmarket_temp`.

Initial focused command:

```text
python -B -m pytest -p no:cacheprovider tests/unit/test_current_v3_validation_authority.py tests/unit/test_phase_h_v3_contract_freeze.py tests/unit/test_l7_a5_r5_temporal_provenance.py tests/unit/test_l7_a5_r5_1_finalization_publication.py --basetemp=C:/twmarket_temp/s1-focused-20261029 -q
```

Result: 124 passed. Final focused rerun after invalid-UTF-8 and simulated-repin
coverage uses `--basetemp=C:/twmarket_temp/s1-focused-final-20261030` (result below).

Required validators, all PASS:

```text
python -B scripts/validate_phase_h_v3_contracts.py
python -B scripts/validate_portable_catalog_sync.py
python -B scripts/validate_runtime_skill_guide_sync.py
python -B scripts/validate_l5_extension_publication_conformance.py
git diff --check
```

`default-ci` is run through its unchanged profile runner with isolated
`TW_MARKET_HOME`, `TW_MARKET_STATE_ROOT`, and operational-event output under
`C:/twmarket_temp/s1-default-ci-20261029`; inherited Security Master/Watchlist/
control-root overrides are removed in that child environment.
`PYTHONDONTWRITEBYTECODE=1`; `PYTEST_ADDOPTS` disables cacheprovider and places
basetemp outside the repository. Result is retained at that root's `result.json`.
No user installation initialization or live acquisition is performed.

Final focused result: **126 passed in 23.76s**, including invalid UTF-8 rejection
and semantic rejection after a simulated fingerprint update.

Command: `python -B scripts/run_test_profile.py default-ci --json` (stdout directed
to the isolated result file described above).
Default-ci result: **FAIL**, pytest/runner return code 1; 1302 collected,
1297 selected, **1281 passed, 12 failed, 4 skipped, 5 deselected**, 22 warnings;
pytest duration 138.65s. The outer PowerShell display command's exit code is not
used as the runner result. The profile and its selection were not changed.

The 12 failed nodes were then replayed explicitly with `python -B -m pytest
-p no:cacheprovider --basetemp=C:/twmarket_temp/s1-existing-failures-20261030
-q --tb=short <the exact 12 FAILED node IDs from result.json>` in the same isolated
installation environment: **12 failed in 7.17s**. Output is retained alongside
`result.json` as `failures-short.txt`.

| Failure family | Nodes | Observed failure |
|---|---:|---|
| I3 A0 preflight/P0/P1/P3/P3-R1/A1 historical containment | 6 | `phase_i_i3_a4_compat.strip_a6_transport_instrumentation`: `h3_transport_call_shape_changed` |
| I3 A3 attempt-2 / R3 historical production containment | 2 | `non_i3_production_authority_drift:docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json` |
| Phase J GHI readiness historical preflight | 4 | Requires unchecked `Phase J` in current ROADMAP |

The failed tests, their historical validators, compatibility helper, production
adapter, Catalog and ROADMAP are unchanged from the starting baseline. The
observed failure paths do not execute the modified current-V3 validator. These
are outside the S1 mutation surface; no marker/skip/profile/assertion was changed
to suppress them. A full independent baseline-checkout default-ci run was not
performed, so this record does not claim paired full-suite baseline recertification.

S3 test-governance authority/count and historical replay context reconciliation
remain outside this candidate (OUT_OF_SCOPE_DEPENDENCY for a green broad gate,
not for the completed S1 focused acceptance).
The new focused test is run explicitly; this S1 does not change profile enrollment.
Historical J-B04-A3's full acceptance is not recertified against today's tree.
Only its frozen source fingerprint and protected gate bytes are verified here.
No Phase L acceptance is reopened and no historical live authority is consumed.

## Review and rollback

Fresh reviewer must verify current/frozen schema equality, R5 acceptance chain,
positive and negative temporal behavior, V1/V2 and route guards, unchanged historical
hashes/records, exact three-file containment, and recorded validation outcomes.
Review is pending; this is not independent-review acceptance.

Rollback before commit: restore only the validator from the starting HEAD and
withdraw the two new S1 files after explicit authorization. No rollback action
was performed. After a future authorized commit, revert only that bounded S1
commit; never revert schema/runtime/release authority.

Commit status: UNCOMMITTED. Staged changes: zero. Push: not performed.
