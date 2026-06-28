from fastapi.testclient import TestClient
from server.main import app
client=TestClient(app)
def test_context_endpoints():
 for path in ['/api/context/canonical','/api/context/snapshot','/api/context/source-health','/api/context/capability-summary','/api/context/briefing']:
  r=client.get(path); assert r.status_code==200; assert r.json()['governance']['network_calls'] is False
def test_canonical_symbols():
 data=client.get('/api/context/canonical').json()['content']; assert [s['symbol'] for s in data['symbols']]==['0050','00929','2330']; assert data['source_date']=='2026-06-26'
