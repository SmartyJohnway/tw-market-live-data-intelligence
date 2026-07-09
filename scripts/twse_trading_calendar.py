"""TWSE trading-calendar authority helpers for M7E-05.

Pure local helpers only: no network requests, no hidden artifact loading, and no
runtime writes. The authority normalizes supplied TWSE OpenAPI holidaySchedule
records into a governed local artifact and resolves TWSE trading-day status from
that artifact when supplied.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TWSE_TRADING_CALENDAR_SCHEMA_VERSION = "twse_trading_calendar.v1"
TWSE_TRADING_DAY_RESOLUTION_SCHEMA_VERSION = "twse_trading_day_resolution.v1"
TWSE_TRADING_CALENDAR_AUTHORITY_SUMMARY_SCHEMA_VERSION = "twse_trading_calendar_authority_summary.v1"
TWSE_HOLIDAY_SCHEDULE_URL = "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule"
CALENDAR_CONFIDENCE_ARTIFACT = "controlled_twse_holiday_schedule_artifact"


def parse_twse_roc_date(value: str) -> date:
    """Parse TWSE ROC/Minguo YYYMMDD date into Gregorian date."""
    if not isinstance(value, str) or len(value) != 7 or not value.isdigit():
        raise ValueError("TWSE ROC date must be exactly 7 digits in YYYMMDD form")
    roc_year = int(value[:3])
    if roc_year <= 0:
        raise ValueError("ROC year must be positive")
    return date(roc_year + 1911, int(value[3:5]), int(value[5:7]))


def _parse_target_date(target_date: str | date) -> date:
    if isinstance(target_date, date) and not isinstance(target_date, datetime):
        return target_date
    if isinstance(target_date, str):
        return date.fromisoformat(target_date)
    raise ValueError("target_date must be YYYY-MM-DD string or date")


def _normalized_evidence(record: dict[str, object], classification: str) -> dict[str, object]:
    return {
        "source_name": record.get("Name"),
        "source_date_roc": record.get("Date"),
        "source_weekday": record.get("Weekday"),
        "classification": classification,
    }


def _empty_resolution(target: date, *, status: str, is_trading_day: bool | None, reason: str, confidence: str, source: str, caveats: list[str]) -> dict[str, object]:
    return {
        "schema_version": TWSE_TRADING_DAY_RESOLUTION_SCHEMA_VERSION,
        "market": "TWSE",
        "date": target.isoformat(),
        "is_trading_day": is_trading_day,
        "trading_day_status": status,
        "reason": reason,
        "calendar_confidence": confidence,
        "source": source,
        "not_full_exchange_calendar_engine": True,
        "no_realtime_sla": True,
        "not_trading_advice": True,
        "caveats": caveats,
    }


def build_twse_trading_calendar_from_holiday_schedule(
    *,
    year: int,
    holiday_schedule_records: list[dict[str, object]],
    generated_at_utc: str | None = None,
    source_url: str = TWSE_HOLIDAY_SCHEDULE_URL,
) -> dict[str, object]:
    """Build a governed annual TWSE trading-calendar artifact from supplied records."""
    evidence_by_date: dict[str, list[dict[str, object]]] = {}
    invalid_records: list[dict[str, object]] = []
    for idx, record in enumerate(holiday_schedule_records or []):
        if not isinstance(record, dict):
            invalid_records.append({"index": idx, "reason": "record must be an object"})
            continue
        name = record.get("Name")
        raw_date = record.get("Date")
        try:
            if not isinstance(name, str):
                raise ValueError("Name must be a string")
            if not isinstance(raw_date, str):
                raise ValueError("Date must be a ROC_YYYMMDD string")
            parsed = parse_twse_roc_date(raw_date)
        except Exception as exc:
            invalid_records.append({"index": idx, "Name": name, "Date": raw_date, "Weekday": record.get("Weekday"), "reason": str(exc)})
            continue
        if parsed.year != year:
            continue
        classification = "explicit_endpoint_trading_label" if "交易日" in name else "endpoint_non_trading_date"
        evidence_by_date.setdefault(parsed.isoformat(), []).append(_normalized_evidence(record, classification))

    start = date(year, 1, 1)
    end = date(year, 12, 31)
    current = start
    dates: list[dict[str, object]] = []
    trading_count = 0
    non_trading_count = 0
    while current <= end:
        iso = current.isoformat()
        is_weekend = current.weekday() >= 5
        evidence = evidence_by_date.get(iso, [])
        has_endpoint_non = any(e.get("classification") == "endpoint_non_trading_date" for e in evidence)
        has_explicit_trading = any(e.get("classification") == "explicit_endpoint_trading_label" for e in evidence)
        if is_weekend and has_endpoint_non:
            is_trading = False
            reason = "weekend_and_endpoint_non_trading_date"
        elif is_weekend:
            is_trading = False
            reason = "weekend_non_trading"
        elif has_endpoint_non:
            is_trading = False
            reason = "endpoint_non_trading_date"
        elif has_explicit_trading:
            is_trading = True
            reason = "explicit_endpoint_trading_label"
        else:
            is_trading = True
            reason = "regular_weekday_trading_day"
        if is_trading:
            trading_count += 1
        else:
            non_trading_count += 1
        dates.append({
            "date": iso,
            "weekday": current.strftime("%A"),
            "is_weekend": is_weekend,
            "is_trading_day": is_trading,
            "trading_day_status": "trading_day" if is_trading else "non_trading_day",
            "reason": reason,
            "source_evidence": evidence,
        })
        current += timedelta(days=1)

    return {
        "schema_version": TWSE_TRADING_CALENDAR_SCHEMA_VERSION,
        "market": "TWSE",
        "year": year,
        "timezone": "Asia/Taipei",
        "source": {
            "source_name": "TWSE OpenAPI holidaySchedule",
            "source_url": source_url,
            "date_format": "ROC_YYYMMDD",
            "normalization_rule": "weekends_plus_endpoint_dates_excluding_names_containing_trading_day",
            "runtime_fetch": False,
        },
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "calendar_confidence": CALENDAR_CONFIDENCE_ARTIFACT,
        "not_full_exchange_calendar_engine": True,
        "no_realtime_sla": True,
        "not_trading_advice": True,
        "date_count": len(dates),
        "trading_day_count": trading_count,
        "non_trading_day_count": non_trading_count,
        "dates": dates,
        "invalid_records": invalid_records,
        "caveats": [],
    }


def load_twse_trading_calendar_artifact(path: str | Path) -> dict[str, object]:
    artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(artifact, dict):
        raise ValueError("TWSE trading calendar artifact must be a JSON object")
    if artifact.get("schema_version") != TWSE_TRADING_CALENDAR_SCHEMA_VERSION:
        raise ValueError("Unsupported TWSE trading calendar artifact schema_version")
    if artifact.get("market") != "TWSE" or not isinstance(artifact.get("dates"), list):
        raise ValueError("Malformed TWSE trading calendar artifact")
    return deepcopy(artifact)


def resolve_twse_trading_day(*, target_date: str | date, calendar_artifact: dict[str, object] | None = None) -> dict[str, object]:
    target = _parse_target_date(target_date)
    if calendar_artifact is None:
        is_weekend = target.weekday() >= 5
        return _empty_resolution(
            target,
            status="non_trading_day" if is_weekend else "trading_day",
            is_trading_day=not is_weekend,
            reason="weekend_non_trading" if is_weekend else "regular_weekday_trading_day",
            confidence="weekday_heuristic_only",
            source="weekday_heuristic",
            caveats=["TWSE controlled trading calendar artifact not supplied; weekday heuristic only."],
        )
    if calendar_artifact.get("schema_version") != TWSE_TRADING_CALENDAR_SCHEMA_VERSION:
        raise ValueError("Unsupported TWSE trading calendar artifact schema_version")
    for entry in calendar_artifact.get("dates", []):
        if isinstance(entry, dict) and entry.get("date") == target.isoformat():
            return _empty_resolution(
                target,
                status=str(entry.get("trading_day_status")),
                is_trading_day=entry.get("is_trading_day") if isinstance(entry.get("is_trading_day"), bool) else None,
                reason=str(entry.get("reason")),
                confidence=str(calendar_artifact.get("calendar_confidence", CALENDAR_CONFIDENCE_ARTIFACT)),
                source="local_calendar_artifact",
                caveats=list(calendar_artifact.get("caveats", [])) if isinstance(calendar_artifact.get("caveats"), list) else [],
            )
    return _empty_resolution(
        target,
        status="unknown",
        is_trading_day=None,
        reason="date_not_found_in_artifact",
        confidence="artifact_missing_date",
        source="local_calendar_artifact",
        caveats=["Date not found in supplied TWSE trading calendar artifact."],
    )


def is_twse_trading_day(target_date: str | date, calendar_artifact: dict[str, object] | None = None) -> bool | None:
    resolved = resolve_twse_trading_day(target_date=target_date, calendar_artifact=calendar_artifact)
    value = resolved.get("is_trading_day")
    return value if isinstance(value, bool) else None


def build_twse_trading_calendar_authority_summary(calendar_artifact: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "schema_version": TWSE_TRADING_CALENDAR_AUTHORITY_SUMMARY_SCHEMA_VERSION,
        "authority": "TWSE_TRADING_CALENDAR_AUTHORITY",
        "supported_modes": ["Mode A", "Mode B", "Mode C"],
        "shared_resolver": "scripts/twse_trading_calendar.py::resolve_twse_trading_day",
        "calendar_confidence": str(calendar_artifact.get("calendar_confidence")) if isinstance(calendar_artifact, dict) else "weekday_heuristic_only",
        "runtime_fetch": False,
        "startup_network": False,
        "not_full_exchange_calendar_engine": True,
        "no_realtime_sla": True,
        "not_trading_advice": True,
        "mode_contract": {
            "mode_a": "must use shared resolver for TWSE source-date trading-day checks",
            "mode_b": "must use shared resolver for latest-observation/currentness trading-day checks",
            "mode_c": "must use shared resolver for AI handoff trading-day language",
        },
    }
