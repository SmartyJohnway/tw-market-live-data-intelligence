"""Attempt 2 runner tests use injected synthetic payloads only; no sockets."""
import json
import shutil
from pathlib import Path

import pytest

from scripts import run_phase_i_i3_a0_attempt2 as a2
from scripts import run_phase_i_i3_a0_preflight as p0


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Attempt 2 tests must not use network")
    monkeypatch.setattr("socket.socket.connect", deny)
    monkeypatch.setattr("socket.create_connection", deny)


def synthetic_bodies():
    fixtures = p0.ROOT / "tests/fixtures/phase_i_i3_a0"
    twse = (fixtures / "twse_synthetic.json").read_bytes()
    scenarios = json.loads((fixtures / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))
    tpex = json.dumps(scenarios["unique_candidate_a"], ensure_ascii=False).encode("utf-8")
    return twse, tpex


def test_fixed_acquisition_delegate_observes_one_exact_bounded_get():
    body = b"[]"
    calls = []
    def fake(url, **kwargs):
        calls.append((url, kwargs))
        return {"http_status": 200, "content_type": "application/json; charset=utf-8", "body": body}
    telemetry, returned = a2.acquire_once("TPEX", fake)
    assert returned == body
    assert telemetry["base_mime"] == "application/json"
    assert telemetry["retry_count"] == 0 and telemetry["timeout_seconds"] == 30
    assert telemetry["response_byte_count"] == 2
    assert calls == [(a2.URLS["TPEX"], {"timeout": 30, "max_bytes": 4 * 1024 * 1024 + 1,
                                           "follow_redirects": False, "method": "GET"})]


@pytest.mark.parametrize("response,expected", [
    ({"http_status": 302, "content_type": "application/json", "body": b"[]"}, "http_status_not_200"),
    ({"http_status": 200, "content_type": "text/html", "body": b"[]"}, "unsupported_content_type"),
    ({"http_status": 200, "content_type": "application/json", "body": b"x" * (4 * 1024 * 1024 + 1)}, "response_byte_limit_exceeded"),
])
def test_transport_rejects_nonaccepted_fake_responses(response, expected):
    telemetry, body = a2.acquire_once("TWSE", lambda *_args, **_kwargs: response)
    assert body is None
    assert telemetry["error_code"] == expected


def test_attempt2_two_market_fake_execution_consumes_latch_before_transport(tmp_path, monkeypatch):
    twse, tpex = synthetic_bodies()
    # The runner writes only under a temporary root for this test. Its accepted
    # immutable authorities are copied byte-for-byte into that isolated root.
    monkeypatch.setattr(a2, "ROOT", tmp_path)
    monkeypatch.setattr(a2, "verify_starting_git_state", lambda: None)
    monkeypatch.setattr(a2, "resolve_security_master", lambda: {
        "release_id": "security-master-20260926T151841Z",
        "index_sha256": a2.SM_INDEX_SHA,
        "qualification_sha256": a2.SM_QUALIFICATION_SHA,
        "qualification_status": "PASS",
        "targets": {
            "TWSE:1101": {"canonical_target_id": "TWSE:1101", "market": "TWSE", "security_code": "1101",
                           "instrument_family": "company_share", "instrument_type": "common_share",
                           "execution_eligibility": "allowed", "record_hash": "a" * 64},
            "TPEX:5347": {"canonical_target_id": "TPEX:5347", "market": "TPEX", "security_code": "5347",
                           "instrument_family": "company_share", "instrument_type": "common_share",
                           "execution_eligibility": "allowed", "record_hash": "b" * 64},
        },
    })
    historical_paths = [
        p0.RECORD,
        "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_PROBE_MAPPING_V1.json",
        "docs/governance/phase_i/PHASE_I_I3_A0_P0_OFFLINE_PROBE_HARNESS_CLOSURE_2026-10-01.json",
        "docs/governance/phase_i/PHASE_I_I3_A0_TPEX_DEALER_SELL_ADJUDICATION_V1.json",
        "docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json",
        "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_PROVENANCE_ERRATUM_2026-10-02.json",
    ]
    for rel in historical_paths:
        destination = tmp_path / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p0.ROOT / rel, destination)
    source_bodies = {"TWSE": twse, "TPEX": tpex}
    calls = []
    def fake(url, **kwargs):
        assert (tmp_path / a2.CONSUMED_REL).exists(), "durable consumed latch must precede first delegate"
        market = "TWSE" if url == a2.URLS["TWSE"] else "TPEX" if url == a2.URLS["TPEX"] else None
        assert market is not None
        calls.append(market)
        return {"http_status": 200, "content_type": "application/json", "body": source_bodies[market]}
    result = a2.run_attempt2(transport=fake, now=lambda: "2026-10-02T01:00:00Z")
    assert calls == ["TWSE", "TPEX"]
    assert result["actual_network_counts"] == {"TWSE": 1, "TPEx": 1, "TAIFEX": 0, "other_market_data": 0}
    assert result["tpex_dealer_sell_adjudication"]["selection_status"] == "RESOLVED"
    assert result["tpex_dealer_sell_adjudication"]["selected_candidate"] == "Dealers-TotalSell"
    assert result["raw_persistence"]["result"] == "NONE"
    assert result["reservation"]["consumed"] is True
    assert (tmp_path / a2.RESERVATION_REL).exists() and (tmp_path / a2.CONSUMED_REL).exists()
    raw = (tmp_path / a2.RESULT_REL).read_bytes()
    assert twse not in raw and tpex not in raw
    from scripts.validate_phase_i_i3_a0_attempt2 import validate
    assert validate(result, root=tmp_path, verify_runtime=False) is result
    with pytest.raises(ValueError, match="one_shot_latch"):
        a2.run_attempt2(transport=fake, now=lambda: "2026-10-02T01:00:01Z")
    assert calls == ["TWSE", "TPEX"]
