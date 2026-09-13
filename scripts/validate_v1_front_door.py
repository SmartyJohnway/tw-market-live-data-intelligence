"""Validate the small, current-product surfaces used to enter the V1 repository."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-TW.md"
DOC_INDEX = ROOT / "docs" / "INDEX.md"


REQUIRED_README_FACTS = (
    "1.0.0-rc.1",
    "v0.1.0",
    "no RC tag or GitHub prerelease",
    "Persistent Watchlists are supported",
    "no automatic polling, scheduler, startup market fetch",
    "python scripts/run_unified_workbench.py",
    "python scripts/run_unified_market_evidence_mcp.py",
    "market_describe_capabilities",
    "market_fetch_evidence",
    "docs/assets/workbench-overview.png",
)

FORBIDDEN_CURRENT_CLAIMS = (
    "There is no persistent watchlist",
    "M8R-06 not implemented",
    "direct MCP unavailable",
    "manual handoff only",
    "Unified MCP future",
)


def validate() -> list[str]:
    errors: list[str] = []
    readme = README.read_text(encoding="utf-8")
    readme_zh = README_ZH.read_text(encoding="utf-8")
    index = DOC_INDEX.read_text(encoding="utf-8")
    for fact in REQUIRED_README_FACTS:
        if fact not in readme:
            errors.append(f"front_door_missing:{fact}")
    for claim in FORBIDDEN_CURRENT_CLAIMS:
        if claim in readme:
            errors.append(f"front_door_forbidden_current_claim:{claim}")
    if "Persistent Watchlists" not in readme_zh or "preview/commit" not in readme_zh:
        errors.append("front_door_zh_tw_missing_current_watchlist_contract")
    if "Engineering history / protocol archive" not in index:
        errors.append("docs_index_missing_history_boundary")
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
