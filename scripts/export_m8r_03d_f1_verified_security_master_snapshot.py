#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8r_03d_f1_security_master_snapshot_exporter import export_verified_security_master_snapshot, canonical_json
from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot

def _load(path):
    s=str(path)
    if s.startswith(('http://','https://')): raise SystemExit('URL input is rejected; CLI is non-network only')
    return json.loads(Path(path).read_text(encoding='utf-8'))
def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--classification-input',required=True); ap.add_argument('--lifecycle-events',required=True); ap.add_argument('--source-context',required=True); ap.add_argument('--output',required=True); ap.add_argument('--manifest-output',required=True); ap.add_argument('--generated-at-utc',required=True); ap.add_argument('--effective-observation-date',required=True)
    ns=ap.parse_args(argv)
    records=_load(ns.classification_input); events=_load(ns.lifecycle_events); ctx=_load(ns.source_context)
    if isinstance(records,dict): records=records.get('records') or records.get('candidates') or []
    snap,man=export_verified_security_master_snapshot(classification_records=records,lifecycle_events=events,source_context=ctx,generated_at_utc=ns.generated_at_utc,effective_observation_date=ns.effective_observation_date)
    Path(ns.output).write_text(json.dumps(snap,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    Path(ns.manifest_output).write_text(json.dumps(man,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    load_verified_security_master_snapshot(ns.output, ns.manifest_output, allow_fixture_snapshot=True)
    print(canonical_json({'snapshot_id':snap['snapshot_id'],'record_count':len(snap['records']),'validation_status':'passed'}))
if __name__=='__main__': main()
