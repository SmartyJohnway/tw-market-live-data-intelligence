import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

from scripts.controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload
def test_every_invalid_fixture_fails_with_error_code():
    for case in json.loads((ROOT/'tests/fixtures/staging_payloads/invalid_payloads.json').read_text()):
        errs=validate_controlled_refresh_staging_payload(case['payload']); assert errs, case['name']; assert errs[0]['code']
