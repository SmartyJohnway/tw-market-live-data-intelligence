from __future__ import annotations

import json
import hashlib
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_phase_i_i3_a0_attempt3 as attempt3
from scripts.validate_phase_i_i3_a0_attempt3 import validate_go_proofs
from scripts.run_phase_i_i3_a0_preflight import (
    analyze_acquired_payloads,
    load_adjudication_authority,
    load_mapping,
)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Attempt 3 offline tests cannot open sockets")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


def reviewed_git(*args):
    return {("branch", "--show-current"): attempt3.BRANCH,
            ("rev-parse", "HEAD"): attempt3.STARTING_HEAD,
            ("rev-parse", "HEAD^{tree}"): attempt3.STARTING_TREE,
            ("rev-parse", "origin/main"): attempt3.BASELINE,
            ("diff", "--name-only", "HEAD"): ""}[args]


def test_attempt3_preflight_uses_exact_security_master_targets_and_p2_ready(monkeypatch):
    monkeypatch.setattr(attempt3, "_git", reviewed_git)
    calls = []
    def resolve(canonical, *, market_hint):
        calls.append((canonical, market_hint))
        code = canonical.split(":")[1]
        return SimpleNamespace(status="resolved", reason_codes=["exact_listing_id"], selected={
            "classification": {"market": market_hint, "instrument_family": "company_share", "instrument_type": "common_share"},
            "identity": {"security_code": code, "isin": "TW0001101004" if code == "1101" else "TW0005347009"},
            "execution_eligibility": {"status": "allowed"}})
    service = SimpleNamespace(resolve=resolve, release_id="security-master-20260926T151841Z", manifest_hash="a" * 64)
    monkeypatch.setattr(attempt3, "load_active_identity_service", lambda **kwargs: (service, {"release_index_sha256": "b" * 64}, None, None))
    result = attempt3.validate_preflight()
    assert result["authority_chain"]["authority_chain_status"] == "REVIEWED_FIXED_HISTORICAL_ANCHORS"
    assert result["security_master"]["release_id"] == "security-master-20260926T151841Z"
    assert result["targets"]["TWSE"] == {
        "canonical_target_id": "TWSE:1101", "isin": "TW0001101004", "security_code": "1101",
        "market": "TWSE", "instrument_family": "company_share", "instrument_type": "common_share",
        "execution_eligibility": "allowed", "resolution_reason": "exact_listing_id",
    }
    assert result["targets"]["TPEX"]["canonical_target_id"] == "TPEX:5347"
    assert result["targets"]["TPEX"]["isin"] == "TW0005347009"
    assert calls == [("TWSE:1101", "TWSE"), ("TPEX:5347", "TPEX")]


@pytest.mark.parametrize("field", ["HEAD", "HEAD^{tree}", "origin/main", "tracked"])
def test_preflight_rejects_drift_before_reservation(monkeypatch, field):
    def drift(*args):
        if args == ("rev-parse", field) or (field == "tracked" and args == ("diff", "--name-only", "HEAD")):
            return "unexpected"
        return reviewed_git(*args)
    monkeypatch.setattr(attempt3, "_git", drift)
    with pytest.raises(RuntimeError, match="guard_failed"):
        attempt3.validate_preflight()


def test_reviewed_synthetic_source_fixtures_pass_same_analyzer_as_attempt3():
    fixtures = Path("tests/fixtures/phase_i_i3_a0")
    twse = (fixtures / "twse_synthetic.json").read_bytes()
    tpex_scenarios = json.loads((fixtures / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))
    result = analyze_acquired_payloads(twse, tpex_scenarios["unique_candidate_a"],
                                       load_mapping(), load_adjudication_authority())
    assert result["status"] == "PASS"
    assert result["dealer_sell_adjudication"]["selection_status"] == "RESOLVED"
    assert result["dealer_sell_adjudication"]["selected_candidate"] == "Dealers-TotalSell"
    assert result["sources"]["TWSE"]["selected_observation"]["trade_date"] == "2026-09-30"
    assert result["sources"]["TWSE"]["selected_observation"]["unit"] == "share"
    assert result["sources"]["TPEX"]["selected_observation"]["unit"] == "share"


def test_twse_source_shape_keeps_only_bounded_metadata_and_fixed_date():
    fixture = Path("tests/fixtures/phase_i_i3_a0/twse_synthetic.json").read_bytes()
    shape = attempt3._assert_twse_source_shape(fixture, load_mapping())
    assert shape["root_type"] == "object"
    assert shape["row_count"] == 2
    assert shape["source_date"] == "20260930"
    assert "date" in shape["top_level_keys"]
    assert b"1101" not in json.dumps(shape).encode()
    payload = json.loads(fixture)
    payload["date"] = "20261002"
    with pytest.raises(ValueError, match="unexpected_twse_official_date"):
        attempt3._assert_twse_source_shape(json.dumps(payload).encode(), load_mapping())


def test_tpex_source_shape_records_exact_date_and_key_inventory():
    scenarios = json.loads(Path("tests/fixtures/phase_i_i3_a0/dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))
    shape = attempt3._tpex_source_shape(json.dumps(scenarios["unique_candidate_a"], ensure_ascii=False).encode(), load_mapping())
    assert shape["root_type"] == "array"
    assert shape["row_count"] > 0
    assert shape["raw_unique_date_values"]
    assert shape["normalized_trade_dates"] == ["2026-09-30"]
    assert "Dealers-TotalSell" in shape["field_names"]


def fake_run(monkeypatch, tmp_path, *, fail_market=None, fail_code="URLError", scenario="unique_candidate_a"):
    fixtures = attempt3.ROOT / "tests/fixtures/phase_i_i3_a0"
    payloads = {"TWSE": (fixtures / "twse_synthetic.json").read_bytes(),
                "TPEx": json.dumps(json.loads((fixtures / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))[scenario], ensure_ascii=False).encode()}
    preflight = {"mapping": load_mapping(), "adjudication": load_adjudication_authority(),
                 "p2_record_sha256": attempt3.EXPECTED_P2_SHA, "targets": {},
                 "security_master": {"release_id": "synthetic_test_release"}}
    monkeypatch.setattr(attempt3, "ROOT", tmp_path)
    monkeypatch.setattr(attempt3, "validate_preflight", lambda: preflight)
    calls = []
    def reader(market, *, policy):
        assert (tmp_path / attempt3.CONSUMED_REL).is_file()
        latch = json.loads((tmp_path / attempt3.CONSUMED_REL).read_text(encoding="utf-8"))
        assert latch["consumed"] is True and latch["consumed_before_first_http_attempt"] is True
        calls.append((market, policy))
        body = payloads[market]
        telemetry = {"market": market, "endpoint": attempt3.transport.URLS[market], "method": "GET",
                     "timeout_seconds": 30, "retry_count": 0, "redirect_policy": "reject", "ssl_policy": policy,
                     "http_status": 200, "content_type": "application/json", "base_mime": "application/json",
                     "retrieved_at": "2026-10-02T00:00:00Z", "response_byte_count": len(body),
                     "response_sha256": hashlib.sha256(body).hexdigest(), "error_code": None}
        if market == fail_market:
            telemetry.update(error_code=fail_code, reason_classification="timeout", reason_type="TimeoutError")
            if fail_code == "URLError":
                telemetry.update(http_status=None, response_byte_count=0, response_sha256=None)
            return telemetry, None
        return telemetry, body
    result = attempt3.run_attempt3(reader=reader)
    return result, calls, payloads, reader


def test_fake_full_run_unique_resolution_preserves_only_normalized_observations_and_denies_replay(monkeypatch, tmp_path):
    result, calls, payloads, reader = fake_run(monkeypatch, tmp_path)
    assert calls == [("TWSE", "compatibility"), ("TPEx", "strict")]
    assert result["final_decision"] == "GO_PASS"
    assert result["dealer_sell_adjudication"]["selected_candidate"] == "Dealers-TotalSell"
    assert result["normalized_observations"]["TPEX:5347"]["market"] == "TPEX"
    assert result["normalized_observations"]["TWSE:1101"]["dealer_total"]["net_shares"] is not None
    for path in tmp_path.rglob("*.json"):
        for body in payloads.values():
            assert body not in path.read_bytes()
    with pytest.raises(RuntimeError, match="already_exists"):
        attempt3.run_attempt3(reader=reader)
    assert len(calls) == 2
    validate_go_proofs(result)


@pytest.mark.parametrize("corruption", ["acquisition", "binding", "date", "unit", "dealer_alias", "total", "arithmetic"])
def test_go_validator_rejects_incomplete_or_falsified_proof(monkeypatch, tmp_path, corruption):
    result, _, _, _ = fake_run(monkeypatch, tmp_path)
    if corruption == "acquisition":
        result["source_telemetry"]["TPEX"]["error_code"] = "URLError"
    elif corruption == "binding":
        result["target_binding"]["TPEX:5347"] = 2
    elif corruption == "date":
        result["source_payload_summaries"]["TPEX"]["normalized_trade_dates"] = ["2026-09-30", "2026-10-01"]
    elif corruption == "unit":
        result["unit_proof"]["TPEx"] = "lot"
    elif corruption == "dealer_alias":
        stats = result["dealer_sell_adjudication"]["candidate_statistics"]["Dealers -TotalSell"]
        stats.update(rows_failed=0, rows_passed=stats["rows_checked"])
    elif corruption == "total":
        result["dealer_sell_adjudication"]["institutional_total_invariant"]["rows_failed"] = 1
    else:
        result["whole_dataset_arithmetic"]["TWSE"]["investment_trust"]["rows_failed"] = 1
    with pytest.raises(AssertionError):
        validate_go_proofs(result)


def test_twse_transport_failure_stops_before_tpex_and_records_consumed_hold(monkeypatch, tmp_path):
    result, calls, _, _ = fake_run(monkeypatch, tmp_path, fail_market="TWSE")
    assert calls == [("TWSE", "compatibility")]
    assert result["actual_get_counts"] == {"TWSE": 1, "TPEx": 0, "TAIFEX": 0, "other_market_data": 0}
    assert result["final_decision"] == "HOLD"
    assert result["source_semantics_state"] == "SOURCE_SEMANTICS_NOT_EVALUATED"
    assert result["source_telemetry"]["TWSE"]["request_dispatched"] is True


def test_invalid_json_is_source_schema_failure_and_stops_tpex(monkeypatch, tmp_path):
    result, calls, _, _ = fake_run(monkeypatch, tmp_path, fail_market="TWSE", fail_code="invalid_json_payload")
    assert len(calls) == 1
    assert result["source_semantics_state"] == "SOURCE_SCHEMA_FAILED"
    assert result["final_decision"] == "HOLD"


def test_tpex_transport_failure_preserves_twse_normalization_and_arithmetic(monkeypatch, tmp_path):
    result, calls, _, _ = fake_run(monkeypatch, tmp_path, fail_market="TPEx")
    assert len(calls) == 2
    assert result["final_decision"] == "HOLD"
    assert result["normalized_observations"]["TWSE:1101"]["unit"] == "share"
    assert all(check["rows_failed"] == 0 for check in result["whole_dataset_arithmetic"]["TWSE"].values())
    assert result["normalized_observations"]["TPEX:5347"] is None
