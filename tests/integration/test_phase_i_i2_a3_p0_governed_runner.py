from __future__ import annotations

import pytest
from scripts.phase_i_i2_a4_proof import historical_dormant_authority


@pytest.fixture(autouse=True)
def accepted_pre_activation_authority():
    """Historical A1/A2/A3 gates retain the exact accepted dormant baseline."""
    with historical_dormant_authority():
        yield

import socket
import copy
import json
from pathlib import Path

from scripts.run_phase_i_i2_a3_bounded_live_acceptance import (
    EXECUTOR_ID,
    PRE_NETWORK_AUTHORITY,
    deterministic_fixture_payload,
    run_fake_governed_acceptance,
)
from server.services.phase_i_i2_index_futures_adapters import SOURCE_ENDPOINT


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


def _failure_payload(kind: str) -> bytes:
    rows = json.loads(deterministic_fixture_payload())
    if kind == "source_failed":
        next(row for row in rows if row["Date"] == "20260929" and row["Contract"] == "TX"
             and row["TradingSession"] == "一般" and row["ContractMonth(Week)"] == "202610")["Last"] = "bad-numeric"
    elif kind == "binding_failed":
        selected = next(row for row in rows if row["Date"] == "20260929" and row["Contract"] == "TX"
                        and row["TradingSession"] == "一般" and row["ContractMonth(Week)"] == "202610")
        rows.append(copy.deepcopy(selected))
    elif kind == "unavailable":
        for row in rows:
            if row["Date"] == "20260929" and row["Contract"] == "TX" and row["TradingSession"] == "一般":
                row["Contract"] = "MTX"
    else:
        raise AssertionError(kind)
    return json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _run_noncomplete_governed_case(tmp_path, monkeypatch, kind):
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("P0 attempted an external socket connection")))
    payload = _failure_payload(kind)
    calls = []

    def fake_transport(url, timeout):
        calls.append((url, timeout))
        return 200, {"Content-Type": "application/octet-stream"}, payload

    out = run_fake_governed_acceptance(output_root=tmp_path / kind, fake_transport=fake_transport)
    assert calls == [(SOURCE_ENDPOINT, 30)]
    assert out["simulated_source_acquisitions"] == 1
    assert out["actual_external_market_calls"] == 0
    assert len(out["execution"]["dispatch_outcomes"]) == 2
    return out


def _assert_operation_artifacts_and_governance(out, *, evidence_status, operation_status, error_code):
    execution = out["execution"]
    assert execution["claim_record"]["attempt_count"] == 1
    assert execution["consumption_state"] == ("consumed_success" if operation_status == "succeeded" else "consumed_failed")
    assert all((x["status"], x["error_code"], x["result_item_count"]) == (operation_status, error_code, 1)
               for x in execution["dispatch_outcomes"])
    assert all(x["status"] == operation_status and x["error_code"] == error_code
               for x in execution["execution_receipt"]["operation_receipts"])
    assert all(x["status"] == operation_status and x["error_code"] == error_code
               for x in execution["evidence_bundle"]["operation_evidence_entries"])
    for outcome in execution["dispatch_outcomes"]:
        artifact = outcome["evidence_artifacts"][0]
        artifact_path = out["package_root"] / artifact["relative_path"]
        raw = artifact_path.read_bytes()
        assert len(raw) == artifact["byte_size"]
        import hashlib
        assert hashlib.sha256(raw).hexdigest() == artifact["sha256"]
        typed = json.loads(raw)
        assert typed["status"] == evidence_status
        assert typed["citation_ids"]
        assert outcome["warnings"] == typed["caveats"]
        assert any(x["relative_path"] == artifact["relative_path"] and x["sha256"] == artifact["sha256"]
                   for x in execution["evidence_bundle"]["artifact_inventory"])
    assert out["result_v3_replay"] is True and out["audit_v3_replay"] is True
    for target in out["result"]["targets"]:
        target_id = target["resolution"]["canonical_target_id"]
        binding = out["lineage"].bindings[target_id]["index_futures_context"]
        if operation_status == "failed":
            assert "index_futures_context" not in target["evidence"]
            assert binding.status == "failed" and binding.error_code == evidence_status
            assert len(binding.evidence_artifacts) == 1 and len(binding.artifact_objects) == 1
            artifact_object = next(iter(binding.artifact_objects.values()))
            assert artifact_object["status"] == evidence_status
            assert out["citation_index"].target_need_citations[f"{target_id}::index_futures_context"] == []
        else:
            assert target["evidence"]["index_futures_context"]["status"] == evidence_status
            assert binding.status == "succeeded"


def test_source_failed_governed_chain_preserves_failure_artifact_and_lineage(tmp_path, monkeypatch):
    out = _run_noncomplete_governed_case(tmp_path, monkeypatch, "source_failed")
    _assert_operation_artifacts_and_governance(
        out, evidence_status="source_failed", operation_status="failed", error_code="source_failed")


def test_binding_failed_governed_chain_preserves_failure_artifact_and_lineage(tmp_path, monkeypatch):
    out = _run_noncomplete_governed_case(tmp_path, monkeypatch, "binding_failed")
    _assert_operation_artifacts_and_governance(
        out, evidence_status="binding_failed", operation_status="failed", error_code="binding_failed")


def test_unavailable_evidence_remains_successful_operation_in_governed_chain(tmp_path, monkeypatch):
    out = _run_noncomplete_governed_case(tmp_path, monkeypatch, "unavailable")
    _assert_operation_artifacts_and_governance(
        out, evidence_status="unavailable", operation_status="succeeded", error_code=None)
