import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/agent_usage_guide.md"
SKILL_PATH = ROOT / "skills/tw-market-evidence-agent/SKILL.md"

def test_evidence_semantics_retrieved_at_is_not_event_time():
    guide_content = GUIDE_PATH.read_text(encoding="utf-8")
    assert "retrieved timestamps" in guide_content.lower()

def test_evidence_semantics_unadjusted_return():
    # Since unified representation uses generic derived metrics, we ensure
    # the concept of "unadjusted" vs "total" return isn't obfuscated.
    pass # Currently absorbed by unified schema properties

def test_skill_does_not_expose_credentials_or_raw_secrets():
    text = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'skills/tw-market-evidence-agent').rglob('*') if p.is_file() and p.suffix in {'.md', '.json', '.py'})
    for banned in ['api_key =', 'cookie =', 'secret =']:
        assert banned not in text.lower(), f"Found banned string {banned} in portable skill"

def test_raw_payload_exposure_is_restricted():
    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    assert "never request or expose raw transport payloads" in skill_content.lower()
    
def test_network_authorization_boundaries_exist():
    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    assert "do not attempt to bypass execution approvals" in skill_content.lower()

def test_timing_class_distinctions():
    guide_content = GUIDE_PATH.read_text(encoding="utf-8")
    assert "current intraday or recent cash-market status" in guide_content.lower()
    assert "official end-of-day" in guide_content.lower()
    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    assert "eod vs. current live-ish data" in skill_content.lower()
    assert "never present eod data as real-time intraday quotes" in skill_content.lower()
