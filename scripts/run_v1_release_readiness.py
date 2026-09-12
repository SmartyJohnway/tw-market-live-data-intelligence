#!/usr/bin/env python3
"""Run the offline V1 RC readiness gate against one exact checked-out tree.

All generated evidence is directed to ``--output-root``.  The source tree is
read-only during the gate; a non-clean worktree before or after execution is a
release failure, not something this runner repairs.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_clean() -> bool:
    return not git_value("status", "--porcelain", "--untracked-files=all")


def run(name: str, command: list[str], *, cwd: Path = ROOT) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {
        "name": name,
        "command": command,
        "return_code": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "output_tail": completed.stdout[-4000:],
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def source_archive_smoke(output_root: Path) -> dict[str, Any]:
    archive = output_root / "source-archive.zip"
    extracted = output_root / "source-archive"
    if extracted.exists():
        raise RuntimeError("source_archive_output_already_exists")
    subprocess.run(["git", "archive", "--format=zip", "--output", str(archive), "HEAD"], cwd=ROOT, check=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(extracted)
    checks = [
        run("archive_environment", [sys.executable, "scripts/verify_environment.py"], cwd=extracted),
        run("archive_version", [sys.executable, "-c", "from scripts.product_version import product_version; assert product_version() == '1.0.0-rc.1'; print(product_version())"], cwd=extracted),
        run("archive_local_service_import", [sys.executable, "-c", "from server.main import app; assert app.title; print(app.title)"], cwd=extracted),
        run("archive_mcp_startup", [sys.executable, "server/mcp_server.py", "--startup-check"], cwd=extracted),
    ]
    no_git = not (extracted / ".git").exists()
    return {
        "status": "PASS" if no_git and all(check["status"] == "PASS" for check in checks) else "FAIL",
        "archive": str(archive),
        "extracted_root": str(extracted),
        "git_directory_absent": no_git,
        "checks": checks,
    }


def javascript_syntax(output_root: Path) -> dict[str, Any]:
    node = shutil.which("node")
    paths = sorted((ROOT / "frontend").rglob("*.js"))
    if node is None:
        return {"status": "FAIL", "reason_code": "node_unavailable", "checked_files": 0}
    failures: list[str] = []
    for path in paths:
        completed = subprocess.run([node, "--check", str(path)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        if completed.returncode:
            failures.append(f"{path.relative_to(ROOT)}: {completed.stdout[-300:]}")
    return {"status": "PASS" if not failures else "FAIL", "checked_files": len(paths), "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True, help="External directory for all release-gate evidence.")
    args = parser.parse_args(argv)
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "v1_release_readiness.json"
    report: dict[str, Any] = {
        "schema_version": "v1_release_readiness.v1",
        "generated_at": utc_now(),
        "candidate_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "validated_code_commit": git_value("rev-parse", "HEAD"),
        "validated_code_tree_sha": git_value("rev-parse", "HEAD^{tree}"),
        "worktree_clean_before": git_clean(),
        "market_network_used": False,
        "gates": [],
    }
    commands = [
        ("environment", [sys.executable, "scripts/verify_environment.py"]),
        ("dependency_check", [sys.executable, "-m", "pip", "check"]),
        ("version_consistency", [sys.executable, "scripts/validate_product_version_consistency.py"]),
        ("public_contracts", [sys.executable, "scripts/validate_v1_public_contracts.py"]),
        ("release_hygiene_links_and_secrets", [sys.executable, "scripts/validate_release_hygiene.py"]),
        ("portable_catalog", [sys.executable, "scripts/validate_portable_catalog_sync.py"]),
        ("runtime_skill_guide_semantics", [sys.executable, "scripts/validate_runtime_skill_guide_sync.py"]),
        ("market_evidence_skill", [sys.executable, "skills/tw-market-evidence-agent/scripts/validate_skill.py"]),
        ("security_master_skill", [sys.executable, "skills/tw-security-master-classifier/scripts/validate_skill.py"]),
        ("compileall", [sys.executable, "-m", "compileall", "scripts", "server", "tests"]),
        ("default_ci", [sys.executable, "scripts/run_test_profile.py", "default-ci", "--json", "--output-root", str(output_root / "default-ci")]),
        ("full_non_network", [sys.executable, "scripts/run_test_profile.py", "full-non-network", "--json", "--output-root", str(output_root / "full-non-network")]),
        ("operator_preflight", [sys.executable, "scripts/run_test_profile.py", "operator-preflight", "--json", "--output-root", str(output_root / "operator-preflight")]),
        ("browser_e2e", [sys.executable, "scripts/run_test_profile.py", "browser-e2e", "--json", "--output-root", str(output_root / "browser-e2e")]),
        ("release_manifest", [sys.executable, "scripts/build_v1_release_manifest.py", "--output", str(output_root / "v1_release_manifest.json")]),
    ]
    if not report["worktree_clean_before"]:
        report["gates"].append({"name": "worktree_clean_before", "status": "FAIL"})
    else:
        for name, command in commands:
            gate = run(name, command)
            report["gates"].append(gate)
            if gate["status"] != "PASS":
                break
        if all(gate["status"] == "PASS" for gate in report["gates"]):
            report["gates"].append({"name": "javascript_syntax", **javascript_syntax(output_root)})
            report["gates"].append({"name": "source_archive", **source_archive_smoke(output_root)})
    report["worktree_clean_after"] = git_clean()
    report["status"] = "PASS" if report["worktree_clean_before"] and report["worktree_clean_after"] and all(gate["status"] == "PASS" for gate in report["gates"]) else "FAIL"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path)}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
