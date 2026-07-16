#!/usr/bin/env python
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8r_03c_watchlist_bundle_builder import build_watchlist_snapshot_bundle, build_watchlist_performance_bundle
from scripts.m8r_03c_conversation_contract_validator import M8R03CValidationError

def main(argv=None):
    p=argparse.ArgumentParser(description='Run M8R-03C non-network watchlist bundle fixture')
    p.add_argument('--request', required=True); p.add_argument('--observations', required=True); p.add_argument('--bundle-type', choices=['snapshot','performance'], required=True); p.add_argument('--output', required=True); p.add_argument('--generated-at-utc', default='2026-07-16T01:30:05Z')
    bad={'--url','--network','--polling','--scheduler'}
    if argv and any(a.split('=')[0] in bad for a in argv): p.error('network URLs/polling/scheduler are unsupported')
    args=p.parse_args(argv)
    if any(str(getattr(args,n)).startswith(('http://','https://')) for n in ('request','observations','output')): p.error('URLs are unsupported')
    req=json.loads(Path(args.request).read_text(encoding='utf-8')); obs=json.loads(Path(args.observations).read_text(encoding='utf-8'))
    try:
        out=build_watchlist_snapshot_bundle(request=req,observations=obs,generated_at_utc=args.generated_at_utc) if args.bundle_type=='snapshot' else build_watchlist_performance_bundle(request=req,observations=obs,generated_at_utc=args.generated_at_utc)
    except M8R03CValidationError as exc:
        print(json.dumps({'error':exc.code,'path':exc.path,'detail':exc.detail}, ensure_ascii=False), file=sys.stderr); return 2
    Path(args.output).parent.mkdir(parents=True, exist_ok=True); Path(args.output).write_text(json.dumps(out, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8'); return 0
if __name__=='__main__': raise SystemExit(main(sys.argv[1:]))
