#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,sys,math
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'scripts'))
from build_m5f_canonical_market_context_package import build_package, reject_forbidden_nested, SYMBOL_ALLOWLIST, ALLOWED_FRESHNESS, ALLOWED_BADGES, validate_symbol_shape
FILES={'canonical_market_context.json','latest_market_snapshot.json','watchlist_observations.json','ai_context_pack.json','ai_context_pack.md','chatgpt_briefing.md','source_health.json','capability_summary.json','lineage.json','validation_report.json','sha256_manifest.json'}
CAVEATS={'not_realtime_guaranteed','not_trading_signal','not_production_current_state','source_risk_present','freshness_must_be_displayed'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _canonical_checks(c):
    reject_forbidden_nested(c)
    if c.get('schema_version')!='m5f_canonical_market_context.v1': raise ValueError('bad schema')
    symbols=c.get('symbols',[])
    if not isinstance(symbols,list) or not symbols: raise ValueError('bad symbols')
    syms={s.get('symbol'):s for s in symbols}
    if None in syms or len(syms)!=len(symbols): raise ValueError('bad or duplicate symbols')
    for s in symbols:
        extra=set(s)-SYMBOL_ALLOWLIST
        if extra: raise ValueError(f'unexpected symbol fields: {sorted(extra)}')
        validate_symbol_shape(s)
        if s.get('source_id') != c.get('source') or s.get('source_timestamp') != c.get('source_date'):
            raise ValueError('symbol source/date diverges from canonical')
    gov=c.get('governance',{})
    required={'historical_evidence_snapshot':True,'current_realtime':False,'production_current_state':False,'production_ready':False,'realtime_guaranteed':False,'trading_signal':False,'readonly_only':True}
    for k,v in required.items():
        if gov.get(k)!=v: raise ValueError(f'bad governance {k}')
    if gov.get('stale_status') not in ALLOWED_FRESHNESS or gov.get('badge') not in ALLOWED_BADGES: raise ValueError('bad freshness badge')
    if not CAVEATS.issubset(set(c.get('global_caveats',[]))): raise ValueError('missing caveats')
def validate_package(package_dir:Path):
    package_dir=package_dir.resolve()
    if not package_dir.is_dir(): raise ValueError('missing package dir')
    entries=list(package_dir.iterdir())
    dirs=[p.name for p in entries if p.is_dir()]
    if dirs: raise ValueError(f'unexpected package directory: {sorted(dirs)}')
    names={p.name for p in entries if p.is_file()}
    if names!=FILES: raise ValueError(f'exact file set mismatch: {sorted(names)}')
    m=load(package_dir/'sha256_manifest.json')
    if m.get('manifest_final') is not True or m.get('no_artifact_modification_after_manifest') is not True: raise ValueError('manifest final flags missing')
    if set(m.get('files',{})) != FILES-{'sha256_manifest.json'}: raise ValueError('manifest file set mismatch')
    for n,h in m['files'].items():
        if sha(package_dir/n)!=h: raise ValueError(f'hash mismatch {n}')
    c=load(package_dir/'canonical_market_context.json')
    _canonical_checks(c)
    expected_artifacts=build_package(REPO/c['derived_from'])
    for n,obj in expected_artifacts.items():
        expected = obj if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n'
        actual=(package_dir/n).read_text(encoding='utf-8')
        if actual != expected: raise ValueError(f'derivative or canonical mismatch: {n}')
    expected_manifest_lineage=expected_artifacts['canonical_market_context.json']['lineage_hashes']
    if c.get('lineage_hashes') != expected_manifest_lineage or m.get('lineage_hashes') != expected_manifest_lineage:
        raise ValueError('lineage hash mismatch')
    return {'status':'passed','symbols':sorted(s['symbol'] for s in c['symbols']),'source':c['source'],'source_date':c['source_date'],'manifest_sha256':sha(package_dir/'sha256_manifest.json')}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--package-dir',default=str(REPO/'research/staging/m5f/m5f_canonical_market_context_01')); a=ap.parse_args(); print(json.dumps(validate_package(Path(a.package_dir)),ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
