"""Zero-socket acceptance-runner tests; fixtures are synthetic, not live evidence."""
import copy
import hashlib
import json
import socket

import pytest

from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3

FIXTURES = a3.ROOT / "tests/fixtures/phase_i_i3_a0"


@pytest.fixture(autouse=True)
def deny_market_sockets(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("a3_test_external_socket_forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


def sources():
    twse = json.loads((FIXTURES / "twse_synthetic.json").read_text(encoding="utf-8"))
    tpex = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
    return twse, tpex


def body(value):
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def targets():
    return {market: {"canonical_target_id": f"{market}:{code}", "market": market, "security_code": code,
            "instrument_family": "company_share", "instrument_type": "common_share",
            "execution_eligibility": "allowed", "isin": "synthetic-test-only"}
            for market, code in (("TWSE", "1101"), ("TPEX", "5347"))}


def response(market, payload, *, error=None, complete=True):
    return {"market": market, "http_status": 200, "base_mime": "application/json",
            "retrieved_at": "2026-10-04T00:00:00Z", "response_byte_count": len(payload) if complete else 0,
            "response_sha256": hashlib.sha256(payload).hexdigest() if complete else None,
            "complete_body_received": complete, "error_code": error, "retry_count": 0,
            "redirect_policy": "reject", "ssl_policy": "compatibility" if market == "TWSE" else "strict"}


def fake_acquirer(*, twse=None, tpex=None, failed_market=None, failure_error="URLError"):
    standard = sources()
    payloads = {"TWSE": body(standard[0] if twse is None else twse),
                "TPEX": body(standard[1] if tpex is None else tpex)}
    calls = []

    def acquire(market):
        calls.append(market)
        payload = payloads[market]
        if failed_market == market:
            info = response(market, payload, error=failure_error, complete=False)
            info["partial_response_byte_count"] = 12
            return info, None
        return response(market, payload), payload

    return acquire, calls, payloads


def test_fake_complete_two_market_path_and_raw_absence():
    acquire, calls, raw = fake_acquirer()
    result, artifacts = a3.execute_with_acquirer(acquire, targets())
    assert calls == ["TWSE", "TPEX"]
    assert result["acquisition_callback_attempts"] == {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0}
    assert result["http_dispatch_count"] == {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
    assert result["A3_decision"] == "PASS"
    assert [result["evidence"][m]["status"] for m in ("TWSE", "TPEX")] == ["complete", "complete"]
    assert result["candidate"]["network_calls"] == 0
    assert result["candidate"]["simulated_source_acquisition_count"] == 2
    assert result["candidate"]["alignment"]["status"] == "same_trade_date"
    assert len(artifacts) == 2
    assert result["raw_payload_persistence"] == "NONE"
    serialized = a3.json_bytes(result) + b"".join(artifacts.values())
    assert all(payload not in serialized for payload in raw.values())


def test_twse_transport_failure_stops_before_tpex():
    acquire, calls, _ = fake_acquirer(failed_market="TWSE")
    result, artifacts = a3.execute_with_acquirer(acquire, targets())
    assert calls == ["TWSE"] and result["acquisition_callback_attempts"]["TPEX"] == 0
    assert result["A3_decision"] == "HOLD" and result["candidate"] is None and artifacts == {}


def test_tpex_transport_failure_has_no_retry():
    acquire, calls, _ = fake_acquirer(failed_market="TPEX")
    result, _ = a3.execute_with_acquirer(acquire, targets())
    assert calls == ["TWSE", "TPEX"] and result["acquisition_callback_attempts"]["TPEX"] == 1
    assert result["A3_decision"] == "HOLD" and result["retry_count"] == 0


@pytest.mark.parametrize("error", ["response_byte_limit_exceeded", "connection_reset"])
def test_partial_or_oversize_body_is_never_normalized(error):
    acquire, calls, _ = fake_acquirer(failed_market="TPEX", failure_error=error)
    result, artifacts = a3.execute_with_acquirer(acquire, targets())
    assert calls == ["TWSE", "TPEX"]
    assert result["candidate"] is None and artifacts == {} and result["A3_decision"] == "HOLD"


def test_candidate_source_failed_is_hold_without_second_acquisition():
    twse, _ = sources()
    twse["data"][0][twse["fields"].index("投信買進股數")] = "bad"
    acquire, calls, _ = fake_acquirer(twse=twse)
    result, artifacts = a3.execute_with_acquirer(acquire, targets())
    assert calls == ["TWSE", "TPEX"] and len(artifacts) == 2
    assert result["A3_decision"] == "HOLD"
    assert result["evidence"]["TWSE"]["status"] == "source_failed"


def test_candidate_binding_failed_is_hold():
    twse, _ = sources()
    twse["data"][0][0] = "9999"
    acquire, calls, _ = fake_acquirer(twse=twse)
    result, _ = a3.execute_with_acquirer(acquire, targets())
    assert calls == ["TWSE", "TPEX"]
    assert result["A3_decision"] == "HOLD" and result["evidence"]["TWSE"]["status"] == "binding_failed"


def test_optional_caveat_can_remain_complete():
    twse, _ = sources()
    position = twse["fields"].index("證券名稱")
    twse["fields"].pop(position)
    for row in twse["data"]:
        row.pop(position)
    acquire, _, _ = fake_acquirer(twse=twse)
    result, _ = a3.execute_with_acquirer(acquire, targets())
    assert result["A3_decision"] == "PASS"
    assert "optional source-native field unavailable: security_name" in result["evidence"]["TWSE"]["caveats"]


@pytest.mark.parametrize("change", ["sha", "bytes"])
def test_live_transport_lineage_mismatch_rejected_before_candidate(change):
    acquire, calls, _ = fake_acquirer()

    def corrupt(market):
        info, payload = acquire(market)
        if market == "TWSE":
            if change == "sha":
                info["response_sha256"] = "0" * 64
            else:
                info["response_byte_count"] += 1
        return info, payload

    result, _ = a3.execute_with_acquirer(corrupt, targets())
    assert calls == ["TWSE"] and result["A3_decision"] == "HOLD"
    assert result["candidate"] is None


def test_candidate_file_or_schema_drift_rejected(monkeypatch):
    original = a3.sha
    def changed(path):
        value = original(path)
        return "0" * 64 if path.name == "cash_institutional_flow_context_evidence.v1.schema.json" else value
    monkeypatch.setattr(a3, "sha", changed)
    with pytest.raises(RuntimeError, match="immutable_authority_hash_drift"):
        a3.immutable_hashes()
    monkeypatch.setattr(a3, "sha", original)
    current = a3.candidate_hashes()
    assert current[a3.CANDIDATE_FILES[0]] != "0" * 64
    assert current[a3.CANDIDATE_FILES[1]] != "0" * 64


def test_sealed_pre_network_guard_rejects_candidate_code_drift(monkeypatch):
    # Model the pre-consumption state; the real consumed latch has precedence.
    monkeypatch.setattr(a3.Path, "exists", lambda path: False)
    closure = json.loads((a3.ROOT / a3.PRE_NETWORK).read_text(encoding="utf-8"))
    historical = {
        "phase_i_i3_a0_source_transport.py": closure["source_transport_sha256"],
        "run_phase_i_i3_a3_bounded_live_acceptance.py": closure["runner_sha256"],
        "validate_phase_i_i3_a3_live_acceptance.py": closure["validator_sha256"],
    }
    original_sha = a3.sha
    monkeypatch.setattr(a3, "sha", lambda path: historical.get(path.name, original_sha(path)))
    monkeypatch.setattr(a3, "git", lambda *args: "f" * 40 if args == ("rev-parse", "HEAD") else
                        a3.BRANCH if args == ("branch", "--show-current") else
                        a3.BASELINE if args == ("rev-parse", "origin/main") else "?? data/")
    monkeypatch.setattr(a3.subprocess, "check_output", lambda *args, **kwargs: b'{"state":"OPEN","isDraft":true}')
    monkeypatch.setattr(a3, "immutable_hashes", lambda: a3.HASHES)
    monkeypatch.setattr(a3, "production_containment", lambda: None)
    monkeypatch.setattr(a3, "candidate_hashes", lambda: {key: "0" * 64 for key in a3.CANDIDATE_FILES})
    with pytest.raises(RuntimeError, match="pre_network_closure_or_candidate_drift"):
        a3.final_pre_network_guard("f" * 40)


def test_full_raw_body_in_candidate_artifact_is_rejected(monkeypatch):
    acquire, _, raw = fake_acquirer()
    accepted = a3.run_i3_candidate_offline_batch

    def contaminated(*args, **kwargs):
        output = accepted(*args, **kwargs)
        key = next(iter(output["artifact_bytes"]))
        output["artifact_bytes"][key] = raw["TWSE"]
        return output

    monkeypatch.setattr(a3, "run_i3_candidate_offline_batch", contaminated)
    with pytest.raises(RuntimeError, match="raw_source_body_persistence_detected"):
        a3.execute_with_acquirer(acquire, targets())


def test_prior_consumed_latch_blocks_second_invocation(monkeypatch):
    monkeypatch.setattr(a3, "git", lambda *args: "f" * 40 if args == ("rev-parse", "HEAD") else
                        a3.BRANCH if args == ("branch", "--show-current") else
                        a3.BASELINE if args == ("rev-parse", "origin/main") else "?? data/")
    monkeypatch.setattr(a3.subprocess, "check_output", lambda *args, **kwargs: b'{"state":"OPEN","isDraft":true}' if args[0][0] == "gh" else b"")
    monkeypatch.setattr(a3, "immutable_hashes", lambda: a3.HASHES)
    monkeypatch.setattr(a3, "production_containment", lambda: None)
    monkeypatch.setattr(a3.Path, "exists", lambda path: str(path).endswith("i3-a3-live-authority-consumed.json"))
    with pytest.raises(RuntimeError, match="single_use_latch_or_outcome_exists"):
        a3.final_pre_network_guard("f" * 40)
