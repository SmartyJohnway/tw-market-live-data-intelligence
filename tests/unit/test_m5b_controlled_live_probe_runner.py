from scripts.run_m5b_controlled_live_probe import validate_execution_scope, map_authorized_targets

def test_check_scope_valid(): assert validate_execution_scope('TWSE_OpenAPI',['2330','0050','00929'],'research/live_probe_runs/m5b/preflight')==[]
def test_mapping(): assert map_authorized_targets(['2330','0050'])=={'2330':'2330','0050':'0050'}


def test_attempt_count_rejects_zero(capsys):
    from scripts.run_m5b_controlled_live_probe import main
    rc = main(['--check-only', '--authorization', 'docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json', '--request', 'tests/fixtures/authorization/valid_m5a_live_probe_request.json', '--source', 'TWSE_OpenAPI', '--targets', '2330', '0050', '00929', '--output-dir', 'research/live_probe_runs/m5b/preflight', '--attempt-count', '0'])
    captured = capsys.readouterr().out
    assert rc == 1
    assert 'attempt_count_out_of_range' in captured


def test_output_root_rejected_before_network():
    errors = validate_execution_scope('TWSE_OpenAPI', ['2330', '0050', '00929'], 'research/live_probe_runs/m5b')
    assert any(error['code'] == 'output_root_forbidden' for error in errors)


def test_output_reserved_consumption_dir_rejected_before_network():
    errors = validate_execution_scope('TWSE_OpenAPI', ['2330', '0050', '00929'], 'research/live_probe_runs/m5b/authorization_consumption')
    assert any(error['code'] == 'output_reserved_dir' for error in errors)


def test_existing_output_dir_rejected_before_network(tmp_path, monkeypatch):
    import scripts.run_m5b_controlled_live_probe as runner
    monkeypatch.setattr(runner, 'ROOT', tmp_path / 'm5b')
    existing = tmp_path / 'm5b' / 'm5b_twse_openapi_20260627T010203Z'
    existing.mkdir(parents=True)
    errors = runner.validate_execution_scope('TWSE_OpenAPI', ['2330', '0050', '00929'], str(existing))
    assert any(error['code'] == 'output_already_exists' for error in errors)
