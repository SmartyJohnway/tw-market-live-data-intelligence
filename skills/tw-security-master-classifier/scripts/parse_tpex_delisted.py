#!/usr/bin/env python3
"""Parse a supplied TPEx terminated-OTC official HTML capture."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from lifecycle_common import LifecycleSchemaDrift, parse_standard_table

def parse(data: bytes, source_url: str) -> list[dict]:
    return parse_standard_table(data, event_type="tpex_delisted", source_family="tpex_termination_table", source_url=source_url)

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("--source-url",required=True); a=p.parse_args()
    try:
        events=parse(a.input.read_bytes(),a.source_url); result={"acquisition_status":"data" if events else "empty_valid","event_count":len(events),"events":events,"issues":[]}; exit_code=0
    except LifecycleSchemaDrift as exc:
        result={"acquisition_status":"schema_drift","event_count":0,"events":[],"issues":[{"code":exc.issue_code,"detail":exc.detail}]}; exit_code=1
    print(json.dumps(result,ensure_ascii=False,indent=2)); sys.exit(exit_code)
