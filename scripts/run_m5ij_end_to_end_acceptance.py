#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, subprocess, sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))

import traceback

def record_check(checks, msg, cond, details=None):
    rec = {'check': msg, 'status': 'passed' if cond else 'failed'}
    if not cond and details:
        rec['details'] = details
    checks.append(rec)
    return cond

def run_checks():
    checks=[]
    from scripts.validate_m5f_canonical_market_context_package import validate_package
    pkg=REPO/'research/staging/m5f/m5f_canonical_market_context_01'
    try:
        res=validate_package(pkg)
        record_check(checks, 'm5f_package_validates', res['status']=='passed', {'actual_status': res.get('status')})
    except Exception as e:
        record_check(checks, 'm5f_package_validates', False, {'exception_type': type(e).__name__, 'exception_message': str(e), 'traceback_excerpt': traceback.format_exc()})
        res={'status': 'failed'}

    try:
        canonical=json.loads((pkg/'canonical_market_context.json').read_text())
        forbidden=json.dumps(canonical).lower()
        forbidden_found = [x for x in ['raw_payload','recommendation','target_price','"buy"','"sell"','"hold"','ranking'] if x in forbidden]
        record_check(checks, 'no_raw_or_trading_fields', not forbidden_found, {'found': forbidden_found})
    except Exception as e:
        record_check(checks, 'no_raw_or_trading_fields', False, {'exception_type': type(e).__name__, 'exception_message': str(e)})

    from fastapi.testclient import TestClient
    from server.main import app
    c=TestClient(app)
    for ep in ['/api/health','/api/governance','/api/context/canonical','/api/context/snapshot','/api/context/source-health','/api/context/capability-summary','/api/context/briefing']:
        r = c.get(ep)
        record_check(checks, f'fastapi_{ep}', r.status_code==200, {'actual_status_code': r.status_code})
    r = c.get('/api/probe/twse')
    record_check(checks, 'fastapi_probe_disabled_410', r.status_code==410, {'actual_status_code': r.status_code})

    import server.mcp_server as mcp
    tools=asyncio.run(mcp.list_tools())
    names=[t.name for t in tools]
    record_check(checks, 'legacy_mcp_live_tool_not_listed', 'run_m3g04_controlled_live_probe_evidence' not in names, {'listed_tools': names})
    out=asyncio.run(mcp.call_tool('run_m3g04_controlled_live_probe_evidence',{}))[0].text
    record_check(checks, 'legacy_mcp_live_tool_disabled_direct_call', 'disabled_pending_m5i' in out, {'actual_output': out})
    out=asyncio.run(mcp.call_tool('get_canonical_market_context',{}))[0].text
    record_check(checks, 'mcp_readonly_canonical', 'canonical_market_context' in out, {'actual_output_snippet': out[:100]})

    m5e_details = {'expected_status': 'superseded_by_m5f', 'actual_status': None, 'publication_performed': None, 'publication_authorized': None}
    try:
        from scripts.run_m5e_controlled_frontend_publication import check_only as m5e_check_only
        m5e = m5e_check_only()
        m5e_details['actual_status'] = m5e.get('status')
        m5e_details['publication_performed'] = m5e.get('publication_performed')
        m5e_details['publication_authorized'] = m5e.get('frontend_publication_authorized')
        m5e_ok = (
            m5e.get('status') == 'superseded_by_m5f'
            and m5e.get('superseded_by_m5f') is True
            and m5e.get('publication_performed') is False
            and m5e.get('frontend_publication_authorized') is False
        )
        m5e_details['reason'] = 'check_only returned mismatched state fields' if not m5e_ok else None
    except Exception as exc:
        m5e_details['exception_type'] = type(exc).__name__
        m5e_details['exception_message'] = str(exc)
        m5e_details['traceback_excerpt'] = traceback.format_exc()
        m5e_ok = False
    record_check(checks, 'm5e_superseded_by_m5f', m5e_ok, m5e_details)

    readme=(REPO/'README.md').read_text(encoding='utf-8')
    readme_ok = 'M3G-08' not in readme and 'disabled pending M5I' in readme
    record_check(checks, 'readme_stale_wording_removed', readme_ok, {'reason': 'Stale M3G-08 wording found or missing M5I pending text'})

    git=subprocess.run(['git','diff','--name-only','origin/main...HEAD'],cwd=REPO,text=True,capture_output=True)
    changed=set(git.stdout.splitlines()) if git.returncode==0 else set()
    forbidden_prefixes=('frontend/public/','research/generated/','research/live_probe_runs/m5b/','research/staging/m5c/','research/staging/m5d/','production/','prod/','broker/','credentials/','tokens/','.env')
    found_forbidden = [x for x in changed if any(x.startswith(pref) for pref in forbidden_prefixes)]
    record_check(checks, 'no_forbidden_paths_changed', not found_forbidden, {'changed_forbidden_paths': found_forbidden, 'git_returncode': git.returncode})

    return checks, res

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--execute-refresh',action='store_true'); ap.add_argument('--authorization'); a=ap.parse_args()
    if a.execute_refresh:
        if not a.authorization: print('authorization required',file=sys.stderr); return 2
        cmd=[sys.executable,'scripts/run_m5i_explicit_bounded_refresh.py','--execute-refresh','--authorization-token',a.authorization,'--source','TWSE_OpenAPI','--targets','0050','00929','2330','--no-frontend-publication','--no-production-refresh','--no-generated-refresh','--no-trading-output']
        r=subprocess.run(cmd,cwd=REPO,text=True,capture_output=True)
        if r.returncode: print(r.stdout+r.stderr); return r.returncode

    checks, res = run_checks()
    failed=[x for x in checks if x['status']!='passed']
    report={'status':'passed' if not failed else 'failed','network_calls':False,'checks':checks,'m5f':res,'release_status':'m5ij_local_product_release_candidate' if not failed else 'request_review_blocked'}
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if not failed else 1
if __name__=='__main__': raise SystemExit(main())
