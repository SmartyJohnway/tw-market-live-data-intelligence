from scripts.validate_m5c_supplemental_audit import validate

def test_m5c_supplemental_audit_validates():
    assert validate()==[]
import json
from scripts.validate_m5c_supplemental_audit import AUDIT, validate

def test_audit_rejects_wrong_artifact_type(tmp_path):
    data=json.loads(AUDIT.read_text(encoding="utf-8"))
    for artifact in data['artifacts']:
        if artifact['path']=='sha256_manifest.json':
            artifact['artifact_type']='package_artifact'
    p=tmp_path/'audit.json'; p.write_text(json.dumps(data), encoding="utf-8")
    assert any(e['code']=='audit_artifact_type_mismatch' for e in validate(p))
