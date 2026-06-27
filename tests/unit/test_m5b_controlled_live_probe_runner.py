from scripts.run_m5b_controlled_live_probe import validate_execution_scope, map_authorized_targets

def test_check_scope_valid(): assert validate_execution_scope('TWSE_OpenAPI',['2330','0050','00929'],'research/live_probe_runs/m5b/preflight')==[]
def test_mapping(): assert map_authorized_targets(['2330','0050'])=={'2330':'2330','0050':'0050'}


def test_attempt_count_rejects_zero(capsys):
    from scripts.run_m5b_controlled_live_probe import main
    rc = main(['--check-only', '--authorization', 'docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json', '--request', 'tests/fixtures/authorization/valid_m5a_live_probe_request.json', '--source', 'TWSE_OpenAPI', '--targets', '2330', '0050', '00929', '--output-dir', 'research/live_probe_runs/m5b/preflight', '--attempt-count', '0'])
    captured = capsys.readouterr().out
    assert rc == 1
    assert 'attempt_count_out_of_range' in captured
