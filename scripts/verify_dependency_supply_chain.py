#!/usr/bin/env python3
"""Offline, read-only validation of the repository dependency authorities."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
DIRECT = ROOT / "requirements.txt"
LOCK = ROOT / "requirements-lock.txt"
BROWSER = ROOT / "requirements-browser-e2e.txt"


def _requirements(path: Path, errors: list[str], *, allow_includes: bool = False) -> list[Requirement]:
    parsed: list[Requirement] = []
    for line_number, original in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = original.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-"):
            if allow_includes and line == "-r requirements-lock.txt":
                continue
            errors.append(f"{path.name}:{line_number}:unsupported_directive")
            continue
        try:
            requirement = Requirement(line)
        except InvalidRequirement:
            errors.append(f"{path.name}:{line_number}:invalid_requirement")
            continue
        if requirement.url:
            errors.append(f"{path.name}:{line_number}:direct_url_forbidden")
        parsed.append(requirement)
    return parsed


def validate(root: Path = ROOT) -> dict:
    direct_path = root / DIRECT.name
    lock_path = root / LOCK.name
    browser_path = root / BROWSER.name
    errors: list[str] = []
    direct = _requirements(direct_path, errors)
    locked = _requirements(lock_path, errors)
    browser_lines = browser_path.read_text(encoding="utf-8").splitlines()
    browser = _requirements(browser_path, errors, allow_includes=True)

    direct_by_name = {canonicalize_name(req.name): req for req in direct}
    lock_by_name: dict[str, Requirement] = {}
    for req in locked:
        name = canonicalize_name(req.name)
        if name in lock_by_name:
            errors.append(f"duplicate_lock_package:{name}")
        lock_by_name[name] = req
        specs = list(req.specifier)
        if len(specs) != 1 or specs[0].operator != "==" or "*" in specs[0].version:
            errors.append(f"lock_not_exact_pin:{name}")

    for name, policy in direct_by_name.items():
        pin = lock_by_name.get(name)
        if pin is None:
            errors.append(f"direct_requirement_missing_from_lock:{name}")
        else:
            pin_specs = list(pin.specifier)
            if len(pin_specs) == 1 and not policy.specifier.contains(pin_specs[0].version, prereleases=True):
                errors.append(f"locked_version_outside_direct_policy:{name}")

    for filename in (direct_path, lock_path, browser_path):
        for line_number, original in enumerate(filename.read_text(encoding="utf-8").splitlines(), 1):
            line = original.strip().lower()
            if line.startswith(("-e ", "--editable ", "git+", "hg+", "svn+", "bzr+")):
                errors.append(f"{filename.name}:{line_number}:editable_or_vcs_forbidden")
            if line.startswith(("--extra-index-url", "--index-url", "--find-links", "--trusted-host")):
                errors.append(f"{filename.name}:{line_number}:custom_source_override_forbidden")

    if direct_by_name.get("mcp") is None or str(direct_by_name["mcp"].specifier) != "==1.29.0":
        errors.append("direct_mcp_pin_mismatch")
    lock_mcp = lock_by_name.get("mcp")
    lock_mcp_specs = list(lock_mcp.specifier) if lock_mcp is not None else []
    if len(lock_mcp_specs) != 1 or lock_mcp_specs[0].version != "1.29.0":
        errors.append("lock_mcp_pin_mismatch")
    includes = [line.strip() for line in browser_lines if line.strip().startswith("-r ")]
    if includes != ["-r requirements-lock.txt"]:
        errors.append("browser_core_lock_inheritance_mismatch")
    browser_playwright = [req for req in browser if canonicalize_name(req.name) == "playwright"]
    if len(browser_playwright) != 1 or str(browser_playwright[0].specifier) != "==1.55.0":
        errors.append("browser_playwright_pin_mismatch")
    if any(req.url for req in direct + locked + browser):
        # Per-line diagnostics above identify direct URLs; keep this aggregate assertion explicit.
        errors.append("url_dependency_forbidden")

    return {
        "status": "PASS" if not errors else "FAIL",
        "direct_count": len(direct),
        "lock_count": len(locked),
        "browser_extra_count": len(browser),
        "errors": sorted(set(errors)),
        "network_access": False,
        "writes": False,
    }


def main() -> int:
    report = validate()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
