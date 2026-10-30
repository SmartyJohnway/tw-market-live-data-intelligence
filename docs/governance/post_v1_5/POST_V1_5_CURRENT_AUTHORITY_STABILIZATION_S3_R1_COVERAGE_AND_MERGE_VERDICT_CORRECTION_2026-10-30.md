# S3-R1 Coverage Floor and Operational Merge Verdict Correction

Date: 2026-10-30 (Asia/Taipei)
Disposition: READY_FOR_INDEPENDENT_RE_REVIEW
Owner commit gate: NOT_AUTHORIZED; independent re-review required.

## 1. Baseline and containment

Verified before edits: branch main; HEAD and origin/main both
`13dc831f037e52da2ffe5a4f477f5c874817afa0`; staged = 0.
Exactly the original nine-file S3 candidate was present; no unrelated changes.
The explicit S3-R1 Owner prompt supersedes older root next-work prose only for
this bounded correction. S1 remains closed; S2/S4/S5, P1 and Phase M excluded.
Rollback target is the original uncommitted S3 candidate, not a reset of main.
Do not use a whole-tree reset: it would discard the retained initial candidate.

## 2. Independent review and two blockers

Fresh S3 review: CHANGES_REQUIRED; two blocking findings;
OWNER_COMMIT_GATE = NOT_READY. This review is preserved, not disputed.
The initial S3 record is retained and only receives an appended disposition.

1. Six mandatory paths alone allowed default 121 -> 6 and full 168 -> 6,
   and did not protect effective selection from marker drift.
2. Raw default-ci was permanently red on 12 defensibly classified diagnostics;
   manual failed-node comparison was not an operational merge verdict.

## 3. Coverage-floor design and ownership

`config/current_test_coverage_floor.v1.json` owns explicit minimum path and
selected-node identity sets for default-ci and full-current. Original S3 selected
sets were 1,352 / 1,725 nodes. The 15 new R1 regression nodes are also governed,
producing final floors of 1,367 / 1,740 nodes and 121 / 168 explicit paths.
These are identity-set floors, not permanent exact suite counts. Supersets pass.

The manifest records baseline commit, Owner governance ownership, S3-R1 record,
profile roles, enrollment, diagnostic provenance and update policy. The current
validator pins the reviewed manifest SHA-256. Regeneration alone cannot bless a
reduction. A reduction requires explicit Owner governance review and deliberate
update of both floor and validator anchor; do not derive this approval from a
new test run. Legitimate additions do not edit TG5 evidence or counts.

## 4. Effective selection and validator

The current validator checks every floor path is still explicitly enrolled,
then performs real pytest collection under the exact current marker expression.
It compares selected node IDs against the floor for each profile, including
parameterized cases. Keeping a path while marking its governed node historical
(or otherwise excluded) fails. Collection errors fail closed. The complete
floor identities are inspectable in JSON; evidence reports missing sets, not
only counts. The merge run independently checks actual executed selection.

Mandatory S1 and original S3 protections remain. Existing workflow metadata,
manual triggers, historical hashes, rollback enrollment and release delegation
remain independently validated. Reverting merge to raw default-ci is rejected.
Unknown diagnostic IDs/categories and uncollectible known nodes are rejected.

## 5. Operational merge-result model

`scripts/run_current_merge_gate.py` is the bounded operational merge command.
It validates governance, executes the entire default-ci pytest selection,
observes collection and setup/call/teardown reports through a read-only pytest
plugin, and emits `current_merge_verdict.v1` JSON with a process exit verdict.
The plugin never changes marks, assertions, reports, pytest exit status or
failure output. The execution prints full normal pytest diagnostics.

Only failed call reports for the exact governed 12 IDs can be classified as
KNOWN_TRANSITION_DIAGNOSTIC or KNOWN_HISTORICAL_DIAGNOSTIC. Other failures,
setup/teardown failures, incomplete outcomes, collection/runner errors and
coverage disappearance block. Unexpected skip/xfail blocks, including on known
diagnostics. The only authorized skips are the four exact optional historical
artifact witnesses and expected reason strings already owned by the unchanged
release contract. No new skip or xfail was added.

A known node that passes is not blocking and appears in
`known_diagnostic_now_passing`; retirement still requires governance review.
There is no CLI arbitrary-ignore list and no imported arbitrary result waiver.
The generic profile runner and deterministic release runner are unchanged.

## 6. Final role model and commands

```text
merge = current-merge-gate
  python -B scripts/run_current_merge_gate.py --output C:/twmarket_temp/s3-r1-merge-final.json
raw default diagnostic = default-ci
  python -B scripts/run_test_profile.py default-ci --json
CI workflow = manual workflow_dispatch, default-ci / full-non-network
broad-current = full-current
  python -B scripts/run_test_profile.py full-current --json
release-blocking = release-blocking-ci
  python -B scripts/run_test_profile.py release-blocking-ci --json --output-root C:/twmarket_temp/release-check
historical diagnostic = historical-milestone-replay
  python -B scripts/run_test_profile.py historical-milestone-replay --json
```

Workflow files/triggers were not changed. This is not automatic PR enforcement.

## 7. Known diagnostic authority and independent inspection

All 12 IDs are independently present in the protected release contract's
`historical_diagnostics`; that contract hash is recorded in the floor. Its
historical assertion classification and current-equivalent coverage are reused,
without modifying the contract or changing release selection semantics.

The exact test bodies were inspected: the first six invoke frozen I3 entry /
containment validators; the next two preserve frozen candidate/replay lineage
and production-containment assertions; the last four invoke Phase J readiness
assumptions superseded by later accepted lifecycle state. The S3-R1 6/6 taxonomy
is bounded to those existing facts, not a license to waive a new runtime defect.

- `tests/unit/test_phase_i_i3_a0_preflight.py::test_current_hold_record_and_runtime_containment` — `KNOWN_TRANSITION_DIAGNOSTIC`
- `tests/unit/test_phase_i_i3_a0_preflight.py::test_p0_validator_cannot_claim_pass_or_rearm` — `KNOWN_TRANSITION_DIAGNOSTIC`
- `tests/unit/test_phase_i_i3_a0_p1_adjudication.py::test_p1_governance_validator_passes_under_network_denial` — `KNOWN_TRANSITION_DIAGNOSTIC`
- `tests/unit/test_phase_i_i3_a0_p3.py::test_p3_validator_production_containment_and_readiness` — `KNOWN_TRANSITION_DIAGNOSTIC`
- `tests/unit/test_phase_i_i3_a0_p3_r1.py::test_r1_validator` — `KNOWN_TRANSITION_DIAGNOSTIC`
- `tests/unit/test_phase_i_i3_a1.py::test_a1_validator_and_immutable_a0_anchors` — `KNOWN_TRANSITION_DIAGNOSTIC`
- `tests/unit/test_phase_i_i3_a3_attempt_2_bounded_live.py::test_exact_mapping_and_frozen_candidate_and_production_containment` — `KNOWN_HISTORICAL_DIAGNOSTIC`
- `tests/unit/test_phase_i_i3_a3_r3_http520_lifecycle.py::test_committed_attempt4_pass_lineage_and_containment` — `KNOWN_HISTORICAL_DIAGNOSTIC`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_current_record` — `KNOWN_HISTORICAL_DIAGNOSTIC`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_unchecked_g_h_do_not_themselves_block_pass` — `KNOWN_HISTORICAL_DIAGNOSTIC`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-08]` — `KNOWN_HISTORICAL_DIAGNOSTIC`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-10]` — `KNOWN_HISTORICAL_DIAGNOSTIC`

## 8. Focused regression acceptance

```text
python -B -m pytest tests/unit/test_current_test_governance.py tests/unit/test_test_governance_tg5.py tests/unit/test_current_v3_validation_authority.py tests/unit/test_run_test_profile.py -q
```

Final focused run: 93 passed, including original S3, S1 and runner protections.
Mutation tests reject both six-path attacks, a non-mandatory path removal, and
required-node selection loss. A real temporary test's historical marker causes
collection-floor failure; removing that marker and adding a new test preserves
the floor and passes. The existing legitimate profile-superset test also passes.

Merge-result tests cover only-known failures, an extra failure, disappearance,
known-now-passing, unexpected skip, xfail, setup failure and collection error.

## 9. Raw profile execution

| Profile | Selected | Passed | Failed | Skipped | Deselected |
|---|---:|---:|---:|---:|---:|
| default-ci | 1367 | 1351 | 12 | 4 | 5 |
| full-current | 1740 | 1724 | 12 | 4 | 5 |
| historical-milestone-replay | 94 | 90 | 4 | 0 | 0 |

Both raw current failure sets were machine-compared to the exact 12 governed IDs and matched. Raw exits remain 1. Historical diagnostic exit remains 1.

## 10. Operational merge execution

```json
{
  "schema_version": "current_merge_verdict.v1",
  "MERGE_VERDICT": "PASS",
  "blocking_failures": 0,
  "known_diagnostic_failures": 12,
  "known_diagnostic_now_passing": [],
  "coverage_status": "PASS",
  "raw_pytest_exitstatus": 1
}
```

Actual execution selected all 1,367 governed default nodes; gate process exit = 0. The four authorized optional historical artifact skips remain visible. No governed node was newly skipped or xfailed.

## 11. Controlled unexpected-failure proof

A temporary additional test outside the repository is appended only to an
in-memory execution profile. It asserts false with an explicit S3-R1 injection
message. The actual default selection still executes in full; canonical test
assertions and enrollment files are not edited. Classification uses the same
canonical gate classifier, not a second waiver implementation.

```json
{
  "schema_version": "current_merge_verdict.v1",
  "MERGE_VERDICT": "FAIL",
  "blocking_failures": 1,
  "blocking_details": [
    {
      "nodeid": "::test_s3_r1_unexpected_current_failure",
      "classification": "BLOCKING_CURRENT_FAILURE",
      "reason": "unexpected failure"
    }
  ],
  "known_diagnostic_failures": 12,
  "coverage_status": "PASS"
}
```

Actual injected execution: 1,368 selected, 1,351 passed, 13 failed, 4 skipped, 5 deselected. The negative-proof harness exited 0 because the required FAIL / 1 blocker / 12 known diagnostics assertions passed. The injected test alone is the blocking failure. Temporary test content was `def test_s3_r1_unexpected_current_failure(): assert False, "controlled S3-R1 negative acceptance"`.

## 12. Validators

All six requested Python validators passed on the final floor and runner:

```text
python -B scripts/validate_current_test_governance.py
python -B scripts/validate_test_governance_tg5.py
python -B scripts/validate_phase_h_v3_contracts.py
python -B scripts/validate_portable_catalog_sync.py
python -B scripts/validate_runtime_skill_guide_sync.py
python -B scripts/validate_l5_extension_publication_conformance.py
```

`python -B -m compileall -q scripts server tests` also exited 0.
Final `git diff --check` is recorded in the closing evidence below.

## 13. Historical authority preservation

Historical current-tree diagnostic != exact historical-context replay.
The historical profile is HISTORICAL_REPLAY_DIAGNOSTIC_ONLY. Its current-tree
94 selected / 90 passed / 4 failed does not invalidate frozen historical
acceptance. Reproduction of that acceptance requires its historical source
context. None of these four diagnostic failures enters current merge authority.
Historical TG records, acceptance ledgers, fixed historical counts and protected
SHA facts remain unchanged. The S3 historical/current separation is retained.

## 14. Release authority preservation

Release-blocking contract, deterministic runner, schemas, Catalog, Routing,
executor registry, production services, MCP, Workbench, Security Master,
Watchlists and P1 remain unchanged. Local v1.5.0 still resolves to frozen source
`acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`. No release asset, Registry metadata,
Docker publication, network acquisition or consumed live authority was touched.
No seventh MCP tool, scheduler or polling was introduced.

## 15. Changed-file containment

Original S3 nine-file candidate retained:

- CONTRIBUTING.md
- config/test_execution_profiles.json
- config/test_governance_authority.json
- scripts/test_governance_authority.py
- scripts/validate_test_governance_tg5.py
- scripts/validate_current_test_governance.py
- tests/unit/test_test_governance_tg5.py
- tests/unit/test_current_test_governance.py
- docs/governance/post_v1_5/POST_V1_5_CURRENT_AUTHORITY_STABILIZATION_S3_TEST_GOVERNANCE_AUTHORITY_RECONCILIATION_2026-10-30.md

Three bounded R1 additions:

- config/current_test_coverage_floor.v1.json
- scripts/run_current_merge_gate.py
- this S3-R1 governance record

No production file, existing failing test, test marker or assertion was changed.
No test was deleted, excluded because it failed, skipped or xfailed by R1.
No stage/commit/push was performed.

## 16. Intermediate execution disclosure

An initial raw default/full execution overlapped the deliberate extension of
the floor to cover the 15 R1 nodes. Five governance assertions loaded the old
pinned digest while reading the new floor and failed. The gate correctly
classified these five as blocking current failures, rather than hiding them.
Those intermediate 17-failure runs and initial gate outputs are retained under
`C:/twmarket_temp/s3-r1-*`; they are not final acceptance evidence. Final runs
use the fixed candidate and separate `final` evidence filenames. No further
implementation/floor changes were made during final acceptance.

## 17. Remaining debt

S3 blockers: both implementation corrections and deterministic acceptance complete; fresh independent re-review remains required. No commit readiness or Owner approval is implied.
Post-S3 debt: the review's NON_BLOCKING historical SHA trust-root note remains
unchanged; current manifests still reference some historical SHA authorities.
Retiring known diagnostics requires later explicit governance review. Raw
profiles remain transparently red on authorized diagnostics; manual workflows
are not automated merge enforcement. None authorizes S2/S4/S5 or Phase M.

## 18. Git state and acceptance evidence

HEAD = origin/main = `13dc831f037e52da2ffe5a4f477f5c874817afa0`; branch main; staged = 0; intended candidate = 12 files. COMMIT/PUSH = NOT AUTHORIZED and not performed.

Local evidence is retained outside the checkout; the machine summaries above are portable governance evidence.

| Local evidence | SHA-256 |
|---|---|
| `C:/twmarket_temp/s3-r1-focused-final.log` | `8245ff8b61f959d04ba7e3d899864a5ca0219d6ffe5b655502f5e3d5c8c73e1e` |
| `C:/twmarket_temp/s3-r1-final-default-ci.json` | `29238b5f8fdd8a877d323f68b001ba2fd7899da935e09f28e5d1318bc79b35e7` |
| `C:/twmarket_temp/s3-r1-final-full-current.json` | `6c5ca9c64d0b0ba6a8f376b075ac19fa54b3b4f0c813ce0988379ecbd65f48b5` |
| `C:/twmarket_temp/s3-r1-historical-milestone-replay.json` | `6bc6f79fe47b41c17fe6fd12ef26237e37a71e6c3846cb1073ba5b9ddf059a52` |
| `C:/twmarket_temp/s3-r1-merge-final.json` | `ffbd7074f08c7e58cbe068809f52e3cad5a4c9819ac7c1d304d30a7e7d9295d8` |
| `C:/twmarket_temp/s3-r1-merge-final.log` | `b49608b8b83fec5f558ca33f7815b9516df323542c4dba8a232969f22ba76a3d` |
| `C:/twmarket_temp/s3-r1-negative-merge-final.json` | `e7e23816f452eb8e51acad911f1fcd771cee126964b75d7233b8868d89fb95b1` |
| `C:/twmarket_temp/s3-r1-negative-merge-final.log` | `8c849976b665c5968f631b0a5691d45fc92a21f7396761f5852255d0db8a142d` |
| `C:/twmarket_temp/s3-r1-validators-final.json` | `1c3c822cc89ae1b332a9f9a8f885513b0795a68c242253138b23416afa8f439d` |

Final coverage floor SHA-256: `1a29cac73109a335263751656897a039c88f5ce25c6eb618ed81de552dd6d50b`.
Protected release contract SHA-256: `b80476b43307d670a5a3000e84e84c3b617085db6c68373fc9b522c92708d2e7`; byte-for-byte equal to HEAD.

Final `git diff --check`: PASS (exit 0). All changed/untracked files are in the twelve-file list above; protected surfaces have no changes.


## 19. Fresh independent re-review handoff

- Reproduce 121 -> 6 and 168 -> 6, plus one non-mandatory path removal.
- Keep a file enrolled but deselect a governed parameterized/current node;
  require validator failure. Confirm a legitimate superset still passes.
- Inspect floor provenance, exact identities, digest pin and explicit reduction
  review policy; ensure regeneration cannot silently approve coverage loss.
- Verify the exact 12 diagnostic IDs against unchanged release authority;
  confirm all actually execute with full failure output.
- Reproduce known-only PASS / new-failure FAIL / disappearance FAIL /
  known-now-passing disclosure / unexpected skip or xfail FAIL.
- Inspect the temporary extra-failure execution evidence, not only synthetic
  classifier unit tests. Confirm raw profile exit status remains red.
- Confirm historical diagnostics are not exact historical-context acceptance,
  and protected release/runtime/workflow surfaces remain unchanged.
- Reconfirm HEAD/origin/main, staged=0 and the twelve-file candidate boundary.
- Re-review only the two S3 blockers; carry the SHA trust-root note as debt.
