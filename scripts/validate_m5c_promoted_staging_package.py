from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
REQ=['authorization_snapshot.json','request_snapshot.json','source_binding.json','staging_payload.json','promotion_receipt.json','validation_report.json','lineage.json','evidence_ledger.json','rollback_plan.json','frontend_readonly_context_package.json','run_summary.json','sha256_manifest.json']
TARGETS={'2330','0050','00929'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def validate(d):
    d=Path(d); errs=[]
    for n in REQ:
        if not (d/n).exists(): errs.append({'code':'missing_artifact','path':n})
    if errs: return errs
    man=load(d/'sha256_manifest.json').get('manifest',{})
    if set(man)!=set(REQ)-{'sha256_manifest.json'}: errs.append({'code':'manifest_artifact_set_mismatch'})
    for n,h in man.items():
        if sha(d/n)!=h: errs.append({'code':'manifest_hash_mismatch','path':n})
    for n in REQ:
        obj=load(d/n)
        for k,v in {'historical_evidence_snapshot':True,'current_realtime':False,'realtime_guaranteed':False,'staging_only':True,'production_ready':False,'frontend_publication_authorized':False,'generated_artifact_write':False,'trading_signal':False}.items():
            if obj.get(k)!=v: errs.append({'code':'flag_mismatch','path':n,'field':k})
    payload=load(d/'staging_payload.json'); rows=payload.get('rows',[]); syms=[str(r.get('symbol')) for r in rows]
    if set(syms)!=TARGETS or len(syms)!=len(set(syms)): errs.append({'code':'target_uniqueness_failed'})
    if any(r.get('source')!='TWSE_OpenAPI' for r in rows): errs.append({'code':'source_mismatch'})
    if payload.get('full_market_payload_retained') is not False: errs.append({'code':'raw_full_market_payload_forbidden'})
    return errs
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--package-dir',required=True); ns=ap.parse_args(argv)
    errs=validate(ns.package_dir); print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
