import json
import tempfile
from pathlib import Path

import pytest

import scripts.run_m5b_controlled_live_probe as runner
from scripts.build_m5b_staging_candidate import build
from scripts.validate_m5b_execution_authorization import validate_authorization

AUTH = Path('docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json')
REQ = 'tests/fixtures/authorization/valid_m5a_live_probe_request.json'


def copy_auth(**updates):
    data = json.loads(AUTH.read_text())
    data.update(updates)
    path = Path(tempfile.mkdtemp()) / 'auth.json'
    path.write_text(json.dumps(data))
    return str(path)


def codes(errors):
    return {error['code'] for error in errors}


def test_expired_authorization():
    assert 'authorization_expired' in codes(validate_authorization(copy_auth(expires_at_utc='2026-06-26T00:00:00Z'), REQ))


def test_wrong_hash():
    assert 'request_sha256_mismatch' in codes(validate_authorization(copy_auth(request_sha256='0' * 64), REQ))


def test_source_mismatch():
    assert 'source_mismatch' in codes(runner.validate_execution_scope('Yahoo_Finance', ['2330', '0050', '00929'], 'research/live_probe_runs/m5b/x'))


def test_extra_target():
    assert 'target_set_mismatch' in codes(runner.validate_execution_scope('TWSE_OpenAPI', ['2330', '0050', '00929', '2317'], 'research/live_probe_runs/m5b/x'))


def test_duplicate_target():
    assert 'duplicate_targets' in codes(runner.validate_execution_scope('TWSE_OpenAPI', ['2330', '2330', '00929'], 'research/live_probe_runs/m5b/x'))


def test_wildcard():
    assert 'wildcard_target' in codes(runner.validate_execution_scope('TWSE_OpenAPI', ['*'], 'research/live_probe_runs/m5b/x'))


def test_output_traversal():
    assert 'output_path_unsafe' in codes(runner.validate_execution_scope('TWSE_OpenAPI', ['2330', '0050', '00929'], 'research/live_probe_runs/m5b/../x'))


def test_absolute_output():
    assert 'output_path_unsafe' in codes(runner.validate_execution_scope('TWSE_OpenAPI', ['2330', '0050', '00929'], '/tmp/x'))


def test_retry_classification():
    assert not runner.classify_retryable_failure(400)
    assert runner.classify_retryable_failure(429)
    assert runner.classify_retryable_failure(500)
    assert runner.classify_retryable_failure(exc=TimeoutError())


def test_forbidden_flags():
    assert 'schema_error' in codes(validate_authorization(copy_auth(trading_signal=True), REQ))


def test_single_use_consumption_is_global_per_authorization_id(monkeypatch, tmp_path):
    auth_path = copy_auth(authorization_id='m5b-test-single-use')
    monkeypatch.setattr(runner, 'CONSUMPTION_ROOT', tmp_path / 'authorization_consumption')
    first = runner._create_consumption_record(auth_path, REQ, 'research/live_probe_runs/m5b/one')
    assert first.exists()
    with pytest.raises(FileExistsError):
        runner._create_consumption_record(auth_path, REQ, 'research/live_probe_runs/m5b/two')


def test_malformed_probe_result_is_parse_failed():
    errors = [{'code': 'json_parse_failed', 'detail': 'not json'}]
    assert runner._contract_status([], 200, False, errors) == 'parse_failed'


def test_result_contains_unauthorized_symbols_guard():
    row = {'symbol': '2317', 'realtime_guaranteed': False}
    errors = []
    if row['symbol'] not in runner.ALLOWED_TARGETS:
        errors.append({'code': 'unauthorized_symbol_in_result'})
    assert runner._contract_status([], 200, True, errors) == 'execution_failed'


def test_attempted_full_raw_payload_retention_guard(tmp_path):
    run_dir = tmp_path / 'run'
    run_dir.mkdir()
    result = {'rows': [{'symbol': '2330', 'raw_full_response': {'unexpected': 'payload'}}]}
    (run_dir / 'bounded_probe_result.json').write_text(json.dumps(result))
    (run_dir / 'run_summary.json').write_text(json.dumps({'run_id': 'run'}))
    with pytest.raises(ValueError, match='forbidden'):
        build(run_dir)


def test_forbidden_trading_field_guard():
    errors = runner._detect_forbidden_normalized_fields({'symbol': '2330', 'buy': 'yes'}, 0)
    assert {'code': 'forbidden_trading_field', 'path': '$.rows[0].buy'} in errors
    assert runner._contract_status([], 200, True, errors) == 'execution_failed'


def test_forbidden_realtime_guarantee_guard():
    errors = runner._detect_forbidden_normalized_fields({'symbol': '2330', 'realtime_guaranteed': True}, 0)
    assert {'code': 'forbidden_realtime_guarantee', 'path': '$.rows[0].realtime_guaranteed'} in errors
    assert runner._contract_status([], 200, True, errors) == 'execution_failed'


def test_non_retryable_http_400_fails_contract():
    assert runner._contract_status([], 400, False, [{'code': 'http_failed'}]) == 'http_failed'
