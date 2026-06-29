import json, subprocess, sys
from pathlib import Path
PKG=Path('research/staging/m5f/m5f_canonical_market_context_01')
def test_derivatives_consistent():
 c=json.loads((PKG/'canonical_market_context.json').read_text()); s=json.loads((PKG/'latest_market_snapshot.json').read_text()); a=json.loads((PKG/'ai_context_pack.json').read_text())
 assert [x['symbol'] for x in c['symbols']]==[x['symbol'] for x in s['symbols']]==[x['symbol'] for x in a['symbols']]
 assert c['source_date']==s['source_date']=='2026-06-26'
def test_demo_json_summary():
 cp=subprocess.run([sys.executable,'scripts/run_m5fgh_local_product_demo.py','--check-only'],capture_output=True,text=True,check=True)
 data=json.loads(cp.stdout); assert data['symbols']==['0050','00929','2330']; assert data['freshness']=='stale'
