"""Real canonical analyzer -> future evidence proof; synthetic inputs, no sockets."""
from __future__ import annotations

import copy
import json
import socket
from pathlib import Path

import pytest

from scripts import run_phase_i_i3_a0_preflight as analyzer
from scripts import phase_i_i3_a0_future_evidence as evidence
from scripts import phase_i_i3_a0_attempt_authority as authority

FIXTURES = analyzer.ROOT / "tests/fixtures/phase_i_i3_a0"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("R1 network forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


def payloads(scenario="unique_candidate_a"):
    twse = json.loads((FIXTURES / "twse_synthetic.json").read_text(encoding="utf-8"))
    tpex = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))[scenario]
    return twse, tpex


def real_analysis(scenario="unique_candidate_a"):
    return analyzer.analyze_acquired_payloads(*payloads(scenario), analyzer.load_mapping(), analyzer.load_adjudication_authority())


def adapt(result, observed=True):
    return evidence.source_findings_from_analyzer_result(result, complete_body_received=True,
                                                       whole_market_payload_observed=observed)


def test_real_analyze_market_twse_adapter():
    twse, _ = payloads()
    actual = analyzer.analyze_market("TWSE", twse, analyzer.load_mapping()["markets"]["TWSE"])
    value = adapt(actual)
    assert value["evaluation_status"] == "EVALUATED" and value["target_binding"] == 1
    assert value["unit_proof"] == actual["selected_observation"]["unit"] == "share"
    assert value["normalized_observation"] == {"market": "TWSE", **actual["selected_observation"]}
    assert value["whole_dataset_arithmetic"] == actual["arithmetic"]


@pytest.mark.parametrize("scenario,key", [("unique_candidate_a", "Dealers-TotalSell"), ("unique_candidate_b", "Dealers -TotalSell")])
def test_real_acquired_p1_unique_resolution_tpex_adapter(scenario, key):
    result = real_analysis(scenario)
    assert result["status"] == "PASS"
    assert result["dealer_sell_adjudication"]["selection_status"] == "RESOLVED"
    assert result["dealer_sell_adjudication"]["selected_candidate"] == key
    actual = result["sources"]["TPEX"]
    assert not {"unit", "observation", "whole_market_payload"} & set(actual)
    value = adapt(actual)
    assert value["evaluation_status"] == "EVALUATED" and value["target_binding"] == 1
    assert value["unit_proof"] == "share" and value["batching_observation"] == "PROVEN"
    assert value["normalized_observation"] == {"market": "TPEX", **actual["selected_observation"]}
    assert value["normalized_observation"]["security_code"] == "5347"
    assert value["whole_dataset_arithmetic"] is actual["arithmetic"]


def test_real_canonical_composite_interface_preserves_both_sources_and_prior_support():
    result = real_analysis()
    composite = evidence.compose_analyzer_evidence(result["sources"]["TWSE"], result["sources"]["TPEX"],
        result["dealer_sell_adjudication"], whole_market_observations={"TWSE": True, "TPEx": True},
        prior_evidence_refs=["synthetic-accepted-TWSE-summary", "synthetic-P1-adjudication"])
    assert composite["mixed_market_observation"] == "PROVEN"
    assert composite["batching_observation"] == {"TWSE": "PROVEN", "TPEx": "PROVEN"}
    assert composite["batching_contract_support"]["prior_evidence_refs"]
    for market, upstream in (("TWSE", "TWSE"), ("TPEx", "TPEX")):
        value = composite["sources"][market]
        assert value["evaluation_status"] == "EVALUATED" and value["target_binding"] == 1
        assert value["unit_proof"] == "share"
        assert value["normalized_observation"] == {"market": upstream, **result["sources"][upstream]["selected_observation"]}
    assert composite["market_network_calls"] == 0 and composite["raw_payload_persistence"] == "NONE"


def test_no_complete_body_null_distinct_from_binding_failed():
    assert evidence.source_findings_from_analyzer_result(None, complete_body_received=False,
        whole_market_payload_observed=False) == {
        "evaluation_status": "NOT_EVALUATED", "target_binding": None, "whole_dataset_arithmetic": None,
        "unit_proof": None, "normalized_observation": None, "batching_observation": "NOT_EVALUATED"}
    with pytest.raises(ValueError, match="partial_payload_semantics_forbidden"):
        evidence.source_findings_from_analyzer_result(real_analysis()["sources"]["TPEX"],
            complete_body_received=False, whole_market_payload_observed=True)


@pytest.mark.parametrize("market,count", [("TWSE", 0), ("TWSE", 2), ("TPEX", 0), ("TPEX", 2)])
def test_real_payload_zero_and_duplicate_binding_never_fabricate_analyzer_success(market, count):
    twse, tpex = payloads()
    payload = twse if market == "TWSE" else tpex
    if market == "TWSE":
        index = twse["fields"].index("證券代號")
        row = next(r for r in twse["data"] if r[index] == "1101")
        if count == 0:
            twse["data"].remove(row)
        else:
            twse["data"].append(copy.deepcopy(row))
        mapping = analyzer.load_mapping()["markets"]["TWSE"]
    else:
        row = next(r for r in tpex if r["SecuritiesCompanyCode"] == "5347")
        if count == 0:
            tpex.remove(row)
        else:
            tpex.append(copy.deepcopy(row))
        mapping = analyzer.load_mapping()["markets"]["TPEX"]
    with pytest.raises(ValueError, match="target_binding_failed"):
        analyzer.analyze_market(market, payload, mapping)
    value = evidence.binding_findings_from_payload(market, payload, complete_body_received=True,
                                                   whole_market_payload_observed=True)
    assert value["evaluation_status"] == "EVALUATED_BINDING_FAILED" and value["target_binding"] == count
    assert value["normalized_observation"] is value["unit_proof"] is value["whole_dataset_arithmetic"] is None


def test_old_helper_shaped_dictionary_rejected():
    with pytest.raises(ValueError, match="invalid_canonical_analyzer_shape"):
        adapt({"exact_matches": 1, "unit": "share", "observation": {}, "arithmetic": {}, "whole_market_payload": True})


@pytest.mark.parametrize("change", ["missing_field", "extra_field", "bool_binding", "zero_binding", "unit", "market", "dates", "row_count", "arithmetic", "status", "optional_raw"])
def test_canonical_contract_tampering_rejected(change):
    actual = copy.deepcopy(real_analysis()["sources"]["TPEX"])
    if change == "missing_field":
        del actual["field_count"]
    elif change == "extra_field":
        actual["unit"] = "share"
    elif change == "bool_binding":
        actual["exact_matches"] = True
    elif change == "zero_binding":
        actual["exact_matches"] = 0
    elif change == "unit":
        actual["selected_observation"]["unit"] = "lot"
    elif change == "market":
        actual["market"] = "UNKNOWN"
    elif change == "dates":
        actual["normalized_trade_dates"] = ["2026-02-30"]
    elif change == "row_count":
        actual["row_count"] = False
    elif change == "arithmetic":
        actual["arithmetic"] = {}
    elif change == "optional_raw":
        actual["selected_observation"]["source_native_optional"]["raw_body"] = "forbidden"
    else:
        actual["status"] = "HOLD"  # Not the canonical analyzer status vocabulary.
    with pytest.raises(ValueError, match="invalid_canonical"):
        adapt(actual)


def test_explicit_false_observation_does_not_infer_batching_from_endpoint():
    result = real_analysis()
    values = {m: adapt(result["sources"][k], m == "TWSE") for m, k in (("TWSE", "TWSE"), ("TPEx", "TPEX"))}
    batch = evidence.batching_findings(values, ["prior-design-whole-market"])
    assert values["TPEx"]["batching_observation"] == "NOT_PROVEN"
    assert batch["mixed_market_observation"] != "PROVEN"


def test_arithmetic_fail_not_promoted_to_pass():
    twse, _ = payloads()
    twse["data"][0][twse["fields"].index("三大法人買賣超股數")] = "123456"
    actual = analyzer.analyze_market("TWSE", twse, analyzer.load_mapping()["markets"]["TWSE"])
    assert actual["status"] == "FAIL"
    value = adapt(actual)
    assert value["semantic_status"] == "HOLD" and value["whole_dataset_arithmetic"] == actual["arithmetic"]


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_attempt4_old_or_default_authority_rejected(version):
    with pytest.raises(ValueError, match="attempt4_requires_explicit_v3"):
        authority.load_reviewed_authority_chain(version=version, attempt_number=4)
    with pytest.raises(ValueError, match="attempt4_requires_explicit_v3"):
        authority.load_reviewed_authority_chain(attempt_number=4)


def test_attempt4_explicit_v3_remains_valid_and_consumed_latch_is_v3_bound():
    chain = authority.load_reviewed_authority_chain(version="v3", attempt_number=4)
    assert chain["execution_authorized"] is False
    root = analyzer.ROOT / "docs/governance/phase_i/acceptance_runs"
    reservation = json.loads((root / "i3-a0-attempt4-authority-reservation.json").read_text(encoding="utf-8"))
    consumed = json.loads((root / "i3-a0-attempt4-authority-consumed.json").read_text(encoding="utf-8"))
    authority.validate_reservation(reservation, chain)
    authority.validate_consumed_latch(consumed, chain)
    assert reservation["attempt_number"] == consumed["attempt_number"] == 4
    assert consumed["consumed_before_first_http_attempt"] is True


@pytest.mark.parametrize("target", ["v3", "r1_erratum", "r1_closure", "erratum_absent"])
def test_v3_every_byte_anchor_sealed(monkeypatch, target):
    chain = authority.load_reviewed_authority_chain(version="v3")
    path = authority.AUTHORITY_V3_PATH if target == "v3" else authority.ROOT / (
        chain["r1_closure_reference"]["path"] if target == "r1_closure" else chain["r1_erratum"]["path"])
    original = Path.read_bytes
    def tampered(self):
        if self == path:
            if target == "erratum_absent":
                raise FileNotFoundError("erratum absent")
            return original(self) + b" "
        return original(self)
    monkeypatch.setattr(Path, "read_bytes", tampered)
    with pytest.raises((ValueError, FileNotFoundError)):
        authority.load_reviewed_authority_chain(version="v3")


def test_network_denied():
    with pytest.raises(AssertionError, match="network forbidden"):
        socket.create_connection(("www.tpex.org.tw", 443))


def test_r1_validator():
    from scripts.validate_phase_i_i3_a0_p3_r1 import validate
    assert validate()["decision"] == "P3_R1_PASS"
