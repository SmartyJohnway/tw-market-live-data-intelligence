#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys,asyncio
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO)); sys.path.insert(0,str(REPO/'scripts'))
from validate_m5f_canonical_market_context_package import validate_package
PKG=REPO/'research/staging/m5f/m5f_canonical_market_context_01'
def _symbols(payload): return [s['symbol'] for s in payload['symbols']]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true',default=True); a=ap.parse_args()
    v=validate_package(PKG); c=json.loads((PKG/'canonical_market_context.json').read_text())
    from fastapi.testclient import TestClient
    from server.main import app
    client=TestClient(app)
    api={p: client.get(p).json() for p in ['/api/context/canonical','/api/context/snapshot','/api/context/source-health','/api/context/capability-summary','/api/context/briefing']}
    legacy=client.get('/api/probe/twse?confirm_manual_probe=true')
    if legacy.status_code != 410: raise SystemExit('legacy FastAPI probe route not disabled')
    if _symbols(api['/api/context/canonical']['content']) != _symbols(c): raise SystemExit('FastAPI canonical mismatch')
    from server import mcp_server
    async def mcp_calls():
        out={}
        for name in ['get_canonical_market_context','get_latest_market_snapshot','get_ai_context_pack','get_source_health','get_capability_matrix','get_chatgpt_briefing']:
            resp=await mcp_server.call_tool(name,{})
            out[name]=json.loads(resp[0].text)
        return out
    mcp=asyncio.run(mcp_calls())
    if _symbols(mcp['get_canonical_market_context']['content']) != _symbols(c): raise SystemExit('MCP canonical mismatch')
    frontend_status='not_run_node_unavailable'
    try:
        import subprocess, tempfile
        adapter_text=(REPO/'frontend/readonly-preview/m5e-market-context-adapter.js').read_text()
        with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False) as ah:
            ah.write(adapter_text); adapter_path=ah.name
        js = f'''
import {{ webcrypto }} from 'node:crypto';
if (!globalThis.crypto) Object.defineProperty(globalThis, 'crypto', {{ value: webcrypto }});
globalThis.window = {{ location: {{ href: 'http://127.0.0.1:8000/frontend/readonly-preview/M5EMarketContextPreview.html' }} }};
const mod = await import('file://' + {json.dumps(adapter_path)});
globalThis.fetch = async () => ({{ ok: true, json: async () => ({json.dumps(api['/api/context/canonical'])}) }});
const context = await mod.fetchValidatedCanonicalFromApi('/api/context/canonical');
const model = mod.buildDisplayModel(context);
if (model.symbols.length !== 3 || model.source !== 'TWSE_OpenAPI') throw new Error('frontend model mismatch');
console.log(JSON.stringify({{status:'ok', symbols:model.symbols.map(s=>s.symbol)}}));
'''
        with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False) as fh:
            fh.write(js); path=fh.name
        cp=subprocess.run(['node', path], capture_output=True, text=True, timeout=10)
        if cp.returncode != 0: raise RuntimeError(cp.stderr or cp.stdout)
        frontend_status=json.loads(cp.stdout)['status']
    except FileNotFoundError:
        frontend_status='not_run_node_unavailable'
    summary={'status':'ok','check_only':True,'symbols':_symbols(c),'source':c['source'],'source_date':c['source_date'],'freshness':c['governance']['stale_status'],'caveats':c['global_caveats'],'manifest_verification':v,'consumer_checks':{'fastapi_paths':list(api),'fastapi_legacy_probe_disabled':True,'mcp_tools':list(mcp),'frontend_adapter_execution':frontend_status}}
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
