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
