from pathlib import Path
from fastapi.testclient import TestClient
from server.main import app
client=TestClient(app)
def test_context_endpoints():
 for path in ['/api/context/canonical','/api/context/snapshot','/api/context/source-health','/api/context/capability-summary','/api/context/briefing']:
  r=client.get(path); assert r.status_code==200; assert r.json()['governance']['network_calls'] is False
def test_canonical_symbols():
 data=client.get('/api/context/canonical').json()['content']; assert [s['symbol'] for s in data['symbols']]==['0050','00929','2330']; assert data['source_date']=='2026-06-26'



def _build_temp_package(tmp_path, stale_status, badge):
 import json, shutil, hashlib
 from scripts.build_m5f_canonical_market_context_package import build_package, write_package
 src=Path('research/staging/m5d/m5d_frontend_publication_candidate_01')
 tmp_path.mkdir(parents=True, exist_ok=True)
 cand=tmp_path/'candidate'; shutil.copytree(src,cand)
 data=json.loads((cand/'market-context.json').read_text())
 data['stale_status']=stale_status; data['badge']=badge
 for row in data['symbols']:
  row['freshness_status']=stale_status; row['delay_status']=stale_status
 (cand/'market-context.json').write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)+'\n')
 manifest=json.loads((cand/'sha256_manifest.json').read_text())
 manifest['files']['market-context.json']=hashlib.sha256((cand/'market-context.json').read_bytes()).hexdigest()
 (cand/'sha256_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+'\n')
 pkg=tmp_path/'pkg'; write_package(pkg, build_package(cand/'market-context.json'))
 return pkg


def test_context_governance_derives_freshness_from_temp_package(monkeypatch, tmp_path):
 import server.main as main
 for status,badge in [('fresh','historical/fresh'),('delayed','historical/delayed')]:
  pkg=_build_temp_package(tmp_path/status, status, badge)
  monkeypatch.setattr(main, 'M5F_PACKAGE_DIR', pkg)
  r=client.get('/api/context/canonical')
  assert r.status_code==200
  gov=r.json()['governance']
  assert gov['stale_status']==status
  assert gov['badge']==badge
  assert gov['realtime_guaranteed'] is False
  assert gov['trading_signal'] is False
  assert gov['production_current_state'] is False
