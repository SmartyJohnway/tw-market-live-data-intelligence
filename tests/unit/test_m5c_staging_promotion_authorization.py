from scripts.validate_m5c_staging_promotion_authorization import validate

def test_m5c_authorization_binding_passes():
    assert validate() == []
