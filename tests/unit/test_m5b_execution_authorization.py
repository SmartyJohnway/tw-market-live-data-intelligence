from scripts.validate_m5b_execution_authorization import validate_authorization
AUTH='docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json'; REQ='tests/fixtures/authorization/valid_m5a_live_probe_request.json'
def test_valid_authorization(): assert validate_authorization(AUTH,REQ)==[]
