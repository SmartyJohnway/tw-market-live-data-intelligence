import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/agent_usage_guide.md"
POLICY_PATH = ROOT / "docs/ai_safety_policy.md"
SKILL_PATH = ROOT / "skills/tw-market-evidence-agent/SKILL.md"

def test_guide_aligns_with_unified_evidence():
    assert GUIDE_PATH.exists()
    content = GUIDE_PATH.read_text(encoding="utf-8")
    assert "unified_market_evidence_request.v1" in content
    assert "data_needs" in content
    assert "preview" in content
    # Remove M5F Mode ABC / smallest sufficient as canonical AI-facing input
    assert "Mode A" not in content or "Manual Workbench" in content
    assert "smallest sufficient" not in content.lower()

def test_policy_scopes_recommendation_ban():
    assert POLICY_PATH.exists()
    content = POLICY_PATH.read_text(encoding="utf-8")
    # Recommendation ban must be scoped to project output
    assert "Project Canonical Output Constraints" in content
    assert "AI Conversational Policy" in content

def test_skill_realignment():
    assert SKILL_PATH.exists()
    content = SKILL_PATH.read_text(encoding="utf-8")
    assert "unified_market_evidence_request.v1.schema.json" in content
    assert "smallest sufficient" not in content.lower()
    assert "safety boundaries" in content.lower()
