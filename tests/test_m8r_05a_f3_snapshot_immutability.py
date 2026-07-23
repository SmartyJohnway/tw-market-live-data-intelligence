import copy,json
from pathlib import Path
from scripts.m8r_03d_f1_security_master_snapshot_exporter import canonical_json,sha256_json
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
def test_snapshot_is_unchanged():
 s=load_f3_verified_security_master('tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json','tests/fixtures/m8r_05a_f3/verified_security_master_snapshot_manifest.json',allow_fixture_snapshot=True); before=canonical_json(s.snapshot),sha256_json(s.snapshot); r={'schema_version':'unified_market_evidence_request.v1','request_id':'immutable','targets':[{'input':'2330'}],'data_needs':[{'type':'identity','priority':'required'}],'execution_mode':'preview'}; validate_unified_market_evidence_request(r,security_master=s,capability_catalog=json.loads(Path('docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json').read_text()),request_schema=json.loads(Path('schemas/unified_market_evidence_request.v1.schema.json').read_text()),allow_fixture_snapshot=True); assert before==(canonical_json(s.snapshot),sha256_json(s.snapshot))
