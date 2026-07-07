import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"


def load_inventory():
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def test_twse_mis_rich_inventory_boundary_flags():
    inv = load_inventory()
    assert inv["schema_version"] == "m7a_twse_mis_rich_field_inventory.v1"
    assert inv["source_id"] == "TWSE_MIS"
    assert inv["runtime_behavior_changed"] is False
    assert inv["normalization_changed"] is False
    assert inv["full_market_scan"] is False
    assert inv["polling"] is False
    assert inv["scheduler"] is False
    assert inv["probe_executed"] is False
    assert inv["manual_probe_harness_added"] is True
    assert inv["probe_evidence_available"] is False
    assert inv["ci_network_required"] is False
    harness = inv["manual_probe_harness"]
    assert harness["script"] == "scripts/probe_twse_mis_rich_fields.py"
    assert harness["execution_mode"] == "manual_explicit_only"
    assert harness["max_symbols_limit"] <= 10
    assert harness["writes_runtime_artifacts"] is False
    assert harness["writes_m5k_latest_observation"] is False
    assert harness["raw_payload_committed"] is False
    assert harness["ci_invoked"] is False


def test_twse_mis_required_fields_are_inventoried_and_not_discarded():
    inv = load_inventory()
    fields = {row["raw_field"]: row for row in inv["field_inventory"]}
    for required in ["z", "y", "o", "h", "l", "v", "tv", "b", "g", "a", "f", "u", "w", "d", "t", "tlong"]:
        assert required in fields

    assert fields["y"]["candidate_normalized_fact"] in {
        "price_facts.previous_close",
        "price_facts.previous_close_candidate",
    }
    assert fields["y"]["validation_status"] in {
        "partially_validated_from_existing_code",
        "requires_probe_validation",
        "requires_cross_source_validation",
    }

    assert fields["v"]["unit_status"] in {"unverified", "requires_validation"}
    assert fields["tv"]["unit_status"] in {"unverified", "requires_validation"}

    assert fields["b"]["candidate_normalized_fact"].startswith("displayed_depth_facts")
    assert fields["a"]["candidate_normalized_fact"].startswith("displayed_depth_facts")

    for row in inv["field_inventory"]:
        assert row["normalization_status"] != "discard"


def test_twse_mis_unknown_fields_are_preserved_raw_only():
    inv = load_inventory()
    fields = {row["raw_field"]: row for row in inv["field_inventory"]}
    for raw_field in ["@", "ps", "pid", "pz", "bp", "m%", "^", "#", "mt", "i", "ip", "p", "s", "nf", "ts", "q", "r", "oa", "ob"]:
        row = fields[raw_field]
        assert row["semantic_status"] == "unknown" or row["ai_exposure_status"] == "not_safe_yet"
        assert row["normalization_status"] == "preserve_raw_only" or row["ai_exposure_status"] == "not_safe_yet"


def test_twse_mis_forbidden_language_guardrails_are_explicit():
    inv = load_inventory()
    forbidden = set(inv["semantic_guardrails"]["forbidden_language"])
    for phrase in [
        "buy signal",
        "sell signal",
        "hold",
        "target price",
        "support/resistance",
        "main force",
        "主力",
        "買賣建議",
    ]:
        assert phrase in forbidden
