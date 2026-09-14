#!/usr/bin/env python3
"""Offline RC hygiene gate for tracked documentation links and secrets."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HIGH_CONFIDENCE_SECRET = re.compile(
    r"(?:AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9]{20,})"
)
CURRENT_DOCUMENTS = (
    "README.md",
    "docs/INDEX.md",
    "docs/contracts/V1_PUBLIC_CONTRACTS.md",
    "docs/contracts/V1_API_ERROR_POLICY.md",
    "docs/release/README.md",
    "docs/release/V1_RELEASE.md",
    "docs/release/V1_RELEASE_CANDIDATE.md",
    "docs/release/V1_MIGRATION.md",
)


def tracked_files(root: Path = ROOT) -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], cwd=root, text=True)
    return [root / item for item in output.splitlines()]


def check_markdown_links(root: Path = ROOT) -> list[str]:
    missing: list[str] = []
    for relative in CURRENT_DOCUMENTS:
        path = root / relative
        if not path.is_file():
            missing.append(f"missing current document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            target = target.strip().strip("<>")
            target_path = target.split("#", 1)[0]
            if not target_path or "://" in target_path or target_path.startswith(("mailto:", "codex:")):
                continue
            candidate = (path.parent / target_path).resolve()
            if not candidate.exists():
                missing.append(f"{path.relative_to(root)} -> {target}")
    return sorted(missing)


def check_high_confidence_secrets(root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    for path in tracked_files(root):
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if HIGH_CONFIDENCE_SECRET.search(text):
            findings.append(str(path.relative_to(root)))
    return sorted(findings)


def main() -> int:
    links = check_markdown_links()
    secrets = check_high_confidence_secrets()
    if links or secrets:
        print({"status": "FAIL", "missing_links": links, "high_confidence_secret_files": secrets})
        return 1
    print({"status": "PASS", "checked": "tracked docs and source files"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
