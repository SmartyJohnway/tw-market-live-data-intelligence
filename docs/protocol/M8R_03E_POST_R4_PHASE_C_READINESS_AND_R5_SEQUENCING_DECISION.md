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

### 2.2. Failure Classification & Root-Cause Confirmation
Every failing node ID has been analyzed. We separate the provisional category assignment from final causal confirmation:
- **Failure Assignment Status**: `complete` (all 48 node IDs are assigned to one provisional category).
- **Root-Cause Confirmation Status**: `partial` (not every node has independently demonstrated causal proof; CRLF drift remains a hypothesis with partial confirmation via representative files).
- **Regression Determination Status**: `not_demonstrated_on_equivalent_cross_platform_baseline` (no new regression determination is made from the Windows-only expanded failure set).

### 2.3. Root-Cause Groups
The 48 observed Windows-local failures are grouped into 4 distinct root-cause groups in `docs/acceptance_runs/M8R_03E_POST_R4_PHASE_C_READINESS_DECISION.json`:

1. **`WINDOWS-PYTHONPATH-01`** (environment_or_dependency, 4 nodes):
   - **Root Cause**: Windows uses `;` rather than `:` as the PYTHONPATH separator. Subprocesses fail to import project modules under Windows.
   - **Confirmation**: Confirmed.
   - **Representative Observed Failure**: `ModuleNotFoundError: No module named 'scripts.probe_twse_openapi'`.

2. **`WINDOWS-PATH-SEMANTICS-01`** (windows_path_semantics, 5 nodes):
   - **Root Cause**: PurePosixPath does not recognize backslashes (`\`) as separators, and drive-relative paths (starting with forward-slash) bypass absolute blocks on Windows.
   - **Confirmation**: Confirmed.
   - **Representative Observed Failure**: `Failed: DID NOT RAISE ValueError` (R2 containment checks fail to raise expected fail-closed exceptions).

3. **`CRLF-HASH-DRIFT-01`** (artifact_or_fixture_drift, 37 nodes):
   - **Root Cause Hypothesis**: Git checkout auto-CRLF converts LF to CRLF in Windows checkouts, altering file bytes of checked-in JSON templates/schema files, yielding sha256 checksum mismatches.
   - **Confirmation Status**: Partial (due to platform-specific failure expansion; core.autocrlf=false or Linux runs not completed).
   - **Representative Hash Proof**:
     - `valid_single_source_twse_mis.json`: Expected `84cf99b8...`, Windows `4b39a614...`, LF-normalized `84cf99b8...` (Matches: **True**).
     - `valid_multi_source_mixed.json`: Expected `e4e9413a...`, Windows `1e6e6810...`, LF-normalized `e4e9413a...` (Matches: **True**).
     - `golden_single_source_twse_mis.json`: Expected `a3e9e88e...`, Windows `220c3006...`, LF-normalized `a3e9e88e...` (Matches: **True**).
     - `golden_multi_source_mixed.json`: Expected `eff11d56...`, Windows `8d6dc9fa...`, LF-normalized `eff11d56...` (Matches: **True**).

4. **`STALE-GOVERNANCE-01`** (stale_governance_expectation, 2 nodes):
   - **Root Cause**: Old YAML trigger structures or local check-only caveats output drifted from hardcoded unit assertions.
   - **Confirmation**: Confirmed.
   - **Representative Assertion Difference**: `AssertionError: assert 'pass' == 'pass_with_caveats'`.

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

Network preflight was successfully executed. The results below verify parsed record properties. Network probes were not rerun in Commit 4 because no source-level evidence or probe implementation changed.

### 4.1. Network Summary
- **Overall Status**: `partial_market_value_verification`
- **Actual Market Values Verified**: 4 sources
- **Contract Record and Timestamp Verified**: 1 source
- **Failed**: 0 sources
- **Overall Interpretation**: All five source families returned parsed records. Four produced actual market values; TAIFEX MIS produced contract identity and timestamp evidence only because the regular session had closed.

### 4.2. Source Metrics

| Source | Command | Actual Record Count | Trade Date | Exchange Timestamp | Schema Validation | Normalization Validation | Semantic Field Check | Session State / Price Retrieval |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **TWSE_MIS** | `python scripts/probe_twse_mis.py` | 3 | 2026-07-17 | 13:30:00 | `not_available` | `pass` | `pass` | regular_closed / `pz: 2285.0000`, `tv: 9277` |
| **TAIFEX_MIS** | `python scripts/validate_m8c_taifex_mis_live.py --auto-smoke --confirm --pretty` | 3 | 2026-07-17 | 13:45:00 | `not_available` | `pass` | `pass` | `actual_quote_value_unavailable_after_session` |
| **TWSE_OpenAPI** | `python scripts/probe_twse_openapi.py` | 1215 | 2026-07-16 | EOD | `not_available` | `pass` | `pass` | not_applicable / `ClosingPrice: 13.99` |
| **TPEx_OpenAPI** | `python scripts/probe_tpex_openapi.py` | 878 | 2026-07-16 | EOD | `not_available` | `pass` | `pass` | not_applicable / `Close: 44.56` |
| **TAIFEX_OpenAPI** | `python scripts/validate_m8b_taifex_openapi_live.py --contexts put_call_ratio --confirm` | 21 | 2026-07-16 | EOD | `not_available` | `pass` | `pass` | not_applicable / `PutCallVolumeRatio%: 88.01` |

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
- **R4 Regression Evidence Status**: `full_non_network_executed_assignment_complete_root_cause_confirmation_partial`
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
- **Baseline Main SHA**: `9861a90424f3589e12491b876d14e2c37db51f70`
- **Tested Parent SHA**: `0cd81632be83b3f7969da043c7f1510eeeddda00` (Immediately preceding Commit 3 updates)
- **Tested Tree SHA**: `null`
- **Tested Commit SHA**: `null`
- **Binding Status**: `unsealed_precommit_evidence`
- **Evidence Execution Stage**: `pre_commit_unsealed_stage`
- **Reason**: The evidence artifact is part of the tested change set and is not self-referentially bound to its own final tree or commit.
