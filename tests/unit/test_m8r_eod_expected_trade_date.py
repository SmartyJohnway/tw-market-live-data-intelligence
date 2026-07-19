import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from scripts.m8r_eod_expected_trade_date import determine_expected_eod_session_status

TAIPEI = ZoneInfo("Asia/Taipei")

# Helper to generate a dummy calendar
def get_dummy_calendar(holidays=None):
    # holidays is a list of "YYYY-MM-DD"
    holidays = set(holidays or [])
    dates = []
    # Populate a year of dates around July 2026
    start_date = datetime(2026, 1, 1)
    for i in range(365):
        d = start_date + timedelta(days=i)
        d_str = d.date().isoformat()
        is_weekend = d.weekday() >= 5
        is_holiday = d_str in holidays
        is_trading = not (is_weekend or is_holiday)
        dates.append({
            "date": d_str,
            "is_weekend": is_weekend,
            "is_trading_day": is_trading,
            "trading_day_status": "trading_day" if is_trading else "non_trading_day",
            "reason": "weekend" if is_weekend else ("official_holiday" if is_holiday else "regular_weekday")
        })
    return {"schema_version": "twse_trading_calendar.v1", "market": "TWSE", "dates": dates}

from datetime import timedelta

# A. 普通交易日盤前
def test_matrix_a_monday_pre_market():
    # Monday 2026-07-20 at 08:00 AM Taipei
    ref = datetime(2026, 7, 20, 8, 0, 0, tzinfo=TAIPEI)
    # expected latest trade date should be last Friday: 2026-07-17
    # actual is last Friday
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-17"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-17"
    assert res["currentness_status"] == "official_previous_session_eod_before_close"

# B. 普通交易日盤中
def test_matrix_b_mid_market():
    # Tuesday 2026-07-21 at 11:00 AM Taipei
    ref = datetime(2026, 7, 21, 11, 0, 0, tzinfo=TAIPEI)
    # expected latest is yesterday (2026-07-20), actual is yesterday
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-20"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-20"
    assert res["currentness_status"] == "official_previous_session_eod_before_close"

# C. 收盤後已更新
def test_matrix_c_post_market_updated():
    # Tuesday 2026-07-21 at 16:00 Taipei (after close and after grace)
    ref = datetime(2026, 7, 21, 16, 0, 0, tzinfo=TAIPEI)
    # expected latest is today, actual is today
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-21"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-21"
    assert res["currentness_status"] == "official_latest_completed_eod"

# D. 收盤後grace內未更新
def test_matrix_d_post_market_within_grace_not_updated():
    # Tuesday 2026-07-21 at 13:50 Taipei (close at 13:30, grace 60 mins -> expires 14:30)
    ref = datetime(2026, 7, 21, 13, 50, 0, tzinfo=TAIPEI)
    # expected latest is today 2026-07-21, actual is yesterday 2026-07-20
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-20"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-21"
    assert res["currentness_status"] == "not_yet_published_after_close"
    assert res["publication_grace_applied"] is True

# E. 收盤後超過grace仍未更新
def test_matrix_e_post_market_after_grace_not_updated():
    # Tuesday 2026-07-21 at 15:00 Taipei (grace ended at 14:30)
    ref = datetime(2026, 7, 21, 15, 0, 0, tzinfo=TAIPEI)
    # expected latest is today 2026-07-21, actual is yesterday 2026-07-20
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-20"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-21"
    assert res["currentness_status"] == "unexpected_stale_eod"
    assert res["publication_grace_applied"] is False

# F. 週末
def test_matrix_f_weekend():
    # Saturday 2026-07-18 at 16:00 Taipei
    ref = datetime(2026, 7, 18, 16, 0, 0, tzinfo=TAIPEI)
    # expected latest is Friday 2026-07-17, actual is Friday
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-17"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-17"
    assert res["session_status"] == "weekend"
    assert res["currentness_status"] == "official_latest_completed_eod"

# G. 官方例行休市日
def test_matrix_g_official_holiday():
    # Suppose 2026-07-15 is an official holiday
    cal = get_dummy_calendar(holidays=["2026-07-15"])
    # Reference clock is holiday date 2026-07-15
    ref = datetime(2026, 7, 15, 16, 0, 0, tzinfo=TAIPEI)
    # expected latest is Tuesday 2026-07-14, actual is 2026-07-14
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-14"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-14"
    assert res["session_status"] == "official_holiday"
    assert res["currentness_status"] == "official_latest_completed_eod"

# H. 台北市全日停班
def test_matrix_h_taipei_full_day_closure():
    # Tuesday 2026-07-21, full day closure event
    ev = {
        "status": "Actual",
        "area_name": "臺北市",
        "area_level": "municipality",
        "work_status": "closed",
        "decision_status": "closure_confirmed",
        "closure_scope": "full_day",
        "target_date": "2026-07-21"
    }
    # Reference clock is 2026-07-21 16:00
    ref = datetime(2026, 7, 21, 16, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[ev],
        actual_trade_date="2026-07-20"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-20"
    assert res["session_status"] == "market_closed_no_session"
    assert res["currentness_status"] == "official_latest_completed_eod"

# I. 台北市上午停班
def test_matrix_i_taipei_morning_closure():
    # Tuesday 2026-07-21, morning closure event -> entire day is closed
    ev = {
        "status": "Actual",
        "area_name": "台北市",
        "area_level": "municipality",
        "work_status": "closed",
        "decision_status": "closure_confirmed",
        "closure_scope": "morning",
        "target_date": "2026-07-21"
    }
    ref = datetime(2026, 7, 21, 16, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[ev],
        actual_trade_date="2026-07-20"
    )
    assert res["expected_latest_completed_trade_date"] == "2026-07-20"
    assert res["session_status"] == "market_closed_no_session"
    assert res["currentness_status"] == "official_latest_completed_eod"

# J. 台北市下午停班
def test_matrix_j_taipei_afternoon_closure():
    # Tuesday 2026-07-21, afternoon closure event -> session remains valid
    ev = {
        "status": "Actual",
        "area_name": "臺北市",
        "area_level": "municipality",
        "work_status": "closed",
        "decision_status": "closure_confirmed",
        "closure_scope": "afternoon",
        "target_date": "2026-07-21"
    }
    ref = datetime(2026, 7, 21, 16, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[ev],
        actual_trade_date="2026-07-21"
    )
    # Since session remains valid, expected is today 2026-07-21, actual 2026-07-21 -> current!
    assert res["expected_latest_completed_trade_date"] == "2026-07-21"
    assert res["session_status"] == "regular_trading_day"
    assert res["currentness_status"] == "official_latest_completed_eod"

# K. Closure unresolved
def test_matrix_k_closure_unresolved():
    ref = datetime(2026, 7, 21, 16, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    # closure_status is None (unresolved)
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=None,
        actual_trade_date="2026-07-21"
    )
    assert res["fallback_policy_used"] is True
    assert res["fallback_policy"] == "provisional_bounded_age"
    assert res["currentness_status"] == "calendar_status_unresolved"

# L. Future trade date
def test_matrix_l_future_trade_date():
    ref = datetime(2026, 7, 21, 16, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    # actual is tomorrow's date!
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-22"
    )
    assert res["currentness_status"] == "future_trade_date_invalid"

# M. Cross-market
def test_matrix_m_cross_market():
    # Test different close times
    # Friday 2026-07-17 at 13:40 Taipei
    # For TWSE/TPEX, close is 13:30. At 13:40, today's session is completed! Expected should be 2026-07-17.
    ref = datetime(2026, 7, 17, 13, 40, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    
    twse_res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-17"
    )
    assert twse_res["expected_latest_completed_trade_date"] == "2026-07-17"
    
    # For TAIFEX, close is 13:45. At 13:40, today's session is NOT yet completed!
    # Expected should be yesterday (2026-07-16)
    taifex_res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TAIFEX",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-16"
    )
    assert taifex_res["expected_latest_completed_trade_date"] == "2026-07-16"

# Test schema validation helper
def test_json_schema_validation():
    import json
    import jsonschema
    from pathlib import Path
    
    schema_path = Path("schemas/m8r_eod_expected_trade_date_status.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    
    ref = datetime(2026, 7, 21, 16, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=[],
        actual_trade_date="2026-07-21"
    )
    # validate structure
    jsonschema.validate(instance=res, schema=schema)

def test_unresolved_inputs_pre_market_and_mid_market():
    # Pre-market (Monday 8:00 AM) with closure_status as None (unresolved)
    ref = datetime(2026, 7, 20, 8, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    res_pre = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=None,
        actual_trade_date="2026-07-17"
    )
    assert res_pre["fallback_policy_used"] is True
    assert res_pre["currentness_status"] == "calendar_status_unresolved"
    assert res_pre["provisional_candidate_status"] == "official_previous_session_eod_before_close"

    # Mid-market (Tuesday 11:00 AM) with closure_status as None (unresolved)
    ref = datetime(2026, 7, 21, 11, 0, 0, tzinfo=TAIPEI)
    res_mid = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=None,
        actual_trade_date="2026-07-20"
    )
    assert res_mid["fallback_policy_used"] is True
    assert res_mid["currentness_status"] == "calendar_status_unresolved"
    assert res_mid["provisional_candidate_status"] == "official_previous_session_eod_before_close"

def test_invalid_actual_trade_date_formats():
    ref = datetime(2026, 7, 21, 16, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    for bad_fmt in ["2026-7-2", "20260721", "garbage", "", "   "]:
        res = determine_expected_eod_session_status(
            reference_time_utc=ref,
            market="TWSE",
            official_calendar=cal,
            closure_status=[],
            actual_trade_date=bad_fmt
        )
        assert res["currentness_status"] == "invalid_trade_date_format"


# Blocker 2: TAIFEX Taipei closure rule isolation tests
# TAIFEX must NOT apply market_closed_no_session when Taipei work suspension exists.
# Instead, closure_src should end with 'unresolved', triggering fallback_policy_used=True.

def _taipei_full_day_closure(target_date_str: str) -> list:
    return [{
        "status": "Actual",
        "area_name": "臺北市",
        "area_level": "municipality",
        "work_status": "closed",
        "decision_status": "closure_confirmed",
        "target_date": target_date_str,
        "closure_scope": "full_day"
    }]

def _taipei_morning_closure(target_date_str: str) -> list:
    return [{
        "status": "Actual",
        "area_name": "臺北市",
        "area_level": "municipality",
        "work_status": "closed",
        "decision_status": "closure_confirmed",
        "target_date": target_date_str,
        "closure_scope": "morning"
    }]

def test_taifex_taipei_full_day_closure_does_not_produce_market_closed():
    """TAIFEX + Taipei full-day closure must NOT yield market_closed_no_session.
    Authority for applying Taipei closure to TAIFEX is provisional_unresolved.
    Expected: fallback_policy_used=True, status=calendar_status_unresolved.
    """
    # 2026-07-21 Tuesday mid-market — TAIFEX would normally be open
    ref = datetime(2026, 7, 21, 11, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    closure = _taipei_full_day_closure("2026-07-21")

    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TAIFEX",
        official_calendar=cal,
        closure_status=closure,
        actual_trade_date="2026-07-20"
    )
    # Must NOT be market_closed_no_session
    assert res["session_status"] != "market_closed_no_session", (
        "TAIFEX must not inherit Taipei closure rule without official authority"
    )
    # Closure authority is unresolved → fail-closed → fallback_policy_used
    assert res["fallback_policy_used"] is True
    assert res["currentness_status"] == "calendar_status_unresolved"
    # Caveats must mention the unresolved authority
    assert any("provisional_unresolved" in c for c in res.get("caveats", []))


def test_taifex_taipei_morning_closure_does_not_produce_market_closed():
    """TAIFEX + Taipei morning closure must NOT yield market_closed_no_session."""
    ref = datetime(2026, 7, 21, 11, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    closure = _taipei_morning_closure("2026-07-21")

    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TAIFEX",
        official_calendar=cal,
        closure_status=closure,
        actual_trade_date="2026-07-20"
    )
    assert res["session_status"] != "market_closed_no_session"
    assert res["fallback_policy_used"] is True
    assert res["currentness_status"] == "calendar_status_unresolved"


def test_twse_taipei_full_day_closure_produces_market_closed():
    """TWSE + Taipei full-day closure MUST yield market_closed_no_session.
    Taipei closure authority for TWSE is 'enabled'.
    """
    ref = datetime(2026, 7, 21, 11, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    closure = _taipei_full_day_closure("2026-07-21")

    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TWSE",
        official_calendar=cal,
        closure_status=closure,
        actual_trade_date="2026-07-21"
    )
    assert res["session_status"] == "market_closed_no_session"
    assert res["fallback_policy_used"] is False


def test_tpex_taipei_full_day_closure_applies_with_caveat():
    """TPEX + Taipei full-day closure MUST yield market_closed_no_session.
    TPEX closure authority is 'enabled_synchronized'; a synchronized-market caveat
    must appear in caveats.
    """
    ref = datetime(2026, 7, 21, 11, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    closure = _taipei_full_day_closure("2026-07-21")

    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TPEX",
        official_calendar=cal,
        closure_status=closure,
        actual_trade_date="2026-07-21"
    )
    assert res["session_status"] == "market_closed_no_session"
    assert res["fallback_policy_used"] is False
    assert any("synchronized" in c.lower() for c in res.get("caveats", []))

def test_taifex_prior_date_taipei_closure_does_not_skip_trading_day():
    """TAIFEX backward traversal must not apply Taipei closure rule.
    If the prior day was a Taipei full-day closure, it should NOT be skipped as a non-trading day for TAIFEX.
    Expected: the expected_latest_completed_trade_date will resolve to that prior date (2026-07-20).
    """
    # 2026-07-21 08:00 (Pre-market). Ref date is 21st.
    ref = datetime(2026, 7, 21, 8, 0, 0, tzinfo=TAIPEI)
    cal = get_dummy_calendar()
    # 2026-07-20 (Yesterday) had a Taipei full day closure
    closure = _taipei_full_day_closure("2026-07-20")

    res = determine_expected_eod_session_status(
        reference_time_utc=ref,
        market="TAIFEX",
        official_calendar=cal,
        closure_status=closure,
        actual_trade_date="2026-07-17"  # actual is trailing
    )
    # The expected trade date should be 2026-07-20 since TAIFEX doesn't skip it.
    assert res["expected_latest_completed_trade_date"] == "2026-07-20"

