#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'scripts'))
from validate_m5f_canonical_market_context_package import validate_package
PKG=REPO/'research/staging/m5f/m5f_canonical_market_context_01'
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true',default=True); a=ap.parse_args()
 v=validate_package(PKG); c=json.loads((PKG/'canonical_market_context.json').read_text())
 summary={'status':'ok','check_only':True,'symbols':[s['symbol'] for s in c['symbols']],'source':c['source'],'source_date':c['source_date'],'freshness':c['governance']['stale_status'],'caveats':c['global_caveats'],'consumer_paths':{'frontend':'frontend/readonly-preview/M5EMarketContextPreview.html','fastapi':['/api/context/canonical','/api/context/snapshot','/api/context/source-health','/api/context/capability-summary','/api/context/briefing'],'mcp':['get_canonical_market_context','get_source_health','get_capability_matrix','get_source_catalog','get_latest_market_snapshot','get_watchlist_observations','get_ai_context_pack','get_chatgpt_briefing']},'manifest_verification':v}
 print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
