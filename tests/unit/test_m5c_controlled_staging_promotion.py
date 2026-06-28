from scripts.run_m5c_controlled_staging_promotion import check

def test_m5c_controlled_check_only_passes_before_execution_or_blocks_after_single_use():
    errors = check()
    assert errors == [] or any(e['code'] in {'destination_exists','authorization_already_consumed'} for e in errors)
