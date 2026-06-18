import os
import pytest

DOCS_DIR = os.path.join(os.path.dirname(__file__), '../../docs')
PROTOCOL_FILE = os.path.join(DOCS_DIR, 'protocol', 'TWSE_MIS_PROTOCOL.md')
FIELD_DICT_FILE = os.path.join(DOCS_DIR, 'protocol', 'TWSE_MIS_FIELD_DICTIONARY.md')

def test_protocol_doc_exists_and_contains_safety_phrases():
    assert os.path.exists(PROTOCOL_FILE), "TWSE_MIS_PROTOCOL.md does not exist"

    with open(PROTOCOL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    content_lower = content.lower()

    # Check for required safety phrases
    assert "unofficial" in content_lower, "Protocol doc must mention it is unofficial"
    assert "not an officially documented" in content_lower or "not an official" in content_lower, "Protocol doc must clarify it is not an official API"
    assert "low-frequency" in content_lower, "Protocol doc must mention low-frequency usage"
    assert "high-frequency" in content_lower and ("unsuitable" in content_lower or "prohibit" in content_lower), "Protocol doc must prohibit high-frequency usage"
    assert "risk" in content_lower, "Protocol doc must discuss risks"

def test_field_dictionary_contains_required_fields():
    assert os.path.exists(FIELD_DICT_FILE), "TWSE_MIS_FIELD_DICTIONARY.md does not exist"

    with open(FIELD_DICT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # List of required raw fields that must be documented
    required_fields = ['c', 'n', 'ex', 'ch', 'z', 'y', 'o', 'h', 'l', 'v', 'tv', 'a', 'f', 'b', 'g', 'u', 'w', 'd', 't', 'tlong', 'queryTime', 'userDelay', 'cachedAlive']

    for field in required_fields:
        # Looking for `field` in the markdown table structure
        assert f"`{field}`" in content, f"Required field `{field}` is missing from the Field Dictionary"

def test_field_dictionary_contains_caveats():
    with open(FIELD_DICT_FILE, 'r', encoding='utf-8') as f:
        content = f.read().lower()

    assert "observed" in content, "Field Dictionary must mention it is an observed contract"
    assert "intraday" in content and "post-market" in content, "Field Dictionary must mention intraday vs post-market behavior"
    assert "official" in content and ("not an official" in content or "not official" in content), "Field Dictionary must state it is not an official API"

def test_no_claims_of_official_api():
    # Double check that we don't accidentally claim it IS an official API
    with open(PROTOCOL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "is an official API" not in content, "Protocol doc must not claim TWSE MIS is an official API"

    with open(FIELD_DICT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "is an official API" not in content, "Field Dictionary must not claim TWSE MIS is an official API"
