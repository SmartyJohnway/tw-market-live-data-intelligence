import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.run_ci_delivery_acceptance import run_ci_delivery_acceptance, main


def test_ci_wrapper_check_only():
    r = run_ci_delivery_acceptance(ROOT)
    assert r["ok"] and r["check_only"] and r["network"] is False


def test_write_report_tmp_path(tmp_path):
    out = tmp_path / "report.json"
    assert main(["--repo-root", str(ROOT), "--write-report", str(out)]) == 0 and out.exists()


def test_ci_wrapper_can_check_pr_body_changed_files_without_git_remote():
    changed = ["scripts/run_ci_delivery_acceptance.py", "tests/unit/test_ci_delivery_acceptance.py"]
    body = "## Actual changed files\n```\nscripts/run_ci_delivery_acceptance.py\ntests/unit/test_ci_delivery_acceptance.py\n```\n"
    r = run_ci_delivery_acceptance(ROOT, changed_files=changed, pr_body=body)
    assert r["ok"] is True
    assert r["pr_body_changed_files_consistency"]["ok"] is True


def test_ci_wrapper_blocks_frontend_public_changed_files_without_git_remote():
    r = run_ci_delivery_acceptance(ROOT, changed_files=["frontend/public/index.html"])
    assert r["ok"] is False
    assert r["frontend_public_changed_files"] == ["frontend/public/index.html"]
