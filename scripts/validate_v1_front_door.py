"""Validate the small, current-product surfaces used to enter the V1 repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.product_version import product_version


README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-TW.md"
DOC_INDEX = ROOT / "docs" / "INDEX.md"
SECURITY = ROOT / "SECURITY.md"
SECURITY_CONTACT_FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "security_contact_request.yml"


COMMON_REQUIRED_README_FACTS = (
    "Persistent Watchlists are supported",
    "no automatic polling, scheduler, startup market fetch",
    "python scripts/run_unified_workbench.py",
    "python scripts/run_unified_market_evidence_mcp.py",
    "market_describe_capabilities",
    "market_fetch_evidence",
    "docs/assets/workbench-overview.png",
    "[English](README.md) | [繁體中文](README.zh-TW.md)",
    "Project History",
    "Engineering history / protocol",
)


def required_release_patterns() -> tuple[str, ...]:
    if product_version() == "1.0.0-rc.1":
        return (
            r"1\.0\.0-rc\.1",
            r"v0\.1\.0",
            r"latest\s+prerelease\s+is\s+`v1\.0\.0-rc\.1`",
            r"final\s+`v1\.0\.0`\s+is\s+not\s+released,\s+and\s+phase\s+g\s+has\s+not\s+started",
        )
    if product_version() == "1.0.0":
        return (
            r"productversion\s*=\s*`1\.0\.0`",
            r"v1\.0\.0-rc\.1",
            r"latest\s+prerelease\s+is\s+`v1\.0\.0-rc\.1`",
            r"final\s+`v1\.0\.0`\s+has\s+not\s+yet\s+been\s+published,\s+and\s+phase\s+g\s+has\s+not\s+started",
        )
    return ()

FORBIDDEN_CURRENT_CLAIMS = (
    "There is no persistent watchlist",
    "M8R-06 not implemented",
    "direct MCP unavailable",
    "manual handoff only",
    "Unified MCP future",
    "## Historical M8 architecture",
    "## M8A official EOD context capability",
    "## M6D SSL/TLS compatibility policy",
    "security contact shown on the GitHub repository profile",
)


def validate() -> list[str]:
    errors: list[str] = []
    readme = README.read_text(encoding="utf-8")
    readme_zh = README_ZH.read_text(encoding="utf-8")
    index = DOC_INDEX.read_text(encoding="utf-8")
    security = SECURITY.read_text(encoding="utf-8")
    for fact in COMMON_REQUIRED_README_FACTS:
        if fact not in readme:
            errors.append(f"front_door_missing:{fact}")
    for pattern in required_release_patterns():
        if not re.search(pattern, readme, flags=re.IGNORECASE):
            errors.append(f"front_door_missing_release_status:{pattern}")
    for claim in FORBIDDEN_CURRENT_CLAIMS:
        if claim in readme:
            errors.append(f"front_door_forbidden_current_claim:{claim}")
    if (
        "Persistent Watchlists" not in readme_zh
        or "preview/commit" not in readme_zh
        or "[English](README.md) | [繁體中文](README.zh-TW.md)" not in readme_zh
    ):
        errors.append("front_door_zh_tw_missing_current_watchlist_contract")
    if "Engineering history / protocol archive" not in index:
        errors.append("docs_index_missing_history_boundary")
    if "Security contact request" not in security:
        errors.append("security_policy_missing_executable_fallback")
    if not SECURITY_CONTACT_FORM.is_file():
        errors.append("security_contact_request_form_missing")
    elif "required: true" not in SECURITY_CONTACT_FORM.read_text(encoding="utf-8"):
        errors.append("security_contact_request_form_missing_required_safety_acknowledgement")
    for path in (
        ROOT / "docs" / "assets" / "workbench-overview.png",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
    ):
        if not path.is_file():
            errors.append(f"front_door_missing_file:{path.relative_to(ROOT).as_posix()}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("FAIL")
        print("\n".join(errors))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
