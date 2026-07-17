import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_filesystem_safety import FilesystemSafetyError

def test_execute_watchlist_fail_closed_ordering(tmp_path):
    # Prepare dummy valid request
    request = {
        "persistent_watchlist_reference": {"watchlist_id": "wl-test"},
        "targets": []
    }
    
    # We mock key steps:
    # - _claim_authorization (which writes the authorization consumption record)
    # - _execute_source_groups (which initiates live network observations)
    # - atomic_write_text (which writes final results)
    with patch("scripts.m8r_03d_watchlist_controlled_executor._claim_authorization") as mock_claim, \
         patch("scripts.m8r_03d_watchlist_controlled_executor._execute_source_groups") as mock_exec, \
         patch("scripts.m8r_03d_watchlist_controlled_executor.atomic_write_text") as mock_write:
         
        # Scenario 1: Unsafe artifact_root (traversal)
        with pytest.raises(ValueError) as excinfo:
            execute_watchlist(
                request,
                mode="execute",
                bundle_type="snapshot",
                authorization={"authorization_id": "auth-123", "one_shot_nonce": "nonce-123"},
                artifact_root="../outside_root"
            )
        assert "unsafe_artifact_root" in str(excinfo.value)
        assert mock_claim.call_count == 0
        assert mock_exec.call_count == 0
        assert mock_write.call_count == 0
        
        # Reset mocks
        mock_claim.reset_mock()
        mock_exec.reset_mock()
        mock_write.reset_mock()
        
        # Scenario 2: Unsafe run_id (traversal)
        with pytest.raises(FilesystemSafetyError) as excinfo:
            execute_watchlist(
                request,
                mode="execute",
                bundle_type="snapshot",
                authorization={"authorization_id": "auth-123", "one_shot_nonce": "nonce-123"},
                artifact_root=str(tmp_path),
                run_id="../evil_run"
            )
        assert excinfo.value.code == "path_traversal_forbidden"
        assert mock_claim.call_count == 0
        assert mock_exec.call_count == 0
        assert mock_write.call_count == 0

        # Reset mocks
        mock_claim.reset_mock()
        mock_exec.reset_mock()
        mock_write.reset_mock()
        
        # Scenario 3: Drive-relative run_id
        with pytest.raises(FilesystemSafetyError) as excinfo:
            execute_watchlist(
                request,
                mode="execute",
                bundle_type="snapshot",
                authorization={"authorization_id": "auth-123", "one_shot_nonce": "nonce-123"},
                artifact_root=str(tmp_path),
                run_id="C:evil"
            )
        assert excinfo.value.code == "drive_relative_output_path_forbidden"
        assert mock_claim.call_count == 0
        assert mock_exec.call_count == 0
        assert mock_write.call_count == 0

        # Reset mocks
        mock_claim.reset_mock()
        mock_exec.reset_mock()
        mock_write.reset_mock()
        
        # Scenario 4: UNC run_id
        with pytest.raises(FilesystemSafetyError) as excinfo:
            execute_watchlist(
                request,
                mode="execute",
                bundle_type="snapshot",
                authorization={"authorization_id": "auth-123", "one_shot_nonce": "nonce-123"},
                artifact_root=str(tmp_path),
                run_id="\\\\server\\share"
            )
        assert excinfo.value.code == "unc_output_path_forbidden"
        assert mock_claim.call_count == 0
        assert mock_exec.call_count == 0
        assert mock_write.call_count == 0


from scripts.m8r_one_shot_market_context_orchestrator import FilesystemApprovalConsumptionStore, preflight_approved_market_context_plan

def test_filesystem_approval_consumption_store_fail_closed():
    # Store constructor should reject absolute URI
    with pytest.raises(FilesystemSafetyError) as excinfo:
        FilesystemApprovalConsumptionStore(root="s3://bucket/key")
    assert excinfo.value.code == "absolute_output_path_forbidden"


def test_orchestrator_output_scope_fail_closed():
    plan = {
        "schema_version": "m8r_market_context_execution_plan.v1",
        "plan_id": "plan-123",
        "plan_hash": "hash-123",
        "targets": [],
        "source_to_target_context_mapping": [],
        "output_scope": {
            "artifact_root": "../outside_root"
        }
    }
    approval = {
        "schema_version": "m8r_market_context_execution_plan_approval.v1",
        "approval_id": "app-123",
        "plan_id": "plan-123",
        "plan_hash": "hash-123",
        "approval_status": "approved",
        "single_use": False
    }
    
    res = preflight_approved_market_context_plan(plan, approval)
    assert res["preflight_status"] == "blocked"
    assert any(issue["code"] == "unsafe_output_scope" for issue in res["issues"])


from scripts.run_m8r_controlled_live_validation import derive_runtime_critical_status

def test_controlled_live_validation_artifact_root_fail_closed():
    manifest = {
        "operator_confirmed": True,
        "allow_network": True,
        "artifact_root": "../outside_root"
    }
    status, observed = derive_runtime_critical_status(controls={}, case_results={}, retention={}, manifest=manifest)
    assert observed["artifact_root_bounded"]["passed"] is False


from scripts.run_m8r_conversational_derivatives_context import run as run_conversational_derivatives

def test_conversational_derivatives_diagnostic_output_fail_closed():
    with pytest.raises(SystemExit) as excinfo:
        run_conversational_derivatives("TX", "../outside_root")
    assert "artifact-root must be a bounded relative path" in str(excinfo.value)
