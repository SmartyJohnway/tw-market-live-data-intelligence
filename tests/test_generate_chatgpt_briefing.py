import json
import os
import pytest
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.generate_chatgpt_briefing import (
    load_json,
    validate_context_pack,
    render_chatgpt_briefing,
    render_failed_sources,
    render_failed_targets
)

@pytest.fixture
def valid_pack():
    return {
        "pack_version": "1.0",
        "generated_at_utc": "2023-10-27T10:00:00Z",
        "generated_at_taipei": "2023-10-27T18:00:00+08:00",
        "generation_mode": "test",
        "source_health_summary": {
            "total_sources": 5,
            "unavailable_or_failed_sources": 0
        },
        "source_authority_summary": {
            "usable_live_sources": ["TWSE_MIS"]
        },
        "target_support_summary": {
            "bounded_watchlist_only": True,
            "full_market_coverage": False,
            "target_count": 10,
            "failed_target_count": 0
        },
        "latest_snapshot_summary": {
            "market_session_status": "open",
            "failed_symbol_count": 0
        },
        "watchlist_observation_summary": {
            "observations_count": 5
        },
        "failed_sources": [],
        "failed_targets": [],
        "freshness_and_delay_summary": {
            "stale_count": 0
        },
        "ai_may_say": ["May describe market."],
        "ai_must_not_claim": ["Must not say buy or sell."],
        "mandatory_caveats": ["Data is delayed."]
    }

def test_missing_input_file():
    with pytest.raises(FileNotFoundError):
        load_json("nonexistent_file.json")

def test_missing_required_section(valid_pack):
    del valid_pack["pack_version"]
    with pytest.raises(ValueError, match="Required top-level section 'pack_version' is missing"):
        validate_context_pack(valid_pack)

def test_generated_briefing_includes_all_headings(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    headings = [
        "## Generated Metadata",
        "## Current Scope",
        "## Source Health",
        "## Source Authority",
        "## Market Session Status",
        "## Latest Snapshot Summary",
        "## Watchlist Observation Summary",
        "## Failed Sources",
        "## Failed Targets",
        "## Freshness / Delay / Staleness",
        "## What AI May Say",
        "## What AI Must Not Claim",
        "## Mandatory Caveats",
        "## Suggested Safe Questions"
    ]
    for h in headings:
        assert h in md

def test_bounded_scope_and_market_coverage(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "Bounded Watchlist Only**: true" in md
    assert "Full market coverage: false" in md

def test_failed_sources_and_targets_counts(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "Failed/Unavailable Source Count: 0" in md
    assert "Failed Target Count**: 0" in md

def test_source_authority_distinctions(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "Usable Live Sources**: TWSE_MIS" in md

def test_freshness_delay_staleness(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "Stale Count**: 0" in md
    assert "Unknown freshness limits interpretation." in md
    assert "EOD reference does not imply live intraday data." in md
    assert "Live candidates are not official realtime" in md

def test_ai_boundaries_inclusion(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "May describe market." in md
    assert "Must not say buy or sell." in md
    assert "Data is delayed." in md

def test_safe_questions(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "Which sources failed in the generated context pack?" in md
    assert "Which target has the strongest signal?" not in md

def test_prohibited_language(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "buy" not in md.lower() or "must not say buy" in md.lower()

def test_failed_sources_table_rendering(valid_pack):
    valid_pack["failed_sources"] = [{
        "source_id": "bad_src",
        "source_type": "api",
        "authority_level": "low",
        "error_type": "timeout",
        "affected_symbol_count": 2,
        "caveats": ["c1", "c2"]
    }]
    table = render_failed_sources(valid_pack)
    assert "| bad_src | api | low | timeout | 2 | c1, c2 |" in table

def test_failed_targets_table_rendering(valid_pack):
    valid_pack["failed_targets"] = [{
        "symbol": "1234",
        "target_class": "stock",
        "failure_reason": "404",
        "source_attempts": ["src1"],
        "caveats": ["c3"]
    }]
    table = render_failed_targets(valid_pack)
    assert "| 1234 | stock | 404 | src1 | c3 |" in table

def test_no_raw_python_lists(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "['" not in md
    assert "']" not in md

def test_no_raw_python_dicts(valid_pack):
    md = render_chatgpt_briefing(valid_pack)
    assert "{'" not in md
    assert "'}" not in md

def test_market_session_dict_rendering(valid_pack):
    valid_pack["latest_snapshot_summary"]["market_session_status"] = {
        "status": "open",
        "as_of_taipei": "2023-10-27T18:00:00+08:00",
        "source": "generator_default",
        "evidence": ["e1", "e2"],
        "caveats": ["c1", "c2"]
    }
    md = render_chatgpt_briefing(valid_pack)
    assert "- Status: open" in md
    assert "- As of Taipei: 2023-10-27T18:00:00+08:00" in md
    assert "- Source: generator_default" in md
    assert "- Evidence: e1, e2" in md
    assert "- c1\n  - c2" in md or "- c1\n- c2" in md

def test_table_cell_escaping(valid_pack):
    valid_pack["failed_sources"] = [{
        "source_id": "src|1",
        "source_type": "api",
        "authority_level": "low",
        "error_type": "err",
        "affected_symbol_count": 0,
        "caveats": ["c1|", "c2"]
    }]
    md = render_chatgpt_briefing(valid_pack)
    assert "src\\|1" in md
    assert "c1\\|, c2" in md

def test_empty_lists_render_none(valid_pack):
    valid_pack["target_support_summary"]["target_classes_observed"] = []
    valid_pack["target_support_summary"]["target_support_caveats"] = []
    md = render_chatgpt_briefing(valid_pack)
    assert "Target Classes Observed**: None" in md
