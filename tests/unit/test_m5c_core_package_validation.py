import json
from pathlib import Path
import scripts.run_m5c_controlled_staging_promotion as runner
from scripts.validate_m5c_promoted_staging_package import validate_core_package

def test_core_validation_accepts_fresh_tmp_package_without_historical_audit_or_correction(tmp_path):
    package=tmp_path/'fresh_package'
    package.mkdir()
    consumption=tmp_path/'fresh_consumption.json'
    auth=json.loads(Path('docs/authorization/decisions/M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZATION.json').read_text())
    consumption.write_text(json.dumps({'authorization_id':auth['authorization_id'],'destination':runner.DEST,'status':'finalizing'}))
    runner._build(package, str(consumption))
    assert validate_core_package(package, allowed_consumption_statuses={'finalizing'}) == []
