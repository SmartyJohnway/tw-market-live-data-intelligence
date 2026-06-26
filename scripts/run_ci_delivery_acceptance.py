"""CI wrapper for local delivery acceptance; defaults to check-only and no artifact writes."""
from __future__ import annotations
import argparse, json
from pathlib import Path

from check_pr_body_changed_files_consistency import check_pr_body_changed_files_consistency
from governance_forbidden_path_guard import assert_not_forbidden_repo_write_path, frontend_public_changed_files
from run_local_delivery_acceptance import run_acceptance_checks, write_acceptance_report


def run_ci_delivery_acceptance(
    repo_root: str | Path = ".",
    *,
    changed_files: list[str] | None = None,
    pr_body: str | None = None,
) -> dict:
    report = run_acceptance_checks(repo_root)
    report["ci_wrapper"] = True
    report["check_only"] = True
    report["frontend_public_changed_files"] = frontend_public_changed_files(changed_files or [])
    if pr_body is not None:
        consistency = check_pr_body_changed_files_consistency(pr_body, changed_files or [])
        report["pr_body_changed_files_consistency"] = {
            "ok": consistency.ok,
            "errors": consistency.errors,
            "warnings": consistency.warnings,
            "listed_files": consistency.listed_files,
        }
        report["ok"] = bool(report.get("ok")) and consistency.ok
    if report["frontend_public_changed_files"]:
        report["ok"] = False
    return report


def _read_changed_files(values: list[str], file_path: str | None) -> list[str]:
    files = list(values)
    if file_path:
        files.extend(line.strip() for line in Path(file_path).read_text(encoding="utf-8").splitlines() if line.strip())
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--check-only", action="store_true", default=True)
    ap.add_argument("--write-report")
    ap.add_argument("--pr-body")
    ap.add_argument("--changed-files", nargs="*", default=[])
    ap.add_argument("--changed-files-file")
    a = ap.parse_args(argv)
    changed_files = _read_changed_files(a.changed_files, a.changed_files_file)
    pr_body = Path(a.pr_body).read_text(encoding="utf-8") if a.pr_body else None
    report = run_ci_delivery_acceptance(a.repo_root, changed_files=changed_files, pr_body=pr_body)
    if a.write_report:
        assert_not_forbidden_repo_write_path(a.write_report)
        write_acceptance_report(report, a.write_report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
