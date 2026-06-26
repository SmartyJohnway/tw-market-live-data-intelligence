import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.governance_forbidden_path_guard import (
    frontend_public_changed_files,
    has_frontend_public_changed_file,
)


def test_frontend_public_changed_file_pure_check_detects_forbidden_paths():
    changed_files = [
        "frontend/public/index.html",
        "frontend\\public\\bundle.js",
        "docs/manuals/FRONTEND_CAVEAT_DISPLAY_MANUAL.md",
    ]
    assert has_frontend_public_changed_file(changed_files) is True
    assert frontend_public_changed_files(changed_files) == [
        "frontend/public/index.html",
        "frontend\\public\\bundle.js",
    ]


def test_frontend_public_changed_file_pure_check_allows_safe_paths():
    changed_files = [
        "frontend/readonly-preview/ReadonlyMarketContextPreview.html",
        "docs/examples/frontend_readonly_package_dry_run.md",
        "docs/manuals/FRONTEND_CAVEAT_DISPLAY_MANUAL.md",
    ]
    assert has_frontend_public_changed_file(changed_files) is False
    assert frontend_public_changed_files(changed_files) == []


def test_docs_can_mention_frontend_public_without_being_path_writes():
    assert has_frontend_public_changed_file(["docs/manuals/frontend_public_policy.md"]) is False


def test_builder_default_not_frontend_public():
    text = (ROOT / "scripts/build_frontend_readonly_context_package.py").read_text().lower()
    assert "frontend/public" not in text


def test_local_preview_outside_public():
    assert (ROOT / "frontend/readonly-preview").exists()
