import pytest
from datetime import datetime, timezone, timedelta
from scripts.m8r_03d_watchlist_source_integration import (
    parse_iso_datetime,
    evaluate_evidence_currentness,
    normalize_twse_mis_watchlist_observation
)

def test_parse_iso_datetime_tz_aware():
    # 1. UTC Z 結尾
    dt1 = parse_iso_datetime("2026-07-16T03:00:00Z")
    assert dt1.tzinfo == timezone.utc
    assert dt1.hour == 3
    
    # 2. 台北時區 +08:00
    dt2 = parse_iso_datetime("2026-07-16T11:00:00+08:00")
    assert dt2.tzinfo is not None
    # 轉換為 UTC 比較
    assert dt2.astimezone(timezone.utc) == dt1
    
    # 3. 帶毫秒和時區
    dt3 = parse_iso_datetime("2026-07-16T03:00:00.123456Z")
    assert dt3.second == 0
    assert dt3.tzinfo == timezone.utc
    
    # 4. 沒有時區資訊 -> 預設為 UTC
    dt4 = parse_iso_datetime("2026-07-16T03:00:00")
    assert dt4.tzinfo == timezone.utc

def test_currentness_fresh_liveish():
    # 差值在 900 秒內
    res = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str="2026-07-16T02:55:00Z",
        retrieved_at_str="2026-07-16T02:55:10Z",
        timing_class="liveish_intraday_snapshot",
        max_age_seconds=900.0
    )
    assert res["status"] == "fresh"
    assert res["age_seconds"] == 300.0
    assert res["transport_latency_seconds"] == 10.0

def test_currentness_stale_liveish():
    # 差值超過 900 秒
    res = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str="2026-07-16T02:00:00Z",
        retrieved_at_str="2026-07-16T02:00:10Z",
        timing_class="liveish_intraday_snapshot",
        max_age_seconds=900.0
    )
    assert res["status"] == "stale"
    assert "evidence_age_exceeds_max_limit" in res["reason"]
    assert res["age_seconds"] == 3600.0

def test_currentness_future_timestamp():
    # 來源時間在 reference clock 之後（來自未來）
    res = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str="2026-07-16T04:00:00Z",
        retrieved_at_str="2026-07-16T04:00:05Z",
        timing_class="liveish_intraday_snapshot"
    )
    assert res["status"] == "unresolved"
    assert res["reason"] == "evidence_timestamp_in_future"

def test_currentness_missing_inputs():
    # 缺失 reference clock
    res1 = evaluate_evidence_currentness(
        reference_clock_str=None,
        source_timestamp_str="2026-07-16T03:00:00Z",
        retrieved_at_str="2026-07-16T03:00:00Z",
        timing_class="liveish_intraday_snapshot"
    )
    assert res1["status"] == "unresolved"
    assert res1["reason"] == "missing_reference_clock"
    
    # 缺失 evidence timestamp 且無 retrieved_at 可 fallback
    res2 = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str=None,
        retrieved_at_str=None,
        timing_class="liveish_intraday_snapshot"
    )
    assert res2["status"] == "unresolved"
    assert res2["reason"] == "missing_evidence_timestamp"

def test_currentness_retrieved_at_fallback():
    # 缺失 source_timestamp 時，使用 retrieved_at 作為 fallback 評估 age
    res = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str=None,
        retrieved_at_str="2026-07-16T02:50:00Z",
        timing_class="liveish_intraday_snapshot",
        max_age_seconds=900.0
    )
    assert res["status"] == "fresh"
    assert res["age_seconds"] == 600.0
    assert "transport_latency_seconds" not in res  # 因為無 source_timestamp 無法計算 latency

def test_currentness_timezone_offset_equivalence():
    # 驗證 UTC Z 與 台北 +08:00 偏移量在 age 計算上等價且無漂移
    res = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str="2026-07-16T11:00:00+08:00",
        retrieved_at_str="2026-07-16T11:00:00+08:00",
        timing_class="liveish_intraday_snapshot"
    )
    assert res["status"] == "fresh"
    assert res["age_seconds"] == 0.0

def test_currentness_invalid_tz_fallback():
    # 無效時間格式返回 unresolved
    res = evaluate_evidence_currentness(
        reference_clock_str="invalid-format-string",
        source_timestamp_str="2026-07-16T03:00:00Z",
        retrieved_at_str="2026-07-16T03:00:00Z",
        timing_class="liveish_intraday_snapshot"
    )
    assert res["status"] == "unresolved"

def test_currentness_official_eod():
    # 1. 正常的 EOD (小於 3 天門檻 259200 秒)
    # trade_date = "2026-07-15" (台北收盤 13:30 = UTC 05:30Z)
    # reference clock = "2026-07-16T03:00:00Z" (UTC)
    # age = 2026-07-16T03:00:00Z - 2026-07-15T05:30:00Z = 21.5 小時 (77400 秒)
    res1 = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str=None,
        retrieved_at_str="2026-07-16T00:00:00Z",
        timing_class="official_eod",
        trade_date="2026-07-15"
    )
    assert res1["status"] == "official_completed_eod"
    assert res1["age_seconds"] == 77400.0
    
    # 2. 過期的 EOD (大於 3 天門檻)
    # trade_date = "2026-07-10" -> "2026-07-10T05:30:00Z"
    # reference clock = "2026-07-16T03:00:00Z" -> 差了 6 天 (大於 259200 秒)
    res2 = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str=None,
        retrieved_at_str="2026-07-16T00:00:00Z",
        timing_class="official_eod",
        trade_date="2026-07-10"
    )
    assert res2["status"] == "stale"
    assert res2["reason"] == "eod_older_than_three_days"

def test_currentness_official_eod_missing_date():
    # 缺失 trade date 返回 unresolved
    res = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str=None,
        retrieved_at_str="2026-07-16T00:00:00Z",
        timing_class="official_eod",
        trade_date=None
    )
    assert res["status"] == "unresolved"
    assert res["reason"] == "missing_trade_date"

def test_currentness_unknown_timing_class_fails_closed():
    res = evaluate_evidence_currentness(
        reference_clock_str="2026-07-16T03:00:00Z",
        source_timestamp_str="2026-07-16T02:59:00Z",
        retrieved_at_str="2026-07-16T02:59:10Z",
        timing_class="unknown_timing_class"
    )
    assert res["status"] == "unresolved"
    assert res["reason"] == "unsupported_timing_class:unknown_timing_class"

def test_normalizer_preserves_actual_retrieval_time():
    plan_target = {
        "target_id": "TWSE:2330",
        "requested_identity": {"symbol": "2330", "market": "TWSE"},
        "resolved_identity": {"symbol": "2330", "market": "TWSE", "name": "台積電", "instrument_type": "equity"}
    }
    source_obs = {
        "symbol": "2330",
        "market": "tse",
        "source_timestamp": "2026-07-15T02:59:50Z",
        "retrieved_at_utc": "2026-07-15T03:00:00Z",
        "price": 950.0,
        "volume": 10000
    }
    obs = normalize_twse_mis_watchlist_observation(
        source_obs=source_obs,
        plan_target=plan_target,
        reference_clock_utc="2026-07-16T03:00:00Z"
    )
    # 驗證真實時點保留
    assert obs["retrieved_at_utc"] == "2026-07-15T03:00:00Z"
    assert obs["currentness"]["status"] == "stale"
    assert obs["currentness"]["age_seconds"] == 86410.0
    assert obs["currentness"]["transport_latency_seconds"] == 10.0

