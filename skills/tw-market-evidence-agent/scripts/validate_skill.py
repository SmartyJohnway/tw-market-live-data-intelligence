#!/usr/bin/env python3
import json
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills/tw-market-evidence-agent"


def main():
    print("Validating tw-market-evidence-agent skill realignment...")

    # 1. Run portable catalog sync validator
    sync_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_portable_catalog_sync.py")],
        capture_output=True,
        text=True,
    )
    if sync_check.returncode != 0:
        print(
            f"ERROR: Sync validation failed:\n{sync_check.stdout}\n{sync_check.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Check SKILL.md contents and references
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if "unified_market_evidence_request.v2.schema.json" not in skill_text:
        print(
            "ERROR: SKILL.md does not reference the preferred current Unified Request schema.",
            file=sys.stderr,
        )
        sys.exit(1)

    if "smallest sufficient" in skill_text.lower():
        print(
            "ERROR: SKILL.md still contains prohibited 'smallest sufficient' rule language.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check that recommendation policy is correct (separation of project output vs conversational policy)
    if (
        "recommendation" in skill_text.lower()
        and "safety boundaries" not in skill_text.lower()
    ):
        print(
            "ERROR: SKILL.md does not define the recommendation policy separation.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 3. Current portable narrative must match the registered runtime surface.
    current_paths = [
        SKILL / "SKILL.md",
        SKILL / "references/current_limitations.md",
        SKILL / "references/evidence_semantics.md",
        SKILL / "references/tool_selection_examples.md",
        ROOT / "docs/agent_usage_guide.md",
    ]
    current_text = "\n".join(path.read_text(encoding="utf-8") for path in current_paths)
    required_tools = (
        "market_describe_capabilities",
        "market_validate_request",
        "market_preview_request",
        "market_read_result",
        "market_export_ai_handoff",
        "market_fetch_evidence",
    )
    for tool in required_tools:
        if tool not in current_text:
            print(f"ERROR: current portable instructions omit {tool}.", file=sys.stderr)
            sys.exit(1)
    for required_fact in (
        "Persistent Watchlists",
        "ISIN",
        "temporary request-only targets",
        "three confirmation boundaries",
        "watchlist version",
        "revision hash",
    ):
        if required_fact.casefold() not in current_text.casefold():
            print(f"ERROR: current portable instructions omit {required_fact}.", file=sys.stderr)
            sys.exit(1)
    forbidden = (
        "Direct Unified MCP/service execution is not currently available",
        "Until M8R-06 is implemented",
        "Mode B2, Mode C, and direct Unified MCP execution are **not implemented**",
    )
    if any(statement in current_text for statement in forbidden):
        print(
            "ERROR: current portable instructions retain superseded M8R-06 semantics.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 4. Verify duplicate Quick Guide redirects are present
    old_guide_path = ROOT / "docs/ai/M8_AI_CAPABILITY_QUICK_GUIDE.md"
    if old_guide_path.exists():
        guide_text = old_guide_path.read_text(encoding="utf-8")
        if (
            "superseded" not in guide_text.lower()
            or "unified_market_evidence_capability_catalog" not in guide_text
        ):
            print(
                "ERROR: docs/ai/M8_AI_CAPABILITY_QUICK_GUIDE.md is not converted to a redirect.",
                file=sys.stderr,
            )
            sys.exit(1)

    # 5. Verify duplicate JSON Contract is archived
    old_contract_path = ROOT / "docs/ai/m8_ai_capability_contract.json"
    if old_contract_path.exists():
        with open(old_contract_path, "r", encoding="utf-8") as f:
            old_contract = json.load(f)
        archive_status = old_contract.get("_archive_status")
        archived = archive_status == "historical_superseded_by_m8r_05a" or (
            isinstance(archive_status, dict)
            and archive_status.get("status") == "archived"
            and archive_status.get("active_canonical_source")
            == "../../docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json"
        )
        if not archived:
            print(
                "ERROR: docs/ai/m8_ai_capability_contract.json is not marked archived.",
                file=sys.stderr,
            )
            sys.exit(1)

    # 6. Check no secrets or API keys are written in documents
    active_texts = skill_text + (
        SKILL / "references/capability_quick_guide.md"
    ).read_text(encoding="utf-8")
    if re.search(
        r"(api[-_]?key|token|cookie|secret)\s*[:=]\s*[A-Za-z0-9_\-]{8,}",
        active_texts,
        re.I,
    ):
        print("ERROR: Secret-like credentials found in skill texts.", file=sys.stderr)
        sys.exit(1)

    print("PASS: tw-market-evidence-agent skill validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
