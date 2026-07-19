# M8R_03E_PHASE_C_ACTIVATION_DECISION — Acceptance Report

> [!IMPORTANT]
> **Milestone Status:** Phase C has been verified, contractually integrated, and formally activated in the default runtime registry (`conversation_driven_enabled_with_caveats`) with network execution enabled. It is fully ready for conversation-triggered, one-shot explicit activation.

---

## 1. Lineage & Tested Commit Sealing

- **Tested Parent SHA:** `350898e1bab9b3a6abc16546d994d0ff5f162892` (Commit 9 HEAD)
- **Tested Commit SHA:** `null` (pre-commit validation run)
- **Binding Status:** `unsealed_precommit_evidence`
- **Verification Environment:** Windows (locale cp950), Python 3.13.7, Pytest 9.1.1
- **Acceptance Timestamp:** 2026-07-19T07:33:00Z

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
- **Baseline Run Outcome (PR #157 HEAD `fa4cf6c`):** `1668 passed, 109 failed, 5 skipped, 1 deselected, 1 warning`
- **Failure Set Relation:** `subset` (Current failures are a strict subset of the baseline failures).
- **Novel Regressions:** **0** (`regression_determination_status: no_novel_failing_node_ids_observed`)

### Failure Set Relation Analysis

On Windows platform with CP950 default locale, the test runner encountered 109 baseline failures, including 35 encoding-related errors.
By explicitly enforcing UTF-8 encoding (`read_text(encoding="utf-8")`) on file reads inside the test files, all 35 cp950 encoding errors as well as 14 environment-related failures have been resolved. The remaining 60 failures are pre-existing platform-specific failures:

| Category | Count | Description / Representative Node IDs |
|---|---|---|
| **Pre-existing Windows/Local Environment Failures** | 60 | Legacy staging/promotion validation assertions and test case mocks that fail due to missing local environment states/paths (e.g., `test_m3g04_controlled_live_probe.py`, `test_m5c_staging_promotion.py`). |

There is **no functional regression** introduced by the Phase C activation.
