#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.m5i_common import load, sha, reject_forbidden, ALLOWED_BOUNDED, SOURCE

def validate_candidate(candidate_dir: Path):
    files={'market-context.json','source_binding.json','sha256_manifest.json','refresh_summary.json','validation_report.json'}
    names={p.name for p in candidate_dir.iterdir() if p.is_file()}
    if names!=files: raise ValueError(f'exact file set mismatch: {sorted(names)}')
    m=load(candidate_dir/'sha256_manifest.json')
    if set(m.get('files',{}))!=files-{'sha256_manifest.json'}: raise ValueError('manifest file set mismatch')
    for n,h in m['files'].items():
        if sha(candidate_dir/n)!=h: raise ValueError(f'hash mismatch {n}')
    c=load(candidate_dir/'market-context.json'); b=load(candidate_dir/'source_binding.json')
    reject_forbidden(c); reject_forbidden(b)
    if c.get('schema_version')!='m5i_refresh_candidate.v1': raise ValueError('bad schema')

    rows=c.get('symbols',[])
    syms=[r.get('symbol') for r in rows]

    failed_targets_list=c.get('failed_targets', [])
    if not isinstance(failed_targets_list, list): raise ValueError('failed_targets must be a list')

    failed_targets = []
    for f in failed_targets_list:
        if not isinstance(f, dict): raise ValueError('failed_targets items must be objects/dicts')
        sym = f.get('symbol')
        status = f.get('status')
        if not sym or not isinstance(sym, str): raise ValueError('failed target missing valid symbol string')
        if not status or not isinstance(status, str): raise ValueError('failed target missing valid status string')
        failed_targets.append(sym)

    combined_targets=syms + failed_targets

    if len(combined_targets)!=len(set(combined_targets)): raise ValueError('duplicate targets between symbols and failed_targets')
    if sorted(combined_targets)!=sorted(b.get('targets',[])): raise ValueError('candidate symbols and failed_targets do not match binding targets')
    if set(combined_targets)-ALLOWED_BOUNDED: raise ValueError('unbounded target encountered')
    if c.get('source')!=SOURCE or b.get('source')!=SOURCE: raise ValueError('bad source')
    for flag, val in {'current_realtime':False,'production_current_state':False,'production_ready':False,'realtime_guaranteed':False,'trading_signal':False,'readonly_only':True}.items():
        if c.get(flag)!=val: raise ValueError(f'bad flag {flag}')
    for r in rows:
        if isinstance(r.get('price_like_value'),bool) or not isinstance(r.get('price_like_value'),(int,float)) or not math.isfinite(r['price_like_value']): raise ValueError('bad price_like_value')
        for k in ['display_caveats','source_risk_flags','data_quality_flags']:
            if not isinstance(r.get(k),list) or any(not isinstance(x,str) for x in r[k]): raise ValueError(f'bad {k}')
    return {'status':'passed','symbols':sorted(syms),'manifest_sha256':sha(candidate_dir/'sha256_manifest.json')}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidate-dir',required=True); a=ap.parse_args(); print(json.dumps(validate_candidate(Path(a.candidate_dir)),indent=2,sort_keys=True))
if __name__=='__main__': main()
