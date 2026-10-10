#!/usr/bin/env python3
"""Parse supplied TWSE or TPEx ETN expiry/termination table captures."""
from __future__ import annotations
import argparse, json, re, sys
from datetime import date
from pathlib import Path
from common import canonical_hash
from lifecycle_common import LifecycleSchemaDrift, make_event, parse_standard_table

TWSE_EXPIRED_JSON_ROOT_KEYS = {"stat", "title", "data", "fields"}
TWSE_EXPIRED_JSON_FIELDS = [
    "終止上市日期",
    "證券代號",
    "證券簡稱",
    "發行證券商",
    "終止上市理由",
]

def parse(data: bytes, source_url: str, market: str) -> list[dict]:
    if market not in {"twse", "tpex"}: raise ValueError("market must be twse or tpex")
    base_events = parse_standard_table(data, event_type=f"{market}_delisted", source_family=f"{market}_etn_termination_table", source_url=source_url)
    events: list[dict] = []
    for base in base_events:
        events.append(base)
        for date_field, event_type in (("maturity_date", "matured"), ("last_trading_date", "last_trading")):
            if base.get(date_field) in (None, "unknown", "not_applicable"): continue
            derived = {**base, "event_type": event_type, "effective_date": base[date_field]}
            derived["event_key"] = canonical_hash({key: derived.get(key) for key in ("security_code", "event_type", "effective_date", "source_url")})
            events.append(derived)
    return events


def parse_twse_expired_json(data: bytes, source_url: str) -> list[dict]:
    """Parse the qualified one-response TWSE expired-ETN JSON contract.

    This adapter is deliberately separate from the legacy supplied HTML parser.
    The official page exposes an unfiltered, unpaged response and the returned
    data array is the complete set offered by that page at acquisition time.
    """
    try:
        payload = json.loads(data.decode("utf-8-sig", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LifecycleSchemaDrift("twse_etn_json_malformed_json") from exc

    if not isinstance(payload, dict) or set(payload) != TWSE_EXPIRED_JSON_ROOT_KEYS:
        observed = sorted(payload) if isinstance(payload, dict) else type(payload).__name__
        raise LifecycleSchemaDrift("twse_etn_json_root_drift", {"observed": observed})
    if payload.get("stat") != "ok":
        raise LifecycleSchemaDrift("twse_etn_json_non_ok_stat", {"stat": payload.get("stat")})
    if payload.get("title") != "到期或終止上市資訊":
        raise LifecycleSchemaDrift("twse_etn_json_title_drift")
    if payload.get("fields") != TWSE_EXPIRED_JSON_FIELDS:
        raise LifecycleSchemaDrift("twse_etn_json_fields_drift", {"observed": payload.get("fields")})
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise LifecycleSchemaDrift("twse_etn_json_data_not_array")

    events: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(TWSE_EXPIRED_JSON_FIELDS):
            raise LifecycleSchemaDrift("twse_etn_json_row_width_drift", {"row_index": index})
        if any(not isinstance(value, str) for value in row):
            raise LifecycleSchemaDrift("twse_etn_json_row_value_type_drift", {"row_index": index})

        raw_date, security_code, security_name, issuer, reason = row
        if not re.fullmatch(r"\d{4}/\d{2}/\d{2}", raw_date):
            raise LifecycleSchemaDrift("twse_etn_json_date_shape_drift", {"row_index": index})
        try:
            effective_date = date.fromisoformat(raw_date.replace("/", "-")).isoformat()
        except ValueError as exc:
            raise LifecycleSchemaDrift("twse_etn_json_invalid_date", {"row_index": index}) from exc
        if not security_code.strip():
            raise LifecycleSchemaDrift("twse_etn_json_missing_security_code", {"row_index": index})
        if not security_name.strip():
            raise LifecycleSchemaDrift("twse_etn_json_missing_security_name", {"row_index": index})
        identity = (security_code.strip(), effective_date)
        if identity in seen:
            raise LifecycleSchemaDrift("twse_etn_json_duplicate_lifecycle_identity", {"row_index": index})
        seen.add(identity)

        event = make_event(
            {
                "security_code": security_code.strip(),
                "security_name_zh": security_name.strip(),
                "effective_date": effective_date,
                "reason": reason,
            },
            event_type="twse_delisted",
            source_family="twse_etn_expiry_json",
            source_url=source_url,
            evidence_status="official_explicit",
        )
        event["date_raw"] = raw_date
        event["calendar"] = "Gregorian"
        event["issuer_name"] = issuer.strip()
        event["provenance"] = {
            "adapter": "parse_etn_termination.parse_twse_expired_json",
            "supplied_capture": True,
            "coverage_basis": "complete_data_array_from_unfiltered_unpaged_official_page_response",
        }
        event["event_key"] = canonical_hash(
            {
                key: event.get(key)
                for key in ("security_code", "event_type", "effective_date", "source_url")
            }
        )
        events.append(event)
    return events

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("--source-url",required=True); p.add_argument("--market",required=True,choices=("twse","tpex")); a=p.parse_args()
    try:
        events=parse(a.input.read_bytes(),a.source_url,a.market); result={"acquisition_status":"data" if events else "empty_valid","event_count":len(events),"events":events,"issues":[]}; exit_code=0
    except LifecycleSchemaDrift as exc:
        result={"acquisition_status":"schema_drift","event_count":0,"events":[],"issues":[{"code":exc.issue_code,"detail":exc.detail}]}; exit_code=1
    print(json.dumps(result,ensure_ascii=False,indent=2)); sys.exit(exit_code)
