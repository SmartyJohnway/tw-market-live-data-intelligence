"""M8R EOD Expected Trade Date and Session Status Evaluator."""
from __future__ import annotations
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Any

TAIPEI = ZoneInfo("Asia/Taipei")

MARKET_SESSION_POLICIES = {
    "TWSE": {"market_close_time": "13:30", "publication_grace_period_minutes": 60},
    "TPEX": {"market_close_time": "13:30", "publication_grace_period_minutes": 60},
    "TAIFEX": {"market_close_time": "13:45", "publication_grace_period_minutes": 60},
}

def parse_taipei_datetime(val: str | datetime) -> datetime:
    """Parse input into timezone-aware Asia/Taipei datetime, failing closed on naive datetimes."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            raise ValueError("Naive datetime is forbidden; must be timezone-aware.")
        return val.astimezone(TAIPEI)
    
    if not isinstance(val, str) or not val.strip():
        raise ValueError("Invalid datetime string input.")
        
    s = val.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO datetime string format: {exc}")
        
    if dt.tzinfo is None:
        raise ValueError("Naive datetime string is forbidden; must provide timezone offset (e.g. Z or +08:00).")
    return dt.astimezone(TAIPEI)

def _is_taipei_closure_event(ev: dict, target_date_str: str) -> bool:
    """Check if an event is a valid Taipei city work-closure event for target_date."""
    if not isinstance(ev, dict):
        return False
    is_actual = ev.get("status") == "Actual"
    is_taipei = ev.get("area_name") in {"臺北市", "台北市"}
    is_mun = ev.get("area_level") == "municipality"
    is_closed = ev.get("work_status") == "closed"
    is_confirmed = ev.get("decision_status") in {"closure_confirmed", "criteria_met"}
    date_matches = ev.get("target_date") == target_date_str
    return is_actual and is_taipei and is_mun and is_closed and is_confirmed and date_matches

def get_taipei_closure_scope(closure_events: list | None, target_date_str: str) -> str:
    """Extract Taipei City work closure scope for a target date.
    
    Returns "none", "full_day", "morning", "afternoon", or "unresolved".
    """
    if closure_events is None:
        return "unresolved"
    
    matches = [e for e in closure_events if _is_taipei_closure_event(e, target_date_str)]
    if not matches:
        return "none"
        
    scopes = {e.get("closure_scope") for e in matches if e.get("closure_scope")}
    if "full_day" in scopes:
        return "full_day"
    if "morning" in scopes:
        return "morning"
    if "afternoon" in scopes:
        return "afternoon"
    return "none"

def determine_expected_eod_session_status(
    *,
    reference_time_utc: str | datetime,
    market: str,
    official_calendar: dict | None = None,
    closure_status: list | None = None,
    market_close_time: str | None = None,
    publication_grace_period: int | None = None,
    actual_trade_date: str | None = None,
    exchange_session_override: list | None = None
) -> dict:
    """Pure function to determine EOD expected trade date and session status.
    
    All evaluations are conducted in Asia/Taipei timezone.
    """
    if market not in {"TWSE", "TPEX", "TAIFEX"}:
        raise ValueError(f"Unsupported market: {market}")
        
    # Early actual_trade_date YYYY-MM-DD validation
    actual_date = None
    invalid_format = False
    if actual_trade_date is not None:
        s_trade = str(actual_trade_date).strip()
        # Enforce strict 10-character YYYY-MM-DD pattern validation to override loose Python 3.11+ parses
        if len(s_trade) != 10 or s_trade[4] != '-' or s_trade[7] != '-':
            invalid_format = True
        else:
            try:
                actual_date = date.fromisoformat(s_trade)
            except ValueError:
                invalid_format = True

    # Step 1: Parse reference clock
    ref_tz = parse_taipei_datetime(reference_time_utc)
    ref_local_date = ref_tz.date()
    ref_local_time = ref_tz.time()
    
    # Setup policy defaults
    policy = MARKET_SESSION_POLICIES[market]
    c_time_str = market_close_time or policy["market_close_time"]
    grace_min = publication_grace_period if publication_grace_period is not None else policy["publication_grace_period_minutes"]
    
    c_time = time.fromisoformat(c_time_str)
    
    def is_overridden_closed(d_str: str) -> bool:
        return d_str in set(exchange_session_override or [])
        
    def resolve_date_session_type(d: date) -> tuple[str, bool, str]:
        """Returns (session_status, is_trading_day, calendar_source)"""
        d_str = d.isoformat()
        
        if is_overridden_closed(d_str):
            return "market_closed_no_session", False, "exchange_override"
            
        if official_calendar is None:
            is_weekend = d.weekday() >= 5
            status = "weekend" if is_weekend else "regular_trading_day"
            return status, not is_weekend, "heuristic_unresolved"
            
        dates = official_calendar.get("dates", [])
        for entry in dates:
            if isinstance(entry, dict) and entry.get("date") == d_str:
                is_trading = entry.get("is_trading_day") is True
                reason = entry.get("reason", "")
                if is_trading:
                    status = "regular_trading_day"
                else:
                    if "weekend" in reason.lower() or entry.get("is_weekend") is True:
                        status = "weekend"
                    else:
                        status = "official_holiday"
                return status, is_trading, "official_calendar_artifact"
                
        return "calendar_status_unresolved", False, "official_calendar_artifact_missing_date"

    # Step 2 & 3: Evaluate current reference date
    sess_status, is_trading_day, cal_source = resolve_date_session_type(ref_local_date)
    
    tpe_closure = get_taipei_closure_scope(closure_status, ref_local_date.isoformat())
    closure_src = "none_detected"
    
    if tpe_closure == "unresolved":
        closure_src = "unresolved"
    elif tpe_closure in {"full_day", "morning"}:
        sess_status = "market_closed_no_session"
        is_trading_day = False
        closure_src = "NCDR_DGPA_CLOSURE_CAP"
    elif tpe_closure == "afternoon":
        closure_src = "NCDR_DGPA_CLOSURE_CAP"
    
    # Check if today's session has completed
    today_completed = False
    if is_trading_day and sess_status not in {"calendar_status_unresolved", "market_closed_no_session"}:
        if ref_local_time >= c_time:
            today_completed = True

    # Search backwards for the latest completed trade date
    expected_date = None
    if today_completed:
        expected_date = ref_local_date
    else:
        found_date = None
        cur_date = ref_local_date - timedelta(days=1)
        for _ in range(365):
            cur_status, cur_trading, _ = resolve_date_session_type(cur_date)
            cur_closure = get_taipei_closure_scope(closure_status, cur_date.isoformat())
            if cur_closure in {"full_day", "morning"}:
                cur_trading = False
            if cur_trading and cur_status not in {"calendar_status_unresolved", "market_closed_no_session"}:
                found_date = cur_date
                break
            cur_date -= timedelta(days=1)
        expected_date = found_date

    expected_date_str = expected_date.isoformat() if expected_date else None

    # Step 5: Resolve currentness and fallback flags
    fallback_policy_used = False
    fallback_policy = None
    caveats = []
    
    # Declare TAIFEX provisional day session policy warning (Blocker 5)
    if market == "TAIFEX":
        caveats.append("TAIFEX is bound by provisional day-session policy only. Night sessions or complex derivatives settlement schedules are not fully evaluated.")
    
    if official_calendar is None or cal_source.endswith("unresolved") or closure_src == "unresolved":
        fallback_policy_used = True
        fallback_policy = "provisional_bounded_age"
        caveats.append("calendar/closure unresolved; falling back to provisional bounded-age policy.")
        
    publication_grace_applied = False
    
    if actual_trade_date is None:
        currentness_status = "source_trade_date_missing"
    elif invalid_format:
        currentness_status = "invalid_trade_date_format"
    else:
        if expected_date and actual_date > expected_date:
            currentness_status = "future_trade_date_invalid"
        elif expected_date and actual_date == expected_date:
            if is_trading_day and not today_completed:
                currentness_status = "official_previous_session_eod_before_close"
            else:
                currentness_status = "official_latest_completed_eod"
        else:
            # Check for publication grace or stale
            if expected_date:
                is_today_expected = (expected_date == ref_local_date)
                if is_today_expected:
                    grace_time = (datetime.combine(ref_local_date, c_time) + timedelta(minutes=grace_min)).time()
                    if c_time <= ref_local_time < grace_time:
                        prev_date = None
                        cur_date = ref_local_date - timedelta(days=1)
                        for _ in range(365):
                            cur_status, cur_trading, _ = resolve_date_session_type(cur_date)
                            cur_closure = get_taipei_closure_scope(closure_status, cur_date.isoformat())
                            if cur_closure in {"full_day", "morning"}:
                                cur_trading = False
                            if cur_trading and cur_status not in {"calendar_status_unresolved", "market_closed_no_session"}:
                                prev_date = cur_date
                                break
                            cur_date -= timedelta(days=1)
                        
                        if actual_date and prev_date and actual_date == prev_date:
                            currentness_status = "not_yet_published_after_close"
                            publication_grace_applied = True
                        else:
                            currentness_status = "unexpected_stale_eod"
                    else:
                        currentness_status = "unexpected_stale_eod"
                else:
                    currentness_status = "unexpected_stale_eod"
            else:
                eff_dt = datetime.combine(actual_date, c_time, tzinfo=TAIPEI)
                age_sec = (ref_tz - eff_dt).total_seconds()
                if age_sec < 0:
                    currentness_status = "future_trade_date_invalid"
                elif age_sec <= 259200.0:
                    currentness_status = "calendar_status_unresolved"
                else:
                    currentness_status = "unexpected_stale_eod"

    # Fail-closed on unresolved logic (Blocker 2)
    provisional_candidate_status = None
    if fallback_policy_used:
        if currentness_status not in {"future_trade_date_invalid", "source_trade_date_missing", "invalid_trade_date_format"}:
            provisional_candidate_status = currentness_status
            currentness_status = "calendar_status_unresolved"

    return {
        "schema_version": "m8r_eod_expected_trade_date_status.v1",
        "market": market,
        "reference_time_utc": ref_tz.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"),
        "reference_time_asia_taipei": ref_tz.isoformat(),
        "reference_local_date": ref_local_date.isoformat(),
        "session_status": sess_status,
        "expected_latest_completed_trade_date": expected_date_str,
        "actual_official_trade_date": actual_trade_date,
        "currentness_status": currentness_status,
        "calendar_source": cal_source,
        "closure_source": closure_src,
        "publication_grace_applied": publication_grace_applied,
        "fallback_policy_used": fallback_policy_used,
        "fallback_policy": fallback_policy,
        "provisional_candidate_status": provisional_candidate_status,
        "caveats": caveats
    }
