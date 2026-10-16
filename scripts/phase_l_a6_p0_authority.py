"""Offline helpers for the one-shot L3-A6-P0 authority materialization."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from hashlib import sha256
import json
from typing import Any
from zoneinfo import ZoneInfo

CALENDAR_URL = "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule"
CLOSURE_URL = "https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33"
CALENDAR_HOST = "openapi.twse.com.tw"
CLOSURE_HOST = "alerts.ncdr.nat.gov.tw"
MAX_CALENDAR = 3
MAX_CLOSURE = 3
MAX_TOTAL = 6


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()


def validate_2026_calendar(artifact: dict[str, Any]) -> dict[str, int]:
    source = artifact.get("source") if isinstance(artifact, dict) else None
    if (artifact.get("schema_version") != "twse_trading_calendar.v1"
            or artifact.get("market") != "TWSE" or artifact.get("year") != 2026
            or artifact.get("timezone") != "Asia/Taipei" or not isinstance(source, dict)
            or source.get("source_url") != CALENDAR_URL or source.get("runtime_fetch") is not False):
        raise ValueError("calendar_authority_contract_invalid")
    dates = artifact.get("dates")
    expected = [(date(2026, 1, 1) + timedelta(days=n)).isoformat() for n in range(365)]
    if not isinstance(dates, list) or [x.get("date") if isinstance(x, dict) else None for x in dates] != expected:
        raise ValueError("calendar_2026_date_coverage_invalid")
    if any(type(x.get("is_trading_day")) is not bool for x in dates):
        raise ValueError("calendar_2026_status_invalid")
    invalid = artifact.get("invalid_records")
    if not isinstance(invalid, list):
        raise ValueError("calendar_invalid_records_uninspected")
    if invalid:
        raise ValueError("calendar_invalid_records_present")
    trading = sum(x["is_trading_day"] for x in dates)
    nontrading = len(dates) - trading
    if artifact.get("date_count") != 365 or artifact.get("trading_day_count") != trading or artifact.get("non_trading_day_count") != nontrading:
        raise ValueError("calendar_2026_aggregate_counts_invalid")
    return {"date_count": 365, "trading_day_count": trading, "non_trading_day_count": nontrading, "invalid_record_count": 0}


def derive_resolver_coverage_dates(evaluation_time: datetime, artifact: dict[str, Any]) -> list[str]:
    if evaluation_time.tzinfo is None or evaluation_time.utcoffset() is None:
        raise ValueError("evaluation_time_timezone_required")
    local_date = evaluation_time.astimezone(ZoneInfo("Asia/Taipei")).date()
    by_date = {x["date"]: x["is_trading_day"] for x in artifact["dates"]}
    if local_date.isoformat() not in by_date:
        raise ValueError("resolver_window_calendar_coverage_missing")
    result = [local_date.isoformat()]
    cursor = local_date - timedelta(days=1)
    for _ in range(367):
        key = cursor.isoformat()
        if key not in by_date:
            raise ValueError("resolver_window_calendar_coverage_missing")
        result.append(key)
        if by_date[key]:
            return result
        cursor -= timedelta(days=1)
    raise ValueError("resolver_window_prior_trading_day_unresolved")


def assess_closure_completeness(parsed: dict[str, Any], coverage_dates: list[str]) -> dict[str, Any]:
    """The current NCDR contract has no exhaustive historical coverage claim."""
    events = parsed.get("events") if isinstance(parsed, dict) else None
    if not isinstance(events, list):
        raise ValueError("closure_events_invalid")
    relevant = [e for e in events if isinstance(e, dict) and e.get("target_date") in coverage_dates
                and e.get("area_name") in {"臺北市", "台北市"}]
    return {
        "coverage_dates": list(coverage_dates),
        "coverage_basis": "resolver_inspection_window_only",
        "source_query_succeeded": parsed.get("closure_query_succeeded") is True,
        "events_relevant_to_coverage_dates": relevant,
        "completeness_reason": "current NCDR dynamic-event source contract does not attest exhaustive historical coverage for requested dates",
        "closure_authority_complete": False,
    }


def normalized_calendar_sha256(artifact: dict[str, Any]) -> str:
    """Bind normalized trading-day facts, excluding retrieval/cache metadata."""
    fields = {k: artifact.get(k) for k in ("schema_version", "market", "year", "timezone", "source", "date_count", "trading_day_count", "non_trading_day_count", "dates", "invalid_records")}
    return canonical_sha256(fields)


def compare_calendar_snapshots(first: dict[str, Any], second: dict[str, Any]) -> str:
    if normalized_calendar_sha256(first) == normalized_calendar_sha256(second):
        return "NORMALIZED_SNAPSHOT_IDENTICAL"
    first_days = {x["date"]: x["is_trading_day"] for x in first.get("dates", [])}
    second_days = {x["date"]: x["is_trading_day"] for x in second.get("dates", [])}
    return "CALENDAR_AUTHORITY_SNAPSHOT_CHANGED" if first_days != second_days else "METADATA_ONLY_DIFFERENCE_TRADING_DAYS_IDENTICAL"


class AcquisitionBudget:
    def __init__(self) -> None:
        self.calendar_count = 0
        self.closure_count = 0

    @property
    def total(self) -> int:
        return self.calendar_count + self.closure_count

    def reserve(self, authority: str) -> int:
        if authority == "TWSE_HOLIDAY_SCHEDULE":
            if self.calendar_count >= MAX_CALENDAR:
                raise ValueError("p0_calendar_acquisition_limit_exceeded")
            self.calendar_count += 1
            return self.calendar_count
        if authority == "NCDR_DGPA_CLOSURE_CAP":
            if self.closure_count >= MAX_CLOSURE:
                raise ValueError("p0_closure_acquisition_limit_exceeded")
            self.closure_count += 1
            return self.closure_count
        raise ValueError("p0_unapproved_source_authority")

    def check_total(self) -> None:
        if self.total >= MAX_TOTAL:
            raise ValueError("p0_total_acquisition_limit_exceeded")
