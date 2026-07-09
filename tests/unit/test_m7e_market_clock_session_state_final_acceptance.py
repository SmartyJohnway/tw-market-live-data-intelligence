import json
import re
from pathlib import Path
from typing import Any

from scripts.m5k_common import build_conversation_context, conversation_context_markdown
from scripts.market_clock_session_state import (
    build_market_clock_session_state,
    promote_market_clock_session_state_for_controlled_context,
)
from tests.unit.test_m7e_market_clock_session_state_context_integration import _watchlist

FINAL_DOC = Path("docs/protocol/M7E_MARKET_CLOCK_SESSION_STATE_FINAL_ACCEPTANCE.md")
INVENTORY = Path("docs/data_capabilities/twse_mis_rich_field_inventory.json")
FORBIDDEN_RAW_KEYS = {
    "raw_payload",
    "twse_mis_rich_facts",
    "raw_rich_facts",
    "raw_unknown_facts",
    "full_ladder",
    "bid_prices",
    "ask_prices",
    "source_investigation_notes",
    "response_sample",
    "raw_fields_sample",
}
POSITIVE_TRADING_PHRASES = [
    "currently rising",
    "currently falling",
    "market is now moving",
    "buy signal",
    "sell signal",
    "recommendation",
    "target price",
    "support",
    "resistance",
    "capital flow",
    "sector rotation",
    "full-market breadth",
]


def _m7e_inventory() -> dict[str, Any]:
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    return inv["rich_observation_contract"]["m7e_market_clock_session_state"]


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        out = set(value)
        for child in value.values():
            out |= _keys(child)
        return out
    if isinstance(value, list):
        out: set[str] = set()
        for child in value:
            out |= _keys(child)
        return out
    return set()


def _assert_market_clock_caveat(context: dict[str, Any]) -> None:
    limitations = context["ai_guidance_summary"]["current_limitations"]
    assert any("M7E indicates latest observation must not be described as current intraday movement" in item for item in limitations)


def test_final_acceptance_doc_exists_and_records_pass_with_caveats():
    text = FINAL_DOC.read_text(encoding="utf-8")
    assert "pass_with_caveats" in text
    assert "bb95c3f47479394c4adf519b8aa7f964d8d76fbc" in text
    for task in ["M7E-00", "M7E-01", "M7E-02", "M7E-03", "M7E-04"]:
        assert task in text
    assert "no live probe" in text
    assert "no TWSE holidaySchedule runtime fetch" in text
    assert "no trading signal/recommendation/target/support/resistance/capital-flow/full-market-breadth claims" in text


def test_inventory_final_closure():
    m7e = _m7e_inventory()
    assert m7e["status"] == "final_acceptance_pass_with_caveats"
    assert m7e["completed_tasks"] == ["M7E-00", "M7E-01", "M7E-02", "M7E-03", "M7E-04"]
    assert m7e["final_acceptance_status"] == "pass_with_caveats"
    assert m7e["final_acceptance_doc"] == str(FINAL_DOC)
    assert m7e["safe_for_ai_context"] is True
    assert m7e["builder_output_safe_for_ai_context"] is False
    assert m7e["controlled_promotion_available"] is True
    assert m7e["shared_context_integration_available"] is True
    assert m7e["holiday_schedule_network_fetch_added"] is False
    assert m7e["holiday_schedule_runtime_fetch_added"] is False
    assert m7e["fastapi_changed"] is False
    assert m7e["mcp_changed"] is False
    assert m7e["frontend_changed"] is False
    assert m7e["next_task"] == "M7F-FRONTEND-OPERATOR-PRESENTATION-AND-CONTEXT-WORKBENCH"


def test_builder_remains_unsafe_and_promoted_context_is_safe():
    candidate = build_market_clock_session_state(
        now_utc="2026-01-05T01:10:00+00:00",
        latest_observation={"retrieved_at_utc": "2026-01-05T01:09:00+00:00"},
    )
    promoted = promote_market_clock_session_state_for_controlled_context(candidate)
    assert candidate["safe_for_ai_context"] is False
    assert candidate["builder_output_safe_for_ai_context"] is False
    assert promoted["safe_for_ai_context"] is True
    assert promoted["builder_output_safe_for_ai_context"] is False
    assert promoted["exposure_status"] == "ai_safe_context_enabled"


def test_malformed_candidate_still_fails_closed():
    promoted = promote_market_clock_session_state_for_controlled_context({"schema_version": "wrong"})
    assert promoted["safe_for_ai_context"] is False
    assert promoted["exposure_status"] == "ai_safe_context_disabled"
    assert promoted["context_status"] == "controlled_context_rejected"


def test_shared_context_contains_promoted_m7e_and_preserves_m7b_m7c_m7d():
    latest = {"schema_version": "latest.v1", "status": "ok", "generated_at_utc": "2026-01-05T01:09:00+00:00", "observations": [{"symbol": "2330", "source": "TWSE_MIS", "status": "ok", "retrieved_at_utc": "2026-01-05T01:09:00+00:00", "price_like_value": 100}]}
    context = build_conversation_context(_watchlist(), latest, now_utc="2026-01-05T01:10:00+00:00")
    for key in ["market_clock_session_state", "ai_safe_market_context_projection", "deterministic_metrics_context", "bounded_watchlist_cross_context", "watchlist_summary", "per_symbol_observations", "latest_observation_summary", "ai_guidance_summary"]:
        assert key in context
    assert context["market_clock_session_state"]["safe_for_ai_context"] is True
    assert context["market_clock_session_state"]["builder_output_safe_for_ai_context"] is False
    assert context["ai_guidance_summary"]["market_clock_session_state"]
    assert context["ai_guidance_summary"]["currentness_language_guardrail"]


def test_no_raw_exposure_in_market_clock_or_markdown():
    latest = {"generated_at_utc": "2026-01-05T01:09:00+00:00", "observations": [{"symbol": "2330", "retrieved_at_utc": "2026-01-05T01:09:00+00:00", "raw_payload": {"x": 1}, "twse_mis_rich_facts": {"x": 1}, "full_ladder": [1], "bid_prices": [1], "ask_prices": [2], "source_investigation_notes": ["x"], "response_sample": {"x": 1}, "raw_fields_sample": {"x": 1}}]}
    context = build_conversation_context(_watchlist(), latest, now_utc="2026-01-05T01:10:00+00:00")
    assert not (FORBIDDEN_RAW_KEYS & _keys(context["market_clock_session_state"]))
    markdown = conversation_context_markdown(context)
    for key in FORBIDDEN_RAW_KEYS:
        assert key not in markdown


def test_markdown_section_remains_safe():
    context = build_conversation_context(_watchlist(), {"generated_at_utc": "2026-01-05T05:44:00+00:00", "observations": []}, now_utc="2026-01-05T05:45:00+00:00")
    markdown = conversation_context_markdown(context)
    for text in ["## Market Clock / Currentness", "Session state:", "Currentness label:", "AI currentness summary:"]:
        assert text in markdown
    for phrase in POSITIVE_TRADING_PHRASES:
        assert not re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", markdown)


def test_weekend_postclose_stale_and_missing_timestamp_guardrails():
    examples = [
        ({"generated_at_utc": "2026-01-05T05:29:00+00:00", "observations": []}, "2026-01-05T05:45:00+00:00"),
        ({"generated_at_utc": "2026-01-03T01:09:00+00:00", "observations": []}, "2026-01-03T01:10:00+00:00"),
        ({"generated_at_utc": "2026-01-05T00:50:00+00:00", "observations": []}, "2026-01-05T01:10:00+00:00"),
        ({"schema_version": "latest.v1", "observations": []}, "2026-01-05T01:10:00+00:00"),
    ]
    for latest, now in examples:
        _assert_market_clock_caveat(build_conversation_context(_watchlist(), latest, now_utc=now))


def test_holiday_heuristic_caveat_remains_when_records_missing():
    context = build_conversation_context(_watchlist(), {"generated_at_utc": "2026-01-05T01:09:00+00:00", "observations": []}, now_utc="2026-01-05T01:10:00+00:00")
    limitations = context["ai_guidance_summary"]["current_limitations"]
    assert any("holiday schedule records missing; weekday heuristic only" in item for item in limitations)
