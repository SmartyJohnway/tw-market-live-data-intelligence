import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/agent_usage_guide.md"
SKILL_PATH = ROOT / "skills/tw-market-evidence-agent/SKILL.md"

def test_evidence_semantics_retrieved_at_is_not_event_time():
    guide_content = GUIDE_PATH.read_text(encoding="utf-8")
    assert "observation/event timestamps, retrieval time" in guide_content
    assert "reference data, not live price." in guide_content

def test_evidence_semantics_unadjusted_return():
    guide_content = GUIDE_PATH.read_text(encoding="utf-8")
    assert "Execution success, freshness, and realtime status are separate facts." in guide_content
    assert "`full_success` never implies realtime." in guide_content

def test_skill_does_not_expose_credentials_or_raw_secrets():
    text = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'skills/tw-market-evidence-agent').rglob('*') if p.is_file() and p.suffix in {'.md', '.json', '.py'})
    for banned in ['api_key =', 'cookie =', 'secret =']:
        assert banned not in text.lower(), f"Found banned string {banned} in portable skill"

def test_raw_payload_exposure_is_restricted():
    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    assert "Do not retry outside the governed workflow" in skill_content
    assert "silently switch sources, invent" in skill_content
    
def test_network_authorization_boundaries_exist():
    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    assert "Preview never authorizes execution." in skill_content
    assert "explicit network **Execute Once** confirmation" in skill_content

def test_timing_class_distinctions():
    guide_content = GUIDE_PATH.read_text(encoding="utf-8")
    assert "Official EOD is completed-session" in guide_content
    assert "`full_success` never implies realtime." in guide_content
    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    assert "Official EOD is completed-session reference data, never a live quote." in skill_content
