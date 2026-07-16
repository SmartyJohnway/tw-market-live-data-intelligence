#!/usr/bin/env python3
"""Merge and deduplicate supplied lifecycle event JSON without overwriting history."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import canonical_hash

def merge(groups: list[list[dict]]) -> dict:
    unique: dict[str, dict] = {}; conflicts: list[dict] = []
    for event in (item for group in groups for item in group):
        key = event.get("event_key") or canonical_hash({k:event.get(k) for k in ("security_code","event_type","effective_date","source_url")})
        if key in unique and unique[key] != event: conflicts.append({"event_key":key,"category":"event_evidence_conflict","values":[unique[key],event]})
        else: unique[key] = event
    events=sorted(unique.values(),key=lambda e:(e.get("security_code", ""),e.get("effective_date", ""),e.get("event_type", "")))
    return {"operation":"merge_lifecycle_events","event_count":len(events),"events":events,"conflicts":conflicts,"completeness":"conflicted" if conflicts else "partial"}

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("inputs",type=Path,nargs="+"); a=p.parse_args(); groups=[]
    for path in a.inputs:
        obj=json.loads(path.read_text(encoding="utf-8")); groups.append(obj.get("events",obj) if isinstance(obj,dict) else obj)
    print(json.dumps(merge(groups),ensure_ascii=False,indent=2))
