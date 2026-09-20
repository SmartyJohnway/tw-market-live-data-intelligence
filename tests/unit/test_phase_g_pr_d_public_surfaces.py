from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from server.unified_mcp.tool_contracts import build_tool_specs


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v2.json"
PORTABLE = ROOT / "skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json"


def test_current_portable_catalog_is_exact_generated_v2_projection():
    result = subprocess.run(
        [sys.executable, "scripts/validate_portable_catalog_sync.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    canonical = json.loads(CATALOG.read_text(encoding="utf-8"))
    portable = json.loads(PORTABLE.read_text(encoding="utf-8"))
    assert portable["schema_version"] == canonical["schema_version"] == "unified_market_evidence_capability_catalog.v2"
    assert portable["contract_versions"] == canonical["contract_versions"]
    assert portable["portable_metadata"]["generated_from_commit"] == subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", CATALOG.relative_to(ROOT).as_posix()],
        cwd=ROOT,
        text=True,
    ).strip()
    assert portable["portable_metadata"]["canonical_git_blob_sha"] == subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{CATALOG.relative_to(ROOT).as_posix()}"],
        cwd=ROOT,
        text=True,
    ).strip()
    capabilities = {item["capability_id"]: item for item in portable["data_need_capabilities"]}
    for capability_id in ("material_disclosures", "monthly_revenue"):
        assert capabilities[capability_id]["support_status"] == "runtime_executable"
        assert capabilities[capability_id]["historical_lookup_supported"] is False
        assert capabilities[capability_id]["instrument_scope"] == {
            "instrument_families": ["company_share"],
            "instrument_types": ["common_share"],
        }
    assert capabilities["recent_performance"]["support_status"] == "contract_supported"
    guide = (ROOT / "skills/tw-market-evidence-agent/references/capability_quick_guide.md").read_text(encoding="utf-8")
    assert "| Capability ID | Support Status |" in guide
    assert "`recent_performance` | `contract_supported`" in guide
    assert "approval boundary does not make a `contract_supported` capability" in guide


def test_current_skill_guides_and_public_docs_are_truthful():
    paths = [
        ROOT / "skills/tw-market-evidence-agent/SKILL.md",
        ROOT / "skills/tw-market-evidence-agent/references/current_limitations.md",
        ROOT / "skills/tw-market-evidence-agent/references/capability_quick_guide.md",
        ROOT / "docs/agent_usage_guide.md",
        ROOT / "README.md",
        ROOT / "README.zh-TW.md",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for required in (
        "unified_market_evidence_request.v2",
        "Request v1",
        "material_disclosures",
        "monthly_revenue",
        "latest completed official daily batch",
        "latest available",
        "financial_summary",
    ):
        assert required.casefold() in text.casefold()
    assert "Phase G has not started" not in text
    assert "Phase G 尚未開始" not in text


def test_public_mcp_surface_remains_exactly_six_tools():
    assert {tool.name for tool in build_tool_specs()} == {
        "market_describe_capabilities",
        "market_validate_request",
        "market_preview_request",
        "market_read_result",
        "market_export_ai_handoff",
        "market_fetch_evidence",
    }
