"""Frozen I3-A1 contract tests; all source-shaped input is synthetic and offline."""
import copy
import json
import socket

import pytest

from scripts import run_phase_i_i3_a0_preflight as analyzer
from scripts import validate_phase_i_i3_a1 as a1


@pytest.fixture(autouse=True)
def deny_external_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("a1_external_network_forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


@pytest.fixture
def contract():
    return json.loads((a1.ROOT / a1.CONTRACT).read_text(encoding="utf-8"))


@pytest.fixture
def synthetic():
    root = a1.ROOT / "tests/fixtures/phase_i_i3_a0"
    twse = json.loads((root / "twse_synthetic.json").read_text(encoding="utf-8"))
    tpex = json.loads((root / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
    return twse, tpex


def mapping_from_contract(contract, market):
    source = contract["sources"][market]
    return {"code_field": source["code_field"], "date_field": source["date_field"],
            "date_source": "top_level" if market == "TWSE" else "row",
            "date_encoding": source["date_encoding"], "single_date_required": True,
            "required_common_core": source["required_common_core"],
            "source_native_optional": source["source_native_optional"],
            "conditional_invariants": {"dealer_component_split": ["dealer_proprietary", "dealer_hedging"] if market == "TWSE" else []}}


def test_a1_validator_and_immutable_a0_anchors(contract):
    assert a1.validate() == contract
    for key, (path, expected) in a1.EVIDENCE.items():
        assert a1.sha(a1.ROOT / path) == expected == contract["a0_evidence"][key]


@pytest.mark.parametrize("change", [
    lambda c: c["sources"]["TPEX"]["required_common_core"]["foreign_and_mainland_excluding_foreign_dealer"].update(
        buy_shares=["ForeignInvestorsIncludeMainlandAreaInvestors-TotalBuy"]),
    lambda c: c["semantic_contract"]["institutional_total_formula"].append("foreign_dealer.net_shares"),
    lambda c: c["sources"]["TWSE"]["required_common_core"]["dealer_total"].update(
        buy_shares=["自營商買進股數(自行買賣)"]),
    lambda c: c["sources"]["TPEX"]["required_common_core"]["dealer_total"].update(
        sell_shares=["Dealers -TotalSell"]),
    lambda c: c["semantic_contract"]["institutional_total_formula"].remove("dealer_total.net_shares"),
])
def test_semantic_symmetry_independent_of_a0_go(contract, change):
    change(contract)
    assert contract["a0_evidence"]["decision"] == "GO_PASS"
    with pytest.raises(ValueError):
        a1.validate_contract(contract)


@pytest.mark.parametrize("change", [
    lambda c: c["sources"]["TWSE"].update(automatic_previous_trading_day_fallback=True),
    lambda c: c["timing"].update(retrieved_at_alone_proves_finality=True),
    lambda c: c["timing"].update(different_date_numeric_same_session_interpretation=True),
    lambda c: c["timing"].update(same_date_implies_simultaneous_publication=True),
    lambda c: c["normalized_evidence"].update(unit="lot"),
    lambda c: c["batching"].update(per_target_refetch=True),
    lambda c: c["authorization_boundary"].update(a2_implementation_authorized=True),
    lambda c: c["sources"]["TPEX"]["transport"].update(partial_body_analysis=True),
])
def test_date_transport_and_authority_mutation_rejected(contract, change):
    change(contract)
    with pytest.raises(ValueError):
        a1.validate_contract(contract)


def test_independent_dates_and_unknown_finality_allowed(contract):
    a1.validate_contract(contract)
    assert contract["timing"]["source_trade_dates"] == "independent"
    assert "different_trade_date" in contract["timing"]["alignment_statuses"]
    assert contract["timing"]["v1_publication_finality_without_separate_authority"] == "unknown"
    assert contract["timing"]["same_date_implies_simultaneous_publication"] is False


def test_synthetic_complete_both_markets(contract, synthetic):
    twse, tpex = synthetic
    for market, payload in (("TWSE", twse), ("TPEX", tpex)):
        result = analyzer.analyze_market(market, payload, mapping_from_contract(contract, market))
        assert result["status"] == "PASS"
        assert result["exact_matches"] == 1
        assert result["selected_observation"]["unit"] == "share"
        assert all(x["rows_failed"] == 0 for x in result["arithmetic"].values())
    assert analyzer.analyze_market("TPEX", tpex, mapping_from_contract(contract, "TPEX"))["arithmetic"]["dealer_component_net"]["status"] == analyzer.NOT_APPLICABLE


@pytest.mark.parametrize("market,key,field", [
    ("TWSE", "dealer_component_net", "自營商買賣超股數(自行買賣)"),
    ("TWSE", "institutional_total_net", "三大法人買賣超股數"),
    ("TPEX", "dealer_total", "Dealers-TotalSell"),
    ("TPEX", "institutional_total_net", "TotalDifference"),
])
def test_whole_dataset_arithmetic_detects_source_mutation(contract, synthetic, market, key, field):
    twse, tpex = copy.deepcopy(synthetic)
    mapping = mapping_from_contract(contract, market)
    if market == "TWSE":
        index = twse["fields"].index(field)
        twse["data"][0][index] = str(int(twse["data"][0][index]) + 1)
        payload = twse
    else:
        tpex[0][field] = str(int(tpex[0][field]) + 1)
        payload = tpex
    result = analyzer.analyze_market(market, payload, mapping)
    assert result["status"] == "FAIL"
    assert result["arithmetic"][key]["rows_failed"] >= 1


def test_wrong_tpex_dealer_alias_fails_arithmetic(contract, synthetic):
    mapping = mapping_from_contract(contract, "TPEX")
    mapping["required_common_core"]["dealer_total"]["sell_shares"] = ["Dealers -TotalSell"]
    result = analyzer.analyze_market("TPEX", synthetic[1], mapping)
    assert result["status"] == "FAIL"
    assert result["arithmetic"]["dealer_total"]["rows_failed"] == 2


@pytest.mark.parametrize("matches", [0, 2])
def test_binding_zero_or_duplicate_fails_without_name_fallback(contract, synthetic, matches):
    twse = copy.deepcopy(synthetic[0])
    if matches == 0:
        twse["data"] = [row for row in twse["data"] if row[0] != "1101"]
    else:
        twse["data"].append(copy.deepcopy(twse["data"][0]))
    with pytest.raises(ValueError, match="target_binding_failed"):
        analyzer.analyze_market("TWSE", twse, mapping_from_contract(contract, "TWSE"))
    assert contract["target"]["name_fallback"] is False
