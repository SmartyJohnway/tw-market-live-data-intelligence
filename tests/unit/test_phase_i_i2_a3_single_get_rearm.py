from __future__ import annotations

import copy
import json
import socket

import pytest

from scripts import phase_i_i2_a3_live_support as live
from scripts.run_phase_i_i2_a3_bounded_live_acceptance import deterministic_fixture_payload
from server.services.phase_i_i2_index_futures_adapters import SOURCE_ENDPOINT


@pytest.mark.parametrize("authority,confirmed,environment", [
    (None, True, "YES"), (live.SUPERSEDED_AUTHORITY, True, "YES"),
    (live.OWNER_AUTHORITY, False, "YES"), (live.OWNER_AUTHORITY, True, None),
    (live.OWNER_AUTHORITY, True, "NO"),
])
def test_rearm_requires_all_fresh_authority_inputs(authority, confirmed, environment):
    with pytest.raises(ValueError, match="live_execution_not_rearmed"):
        live.require_rearm(authority=authority, confirmed=confirmed, environment=environment)


def test_fresh_authority_with_confirmation_and_environment_is_accepted():
    live.require_rearm(authority=live.OWNER_AUTHORITY, confirmed=True, environment="YES")


def test_one_shot_counts_before_delegate_and_rejects_reuse(tmp_path):
    calls = []
    def fake(url, timeout):
        calls.append((url, timeout))
        raise TimeoutError("fixture")
    one = live.SingleGetDelegate(fake, tmp_path / "single-get-attempt.json")
    with pytest.raises(TimeoutError):
        one(SOURCE_ENDPOINT, 30)
    with pytest.raises(ValueError, match="single_get_scope_or_count_violation"):
        one(SOURCE_ENDPOINT, 30)
    assert calls == [(SOURCE_ENDPOINT, 30)]
    assert json.loads(one.marker_path.read_text())["get_authorization_consumed"] is True
    assert one.telemetry["error_code"] == "source_failed:transport_exception"


@pytest.mark.parametrize("url,timeout", [("https://example.invalid", 30), (SOURCE_ENDPOINT, 15)])
def test_wrong_transport_scope_rejected_before_io(tmp_path, url, timeout):
    calls = []
    one = live.SingleGetDelegate(lambda *args: calls.append(args), tmp_path / "attempt.json")
    with pytest.raises(ValueError):
        one(url, timeout)
    assert calls == []


def _offline_acceptance(tmp_path, monkeypatch, kind):
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network forbidden")))
    # Isolate accepted-authority reservations and ledgers; generated output is
    # temporary. The transport is always an injected in-process source fixture.
    monkeypatch.setattr(live, "LEDGER_PATH", tmp_path / "ledger.json")
    monkeypatch.setattr(live, "ATTEMPT_PATH", tmp_path / "attempt.json")
    monkeypatch.setattr(live, "RESERVATION_PATH", tmp_path / "reservation.json")
    rows = json.loads(deterministic_fixture_payload())
    selected = next(x for x in rows if x["Date"] == "20260929" and x["Contract"] == "TX"
                    and x["TradingSession"] == "一般" and x["ContractMonth(Week)"] == "202610")
    if kind == "partial":
        selected["Open"] = "-"
    elif kind == "unavailable":
        for row in rows:
            row["Contract"] = "MTX"
    elif kind == "source_failed":
        selected["Last"] = "malformed"
    elif kind == "binding_failed":
        rows.append(copy.deepcopy(selected))
    body = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
    calls = []
    def fake(url, timeout):
        calls.append((url, timeout))
        if kind == "transport_failed":
            raise TimeoutError("fixture")
        return 200, {"Content-Type": "application/octet-stream"}, body
    out = live.execute_single_get_acceptance(transport_delegate=fake,
        output_root=tmp_path / "run", write_governance=False)
    assert calls == [(SOURCE_ENDPOINT, 30)]
    assert out["get_authorization_consumed"] is True
    assert out["network"]["retry_count"] == 0
    assert out["raw_payload_persistence"] == "NONE"
    return out


@pytest.mark.parametrize("kind", ["complete", "partial"])
def test_rearmed_packaging_shared_governed_path_passes_offline(tmp_path, monkeypatch, kind):
    out = _offline_acceptance(tmp_path, monkeypatch, kind)
    assert out["status"] == "PASS"
    assert out["owner_authorization_reference"] == live.OWNER_AUTHORITY
    assert out["superseded_authority_consumed"] is False
    assert out["superseded_authority_operational_status"] == "superseded_without_use"
    assert out["governed_execution"]["claim_attempt_count"] == 1
    assert out["governed_execution"]["operation_statuses"] == ["succeeded", "succeeded"]
    assert {x["status"] for x in out["normalized_evidence"]} == {kind}
    assert {x["retrieved_at"] for x in out["normalized_evidence"]} == {out["acceptance_execution_timestamp"]}
    assert out["source_telemetry"]["selected_contract_period"] == "202610"
    assert out["source_telemetry"]["selected_binding_count"] == 1
    assert out["same_source_reuse"]["source_acquisitions"] == 1
    assert out["projection"]["result_replay"] == out["projection"]["audit_replay"] == "PASS"
    assert out["acceptance_package"]["raw_body_absence_verified"] is True
    from scripts import validate_phase_i_i2_a3_live_acceptance as validator
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps(out), encoding="utf-8")
    monkeypatch.setattr(validator, "LEDGER_PATH", ledger)
    monkeypatch.setattr(validator, "_contained", lambda reference: tmp_path / "run" / reference)
    assert validator.validate()["status"] == "PASS"
    out["network"]["TAIFEX"] = 2
    ledger.write_text(json.dumps(out), encoding="utf-8")
    with pytest.raises(ValueError, match="live_network_bounds_invalid"):
        validator.validate()


@pytest.mark.parametrize("kind", ["unavailable", "source_failed", "binding_failed", "transport_failed"])
def test_nonpassing_acquisition_never_creates_pass_ledger_or_retries(tmp_path, monkeypatch, kind):
    out = _offline_acceptance(tmp_path, monkeypatch, kind)
    assert out["status"] == "FAIL"
    assert not (tmp_path / "ledger.json").exists()
    assert (tmp_path / "run/bounded-attempt-summary.json").exists()
    assert out["preserved_governed_artifacts"]


def test_existing_authority_reservation_denies_new_acquisition(tmp_path, monkeypatch):
    reservation = tmp_path / "reservation.json"
    reservation.write_text("{}")
    monkeypatch.setattr(live, "RESERVATION_PATH", reservation)
    with pytest.raises(ValueError, match="single_get_authority_already_recorded"):
        live.check_prior_attempts()


def test_default_delegate_cannot_run_without_cli_guards():
    with pytest.raises(ValueError, match="live_execution_not_rearmed"):
        live.execute_single_get_acceptance()
