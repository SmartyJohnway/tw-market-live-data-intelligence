import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT_PATH = ROOT / "research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_attempt_20260707T030255Z.json"
SUMMARY_PATH = ROOT / "research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_summary_20260707T034516Z.json"
INVENTORY_PATH = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"
APPROVED_SYMBOLS = [
    "tse_t00.tw",
    "tse_2330.tw",
    "tse_0050.tw",
    "otc_8069.tw",
    "otc_5347.tw",
    "tse_1435.tw",
]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_failed_probe_attempt_contract_is_compact_and_non_runtime():
    attempt = _load_json(ATTEMPT_PATH)
    assert attempt["schema_version"] == "m7a_twse_mis_rich_field_probe_attempt.v1"
    assert attempt["source_id"] == "TWSE_MIS"
    assert attempt["probe_type"] == "manual_bounded_probe_attempt"
    assert attempt["probe_evidence_available"] is False
    assert attempt["runtime_behavior_changed"] is False
    assert attempt["normalization_changed"] is False
    assert attempt["full_market_scan"] is False
    assert attempt["polling"] is False
    assert attempt["scheduler"] is False
    assert attempt["startup_network"] is False
    assert attempt["ci_network_required"] is False
    assert attempt["raw_payload_committed"] is False
    assert attempt["headers_committed"] is False
    assert attempt["cookies_committed"] is False
    assert attempt["session_tokens_committed"] is False
    assert attempt["raw_response_body_committed"] is False
    assert attempt["symbols_requested"] == APPROVED_SYMBOLS
    assert attempt["symbols_observed"] == []
    assert attempt["symbols_failed"] == APPROVED_SYMBOLS
    assert attempt["field_semantics_upgraded"] is False
    assert attempt["observed_in_probe_updated"] is False


def test_successful_probe_summary_contract():
    summary = _load_json(SUMMARY_PATH)
    assert summary["schema_version"] == "m7a_twse_mis_rich_field_probe_summary.v1"
    assert summary["source_id"] == "TWSE_MIS"
    assert summary["probe_type"] == "manual_bounded_probe"
    assert summary["runtime_behavior_changed"] is False
    assert summary["normalization_changed"] is False
    assert summary["full_market_scan"] is False
    assert summary["polling"] is False
    assert summary["scheduler"] is False
    assert summary["startup_network"] is False
    assert summary["ci_network_required"] is False
    assert summary["raw_payload_committed"] is False

    req_evidence = summary["request_evidence"]
    assert req_evidence["headers_committed"] is False
    assert req_evidence["cookies_committed"] is False
    assert req_evidence["session_tokens_committed"] is False
    assert req_evidence["raw_response_body_committed"] is False

    assert summary["symbols_requested"] == APPROVED_SYMBOLS
    assert len(summary["symbols_observed"]) == 6
    assert summary["symbols_failed"] == []
    assert summary["successful_strategy"] == "bootstrap_then_api"

    fps = summary["field_presence_summary"]
    assert len(fps) == 45

    # Observed fields present check
    for f in ["z", "y", "o", "h", "l", "v", "tv", "b", "g", "a", "f", "u", "w", "d", "t", "tlong"]:
        assert fps[f]["present_count"] > 0

    # Newly observed fields
    assert "m" in fps
    assert "nu" in fps

    # Not observed fields in this run
    for f in ["q", "oa", "ob", "ot"]:
        assert fps[f]["present_count"] == 0

    # Verify unit_unverified status in semantics
    for f in ["v", "tv", "g", "f"]:
        assert "unit_unverified" in fps[f]["candidate_semantic"]

    # Verify b and a displayed bid/ask price ladder candidates
    assert fps["b"]["candidate_semantic"] == "displayed_bid_price_ladder_candidate"
    assert fps["a"]["candidate_semantic"] == "displayed_ask_price_ladder_candidate"


def test_inventory_points_to_successful_probe_evidence():
    inv = _load_json(INVENTORY_PATH)
    assert inv["probe_execution_attempted"] is True
    assert inv["probe_executed"] is True
    assert inv["probe_evidence_available"] is True
    assert inv["last_successful_probe_summary_path"] == "research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_summary_20260707T034516Z.json"
    assert inv["last_probe_attempt_path"] == "research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_attempt_20260707T030255Z.json"
    assert inv["last_probe_attempt_status"] == "success_bootstrap_then_api"
    assert inv["last_successful_strategy"] == "bootstrap_then_api"
    assert inv["runtime_behavior_changed"] is False
    assert inv["normalization_changed"] is False
    assert inv["full_market_scan"] is False
    assert inv["polling"] is False
    assert inv["scheduler"] is False
    assert inv["ci_network_required"] is False

    # Extract m and nu
    m_field = None
    nu_field = None
    for row in inv["field_inventory"]:
        if row["raw_field"] == "m":
            m_field = row
        elif row["raw_field"] == "nu":
            nu_field = row

    assert m_field is not None
    assert nu_field is not None

    for field in [m_field, nu_field]:
        assert field["normalization_status"] == "preserve_raw_only"
        assert field["ai_exposure_status"] == "not_safe_yet"
        assert field["semantic_status"] == "unknown"
        assert field["observed_in_probe"] is True

    # Not observed fields should remain false
    for row in inv["field_inventory"]:
        if row["raw_field"] in ["q", "oa", "ob", "ot"]:
            assert row["observed_in_probe"] is False
