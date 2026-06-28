import json
from scripts.validate_m5d_frontend_publication_request import REQ, validate

def test_m5d_request_is_request_only():
    assert validate()==[]

def test_m5d_request_rejects_wrong_hash_and_approval_material(tmp_path):
    data=json.loads(REQ.read_text())
    data['m5c_staging_manifest_sha256']='0'*64
    data['approval_token']='not-allowed'
    p=tmp_path/'request.json'; p.write_text(json.dumps(data))
    codes={e['code'] for e in validate(p)}
    assert 'schema_error' in codes
    assert 'staging_manifest_sha_mismatch' in codes
    assert 'approval_material_forbidden' in codes
