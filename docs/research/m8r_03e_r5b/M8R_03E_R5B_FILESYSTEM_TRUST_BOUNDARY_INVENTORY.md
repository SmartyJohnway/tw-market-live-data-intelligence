# Filesystem Trust Boundary Inventory

This inventory registers all repository surfaces that perform path validation, directory creation, or file write operations for artifact persistence.

## Summary

- **Total Surfaces**: 12
- **Authoritative safety module users**: 1 (partially 2)
- **Legacy validators / Ad-hoc gates**: 10
- **Direct write surfaces**: 7
- **Phase C critical surfaces**: 9
- **Migration required count**: 9
- **Unresolved surfaces**: 0

---

## Detailed Inventory Entries

### 1. `validate_output_scope` in `m8r_bounded_market_context_request.py`
- **Repository Path**: [m8r_bounded_market_context_request.py](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_bounded_market_context_request.py)
- **Function/Entrypoint**: `validate_output_scope`
- **Input Origin**: `request`
- **Operation**: `validate`
- **Current Validator**: Ad-hoc `PurePosixPath` checks (absolute path, traversal, secret folders, frontend public / research generated prefixes).
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: No
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: High
- **Notes**: Validates the output artifact root specified in a client request. Needs to migrate to the centralized safety relative path validator.

### 2. `_safe_root` in `m8r_03d_watchlist_controlled_executor.py`
- **Repository Path**: [m8r_03d_watchlist_controlled_executor.py](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_03d_watchlist_controlled_executor.py)
- **Function/Entrypoint**: `_safe_root`
- **Input Origin**: `config`
- **Operation**: `validate`
- **Current Validator**: Ad-hoc `PurePosixPath` checks combined with `validate_authorized_root`.
- **Uses Authoritative Safety Module**: Yes (partially)
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: No
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: High
- **Notes**: Validates artifact root before executing a watchlist request. Must use centralized validator.

### 3. Watchlist execution result write in `m8r_03d_watchlist_controlled_executor.py`
- **Repository Path**: [m8r_03d_watchlist_controlled_executor.py](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_03d_watchlist_controlled_executor.py)
- **Function/Entrypoint**: `_result`
- **Input Origin**: `derived_identifier` (run_id)
- **Operation**: `write`
- **Current Validator**: Calls `safe_destination(..., create_parent=True)`
- **Uses Authoritative Safety Module**: Yes
- **Legacy or Ad-hoc Gate**: No
- **Side Effect Before Final Validation**: No
- **Phase C Relevance**: Direct
- **Migration Required**: Yes (to align with the strengthened `safe_destination` contract)
- **Risk Class**: Medium
- **Notes**: Writes validation and run outputs using `atomic_write_text`.

### 4. `_claim_authorization` in `m8r_03d_watchlist_controlled_executor.py`
- **Repository Path**: [m8r_03d_watchlist_controlled_executor.py](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_03d_watchlist_controlled_executor.py)
- **Function/Entrypoint**: `_claim_authorization`
- **Input Origin**: `internal`
- **Operation**: `authorization_claim`
- **Current Validator**: None (directly uses `mkdir(parents=True, exist_ok=True)` and `os.open` with `O_CREAT|O_EXCL`)
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: Yes (writes authorization receipt files and creates parent directory without canonical path validation)
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: Critical
- **Notes**: Claims one-shot authorization before execution. Failure to validate paths beforehand violates fail-closed ordering.

### 5. `safe_root` in `run_m8r_controlled_live_validation.py`
- **Repository Path**: [run_m8r_controlled_live_validation.py](file:///p:/tw-market-live-data-intelligence-main/scripts/run_m8r_controlled_live_validation.py)
- **Function/Entrypoint**: `safe_root`
- **Input Origin**: `cli`
- **Operation**: `validate`
- **Current Validator**: Ad-hoc `PurePosixPath` absolute and `..` check, plus custom prefix blacklists.
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: No
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: High
- **Notes**: Validates the output directory provided via CLI. Must use centralized validator.

### 6. `write_json` in `run_m8r_controlled_live_validation.py`
- **Repository Path**: [run_m8r_controlled_live_validation.py](file:///p:/tw-market-live-data-intelligence-main/scripts/run_m8r_controlled_live_validation.py)
- **Function/Entrypoint**: `write_json`
- **Input Origin**: `internal`
- **Operation**: `write`
- **Current Validator**: None (uses `path.parent.mkdir`, `.write_text` on a `.tmp` file, and `os.replace`)
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: Yes (directories created and temp files written before canonical safety checks)
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: High
- **Notes**: Write helper for controlled live validation outputs. Must be migrated to `atomic_write_text`.

### 7. `_is_safe_output_scope` in `m8r_one_shot_market_context_orchestrator.py`
- **Repository Path**: [m8r_one_shot_market_context_orchestrator.py](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_one_shot_market_context_orchestrator.py)
- **Function/Entrypoint**: `_is_safe_output_scope`
- **Input Origin**: `config`
- **Operation**: `validate`
- **Current Validator**: Delegates to `validate_output_scope` plus `PurePosixPath` normalization checks.
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: No
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: High
- **Notes**: Validates the output scope from the plan. Must use centralized safety validator.

### 8. `FilesystemApprovalConsumptionStore.consume` in `m8r_one_shot_market_context_orchestrator.py`
- **Repository Path**: [m8r_one_shot_market_context_orchestrator.py](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_one_shot_market_context_orchestrator.py)
- **Function/Entrypoint**: `FilesystemApprovalConsumptionStore.consume`
- **Input Origin**: `internal`
- **Operation**: `authorization_claim`
- **Current Validator**: None (uses `path.parent.mkdir` and `os.open` with `O_CREAT|O_EXCL`)
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: Yes (writes consumption proof directly)
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: Critical
- **Notes**: Stores plan approval consumption. Must validate paths before performing writes or directory creation.

### 9. `write_execution_artifacts` in `m8r_one_shot_market_context_orchestrator.py`
- **Repository Path**: [m8r_one_shot_market_context_orchestrator.py](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_one_shot_market_context_orchestrator.py)
- **Function/Entrypoint**: `write_execution_artifacts`
- **Input Origin**: `derived_identifier` (receipt_id)
- **Operation**: `write`
- **Current Validator**: Ad-hoc `mkdir` and manual `tempfile.mkstemp` and `os.replace`.
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: Yes (creates subdirectories and writes temp files prior to central safety integration)
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: High
- **Notes**: Persists market context validation execution outputs. Must migrate to `atomic_write_text`.

### 10. `safe_root` in `run_m8r_conversational_derivatives_context.py`
- **Repository Path**: [run_m8r_conversational_derivatives_context.py](file:///p:/tw-market-live-data-intelligence-main/scripts/run_m8r_conversational_derivatives_context.py)
- **Function/Entrypoint**: `safe_root`
- **Input Origin**: `cli`
- **Operation**: `validate`
- **Current Validator**: Ad-hoc `PurePosixPath` absolute and `..` check, plus custom prefix blacklists.
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: No
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: High
- **Notes**: Validates artifact root for conversational context runs. Must use centralized validator.

### 11. Write operations in `run_m8r_conversational_derivatives_context.py`
- **Repository Path**: [run_m8r_conversational_derivatives_context.py](file:///p:/tw-market-live-data-intelligence-main/scripts/run_m8r_conversational_derivatives_context.py)
- **Function/Entrypoint**: `write_mis_diagnostic` and `run`
- **Input Origin**: `internal`
- **Operation**: `write`
- **Current Validator**: None (uses `path.write_text` and `mkdir` directly)
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: Yes (directories created and files written with ad-hoc path methods)
- **Phase C Relevance**: Direct
- **Migration Required**: Yes
- **Risk Class**: High
- **Notes**: Writes conversational output and diagnostic artifacts. Must migrate to `atomic_write_text`.

### 12. `is_forbidden_repo_write_path` in `governance_forbidden_path_guard.py`
- **Repository Path**: [governance_forbidden_path_guard.py](file:///p:/tw-market-live-data-intelligence-main/scripts/governance_forbidden_path_guard.py)
- **Function/Entrypoint**: `is_forbidden_repo_write_path`
- **Input Origin**: `internal`
- **Operation**: `validate`
- **Current Validator**: Ad-hoc `PurePosixPath` check.
- **Uses Authoritative Safety Module**: No
- **Legacy or Ad-hoc Gate**: Yes
- **Side Effect Before Final Validation**: No
- **Phase C Relevance**: Indirect
- **Migration Required**: No (read-only code scanner, but should align conceptually)
- **Risk Class**: Medium
- **Notes**: Static codebase / path scanner. Not a runtime artifact write surface.
