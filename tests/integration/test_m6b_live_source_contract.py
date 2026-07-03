import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.run_m6b_source_contract_preflight import build_report, bounded_watchlist
from scripts.m5k_common import execute_live_observation


@pytest.mark.integration
@pytest.mark.network
@pytest.mark.release_preflight
def test_m6b_bounded_live_source_contracts_governed():
    live = execute_live_observation(bounded_watchlist(), write_latest=False, timeout=12)
    report = build_report(mode="execute_live_contract_check", live_result=live)
    assert report["network_calls_may_have_occurred"] is True
    assert report["targets"] == ["2330", "0050", "TX"]
    assert report["raw_payload_included"] is False
    assert len(report["checks"]) == 3
    for check in report["checks"]:
        assert check["source_family"] in {"TWSE_MIS", "TAIFEX_MIS"}
        assert check["json_parse_status"] in {"parsed", "failed_closed"}
        assert check["normalization_status"] in {"normalized_observation", "governed_failure"}
        assert check["raw_payload_included"] is False
