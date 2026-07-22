import json,socket
from pathlib import Path
import pytest
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
FIX=Path('tests/fixtures/m8r_05a_f3')
def test_strict_loader_fixture_rejected_in_production_and_usable_in_test_mode():
 with pytest.raises(Exception): load_f3_verified_security_master(FIX/'verified_security_master_snapshot.json',FIX/'verified_security_master_snapshot_manifest.json')
 assert load_f3_verified_security_master(FIX/'verified_security_master_snapshot.json',FIX/'verified_security_master_snapshot_manifest.json',allow_fixture_snapshot=True).validation['valid']
def test_no_network_and_deterministic(monkeypatch):
 def blocked(*a,**k): raise AssertionError('network attempted')
 monkeypatch.setattr(socket,'socket',blocked); monkeypatch.setattr(socket,'create_connection',blocked)
 s=load_f3_verified_security_master(FIX/'verified_security_master_snapshot.json',FIX/'verified_security_master_snapshot_manifest.json',allow_fixture_snapshot=True)
 r={'schema_version':'unified_market_evidence_request.v1','request_id':'net','targets':[{'input':'2330'}],'data_needs':[{'type':'identity','priority':'required'}],'execution_mode':'preview'}; c=json.loads(Path('docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json').read_text()); sc=json.loads(Path('schemas/unified_market_evidence_request.v1.schema.json').read_text())
 a=validate_unified_market_evidence_request(r,security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); b=validate_unified_market_evidence_request(r,security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); assert json.dumps(a,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()==json.dumps(b,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
