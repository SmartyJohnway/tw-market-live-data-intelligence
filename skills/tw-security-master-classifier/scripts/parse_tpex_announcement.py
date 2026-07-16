#!/usr/bin/env python3
"""Parse supplied TPEx market-announcement table captures with explicit event routing."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from lifecycle_common import LifecycleSchemaDrift, parse_standard_table

ALLOWED = {"emerging_terminated", "gisa_terminated", "tpex_suspended", "tpex_resumed", "tpex_delisted", "early_terminated"}

def parse(data: bytes, source_url: str, event_type: str) -> list[dict]:
    if event_type not in ALLOWED: raise ValueError("event_type must be explicitly selected from the controlled TPEx set")
    return parse_standard_table(data, event_type=event_type, source_family="tpex_announcement", source_url=source_url, evidence_status="official_announcement")

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("--source-url",required=True); p.add_argument("--event-type",required=True,choices=sorted(ALLOWED)); a=p.parse_args()
    try:
        events=parse(a.input.read_bytes(),a.source_url,a.event_type); result={"acquisition_status":"data" if events else "empty_valid","event_count":len(events),"events":events,"issues":[]}; exit_code=0
    except LifecycleSchemaDrift as exc:
        result={"acquisition_status":"schema_drift","event_count":0,"events":[],"issues":[{"code":exc.issue_code,"detail":exc.detail}]}; exit_code=1
    print(json.dumps(result,ensure_ascii=False,indent=2)); sys.exit(exit_code)
