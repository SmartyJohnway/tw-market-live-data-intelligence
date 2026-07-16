#!/usr/bin/env python3
"""Parse supplied TWSE or TPEx ETN expiry/termination table captures."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from common import canonical_hash
from lifecycle_common import LifecycleSchemaDrift, parse_standard_table

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

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("--source-url",required=True); p.add_argument("--market",required=True,choices=("twse","tpex")); a=p.parse_args()
    try:
        events=parse(a.input.read_bytes(),a.source_url,a.market); result={"acquisition_status":"data" if events else "empty_valid","event_count":len(events),"events":events,"issues":[]}; exit_code=0
    except LifecycleSchemaDrift as exc:
        result={"acquisition_status":"schema_drift","event_count":0,"events":[],"issues":[{"code":exc.issue_code,"detail":exc.detail}]}; exit_code=1
    print(json.dumps(result,ensure_ascii=False,indent=2)); sys.exit(exit_code)
