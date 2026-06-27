from pathlib import Path
from scripts.validate_m5c_promoted_staging_package import validate

def test_committed_package_valid_if_present():
    p=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
    if p.exists(): assert validate(p)==[]
