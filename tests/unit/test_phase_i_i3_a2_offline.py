"""Injected-only I3-A2 candidate proof. Fixtures are synthetic, not source evidence."""
import copy
import hashlib
import json
import socket

import pytest
from jsonschema import Draft202012Validator

from server.services.phase_i_i3_cash_institutional_flow_offline_candidate import (
    EXECUTOR_ID, build_i3_candidate_runtime_adapter_registry, run_i3_candidate_offline_batch,
)
from server.services.phase_i_i3_cash_institutional_flow_adapters import (
    CONTRACT_SHA256, ROOT, load_frozen_contract,
)

FIXTURES = ROOT / "tests/fixtures/phase_i_i3_a0"
SCHEMA = json.loads((ROOT / "schemas/cash_institutional_flow_context_evidence.v1.schema.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("a2_market_network_forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


def fixture_payloads():
    twse = json.loads((FIXTURES / "twse_synthetic.json").read_text(encoding="utf-8"))
    tpex = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
    return twse, tpex


def payload_bytes(obj):
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def target(market, code, number):
    return {"market": market, "security_code": code, "canonical_target_id": f"{market}:{code}",
            "instrument_family": "company_share", "instrument_type": "common_share",
            "execution_eligibility": "allowed",
            "operation_id": f"op-{number}", "execution_request_id": "umereq-v2-" + f"{number:020x}",
            "execution_request_hash": f"{number:064x}"}


def execute(targets, sources=None, *, source_date="20260930", timestamps=None):
    twse, tpex = fixture_payloads()
    requested = {t["market"] for t in targets}
    all_sources = {"TWSE": payload_bytes(twse), "TPEX": payload_bytes(tpex)}
    sources = {market: all_sources[market] for market in requested} if sources is None else sources
    times = timestamps or {market: "2026-10-03T21:05:00Z" for market in requested}
    return run_i3_candidate_offline_batch(targets, source_payloads=sources, retrieved_at_by_market=times,
        twse_governed_source_date=source_date if "TWSE" in requested else None)


def evidence(result):
    return [json.loads(body) for body in result["artifact_bytes"].values()]


def test_a1_hash_and_isolated_registry():
    assert hashlib.sha256((ROOT / "docs/governance/phase_i/PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json").read_bytes()).hexdigest() == CONTRACT_SHA256
    assert set(build_i3_candidate_runtime_adapter_registry()) == {(EXECUTOR_ID, "TWSE"), (EXECUTOR_ID, "TPEX")}


@pytest.mark.parametrize("mutation", [
    lambda c: c["sources"]["TPEX"]["required_common_core"]["dealer_total"].update(sell_shares=["Dealers -TotalSell"]),
    lambda c: c["sources"]["TPEX"]["required_common_core"]["foreign_and_mainland_excluding_foreign_dealer"].update(
        buy_shares=["ForeignInvestorsIncludeMainlandAreaInvestors-TotalBuy"]),
    lambda c: c["normalized_evidence"].update(unit="lot"),
    lambda c: c["sources"]["TWSE"].update(automatic_previous_trading_day_fallback=True),
])
def test_in_memory_frozen_contract_mutation_rejected(monkeypatch, mutation):
    from server.services import phase_i_i3_cash_institutional_flow_offline_candidate as candidate
    altered = load_frozen_contract()
    mutation(altered)
    monkeypatch.setattr(candidate, "load_frozen_contract", lambda: altered)
    with pytest.raises(ValueError, match="frozen_a1_contract_object_mutated"):
        execute([target("TWSE", "1101", 1)])


@pytest.mark.parametrize("market,code,trade_date", [("TWSE", "1101", "2026-09-30"), ("TPEX", "5347", "2026-09-30")])
def test_single_complete_and_operation_artifact(market, code, trade_date):
    result = execute([target(market, code, 1)])
    ev = evidence(result)[0]
    assert (ev["status"], ev["trade_date"], ev["unit"], ev["publication_finality"], ev["currentness_status"]) == (
        "complete", trade_date, "share", "unknown", "unknown")
    assert ev["transport"]["network_get_count"] == result["network_calls"] == 0
    assert ev["transport"]["raw_payload_persisted"] is False
    assert result["operation_results"][0]["status"] == "succeeded"
    assert result["operation_results"][0]["result_item_count"] == 1
    path, body = next(iter(result["artifact_bytes"].items()))
    assert result["artifact_inventory"][0]["relative_path"] == path
    assert result["artifact_inventory"][0]["sha256"] == hashlib.sha256(body).hexdigest()
    assert not list(Draft202012Validator(SCHEMA).iter_errors(ev))


@pytest.mark.parametrize("market,codes", [("TWSE", ["1101", "1102"]), ("TPEX", ["5347", "5483"])])
def test_same_market_two_targets_prepare_once(market, codes):
    result = execute([target(market, code, number) for number, code in enumerate(codes, 1)])
    assert result["market_metrics"][market]["decode_count"] == 1
    assert result["market_metrics"][market]["source_prepare_count"] == 1
    assert result["simulated_source_acquisition_count"] == 1
    assert len(result["artifact_bytes"]) == 2
    assert all(ev["status"] == "complete" for ev in evidence(result))


def test_mixed_different_date_and_independent_failure():
    twse, tpex = fixture_payloads()
    for row in tpex:
        row["Date"] = "1151002"
    targets = [target("TWSE", "1101", 1), target("TPEX", "5347", 2)]
    result = execute(targets, {"TWSE": payload_bytes(twse), "TPEX": payload_bytes(tpex)})
    assert result["simulated_source_acquisition_count"] == 2
    assert result["alignment"] == {"status": "different_trade_date", "same_date_implies_simultaneous_publication": False,
                                   "numeric_same_session_interpretation_allowed": False}
    assert [ev["trade_date"] for ev in evidence(result)] == ["2026-09-30", "2026-10-02"]
    tpex[1]["TotalDifference"] = "999"
    failed = execute(targets, {"TWSE": payload_bytes(twse), "TPEX": payload_bytes(tpex)})
    assert [ev["status"] for ev in evidence(failed)] == ["complete", "source_failed"]
    assert failed["alignment"]["status"] == "not_comparable"


def test_same_date_does_not_mean_simultaneous():
    result = execute([target("TWSE", "1101", 1), target("TPEX", "5347", 2)])
    assert result["alignment"]["status"] == "same_trade_date"
    assert result["alignment"]["same_date_implies_simultaneous_publication"] is False


def test_twse_source_date_mismatch_fails_without_substitution():
    result = execute([target("TWSE", "1101", 1)], source_date="20261001")
    assert evidence(result)[0]["status"] == "source_failed"
    assert result["operation_results"][0]["error_code"] == "source_failed"


def test_tpex_multiple_dates_fails():
    _, tpex = fixture_payloads()
    tpex[1]["Date"] = "1151002"
    result = execute([target("TPEX", "5347", 1)], {"TPEX": payload_bytes(tpex)})
    assert evidence(result)[0]["status"] == "source_failed"


@pytest.mark.parametrize("market,code", [("TWSE", "9999"), ("TPEX", "9999")])
def test_absent_binding_has_failure_evidence_without_numbers(market, code):
    result = execute([target(market, code, 1)])
    ev = evidence(result)[0]
    assert ev["status"] == "binding_failed"
    assert result["operation_results"][0]["status"] == "failed"
    for field in ("unit", "foreign_and_mainland_excluding_foreign_dealer", "investment_trust", "dealer_total", "institutional_total_net_shares"):
        assert field not in ev


@pytest.mark.parametrize("market,code", [("TWSE", "1101"), ("TPEX", "5347")])
def test_duplicate_binding_fails(market, code):
    twse, tpex = fixture_payloads()
    if market == "TWSE":
        twse["data"].append(copy.deepcopy(twse["data"][0]))
        source = {market: payload_bytes(twse)}
    else:
        tpex.append(copy.deepcopy(tpex[0]))
        source = {market: payload_bytes(tpex)}
    assert evidence(execute([target(market, code, 1)], source))[0]["status"] == "binding_failed"


@pytest.mark.parametrize("market,field", [
    ("TWSE", "自營商買賣超股數(自行買賣)"), ("TWSE", "三大法人買賣超股數"),
    ("TPEX", "Dealers-TotalSell"), ("TPEX", "TotalDifference"),
])
def test_whole_dataset_bad_second_row_fails_all_targets(market, field):
    twse, tpex = fixture_payloads()
    if market == "TWSE":
        index = twse["fields"].index(field)
        twse["data"][1][index] = "999"
        source = {market: payload_bytes(twse)}
        codes = ["1101", "1102"]
    else:
        tpex[1][field] = "999"
        source = {market: payload_bytes(tpex)}
        codes = ["5347", "5483"]
    result = execute([target(market, code, i) for i, code in enumerate(codes, 1)], source)
    assert [ev["status"] for ev in evidence(result)] == ["source_failed", "source_failed"]
    assert all(r["status"] == "failed" and r["result_item_count"] == 1 for r in result["operation_results"])


def test_tpex_near_alias_not_used_and_foreign_dealer_not_double_counted():
    _, tpex = fixture_payloads()
    tpex[0]["Dealers -TotalSell"] = "not-an-integer"
    tpex[0]["Foreign Dealers-Total Buy"] = "8"
    tpex[0]["Foreign Dealers-TotalSell"] = "3"
    tpex[0]["ForeignDealers-Difference"] = "5"
    ev = evidence(execute([target("TPEX", "5347", 1)], {"TPEX": payload_bytes(tpex)}))[0]
    assert ev["status"] == "complete"
    assert ev["dealer_total"]["sell_shares"] == 10
    assert ev["institutional_total_net_shares"] == 120
    assert ev["source_native_optional"]["foreign_dealer"]["net_shares"] == 5


@pytest.mark.parametrize("hour", ["17:00:00", "18:30:00", "20:30:00"])
def test_finality_unknown_on_both_sides_of_publication_clock(hour):
    time = "2026-10-03T" + hour + "+08:00"
    result = execute([target("TWSE", "1101", 1)], timestamps={"TWSE": time})
    ev = evidence(result)[0]
    assert ev["retrieved_at"] == time
    assert ev["publication_finality"] == ev["currentness_status"] == "unknown"


@pytest.mark.parametrize("change", [
    lambda e: e.pop("dealer_total"),
    lambda e: e.update(unit="lot"),
    lambda e: e["dealer_total"].update(buy_shares=-1),
    lambda e: e["dealer_total"].update(net_shares=0.5),
    lambda e: e.update(publication_finality="inferred_final"),
    lambda e: e.update(status="partial"),
])
def test_schema_mutation_rejected(change):
    ev = evidence(execute([target("TWSE", "1101", 1)]))[0]
    change(ev)
    assert list(Draft202012Validator(SCHEMA).iter_errors(ev))


@pytest.mark.parametrize("status", ["source_failed", "binding_failed"])
def test_failure_schema_rejects_fabricated_core(status):
    result = execute([target("TWSE", "1101" if status == "source_failed" else "9999", 1)],
                     source_date="20261001" if status == "source_failed" else "20260930")
    ev = evidence(result)[0]
    assert ev["status"] == status
    ev["institutional_total_net_shares"] = 0
    assert list(Draft202012Validator(SCHEMA).iter_errors(ev))


def test_test_only_parity_with_historical_a0_analyzer():
    from scripts import run_phase_i_i3_a0_preflight as historical
    twse, tpex = fixture_payloads()
    analyzed = historical.analyze_acquired_payloads(twse, tpex, historical.load_mapping(), historical.load_adjudication_authority())
    result = execute([target("TWSE", "1101", 1), target("TPEX", "5347", 2)])
    for ev in evidence(result):
        source = analyzed["sources"][ev["market"]]["selected_observation"]
        assert (ev["trade_date"], ev["security_code"], ev["unit"]) == (source["trade_date"], source["security_code"], source["unit"])
        assert {key: ev[key] for key in ("foreign_and_mainland_excluding_foreign_dealer", "investment_trust", "dealer_total", "institutional_total_net_shares")} == source["common_core"]
        assert ev["source_native_optional"] == source["source_native_optional"]


def test_no_raw_body_in_return_and_wrong_payload_market_rejected():
    twse, _ = fixture_payloads()
    body = payload_bytes(twse)
    result = execute([target("TWSE", "1101", 1)], {"TWSE": body})
    assert body not in json.dumps(result, default=lambda x: x.decode("utf-8") if isinstance(x, bytes) else str(x), ensure_ascii=False).encode()
    assert not any(key in result for key in ("source_payload", "raw_payload", "rows", "full_source_rows", "partial_source_bytes"))
    with pytest.raises(ValueError, match="injected_payload_market_scope_invalid"):
        execute([target("TWSE", "1101", 1)], {"TWSE": body, "TPEX": b"[]"})


def test_missing_payload_and_missing_timestamp_fail_before_preparation():
    with pytest.raises(ValueError, match="injected_payload_market_scope_invalid"):
        execute([target("TWSE", "1101", 1)], {})
    with pytest.raises(ValueError, match="governed_retrieval_market_scope_invalid"):
        execute([target("TWSE", "1101", 1)], timestamps={"TPEX": "2026-10-03T00:00:00Z"})


def test_malformed_required_share_count_fails_without_zero_coercion():
    twse, _ = fixture_payloads()
    twse["data"][1][twse["fields"].index("投信買進股數")] = "1.5"
    ev = evidence(execute([target("TWSE", "1101", 1)], {"TWSE": payload_bytes(twse)}))[0]
    assert ev["status"] == "source_failed"
    assert "investment_trust" not in ev


def test_invalid_target_or_name_only_cannot_bind():
    invalid = target("TWSE", "1101", 1)
    invalid["execution_eligibility"] = "blocked"
    with pytest.raises(ValueError, match="target_execution_not_eligible"):
        execute([invalid])
    twse, _ = fixture_payloads()
    twse["data"][0][0] = "9999"
    twse["data"][0][1] = "1101"
    ev = evidence(execute([target("TWSE", "1101", 1)], {"TWSE": payload_bytes(twse)}))[0]
    assert ev["status"] == "binding_failed"


def test_oversize_payload_is_source_failed_without_raw_artifact():
    body = b" " * (4 * 1024 * 1024 + 1)
    result = execute([target("TPEX", "5347", 1)], {"TPEX": body})
    ev = evidence(result)[0]
    assert ev["status"] == "source_failed"
    assert ev["transport"]["response_byte_count"] == 0
    assert ev["transport"]["response_sha256"] is None
    assert body not in next(iter(result["artifact_bytes"].values()))
