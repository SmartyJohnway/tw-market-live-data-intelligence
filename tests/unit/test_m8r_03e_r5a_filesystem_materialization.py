import pytest
from pathlib import Path
from scripts.m8r_filesystem_safety import validate_authorized_root, safe_destination, atomic_write_text, FilesystemSafetyError

def test_filesystem_safety_valid_path(tmp_path):
    root = validate_authorized_root(tmp_path)
    dest = safe_destination(root, "valid_file.json", create_parent=True)
    assert dest.path.name == "valid_file.json"
    
    # 正常寫入
    atomic_write_text(root, "valid_file.json", "{}")
    assert (tmp_path / "valid_file.json").read_text() == "{}"

def test_filesystem_safety_blocked_parent_traversal(tmp_path):
    root = validate_authorized_root(tmp_path)
    
    # 測試目錄遍歷路徑
    with pytest.raises(FilesystemSafetyError, match="path_traversal_forbidden"):
        safe_destination(root, "../outside.json")
        
    with pytest.raises(FilesystemSafetyError, match="path_traversal_forbidden"):
        safe_destination(root, "subdir/../../outside.json")

def test_filesystem_safety_blocked_forbidden_directories():
    from scripts.governance_forbidden_path_guard import is_forbidden_repo_write_path
    
    # 驗證 governance 阻擋
    assert is_forbidden_repo_write_path("cookies/token.json") is not None
    assert is_forbidden_repo_write_path("frontend/public/mock.json") is not None
    assert is_forbidden_repo_write_path("research/generated/report.json") is not None
