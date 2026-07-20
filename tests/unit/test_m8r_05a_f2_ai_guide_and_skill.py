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
    
    # 1. when-to-call / when-not-to-call
    assert "When to Call" in content
    assert "When NOT to Call" in content

    # 2. Mode A/B/C retained but clearly defined as operator workflows, not AI JSON parameters
    assert "Mode A (Inspect and Validate)" in content
    assert "Mode B (Preview, Authorize, Execute Once)" in content
    assert "Mode C (Package and Handoff)" in content
    assert "These Modes are NOT AI JSON request parameters" in content

    # 3. Level 1/2 evidence lifecycles defined
    assert "Level 1 (Raw/Transport)" in content
    assert "Level 2 (Canonical/Normalized)" in content

    # 4. Runtime limitations explicitly stated
    assert "Current Runtime Limitations" in content
    assert "MCP or F3 resolvers are NOT yet implemented" in content
    assert "manual handoff via the operator" in content

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
    
    # Skill trigger must be specific
    assert "Current, official, verifiable, time-sensitive, calculated, or source-grounded" in content
    assert "General finance theory" in content # listed in NOT to call
    
    # Terminology fixes
    assert "canonical observations" in content.lower()
    
    # Does not claim unified executor exists
    assert "Direct Unified execution/MCP tools are not currently available" in content
    
    # No legacy phrases
    assert "smallest sufficient" not in content.lower()
    assert "safety boundaries" in content.lower()
