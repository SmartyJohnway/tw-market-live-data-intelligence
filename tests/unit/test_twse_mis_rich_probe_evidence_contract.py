import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT_PATH = ROOT / "research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_attempt_20260707T030255Z.json"
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


def test_inventory_points_to_failed_attempt_without_promoting_probe_evidence():
    inv = _load_json(INVENTORY_PATH)
    assert inv["probe_execution_attempted"] is True
    assert inv["probe_executed"] is False
    assert inv["probe_evidence_available"] is False
    assert inv["last_probe_attempt_path"] == ATTEMPT_PATH.relative_to(ROOT).as_posix()
    assert inv["runtime_behavior_changed"] is False
    assert inv["normalization_changed"] is False
    assert inv["full_market_scan"] is False
    assert inv["polling"] is False
    assert inv["scheduler"] is False
    assert inv["ci_network_required"] is False
    assert all(row["observed_in_probe"] is False for row in inv["field_inventory"])
