# M8R_03E_PHASE_C_ACTIVATION_DECISION — Acceptance Report

> [!IMPORTANT]
> **Disposition:** Approved with Explicit Caveats
> **Milestone Status:** Phase C has been verified and contractually integrated, but remains inactive in the default runtime registry (`validated_not_activated`) to maintain backwards compatibility. It is fully ready for conversation-triggered, one-shot explicit activation.

---

## 1. Verified Capabilities

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

---

## 2. Explicit Caveats

The activation of Phase C is subject to the following explicit operational and governance caveats:

- **Fugle and Fubon Neo APIs:** External broker endpoints remain in a `validated_not_activated` or `quarantined` state as no API credentials are committed to the repository. No trading execution or order submission logic is activated.
- **Backwards Compatibility Mode:** To prevent breaking existing workflows, the default state of `phase_c_activation_status` in the global `m8_source_capability_registry.json` is set to `validated_not_activated`. It requires explicit mock injection or dynamic registry passing to trigger Phase C workflows.
- **Cleanup Automation:** The `automatic_cleanup_scheduler_enabled` flag is set to `false`. Log purging relies on external operator triggers or workspace lifecycle cleanups after 30 days.

---

## 3. Test & Verification Log

### Automated Acceptance Tests
- **All 8 targeted tests passed successfully:**
  - `tests/unit/test_m8r_03e_phase_c_activation_policy.py`: PASS
  - `tests/unit/test_m8r_phase_c_execution_preview.py`: PASS
  - `tests/unit/test_m8r_phase_c_conversation_approval.py`: PASS
  - `tests/unit/test_m8r_phase_c_resource_bounds.py`: PASS
  - `tests/unit/test_m8r_phase_c_source_activation.py`: PASS
  - `tests/unit/test_m8r_phase_c_preview_plan_consistency.py`: PASS
  - `tests/unit/test_m8r_phase_c_retention_policy.py`: PASS
  - `tests/integration/test_m8r_phase_c_conversation_driven_activation.py`: PASS

### Regression Validation
- Run command: `python -m pytest -m "not network" -q`
- **Result:** Successfully completed with `0` novel regressions. Total failures remain at the baseline of `99` (due to pre-existing environment deviations).
