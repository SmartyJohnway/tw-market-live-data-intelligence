import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))

from scripts.governance_forbidden_path_guard import is_forbidden_repo_write_path, assert_not_forbidden_repo_write_path


def test_forbidden_paths_fail():
    for p in ["frontend/public/x.json", "research/generated/a.json", ".env", "credentials/a", "cookies/a", "tokens/a", "broker/a", "production/a", "prod/a", "current_market_state/a", "Frontend/Public/x"]:
        assert is_forbidden_repo_write_path(p)


def test_windows_nested_fail():
    assert is_forbidden_repo_write_path(r"frontend\public\x.json")


def test_safe_paths_pass(tmp_path):
    assert is_forbidden_repo_write_path(tmp_path / "out.json") is None
    assert_not_forbidden_repo_write_path("docs/examples/frontend_public_note.md")
