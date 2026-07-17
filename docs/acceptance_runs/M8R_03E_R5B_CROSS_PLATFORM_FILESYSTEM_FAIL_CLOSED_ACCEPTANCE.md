# M8R-03E R5B Cross-Platform Filesystem Fail-Closed Acceptance Report

This report documents the verification, acceptance metrics, and governance closure for the R5B filesystem safety task.

## Executive Summary

- **Task ID**: `M8R-03E-R5B-CROSS-PLATFORM-FILESYSTEM-FAIL-CLOSED-CONTRACT-AND-WINDOWS-CORRECTION`
- **Disposition**: `resolved`
- **Filesystem Safety Blocker**: `partially_resolved_with_concurrency_fixes`
- **Phase C Implementation Gate**: `ready`
- **Phase C Activation Gate**: `blocked` (pending R5A fixture integration)
- **Operating System**: Windows / POSIX compliant
- **Authoritative Safety Module**: `scripts/m8r_filesystem_safety.py`

---

## 1. Safety Contract & Fail-Closed Evidence

We verified that all 9 critical Phase-C-relevant write surfaces (covering 11 functions) have been fully migrated to the centralized safety contract. Unsafe candidate paths (e.g., traversal, absolute, drive-relative, UNC, reserved device names) fail lexically **before** any of the following side effects:
- **Root Directory creation**: `mkdir` is not executed for candidate paths if validation fails. Unsafe candidates prevent the creation of the root directory itself.
- **Temporary file creation**: `tempfile.mkstemp` is never initiated for unsafe paths.
- **Authorization nonce/token consumption**: `_claim_authorization` is blocked before writing receipts.
- **Network observation adapters**: Adapters are never invoked.

We verified this behavior via mock-based integration tests:
- `tests/unit/test_m8r_03e_r5b_integration.py` assertions pass successfully, validating zero-side-effect fail-closed order.

---

## 2. Exclusive-Create Authorization claim

To eliminate TOCTOU (time-of-check to time-of-use) races, the centralized safety contract now includes a native exclusive-create atomic writing API:
- `atomic_create_text_exclusive`: Uses `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)` to guarantee exclusive-create atomicity at the OS level.
- Highly concurrent worker threads (12 concurrent runners) competing to write the same single-use receipt were tested.
- **Result**: Exactly **1 thread succeeds**, and all other **11 threads fail** with `FileExistsError` or safety exceptions.

---

## 3. Windows Path Corrections

The following confirmed Windows anomalies have been fully corrected and verified:
1. **Delimiter Traversal Bypass**: Mixed delimiters like `a\..\..\x` are correctly classified and rejected.
2. **Drive-Relative Paths**: Paths starting with letters (e.g., `C:file.json`, `z:`) are rejected.
3. **UNC & Device Namespace Paths**: Path starting with `\\` or `//` (UNC shares) and `\\?\` (Device Namespace) are distinguished and rejected with specific error codes.
4. **Reserved Device Names**: Windows reserved names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) are checked per path segment (e.g., `CON.txt` or `nested/PRN`) and rejected.
5. **Special Characters**: Alternate data streams (`name:stream`) and control characters (like `\x00`) are rejected.
6. **Empty/Dot Candidates**: Empty candidates `""` or `"."` are blocked explicitly.

---

## 4. Test & Verification Results

### 4.1. Safety Contract Unit Tests
- **Test File**: `tests/unit/test_m8r_03e_r5b_cross_platform_filesystem_safety.py`
- **Status**: PASSED (9/9 tests passed)
- **Legacy Containment Test**: `tests/unit/test_m8r_filesystem_containment.py`
- **Status**: PASSED (10/10 tests passed)
- **Concurrency Test**: `tests/unit/test_m8r_03e_r5b_concurrency.py`
- **Status**: PASSED (1/1 test passed)

### 4.2. Fail-Closed Integration Tests
- **Test File**: `tests/unit/test_m8r_03e_r5b_integration.py`
- **Status**: PASSED (5/5 tests passed, covering all critical migrated write surfaces including FilesystemApprovalConsumptionStore, Orchestrator preflight, controlled live validation, and conversational derivatives)

### 4.3. Full Non-Network Regression
- **Command**: `$env:PYTHONUTF8=1; .venv\Scripts\python.exe -m pytest -m "not network" -q`
- **Total Tests Run**: 1733
- **Passed**: 1695
- **Failed**: 36 (All 36 are confirmed known pre-existing baseline failures recorded in the R4 readiness decision; zero new regressions introduced)

---

## 5. Governance & Roadmap Realignment

### 5.1. Mirror Active Sequencing Surfaces
In accordance with the owner's sequencing decision to execute R5B before R5A, active metadata has been aligned:
- **Current Task**: `M8R-03E-R5B-CROSS-PLATFORM-FILESYSTEM-FAIL-CLOSED-CONTRACT-AND-WINDOWS-CORRECTION`
- **Next Task after R5B**: `M8R-03E-R5A-PHASE-C-ENABLING-CROSS-LAYER-FIXTURE-INFRASTRUCTURE`

### 5.2. Governance Scanner
The custom static code scanner `scripts/governance_forbidden_path_guard.py` now includes a focused R5B rule set that scans for ad-hoc `PurePosixPath`, `Path.is_absolute`, and ad-hoc file writing patterns.
- **Scanner Status**: PASS

---

## 6. Deployment Boundaries & Limitations
- **Validated Now**: Local filesystem, POSIX relative paths, Windows lexical path validation, deepest-existing-parent containment, same-directory temp files, local os.replace atomic rename, exclusive O_CREAT|O_EXCL creation.
- **Not Validated**: NFS atomic rename, SMB concurrency, Kubernetes PVC, container host-path trust, S3/GCS/Azure Blob object-store, distributed multi-host locking, kernel TOCTOU.

Future cloud deployment must either run the validated local-filesystem backend inside a controlled container volume, or implement a separate object-storage adapter. S3 object keys must never be represented as OS paths.
