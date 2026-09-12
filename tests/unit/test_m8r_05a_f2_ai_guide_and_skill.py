import pytest
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/agent_usage_guide.md"
POLICY_PATH = ROOT / "docs/ai_safety_policy.md"
SKILL_PATH = ROOT / "skills/tw-market-evidence-agent/SKILL.md"

def test_guide_aligns_with_unified_evidence():
    assert GUIDE_PATH.exists()
    content = GUIDE_PATH.read_text(encoding="utf-8")
    
    # The current guide defines the callable boundary semantically rather than
    # preserving the superseded M8R-05A heading text.
    assert "## Use boundary" in content
    assert "Do not call it for general theory" in content

    # Mode names are workflow concepts, not a second request protocol.
    assert "Mode A/B/C are workflow concepts" in content
    assert "not tool names or JSON parameters" in content

    # Current runtime boundaries and handoff are authoritative.
    assert "`market_export_ai_handoff`" in content
    assert "TAIFEX remains provisional/non-executable" in content
    assert "There is no automatic Security Master update" in content

def test_guide_json_examples_schema_valid():
    content = GUIDE_PATH.read_text(encoding="utf-8")
    # Extract the JSON block
    start_marker = "```json"
    end_marker = "```"
    if start_marker in content and end_marker in content.split(start_marker)[1]:
        json_str = content.split(start_marker)[1].split(end_marker)[0].strip()
        try:
            req = json.loads(json_str)
            assert req["schema_version"] == "unified_market_evidence_request.v1"
            assert "targets" in req
            assert "data_needs" in req
        except Exception as e:
            pytest.fail(f"Guide JSON example failed parsing: {e}")

def test_policy_scopes_recommendation_ban():
    assert POLICY_PATH.exists()
    content = POLICY_PATH.read_text(encoding="utf-8")
    # Recommendation ban must be scoped to project output
    assert "Project Canonical Output Constraints" in content
    assert "AI Conversational Policy" in content

def test_skill_realignment():
    assert SKILL_PATH.exists()
    content = SKILL_PATH.read_text(encoding="utf-8")
    
    assert "Use this Skill when fresh, source-grounded Taiwan market evidence is needed." in content
    assert "Do not use for finance theory" in content
    assert "six-tool Unified MCP surface" in content
    assert "Preview never authorizes execution." in content
