import json
from pathlib import Path
from scripts.validate_m5c_staging_promotion_authorization import AUTH, validate

def test_m5c_authorization_binding_passes():
    assert validate() == []

def test_m5c_authorization_schema_blocks_extra_and_wrong_destination(tmp_path):
    data=json.loads(AUTH.read_text())
    data['destination']='research/staging/m5c/other'
    data['extra']='forbidden'
    p=tmp_path/'auth.json'; p.write_text(json.dumps(data))
    codes={e['code'] for e in validate(p)}
    assert 'schema_error' in codes
    assert 'binding_mismatch' in codes
