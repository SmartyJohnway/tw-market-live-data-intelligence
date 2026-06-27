from datetime import datetime, timezone
import json
from pathlib import Path

from scripts.validate_m5b_execution_authorization import validate_authorization

AUTH = 'docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json'
REQ = 'tests/fixtures/authorization/valid_m5a_live_probe_request.json'
RECEIPT = 'research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z/execution_receipt.json'


def codes(errors):
    return {error['code'] for error in errors}


def test_valid_authorization_preflight_with_fixed_now():
    fixed_now = datetime(2026, 6, 27, 1, 0, tzinfo=timezone.utc)
    assert validate_authorization(AUTH, REQ, now=fixed_now) == []


def test_authorization_preflight_before_authorized_rejected():
    before = datetime(2026, 6, 26, 23, 59, 59, tzinfo=timezone.utc)
    assert 'authorization_not_yet_valid' in codes(validate_authorization(AUTH, REQ, now=before, mode='execution_preflight'))


def test_authorization_preflight_exact_authorized_passes():
    exact = datetime(2026, 6, 27, 0, 0, tzinfo=timezone.utc)
    assert validate_authorization(AUTH, REQ, now=exact, mode='execution_preflight') == []


def test_authorization_preflight_just_before_expiry_passes():
    just_before = datetime(2026, 6, 27, 23, 59, 59, 999999, tzinfo=timezone.utc)
    assert validate_authorization(AUTH, REQ, now=just_before, mode='execution_preflight') == []


def test_authorization_preflight_exact_expiry_rejected():
    exact_expiry = datetime(2026, 6, 28, 0, 0, tzinfo=timezone.utc)
    assert 'authorization_expired' in codes(validate_authorization(AUTH, REQ, now=exact_expiry, mode='execution_preflight'))


def test_receipt_audit_ignores_current_wall_clock_after_expiry():
    future_now = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert validate_authorization(AUTH, REQ, receipt=RECEIPT, now=future_now, mode='receipt_audit') == []


def test_receipt_audit_exact_expiry_rejected(tmp_path):
    receipt = json.loads(Path(RECEIPT).read_text())
    receipt['retrieved_at_utc'] = '2026-06-28T00:00:00+00:00'
    receipt_path = tmp_path / 'receipt.json'
    receipt_path.write_text(json.dumps(receipt))
    errors = validate_authorization(AUTH, REQ, receipt=receipt_path, mode='receipt_audit')
    assert 'receipt_outside_authorization_window' in codes(errors)
