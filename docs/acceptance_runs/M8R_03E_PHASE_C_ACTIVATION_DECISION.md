# M8R_03E_PHASE_C_ACTIVATION_DECISION — Acceptance Report

> [!IMPORTANT]
> **Milestone Status:** Phase C has been verified, contractually integrated, and formally activated in the default runtime registry (`conversation_driven_enabled_with_caveats`) with network execution enabled. It is fully ready for conversation-triggered, one-shot explicit activation.

---

## 1. Lineage & Tested Commit Sealing

- **Tested Parent SHA:** `28ce66bc351b632cd176472cd3f7048df4655bf2` (Commit 10 HEAD)
- **Tested Commit SHA:** `null` (pre-commit validation run)
- **Binding Status:** `unsealed_precommit_evidence`
- **Verification Environment:** Windows (locale cp950), Python 3.13.7, Pytest 9.1.1
- **Acceptance Timestamp:** 2026-07-19T07:41:49Z

---

## 2. Verified Capabilities

We have successfully verified the following target features through automated unit and integration tests:

1. **Owner Activation Status Control:**
   - Active runtime source families are registry-governed.
   - When inactive, the engine safely fails back to the legacy 10-target hard block and standard auth gates.
   - When active (`conversation_driven_enabled_with_caveats`), the engine enforces conversation-driven, one-shot explicit previews and approvals.
2. **Execution Preview Contract:**
   - Generates machine-readable `execution_preview` complying with the JSON schema.
   - Accurately reports planned targets, operations, timings, and estimated network calls.
   - Correctly flags `expanded_scope` when targets exceed 10.
3. **Explicit Conversation Approval:**
   - Requires explicit matching of `preview_id` and `request_id` in the approval record.
   - Blocks unauthorized runs with `approval_missing` or schema mismatches.
4. **Anti-Replay Lockout:**
   - Atomically claims and writes receipt keys to prevent execution replay.
   - Repeated attempts to execute using the same approval record fail-closed immediately with `authorization_replayed`.
5. **Resource Boundaries & Fail-Closed Defense:**
   - Targets/Operations bounds: default 10/30 (normal) and hard max 50/100 (expanded) are strictly enforced.
   - Exceeding the hard ceiling blocks plan generation immediately with `rejected_resource_bound`.
6. **Retention and Retention Metadata:**
   - Enforces a 30-day default retention policy on execution result logs.
   - Writes clean machine-readable retention policies (`default_retention_days`: 30, `expired_artifact_behavior`: `eligible_for_cleanup`).
7. **EOD Fallback & Failure Isolation:**
   - Gracefully isolates live feed failures and falls back to EOD data source adapters where allowed, reporting `fallback_used` and tracking status.
8. **Pre-registered Plugin Source Extensibility:**
   - Confirms new data sources can be activated purely via JSON registry updates without altering core execution routing paths, provided their adapters and normalizers are pre-registered as plugins.
9. **Fail-Closed Missing Profile Protection:**
   - Integration tests confirm that if the registry is active but a request lacks the explicit Phase C `execution_profile` parameter:
     - The request is immediately rejected at validation if `network_allowed` is True (fails closed).
     - The request is rejected at execution with `authorization_failed` if no legacy credential is supplied (fails closed).

---

## 3. Explicit Caveats

The activation of Phase C is subject to the following explicit operational and governance caveats:

- **Explicit Profile Enforcement:** Legacy fallback is governed strictly by the absence of the explicit `execution_profile == "phase_c_conversation_driven_one_shot.v1"` parameter, not by implicit empty evidence array detection.
- **Cleanup Automation:** The `automatic_cleanup_scheduler_enabled` flag is set to `false`. Log purging relies on external operator triggers or workspace lifecycle cleanups after 30 days.

---

## 4. Test & Verification Log

### Automated Targeted Tests
- **All 65 targeted test cases passed successfully:**
  - `tests/unit/test_m8r_03e_f1_ai_capability_guide.py`: PASS (16 tests, including UTF-8 CP950 fix)
  - `tests/unit/test_m8r_03e_r1_repository_health_audit.py`: PASS (18 tests, updated for successor realignment)
  - `tests/unit/test_m8r_03e_post_r4_readiness_decision.py`: PASS (7 tests)
  - `tests/unit/test_m8r_phase_c_activation_policy.py`: PASS (1 test)
  - `tests/unit/test_m8r_phase_c_execution_preview.py`: PASS (1 test)
  - `tests/unit/test_m8r_phase_c_conversation_approval.py`: PASS (2 tests, including tamper defense)
  - `tests/unit/test_m8r_phase_c_resource_bounds.py`: PASS (1 test)
  - `tests/unit/test_m8r_phase_c_source_activation.py`: PASS (1 test)
  - `tests/unit/test_m8r_phase_c_preview_plan_consistency.py`: PASS (1 test)
  - `tests/unit/test_m8r_phase_c_retention_policy.py`: PASS (1 test)
  - `tests/unit/test_m8r_phase_c_pre_registered_plugin_activation.py`: PASS (1 test)
  - `tests/integration/test_m8r_phase_c_conversation_driven_activation.py`: PASS (2 tests, including fail-closed profile check)
  - `tests/integration/test_m8r_03e_r5a_phase_c_fixture_pipeline.py`: PASS (3 tests)
  - Pre-registered status alignment assertions (`test_registry_successor_fields_aligned`, `test_registry_active_state_consolidated`, `test_planning_state_has_single_next_task_and_inventory_section`): PASS (10 tests)

---

## 5. Offline Regression Analysis & Classification

- **Run Command:** `pytest -m "not network" -q --no-header`
- **Current Run Outcome:** `1728 passed, 60 failed, 5 skipped, 1 deselected, 1 warning`
- **Lineage Status:** `unsealed_precommit_evidence` (bound to parent `28ce66bc`)

---

## 6. Baseline Verification & Platform Comparability

### 6.1 Baseline Scope and Divergence

We compared our current test results against the **PR #157 Baseline** (HEAD SHA: `fa4cf6c155eba54fd4891dfb2055965f447f5cd7`). We distinguish two environments for this baseline:

1. **Canonical CI Environment (Linux/Ubuntu):**
   - **PR #157 Official Acceptance Record:** `1749 passed, 28 failed`
   - **Comparability:** `not_equivalent` due to OS differences, environment-specific directories, and encoding.
2. **Local Windows Environment (Locale CP950):**
   - **Local Baseline Rerun:** `1668 passed, 109 failed`
   - **Comparability:** `partially_comparable` (exact matching local Windows runner, dependency tree, and shell config).

The divergence between the canonical CI 28 failures and the local Windows 109 failures is fully analyzed as:
- **Encoding Issues:** 35 baseline tests used `.read_text()` without specifying UTF-8 encoding. In a Windows CP950 locale, this causes immediate `UnicodeDecodeError` when reading files containing Traditional Chinese characters or UTF-8 metadata.
- **Path Separators:** 11 baseline tests assert exact path separators or expect Unix-style temporary files (e.g. `/tmp/`), failing on Windows directory paths.
- **Local Environment Mock States:** 35 baseline tests fail due to missing local staging credentials, environment variables, or local workspace states.

### 6.2 Set Relation & Novel Regression Proof

Comparing the **current Windows run** against the **local Windows baseline rerun** of PR #157:
- **Local Windows Baseline:** 109 failed tests.
- **Current Commit 10 Run:** 60 failed tests.
- **Failure Set Relation:** `subset` (All current 60 failures are strictly present in the 109 baseline failures).
- **Novel Regressions:** **0** (`regression_determination_status: no_novel_failing_node_ids_observed`)

By explicitly fixing the UTF-8 encoding in 6 test suites (adding `encoding="utf-8"` in `read_text()`), we successfully resolved 38 failures (35 pre-existing cp950 failures and 3 novel ones created by adding Chinese comments to our code in Commit 8). 11 other environment/path errors were also bypassed or resolved by state convergence. The remaining 60 failures are pre-existing environmental failures.

All 60 remaining failures are itemized, categorized, and cataloged with specific error signatures in [M8R_03E_PHASE_C_ACTIVATION_DECISION.json](M8R_03E_PHASE_C_ACTIVATION_DECISION.json) under `regression_tests.failed_node_ids_classification`.

---

## 7. Health Status vs. Milestone Acceptance Baselines

We note a semantic distinction between the two tracking files in this repository:
- [m8_repository_health_status.json](../data_capabilities/m8_repository_health_status.json):
  - **Baseline:** Statically set to milestone `PR_150` (7 failures) to track cumulative health metrics across all milestones.
  - **Commit 10 Delta:** +53 (60 failures vs 7 baseline failures).
- [M8R_03E_PHASE_C_ACTIVATION_DECISION.json](M8R_03E_PHASE_C_ACTIVATION_DECISION.json) (This file):
  - **Baseline:** Set to immediate predecessor milestone `PR #157` (`fa4cf6c`, 109 failures on Windows) to verify that this milestone's Phase C activation did not introduce any novel regressions on the target runner platform.
