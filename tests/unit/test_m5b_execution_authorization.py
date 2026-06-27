from datetime import datetime, timezone

from scripts.validate_m5b_execution_authorization import validate_authorization

AUTH = 'docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json'
REQ = 'tests/fixtures/authorization/valid_m5a_live_probe_request.json'
RECEIPT = 'research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z/execution_receipt.json'


def test_valid_authorization_preflight_with_fixed_now():
    fixed_now = datetime(2026, 6, 27, 1, 0, tzinfo=timezone.utc)
    assert validate_authorization(AUTH, REQ, now=fixed_now) == []


def test_authorization_preflight_expires_after_window():
    expired_now = datetime(2026, 6, 28, 0, 0, 1, tzinfo=timezone.utc)
    errors = validate_authorization(AUTH, REQ, now=expired_now, mode='execution_preflight')
    assert any(error['code'] == 'authorization_expired' for error in errors)


def test_receipt_audit_ignores_current_wall_clock_after_expiry():
    future_now = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert validate_authorization(AUTH, REQ, receipt=RECEIPT, now=future_now, mode='receipt_audit') == []
