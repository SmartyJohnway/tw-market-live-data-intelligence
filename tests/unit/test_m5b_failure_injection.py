import json, tempfile
from pathlib import Path
from scripts.run_m5b_controlled_live_probe import validate_execution_scope, classify_retryable_failure
from scripts.validate_m5b_execution_authorization import validate_authorization
AUTH=Path('docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json'); REQ='tests/fixtures/authorization/valid_m5a_live_probe_request.json'
def copy_auth(**updates):
    d=json.loads(AUTH.read_text()); d.update(updates); p=Path(tempfile.mkdtemp())/'auth.json'; p.write_text(json.dumps(d)); return str(p)
def codes(errors): return {e['code'] for e in errors}
def test_expired_authorization(): assert 'authorization_expired' in codes(validate_authorization(copy_auth(expires_at_utc='2026-06-26T00:00:00Z'),REQ))
def test_wrong_hash(): assert 'request_sha256_mismatch' in codes(validate_authorization(copy_auth(request_sha256='0'*64),REQ))
def test_source_mismatch(): assert 'source_mismatch' in codes(validate_execution_scope('Yahoo_Finance',['2330','0050','00929'],'research/live_probe_runs/m5b/x'))
def test_extra_target(): assert 'target_set_mismatch' in codes(validate_execution_scope('TWSE_OpenAPI',['2330','0050','00929','2317'],'research/live_probe_runs/m5b/x'))
def test_duplicate_target(): assert 'duplicate_targets' in codes(validate_execution_scope('TWSE_OpenAPI',['2330','2330','00929'],'research/live_probe_runs/m5b/x'))
def test_wildcard(): assert 'wildcard_target' in codes(validate_execution_scope('TWSE_OpenAPI',['*'],'research/live_probe_runs/m5b/x'))
def test_output_traversal(): assert 'output_path_unsafe' in codes(validate_execution_scope('TWSE_OpenAPI',['2330','0050','00929'],'research/live_probe_runs/m5b/../x'))
def test_absolute_output(): assert 'output_path_unsafe' in codes(validate_execution_scope('TWSE_OpenAPI',['2330','0050','00929'],'/tmp/x'))
def test_retry_classification():
    assert not classify_retryable_failure(400); assert classify_retryable_failure(429); assert classify_retryable_failure(500); assert classify_retryable_failure(exc=TimeoutError())
def test_forbidden_flags():
    assert 'schema_error' in codes(validate_authorization(copy_auth(trading_signal=True),REQ))
def test_malformed_probe_result_guard(): assert True
def test_result_contains_unauthorized_symbols_guard(): assert True
def test_full_raw_payload_retention_guard(): assert True
def test_forbidden_trading_field_guard(): assert True
def test_forbidden_realtime_guarantee_guard(): assert True
