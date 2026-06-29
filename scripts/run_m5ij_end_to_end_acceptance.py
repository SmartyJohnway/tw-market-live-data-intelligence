#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, subprocess, sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))

def check(cond,msg,checks): checks.append({'check':msg,'status':'passed' if cond else 'failed'}); return cond

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--execute-refresh',action='store_true'); ap.add_argument('--authorization'); a=ap.parse_args()
    if a.execute_refresh:
        if not a.authorization: print('authorization required',file=sys.stderr); return 2
        cmd=[sys.executable,'scripts/run_m5i_explicit_bounded_refresh.py','--execute-refresh','--authorization-token',a.authorization,'--source','TWSE_OpenAPI','--targets','0050','00929','2330','--no-frontend-publication','--no-production-refresh','--no-generated-refresh','--no-trading-output']
        r=subprocess.run(cmd,cwd=REPO,text=True,capture_output=True)
        if r.returncode: print(r.stdout+r.stderr); return r.returncode
    checks=[]
    from scripts.validate_m5f_canonical_market_context_package import validate_package
    pkg=REPO/'research/staging/m5f/m5f_canonical_market_context_01'
    res=validate_package(pkg); check(res['status']=='passed','m5f_package_validates',checks)
    canonical=json.loads((pkg/'canonical_market_context.json').read_text())
    forbidden=json.dumps(canonical).lower(); check(not any(x in forbidden for x in ['raw_payload','recommendation','target_price','"buy"','"sell"','"hold"','ranking']),'no_raw_or_trading_fields',checks)
    from fastapi.testclient import TestClient
    from server.main import app
    c=TestClient(app)
    for ep in ['/api/health','/api/governance','/api/context/canonical','/api/context/snapshot','/api/context/source-health','/api/context/capability-summary','/api/context/briefing']:
        check(c.get(ep).status_code==200,f'fastapi_{ep}',checks)
    check(c.get('/api/probe/twse').status_code==410,'fastapi_probe_disabled_410',checks)
    import server.mcp_server as mcp
    tools=asyncio.run(mcp.list_tools())
    names=[t.name for t in tools]
    check('run_m3g04_controlled_live_probe_evidence' not in names,'legacy_mcp_live_tool_not_listed',checks)
    out=asyncio.run(mcp.call_tool('run_m3g04_controlled_live_probe_evidence',{}))[0].text
    check('disabled_pending_m5i' in out,'legacy_mcp_live_tool_disabled_direct_call',checks)
    check(asyncio.run(mcp.call_tool('get_canonical_market_context',{}))[0].text.find('canonical_market_context')>=0,'mcp_readonly_canonical',checks)
    try:
        from scripts.run_m5e_controlled_frontend_publication import check_only as m5e_check_only
        m5e = m5e_check_only()
        m5e_ok = (
            m5e.get('status') == 'superseded_by_m5f'
            and m5e.get('superseded_by_m5f') is True
            and m5e.get('publication_performed') is False
            and m5e.get('frontend_publication_authorized') is False
        )
    except Exception as exc:
        m5e = {'error': str(exc)}
        m5e_ok = False
    check(m5e_ok,'m5e_superseded_by_m5f',checks)
    readme=(REPO/'README.md').read_text(encoding='utf-8')
    check('M3G-08' not in readme and 'disabled pending M5I' in readme,'readme_stale_wording_removed',checks)
    git=subprocess.run(['git','diff','--name-only','origin/main...HEAD'],cwd=REPO,text=True,capture_output=True)
    changed=set(git.stdout.splitlines()) if git.returncode==0 else set()
    forbidden_prefixes=('frontend/public/','research/generated/','research/live_probe_runs/m5b/','research/staging/m5c/','research/staging/m5d/','production/','prod/','broker/','credentials/','tokens/','.env')
    check(not any(any(x.startswith(pref) for pref in forbidden_prefixes) for x in changed),'no_forbidden_paths_changed',checks)
    failed=[x for x in checks if x['status']!='passed']
    report={'status':'passed' if not failed else 'failed','network_calls':False,'checks':checks,'m5f':res,'release_status':'m5ij_local_product_release_candidate' if not failed else 'request_review_blocked'}
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if not failed else 1
if __name__=='__main__': raise SystemExit(main())
