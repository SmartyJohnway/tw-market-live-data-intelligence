#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot, build_verified_security_master_lookup, resolve_verified_security_identity

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--snapshot',required=True); ap.add_argument('--manifest',required=True); ap.add_argument('--query',required=True); ap.add_argument('--market-context'); ap.add_argument('--allow-fixture-snapshot',action='store_true')
    ns=ap.parse_args(argv)
    snap,_=load_verified_security_master_snapshot(ns.snapshot,ns.manifest,allow_fixture_snapshot=ns.allow_fixture_snapshot)
    res=resolve_verified_security_identity(ns.query,build_verified_security_master_lookup(snap),market_context=ns.market_context,allow_fixture_snapshot=ns.allow_fixture_snapshot)
    print(json.dumps(res,ensure_ascii=False,sort_keys=True,indent=2))
if __name__=='__main__': main()
