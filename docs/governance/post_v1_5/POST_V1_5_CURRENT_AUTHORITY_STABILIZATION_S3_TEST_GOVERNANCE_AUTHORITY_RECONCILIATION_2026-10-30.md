# S3 — Current Test Governance Authority Reconciliation

Date: 2026-10-30 (Asia/Taipei). Status: READY_WITH_NOTES candidate for independent review.
Owner explicitly authorized S3 implementation/testing/governance only. Commit and push NOT AUTHORIZED.

## Baseline, authority and scope

Starting branch `main`; HEAD and local `origin/main` both
`13dc831f037e52da2ffe5a4f477f5c874817afa0`; working tree clean, staged 0,
untracked 0, ahead/behind 0/0. S1 is COMPLETE / PUSHED at that same commit;
S1 semantic files are unchanged. Local tracking-ref comparison was performed;
no fetch/push or hosted workflow execution was performed.

Stable `v1.5.0` still resolves to `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`,
whose tree is `d44f66dc154c21326ac8b105d2f15fd793f6071b`.
Phase L CLOSED; Phase M NOT_AUTHORIZED. S2/S4/S5, P1, P2–P5 excluded.
Rollback for this uncommitted candidate: restore only the listed tracked S3
files from starting HEAD and remove only the three newly authored candidate files
after explicit Owner approval. No rollback/deletion was executed.

## Root cause and model

The former CURRENT_ACTIVE_MACHINE_AUTHORITY contained TG5 cutover identities,
93/778 default and 156/1245 rollback observations plus historical lifecycle
counts. TG5 static validation required the live default profile to equal the
frozen candidate body. Legitimate post-cutover additions broke that comparison.

The v2 current authority now owns role mapping, mandatory current enrollment,
selection/exclusion policy, workflow truth, and hash-bound references to preserved
historical evidence. It does not own fixed current path/node counts. The current
validator checks paths, duplicates, roles, exact exclusions, broad superset,
mandatory S1/S3/TG5/runner/scanner protection, release-only separation, historical
replay coverage, exact rollback diagnostic selection, and actual workflows.
The old `current` and `release` helper names remain compatible aliases for
merge and release-preflight respectively; `release_blocking` is explicit.

TG5 static validation now reads frozen rollback/TG2/TG4/TG5 snapshots. Historical
count/status/identity assertions are retained against historical owners rather
than current enrollment. Current diagnostic/profile policy assertions moved to
the current validator. The optional TG5 runtime verifier remains a verifier of
historical run artifacts, not current-run acceptance; it was not executed here.

## Role map

```text
merge/default = default-ci
CI = default-ci (manual Default CI workflow)
broad-current = full-current
release-blocking = release-blocking-ci -> scripts/run_deterministic_ci.py -> config/release_blocking_ci.v1.json
release-preflight = release-preflight-current (separate, not release readiness)
historical replay = historical-milestone-replay
rollback diagnostic = pre-tg5-default-ci
mixed historical = mixed-historical-diagnostic
```

`full-current` is explicit lifecycle regression with the default marker policy.
`full-non-network` discovers `tests` excluding only network/historical/performance
and invokes additional acceptance runners. It may encounter browser/live/release
markers or platform-specific collection failures; it is not interchangeable with
full-current or the release authority. It was inspected, not executed in S3.

Specialized inventory (unchanged): fast/changed-fast; component-security,
component-market-source, component-watchlist-evidence, component-agent-skill,
component-governance, component-frontend-publication, component-architecture;
phase-j-regression-authority (J4/J3); operator-preflight; browser-e2e;
bounded-live (separate explicit authorization); performance; milestone-acceptance;
historical-acceptance; release-preflight-current. No specialized runner was
silently promoted into default.

Both `.github/workflows/ci.yml` and `non-network-ci.yml` are workflow_dispatch
only, invoking default-ci and full-non-network respectively. No automatic PR
blocking is asserted. Workflow triggers and branch protection were not changed.

## Profile reconciliation

### default-ci

Before: 118 explicit paths. After: 121.

Added:
- `tests/unit/test_current_v3_validation_authority.py`
- `tests/unit/test_current_test_governance.py`
- `tests/unit/test_test_governance_tg5.py`

Removed: [].

### full-current

Before: 164 explicit paths. After: 168.

Added:
- `tests/unit/test_current_v3_validation_authority.py`
- `tests/unit/test_current_test_governance.py`
- `tests/unit/test_test_governance_tg5.py`
- `tests/unit/test_phase_i_final_exit.py`

Removed: [].

S1, S3 and TG5 tests were missing from current lists; they now protect both current
roles. The broad-only addition `test_phase_i_final_exit.py` already belonged to
default, so adding it closes a superset gap. No paths, assertions, markers or
failures were removed. All other profile objects are unchanged, including release.

## Known 12-failure disposition

All 12 are retained in BOTH default-ci and full-current. No failure was hidden.
No skip, xfail, assertion weakening, production fix, ignore expansion, or test
deletion was introduced. Existing release-blocking authority already labels
these exact nodes HISTORICAL_GOVERNANCE_ASSERTION and supplies current equivalents;
S3 leaves that protected contract and its selection behavior unchanged.

- Six transport-shape failures: TRANSITION_GOVERNANCE_TEST / historical replay
  purpose. `scripts/phase_i_i3_a4_compat.py` calls the check a historical
  compatibility projection, enforcing old H3 transport shape against later source
  hardening. Current equivalents are listed in the existing release contract.
- Two Catalog containment failures: HISTORICAL_REPLAY_TEST; compatibility validators
  compare frozen candidate production snapshots against later accepted Catalog
  authority. Assertions remain untouched.
- Four Phase J preflight failures: HISTORICAL_REPLAY_TEST; validator requires Phase J
  unchecked/not-started, while current ROADMAP and accepted Phase J closure say
  complete. `docs/governance/phase_j/PHASE_J_CLOSURE_AUTHORITY_RECONCILIATION_2026-10-12.md`
  and the release contract document the successor authority.

These nodes are MISCLASSIFIED as ordinary current blockers by residual mixed-file
enrollment, but their containing files also protect valid current behavior.
Removing entire paths would lose coverage. Node-specific selection support would
require changing `scripts/run_test_profile.py`, which is outside the authorized
mutation surface. That optional separation is an OUT_OF_SCOPE_DEPENDENCY, not
permission to suppress nodes. The candidate resolves authority/count coupling
while honestly retaining this limitation. Default remains a bounded normal
validation profile with visible debt; its red result is NOT a passing merge gate
and does not prove complete current coverage or release readiness.

Exact retained failure IDs:

- `tests/unit/test_phase_i_i3_a0_preflight.py::test_current_hold_record_and_runtime_containment`
- `tests/unit/test_phase_i_i3_a0_preflight.py::test_p0_validator_cannot_claim_pass_or_rearm`
- `tests/unit/test_phase_i_i3_a0_p1_adjudication.py::test_p1_governance_validator_passes_under_network_denial`
- `tests/unit/test_phase_i_i3_a0_p3.py::test_p3_validator_production_containment_and_readiness`
- `tests/unit/test_phase_i_i3_a0_p3_r1.py::test_r1_validator`
- `tests/unit/test_phase_i_i3_a1.py::test_a1_validator_and_immutable_a0_anchors`
- `tests/unit/test_phase_i_i3_a3_attempt_2_bounded_live.py::test_exact_mapping_and_frozen_candidate_and_production_containment`
- `tests/unit/test_phase_i_i3_a3_r3_http520_lifecycle.py::test_committed_attempt4_pass_lineage_and_containment`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_current_record`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_unchecked_g_h_do_not_themselves_block_pass`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-08]`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-10]`

## Historical integrity

Unmodified, byte-identical to starting HEAD:

- `docs/governance/test_governance/TG4_ACCEPTANCE_LEDGER_2026-09-23.json` SHA-256 `d8f5c65a47e3fd581681fa831144e64b5b9b971e855e473d9b30f9fcfb600243`
- `docs/governance/test_governance/TG5_ACCEPTANCE_LEDGER_2026-09-23.json` SHA-256 `7e6a7f99a86b31a4803d9bce57e9c71e5f911a45f46fccf5b0ad951885e8f275`
- `docs/governance/test_governance/TG5_ROLLBACK_CONTRACT_2026-09-23.json` SHA-256 `b4936c62f8ba05a4514b651f4ea91090ef6308acaca3a7f94a1f62e087ba895c`
- `docs/governance/test_governance/TG5_ROLLBACK_DIAGNOSTIC_GAPS.v1.json` SHA-256 `4960537d63fc80918b70c4ead0d4eca3bda8d7ba240cc1fd2ae6aae1edad71f5`
- `docs/governance/test_governance/TG4_KNOWN_HISTORICAL_REPLAY_GAPS.v1.json` SHA-256 `1e9b328bc0c7d2897b982d44bebeda63528c00b2a0b78e71c138f2b8f47824bb`
- `config/test_governance_semantic_profiles.json` SHA-256 `af22ab81efd94c8e872ccd0ea4cee3fe2ad4b1c4166f0429961f27aa0edd2f91`

Historical facts remain: TG5 default 93 paths/778 nodes; rollback 156/1245;
broad 1150; replay 94; release 5; mixed 4. TG4 run 35824957803;
TG5 run 35839936603; TG5 merge db3340da61ea6e1f3391cfc1728d42b5376157c7;
rollback baseline 2ff9707d901f40c1a108dd1317fce2f03cc79735. Historical commits,
ledgers, rollback/gap contracts and TG2 semantic manifest were not rewritten.

## Changed-file containment

- `CONTRIBUTING.md`
- `config/test_execution_profiles.json`
- `config/test_governance_authority.json`
- `scripts/test_governance_authority.py`
- `scripts/validate_test_governance_tg5.py`
- `scripts/validate_current_test_governance.py`
- `tests/unit/test_test_governance_tg5.py`
- `tests/unit/test_current_test_governance.py`
- `docs/governance/post_v1_5/POST_V1_5_CURRENT_AUTHORITY_STABILIZATION_S3_TEST_GOVERNANCE_AUTHORITY_RECONCILIATION_2026-10-30.md`

Production runtime, schemas, Routing, Catalog semantics, executor registry,
source adapters, Local Service, MCP, Workbench, Security Master, Watchlists,
P1, S1 semantics, release assets and Phase M: NO changes. No network acquisition
or live acceptance was authorized/performed. The unchanged normal profiles use
their existing deterministic tests; no new network runner was introduced.

## Validation

Focused command:

```text
python -B -m pytest -q tests/unit/test_current_test_governance.py tests/unit/test_test_governance_tg5.py tests/unit/test_run_test_profile.py tests/unit/test_current_v3_validation_authority.py
```

78 passed. This includes all S1 focused protection. Initial implementation
checks caught and corrected an invalid historical lookup, a broad superset gap,
and CRLF output formatting; these are not claimed as initial PASS results.
A read-only review identified missing actual-workflow checking and rollback
binding; both were added with negative coverage before final validation.

Validators / checks, exit 0:

```text
python -B -m compileall -q scripts server tests
python -B scripts/validate_current_test_governance.py
python -B scripts/validate_test_governance_tg5.py
python -B scripts/validate_phase_h_v3_contracts.py
python -B scripts/validate_portable_catalog_sync.py
python -B scripts/validate_runtime_skill_guide_sync.py
python -B scripts/validate_l5_extension_publication_conformance.py
git diff --check
```

S1 current validator PASS. L5 publication conformance PUB-01..PUB-09 PASS,
no writes/network/runtime discovery. No release-blocking run was claimed;
its contract and runner remain byte-identical to starting HEAD.

## Execution evidence

| Profile / role | Explicit paths | Collected | Selected | Passed | Failed | Skipped | Deselected |
|---|---:|---:|---:|---:|---:|---:|---:|
| default-ci BEFORE | 118 | 1302 | 1297 | 1281 | 12 | 4 | 5 |
| default-ci AFTER | 121 | 1357 | 1352 | 1336 | 12 | 4 | 5 |
| full-current BEFORE | 164 | 1674 | 1669 | 1653 | 12 | 4 | 5 |
| full-current AFTER | 168 | 1730 | 1725 | 1709 | 12 | 4 | 5 |
| historical replay | 15 | 94 | 94 | 90 | 4 | 0 | 0 |

Before/after failed node-ID sets are exactly equal across both current profiles (12 nodes).

Evidence hashes:

- `before-default.json` SHA-256 `73ea2939dc54b99a58f4624446381764e5c180b6f1baa16227b204b69004ce97`
- `final-default-complete.json` SHA-256 `e11d8fae45e4cf3d7f1aa58e0220a872d8382f7438671ccf3942bd5c131b1d69`
- `before-broad.json` SHA-256 `466d7b09ff5acb3fa31cc601a2021c0a9f52b43bca83f0cedcbd7cf62554aa9d`
- `final-broad.json` SHA-256 `0ad6bd6621a8f963cccbdbbcfaa50f887dbfe4c076cca29b71d0f8f0e333cc96`
- `historical.json` SHA-256 `0996528d4840e508a15a04e7a7b86b621a53bb89ae86d1e5a1af87b0617a699b`
- `focused.txt` SHA-256 `01f179d3e516ecc549c867aa94a76e6e83dd381d3ab79ac0da6f66e2333ab939`
- `current-validator.json` SHA-256 `c8f3c0a35067066b38bc0ddf4c15f71f0e6682399bf281e2ef822aa1852f15ca`
- `tg5-validator.json` SHA-256 `1c1ec6826829154235355df2d4fb58778fefb9e277c0cb1ff6bfecd91b715542`
- `phase-h.txt` SHA-256 `3e55f067a1e05ac57419a017ef30d13578cfe5ea498e6880d48a3a2409fffe2b`
- `portable.txt` SHA-256 `cf17bf7c7f51a6e423e9e6f280767ba0857391bf52b5aca50f29a977ab36e000`
- `runtime.txt` SHA-256 `887ca201872c114f0ecd90df1c5d44d82e24efa0f1850ac539d1de1a0b15eba7`
- `l5.txt` SHA-256 `9930a057e74dcf82ecdaab502bd303901289259044263e6e6f34c0915da44bed`

Profiles execute via `python -B scripts/run_test_profile.py <profile> --json`.
The runner reports collected/selected separately. Omitted skip metrics on a
summary with no skips are recorded as observed zero, not invented skipped tests.
Complete JSON run output is retained outside the repository at
`C:/twmarket_temp/s3-20261030/`; hashes below bind these local evidence files.
Only current explicit path counts changed; no count was tuned to seek green.
No selected path disappeared. Existing 4 skips and 5 deselections remain.
Historical replay runs on the current tree (not frozen entry) and returned
90 passed / 4 failed of 94, with old topology/document expectations:

- `tests/unit/test_m7f_rich_fact_browser_final_acceptance.py::test_default_ci_includes_final_acceptance_tests`
- `tests/unit/test_m8_00_final_acceptance.py::test_default_ci_includes_m8_final_acceptance_test`
- `tests/unit/test_m8a_final_acceptance.py::test_readme_static_contracts_and_registry_roles`
- `tests/unit/test_m8_through_m8b_consolidated_acceptance.py::test_docs_and_boundaries`

## Git and independent-review handoff

No commit, push, stage, release publication or deletion. HEAD/origin/main remain
13dc831f037e52da2ffe5a4f477f5c874817afa0, branch main, ahead/behind 0/0.
Expected final candidate: 6 tracked modified files, 3 untracked authored files,
0 staged. External evidence files are outside the checkout.

Fresh reviewer should verify:

1. Compare all historical references and protected release files with starting HEAD.
2. Run both validators and focused suite; mutate role/path/mandatory/exclusion/workflow inputs.
3. Confirm S1 selection in default and full-current; no S1 semantic diff.
4. Compare profile bodies: additions only, no disappearing path or hidden node.
5. Confirm before/after failure ID sets equal the same 12 listed above.
6. Distinguish manual CI, current broad regression, release gate, and replay roles.
7. Confirm no production/release/Phase M surface changed and no stage/commit/push.

## Original authority snapshot (historical evidence only)

The complete pre-S3 manifest is retained here as evidence, not operational policy:

```json
{
  "schema_version": "test_governance_authority.v1",
  "date": "2026-09-23",
  "state": "TG5_PROMOTED_ACTIVE",
  "baseline_main": "2ff9707d901f40c1a108dd1317fce2f03cc79735",
  "current_merge_authority": {
    "profile": "default-ci",
    "expected_file_paths": 93,
    "expected_selected_nodes": 778,
    "automatic_ci_allowed": true,
    "expression": "not network and not browser and not live and not release_preflight and not historical and not performance"
  },
  "lifecycle_regression": {
    "broad_current_profile": "full-current",
    "broad_current_expected_nodes": 1150,
    "historical_profile": "historical-milestone-replay",
    "historical_expected_nodes": 94,
    "release_profile": "release-preflight-current",
    "release_expected_nodes": 5,
    "mixed_historical_profile": "mixed-historical-diagnostic",
    "mixed_historical_expected_nodes": 4
  },
  "rollback": {
    "diagnostic_profile": "pre-tg5-default-ci",
    "authoritative_baseline_commit": "2ff9707d901f40c1a108dd1317fce2f03cc79735",
    "exact_contract": "docs/governance/test_governance/TG5_ROLLBACK_CONTRACT_2026-09-23.json",
    "diagnostic_gap_contract": "docs/governance/test_governance/TG5_ROLLBACK_DIAGNOSTIC_GAPS.v1.json",
    "expected_file_paths": 156,
    "expected_selected_nodes": 1245,
    "mechanism": "revert TG-5 merge or restore repository to authoritative_baseline_commit"
  },
  "source_evidence": {
    "tg4_acceptance": "docs/governance/test_governance/TG4_ACCEPTANCE_LEDGER_2026-09-23.json",
    "tg4_workflow_run_id": 35824957803,
    "legacy_unexplained_nodes": 0,
    "tg5_acceptance": "docs/governance/test_governance/TG5_ACCEPTANCE_LEDGER_2026-09-23.json",
    "tg5_workflow_run_id": 35839936603,
    "tg5_merge_commit": "db3340da61ea6e1f3391cfc1728d42b5376157c7"
  },
  "invariants": {
    "tests_deleted": false,
    "production_runtime_changed": false,
    "source_activation_changed": false,
    "routing_changed": false,
    "frozen_schema_changed": false,
    "phase_i_implementation": false
  },
  "authority_role": "CURRENT_ACTIVE_MACHINE_AUTHORITY",
  "current_authority_commit": "db3340da61ea6e1f3391cfc1728d42b5376157c7",
  "historical_migration_evidence": {
    "tg2_semantic_manifest": {
      "path": "config/test_governance_semantic_profiles.json",
      "classification": "HISTORICAL_MIGRATION_EVIDENCE",
      "current_authority": false,
      "preserve_historical_facts": true
    }
  }
}
```

## Independent Review disposition (appended S3-R1)

Independent Review = CHANGES_REQUIRED; Blocking findings = 2.
Superseded for commit-readiness by S3-R1. Initial candidate evidence above is retained.
