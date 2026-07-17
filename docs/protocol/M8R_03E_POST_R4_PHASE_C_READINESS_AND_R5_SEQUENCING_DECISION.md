# M8R-03E Post-R4 Phase C Readiness and R5 Sequencing Decision Protocol

## 1. Purpose

This document records the official preflight evaluation, local Windows-specific security observations, data-provenance network reachability, and strategic sequencing decisions after the partial completion of milestone `M8R-03E-R4-PERFORMANCE-AND-SCALABILITY-HARDENING`. It defines the readiness criteria and entry gates for the implementation and activation of Phase C, as well as the structured task roadmap for the R5 workstream.

---

## 2. Windows-Local Test Results & Failure Classification

A reproducible local execution result was completed in the Windows UTF-8 environment (`$env:PYTHONUTF8=1` via Python 3.11.15) to obtain deterministic execution metrics.

### 2.1. Test Execution Metrics
- **Passed**: 1,664
- **Failed**: 48
- **Skipped**: 1
- **Deselected**: 1
- **Status**: fail

### 2.2. Failure Classification Matrix (48 node IDs)
Every failing node ID has been analyzed and classified into a specific root cause category. The complete machine-readable audit list is registered in `docs/acceptance_runs/M8R_03E_POST_R4_PHASE_C_READINESS_DECISION.json`.

| Category | Count | Primary Cause & Representative Traceback | Auditable Evidence & Repro |
| :--- | :---: | :--- | :--- |
| **windows_path_semantics** | 5 | Platform separator (`\`) or `is_absolute()` / `PurePosixPath` parsing difference. Backslashes bypass `..` check in `_safe_root`. | *Traceback*: `Failed: DID NOT RAISE ValueError` or `FilesystemSafetyError`. *Repro*: `python -m pytest tests/unit/test_m8r_03e_r2_filesystem_containment.py` |
| **environment_or_dependency** | 4 | Windows `PYTHONPATH` separator character is `;` instead of `:`. subprocess failed to import required scripts. | *Traceback*: `ModuleNotFoundError: No module named 'scripts.probe_twse_openapi'`. *Repro*: `python -m pytest tests/test_m3g04_controlled_live_probe.py` |
| **artifact_or_fixture_drift** | 37 | Git `autocrlf` converts LF to CRLF in Windows checkout, altering file bytes of checked-in JSON templates/schema files. | *Traceback*: `manifest_sha256_mismatch` or `current_skill_contract_hash_mismatch`. *Repro*: `python -m pytest tests/unit/test_run_m4_readiness_check.py` |
| **stale_governance_expectation** | 2 | Governance policies or workflow YAML configurations drifted from hardcoded unit test assertions. | *Traceback*: `AssertionError: assert 'pass' == 'pass_with_caveats'`. *Repro*: `python -m pytest tests/test_m6e_operator_acceptance.py` |
| **known_historical_failure** | 0 | None | N/A |
| **test_harness_side_effect** | 0 | None | N/A |
| **new_regression** | 0 | None | N/A |
| **r5a_10_target_dependency** | 0 | None | N/A |
| **unknown_unclassified** | 0 | None | N/A |

**Validation Formula Verification**:
$$\text{Sum of Categories} = 5 (\text{path}) + 4 (\text{env}) + 37 (\text{drift}) + 2 (\text{stale}) = 48 \text{ failures}$$

---

## 3. Windows Filesystem Governance Correction (R2 Containment Status)

Windows-local testing confirmed that the fail-closed path validation contract has platform-specific defects under Windows environments.

### 3.1. Confirmed Fail-Closed Defects
1. **Delimiter Check Defect**: `_safe_root` utilizes `PurePosixPath` which does not recognize Windows backslash delimiters `\` as path separators. Thus, paths like `'artifacts\..\escape'` bypass `..` traversal checks.
2. **Absolute Path Block Defect**: Paths starting with a forward slash (e.g. `/tmp/x.json`) are evaluated as drive-relative on Windows and return `False` for `is_absolute()`, bypassing absolute path guards.
3. **Exception Defect**: Expected fail-closed exceptions (like `unsafe_artifact_root` or `absolute_output_path_forbidden`) are not raised under Windows during these traversal attempts.

### 3.2. Governance Position Update
- **Historical R2 Disposition**: `GO_WITH_CAVEATS`
- **Windows Containment Escape Proven**: `false` (resolved paths are still resolved inside the authorized root, preventing actual escape).
- **Windows Fail-Closed Contract Defect**: `confirmed` (R2 does not fail-closed as specified on Windows).
- **Required Follow-up Task**: `M8R-03E-R5B-WINDOWS-FILESYSTEM-FAIL-CLOSED-CORRECTION` (must be completed before Phase C activation).
- **Phase C Gate Impact**: **Phase C activation blocker**. Coding Phase C may begin, but its tool endpoints cannot be exposed to the assistant until the Windows defect is remediated.

---

## 4. Controlled Live Network Preflight (Parsed Data Retrieval Proof)

Network preflight was successfully executed. The results below verify parsed record properties, while avoiding overclaims on formal schema validation which is not performed by these probes.

| Source | Command | Actual Record Count | Trade Date | Exchange Timestamp | Schema Validation | Normalization Validation | Semantic Field Check | Session State / Price Retrieval | Status |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TWSE_MIS** | `python scripts/probe_twse_mis.py` | 3 | 2026-07-17 | 13:30:00 | `not_available` | `pass` | `pass` | regular_closed / `pz: 2285.0000`, `tv: 9277` | **pass** |
| **TAIFEX_MIS** | `python scripts/validate_m8c_taifex_mis_live.py --auto-smoke --confirm --pretty` | 3 | 2026-07-17 | 13:45:00 | `not_available` | `pass` | `pass` | `actual_quote_value_unavailable_after_session` | **contract_record_and_timestamp_verified** |
| **TWSE_OpenAPI** | `python scripts/probe_twse_openapi.py` | 1215 | 2026-07-16 | EOD | `not_available` | `pass` | `pass` | not_applicable / `ClosingPrice: 13.99` | **pass** |
| **TPEx_OpenAPI** | `python scripts/probe_tpex_openapi.py` | 878 | 2026-07-16 | EOD | `not_available` | `pass` | `pass` | not_applicable / `Close: 44.56` | **pass** |
| **TAIFEX_OpenAPI** | `python scripts/validate_m8b_taifex_openapi_live.py --contexts put_call_ratio --confirm` | 21 | 2026-07-16 | EOD | `not_available` | `pass` | `pass` | not_applicable / `PutCallVolumeRatio%: 88.01` | **pass** |

---

## 5. Governance & Active Contract Synchronization

To prevent contradictions between the decision documents and active runtime contracts, we establish an explicit two-gate model:

```json
"phase_dependencies": {
  "Phase C": "implementation_ready_activation_blocked",
  "Phase C implementation": "ready_after_post_R4_readiness_decision",
  "Phase C activation": "blocked_pending_R5A_10_target_fixture_and_windows_path_validation_correction"
}
```

### 5.1. Status Matrices
- **R4 Regression Evidence Status**: `full_non_network_executed_failure_set_partially_classified`
- **R4 Acceptance Sealing Status**: `unsealed` (R4 remains unsealed because the current regression failure set is not fully classified in main branch and because R4 scope remains partial).
- **R4 Completion Status**: `PARTIAL_COMPLETION`
- **R4 Scope Closure Status**: `not_closed`
- **Phase C Implementation Gate**: `ready_to_begin`
- **Phase C Activation Gate**: `blocked` (pending R5A fixture & R5B path validation correction).
- **R5A Relationship**: `required_for_Phase_C_activation_not_retroactive_R4_regression_claim`

### 5.2. Technical Debt Classifications
- **M8-DEBT-0004 (Wildcard imports)**: Reclassified from `should_complete_before_Phase_C` to `parallel_with_Phase_C`. Wildcard imports do not introduce runtime errors or caching issues in the current Phase C tool APIs, meaning they do not block implementation or activation.
- **M8-DEBT-0005 (Cached validator)**: Resolved in R4 (status is `partially_resolved_in_r4`).

### 5.3. Task Roadmap and Next Successor
The post-R4 decision task is completed. The next authorized workstreams are sequenced as follows:
- **Recommended Next Task (Primary)**: `M8R-03E-R5A-PHASE-C-ENABLING-CROSS-LAYER-FIXTURE-INFRASTRUCTURE`
- **Parallel Authorized Workstream**: `M8R-03E-R5B-WINDOWS-FILESYSTEM-FAIL-CLOSED-CORRECTION`

---

## 6. Tested Tree & Evidence Binding
- **Tested Parent Commit SHA**: `eb118fdc9d337d21827cca5cb4b0af5e1b3c9906`
- **Tested Tree SHA**: `null` (Self-referential tree hashing avoided for consistency)
- **Tested Worktree Diff Digest**: `null` (Avoided self-reference loop)
- **Binding Status**: `unsealed_precommit_evidence`
- **Evidence Execution Stage**: `pre_commit_unsealed_stage`
