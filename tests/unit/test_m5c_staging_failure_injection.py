import json
from pathlib import Path
from scripts.validate_m5c_promoted_staging_package import validate

def test_missing_artifact_blocked(tmp_path):
    (tmp_path/'sha256_manifest.json').write_text(json.dumps({'manifest':{}}))
    assert any(e['code']=='missing_artifact' for e in validate(tmp_path))
