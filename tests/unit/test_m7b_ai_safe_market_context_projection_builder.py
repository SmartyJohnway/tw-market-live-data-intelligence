import copy
import json
from pathlib import Path

from scripts.observation_contract import (
    attach_ai_safe_market_context_projection_from_observation,
    build_ai_safe_market_context_projection_from_observation,
    normalize_twse_mis_row,
)

ROOT = Path(__file__).resolve().parents[2]
BUILDER_NAME = "build_ai_safe_market_context_projection_from_observation"
ATTACH_NAME = "attach_ai_safe_market_context_projection_from_observation"


def _instrument(symbol="2330", display_symbol="台積電", instrument_type="equity"):
    return {
        "symbol": symbol,
        "display_symbol": display_symbol,
        "instrument_type": instrument_type,
        "market": "TWSE",
        "category_id": "tw_equity" if instrument_type != "index" else "tw_index",
    }


def _regular_row(**updates):
    row = {
        "c": "2330",
        "ch": "2330.tw",
        "n": "台積電",
        "ex": "tse",
        "z": "1000",
        "y": "990",
        "o": "995",
        "h": "1005",
        "l": "980",
        "v": "1234",
        "tv": "5678",
        "b": "999_998_997",
        "g": "10_20_30",
        "a": "1000_1001_1002",
        "f": "11_21_31",
        "u": "1089",
        "w": "891",
        "d": "20260707",
        "t": "13:20:00",
        "tlong": "1793952000000",
        "ts": "0",
        "pz": "-",
        "ps": "-",
    }
    row.update(updates)
    return row


def _obs(row=None, instrument=None):
    return normalize_twse_mis_row(
        row or _regular_row(),
        instrument or _instrument(),
        "2026-07-07T05:20:05Z",
    )


def _projection(row=None, instrument=None):
    return build_ai_safe_market_context_projection_from_observation(_obs(row, instrument))


def test_builder_function_exists_and_does_not_mutate_input():
    observation = _obs()
    original = copy.deepcopy(observation)
    projection = build_ai_safe_market_context_projection_from_observation(observation)
    assert callable(build_ai_safe_market_context_projection_from_observation)
    assert observation == original
    assert projection["projection_status"] == "runtime_projected_candidate"
    assert projection["exposure_status"] == "ai_safe_projection_candidate"
    assert projection["safe_for_ai_context"] is False


def test_regular_security_row_maps_instrument_price_and_depth_contexts():
    projection = _projection()
    assert projection["instrument_context"]["instrument_kind"] == "security"
    assert projection["instrument_context"]["market_mode"] == "regular_board"
    assert projection["instrument_context"]["price_domain"] == "equity_price"
    assert projection["price_snapshot_context"]["last_value_available"] is True
    assert projection["price_snapshot_context"]["direction_vs_previous_close"] == "up"
    depth = projection["displayed_depth_context"]
    assert depth["available"] is True
    assert depth["best_bid_available"] is True
    assert depth["best_ask_available"] is True
    assert depth["full_ladder_exposed"] is False
    assert depth["not_trading_signal"] is True


def test_closing_auction_placeholder_z_preserves_reference_context_without_overrides():
    row = _regular_row(z="-", pz="1001", ps="88", ts="1")
    observation = _obs(row)
    projection = build_ai_safe_market_context_projection_from_observation(observation)
    assert projection["price_snapshot_context"]["last_value_available"] is False
    assert projection["price_snapshot_context"]["last_value"] is None
    assert projection["price_snapshot_context"]["direction_vs_previous_close"] == "unknown"
    assert projection["market_session_context"]["closing_auction_candidate"] is True
    assert projection["reference_context"]["reference_only"] == observation["reference_only"]
    assert projection["reference_context"]["auction_or_reference_price_available"] is True
    assert projection["reference_context"]["auction_or_reference_volume_available"] is True
    assert projection["reference_context"]["pz_does_not_override_last_value"] is True
    assert projection["reference_context"]["ps_does_not_override_current_volume"] is True
    assert projection["safe_for_ai_context"] is False


def test_post_close_security_row_marks_post_close_candidate():
    row = _regular_row(z="1000", tv="5678", pz="1000", ps="5678", ts="0")
    projection = _projection(row)
    assert projection["price_snapshot_context"]["last_value_available"] is True
    assert projection["market_session_context"]["post_close_candidate"] is True
    assert projection["reference_context"]["auction_or_reference_price_available"] is True
    assert projection["reference_context"]["auction_or_reference_volume_available"] is True
    assert projection["safe_for_ai_context"] is False


def test_index_row_maps_index_context_and_disables_depth():
    row = _regular_row(c="t00", ch="t00.tw", i="tidx.tw", n="發行量加權股價指數", ex="tse", m="123456", r="789", b="-", g="-", a="-", f="-")
    projection = _projection(row, _instrument("TAIEX", "TAIEX", "index"))
    assert projection["instrument_context"]["instrument_kind"] == "index"
    assert projection["instrument_context"]["price_domain"] == "index_level"
    assert projection["instrument_context"]["market_mode"] == "index"
    index = projection["index_market_context"]
    assert index["applicable"] is True
    assert index["traded_quantity_candidate_available"] is True
    assert index["trade_count_candidate_available"] is True
    assert index["quantity_unit_verified"] is False
    assert projection["displayed_depth_context"]["available"] is False


def test_malformed_numeric_and_ladder_mismatch_carry_quality_warnings():
    row = _regular_row(z="bad-number", b="999_998", g="10", a="1000_bad", f="11_22_33")
    projection = _projection(row)
    quality = projection["data_quality_context"]
    assert projection["projection_status"] == "runtime_projected_candidate"
    assert quality["malformed_fields"]
    assert quality["ladder_mismatch_flags"]
    assert quality["quality_warnings"]
    assert projection["safe_for_ai_context"] is False


def test_missing_rich_facts_blocks_projection_without_raising():
    observation = {"source": "TWSE_MIS", "symbol": "2330"}
    projection = build_ai_safe_market_context_projection_from_observation(observation)
    assert projection["projection_status"] == "blocked_missing_required_input"
    assert projection["exposure_status"] == "blocked"
    assert projection["safe_for_ai_context"] is False
    assert projection["blocked_reason"] == "missing_twse_mis_rich_facts"


def test_non_twse_mis_source_blocks_projection_without_raising():
    observation = {"source": "YAHOO_FINANCE", "symbol": "2330", "twse_mis_rich_facts": {}}
    projection = build_ai_safe_market_context_projection_from_observation(observation)
    assert projection["projection_status"] == "blocked_missing_required_input"
    assert projection["exposure_status"] == "blocked"
    assert projection["safe_for_ai_context"] is False
    assert projection["blocked_reason"] == "non_twse_mis_source"


def test_attach_projection_helper_is_pure_and_runtime_candidate_not_exposed():
    observation = _obs()
    original = copy.deepcopy(observation)
    attached = attach_ai_safe_market_context_projection_from_observation(observation)
    assert observation == original
    assert attached is not observation
    assert attached["ai_safe_market_context_projection"]["exposure_status"] == "ai_safe_projection_candidate"
    assert attached["ai_safe_market_context_projection"]["safe_for_ai_context"] is False


def test_projection_serialized_json_has_no_positive_forbidden_language_or_unsafe_keys():
    projection = _projection()
    text = json.dumps(projection, ensure_ascii=False).lower()
    for phrase in [
        "buy opportunity",
        "sell pressure",
        "support level",
        "resistance level",
        "target price estimate",
        "main force accumulation",
        "liquidity signal",
        "confirmed trend",
        "realtime feed",
        "official api definition validated",
        "verified quantity unit available",
    ]:
        assert phrase not in text
    without_allowed_blocklist = dict(projection)
    without_allowed_blocklist.pop("blocked_interpretations", None)
    key_text = json.dumps(without_allowed_blocklist, ensure_ascii=False).lower()
    for key in [
        "recommendation",
        "buy_sell_hold",
        "target_price_estimate",
        "support_level",
        "resistance_level",
        "liquidity_signal",
        "main_force",
    ]:
        assert f'"{key}"' not in key_text


def test_full_ladder_arrays_are_not_exposed_but_blocked_interpretations_remain():
    projection = _projection()
    text = json.dumps(projection, ensure_ascii=False)
    for forbidden_key in ["bid_prices", "ask_prices", "bid_quantities_raw", "ask_quantities_raw"]:
        assert forbidden_key not in text
    blocked = set(projection["blocked_interpretations"])
    assert {"buy_signal", "target_price", "support_resistance", "true_liquidity"}.issubset(blocked)


def test_runtime_projection_builder_reference_remains_controlled_to_conversation_context():
    checked_roots = ["server", "frontend", "scripts"]
    references = []
    allowed = {
        "scripts/observation_contract.py",
        "scripts/m5k_common.py",
        "tests/unit/test_m7b_ai_safe_market_context_projection_builder.py",
        "tests/unit/test_m7b_ai_safe_market_context_controlled_exposure.py",
    }
    for root in checked_roots:
        base = ROOT / root
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            rel = str(path.relative_to(ROOT))
            if rel in allowed:
                continue
            text = path.read_text(encoding="utf-8")
            if BUILDER_NAME in text or ATTACH_NAME in text:
                references.append(rel)
    assert references == []
