from __future__ import annotations

import socket
from pathlib import Path

from scripts.run_phase_i_i2_a3_bounded_live_acceptance import (
    EXECUTOR_ID,
    PRE_NETWORK_AUTHORITY,
    deterministic_fixture_payload,
    run_fake_governed_acceptance,
)


def test_fake_transport_completes_real_authorization_dispatch_and_v3_chain(tmp_path, monkeypatch):
    calls = []
    payload = deterministic_fixture_payload()

    def network_denied(*args, **kwargs):
        raise AssertionError("P0 attempted an external socket connection")

    monkeypatch.setattr(socket.socket, "connect", network_denied)

    def fake_transport(url, timeout):
        calls.append((url, timeout))
        return 200, {"Content-Type": "application/octet-stream; charset=binary"}, payload

    out = run_fake_governed_acceptance(output_root=tmp_path / "a3-p0", fake_transport=fake_transport)
    assert calls == [("https://openapi.taifex.com.tw/v1/DailyMarketReportFut", 30)]
    assert out["authorization"]["owner_review_reference"] == PRE_NETWORK_AUTHORITY
    assert out["authorization"]["network_authorized"] is True
    assert out["preflight"]["execution_authorized"] is True
    assert out["preflight"]["network_authorized"] is True
    assert out["preflight"]["network_required"] is True
    assert len(out["preflight"]["approved_operation_order"]) == 2
    assert len(out["preflight"]["resolved_batch_bindings"]) == 1
    assert len(out["preflight"]["bounded_execution_requests"]) == 2
    assert {x["schema_version"] for x in out["preflight"]["bounded_execution_requests"]} == {"unified_market_evidence_execution_request.v2"}
    assert {x["operation_id"] for x in out["execution"]["dispatch_outcomes"]} == set(out["operation_ids"])
    assert out["execution"]["claim_record"]["attempt_count"] == 1
    assert out["replay_denied_before_transport"] is True
    assert out["execution"]["consumption_state"] == "consumed_success"
    assert len(out["execution"]["dispatch_outcomes"]) == 2
    assert out["simulated_source_acquisitions"] == 1
    assert out["actual_external_market_calls"] == 0
    assert out["result_v3_replay"] is True and out["audit_v3_replay"] is True
    assert out["raw_payload_persistence"] == "NONE"
    typed = [target["evidence"]["index_futures_context"] for target in out["result"]["targets"]]
    assert {x["target"]["canonical_target_id"] for x in typed} == {"TWSE:1101", "TWSE:1102"}
    assert {x["alignment_status"] for x in typed} == {"not_comparable"}
    assert {x["transport"]["response_sha256"] for x in typed} == {out["source_acquisition"].response_sha256}
    assert {x["transport"]["response_byte_count"] for x in typed} == {out["source_acquisition"].response_byte_count}
    assert {x["transport"]["retrieved_at"] for x in typed} == {out["source_acquisition"].retrieved_at}
    assert {x["contract_period"] for x in typed} == {"202610"}
    assert {x["trade_date"] for x in typed} == {"2026-09-29"}
    assert all(item["executor_id"] == EXECUTOR_ID for item in out["plan"]["operations"])
