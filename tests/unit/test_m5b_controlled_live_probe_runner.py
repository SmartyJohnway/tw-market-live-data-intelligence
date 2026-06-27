from scripts.run_m5b_controlled_live_probe import validate_execution_scope, map_authorized_targets

def test_check_scope_valid(): assert validate_execution_scope('TWSE_OpenAPI',['2330','0050','00929'],'research/live_probe_runs/m5b/preflight')==[]
def test_mapping(): assert map_authorized_targets(['2330','0050'])=={'2330':'2330','0050':'0050'}
