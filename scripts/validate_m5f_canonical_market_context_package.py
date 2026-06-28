#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'scripts'))
from build_m5f_canonical_market_context_package import build_package
FILES={'canonical_market_context.json','latest_market_snapshot.json','watchlist_observations.json','ai_context_pack.json','ai_context_pack.md','chatgpt_briefing.md','source_health.json','capability_summary.json','lineage.json','validation_report.json','sha256_manifest.json'}
EXPECTED={'0050':103.1,'00929':29.96,'2330':2340.0}
CAVEATS={'not_realtime_guaranteed','not_trading_signal','not_production_current_state','source_risk_present','freshness_must_be_displayed'}
FORBIDDEN={'buy','sell','hold','target_price','ranking','recommendation'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _canonical_checks(c):
    if c.get('schema_version')!='m5f_canonical_market_context.v1': raise ValueError('bad schema')
    syms={s.get('symbol'):s for s in c.get('symbols',[])}
    if set(syms)!=set(EXPECTED): raise ValueError('bad symbols')
    for sym,val in EXPECTED.items():
        s=syms[sym]
        if s.get('source_id')!='TWSE_OpenAPI' or s.get('source_timestamp')!='2026-06-26' or float(s.get('price_like_value'))!=val: raise ValueError(f'bad data {sym}')
    gov=c.get('governance',{})
    required={'historical_evidence_snapshot':True,'current_realtime':False,'production_current_state':False,'production_ready':False,'realtime_guaranteed':False,'trading_signal':False,'readonly_only':True}
    for k,v in required.items():
        if gov.get(k)!=v: raise ValueError(f'bad governance {k}')
    if gov.get('stale_status')!='stale' or gov.get('badge')!='historical/stale': raise ValueError('bad stale')
    if not CAVEATS.issubset(set(c.get('global_caveats',[]))): raise ValueError('missing caveats')
    for f in FORBIDDEN:
        if f in c: raise ValueError('forbidden field')
def validate_package(package_dir:Path):
    package_dir=package_dir.resolve()
    if not package_dir.is_dir(): raise ValueError('missing package dir')
    names={p.name for p in package_dir.iterdir() if p.is_file()}
    if names!=FILES: raise ValueError(f'exact file set mismatch: {sorted(names)}')
    m=load(package_dir/'sha256_manifest.json')
    if m.get('manifest_final') is not True or m.get('no_artifact_modification_after_manifest') is not True: raise ValueError('manifest final flags missing')
    if set(m.get('files',{})) != FILES-{'sha256_manifest.json'}: raise ValueError('manifest file set mismatch')
    for n,h in m['files'].items():
        if sha(package_dir/n)!=h: raise ValueError(f'hash mismatch {n}')
    c=load(package_dir/'canonical_market_context.json')
    _canonical_checks(c)
    # Recompute upstream lineage and deterministic derivatives from immutable M5D input.
    expected_artifacts=build_package(REPO/c['derived_from'])
    for n,obj in expected_artifacts.items():
        expected = obj if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
        actual=(package_dir/n).read_text(encoding='utf-8')
        if actual != expected: raise ValueError(f'derivative or canonical mismatch: {n}')
    expected_manifest_lineage=expected_artifacts['canonical_market_context.json']['lineage_hashes']
    if c.get('lineage_hashes') != expected_manifest_lineage or m.get('lineage_hashes') != expected_manifest_lineage:
        raise ValueError('lineage hash mismatch')
    text='\n'.join((package_dir/n).read_text(encoding='utf-8').lower() for n in FILES)
    if 'raw_endpoint_payload' in text or 'response_body' in text: raise ValueError('raw endpoint payload leakage')
    return {'status':'passed','symbols':sorted(EXPECTED),'source':'TWSE_OpenAPI','source_date':'2026-06-26','manifest_sha256':sha(package_dir/'sha256_manifest.json')}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--package-dir',default=str(REPO/'research/staging/m5f/m5f_canonical_market_context_01')); a=ap.parse_args(); print(json.dumps(validate_package(Path(a.package_dir)),ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
