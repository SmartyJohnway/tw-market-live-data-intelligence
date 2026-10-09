"""Network-denied unit coverage for the J-B04-A5 acceptance-only runner."""
from __future__ import annotations

import json
import socket

import pytest

from scripts.phase_j_b04_a5_bounded_live_acceptance import (
    A5Error, ENDPOINT, MAX_BYTES, SingleUseAuthority, response_telemetry,
)
from server.services.phase_h_corporate_action_adapters import normalize_twse_twt48u_all


@pytest.fixture(autouse=True)
def deny_sockets(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("network access forbidden in A5-P0 tests")
    monkeypatch.setattr(socket, "create_connection", denied)


def _response(rows: object, *, url: str = ENDPOINT, content_type: str = "application/json") -> dict:
    return {"raw_bytes": json.dumps(rows).encode(), "status": 200, "content_type": content_type,
        "effective_url": url, "retrieved_at": "2026-10-09T00:00:00Z"}


def _row(code="2330", **updates):
    return {"Code": code, "Date": "2026-10-06", "Exdividend": "2", "StockDividendRatio": "0",
        "SubscriptionRatio": "0", "SubscriptionPricePerShare": "尚未公告", "CashDividend": "2", **updates}


def test_response_telemetry_accepts_exact_endpoint_array_and_hashes_only() -> None:
    result = response_telemetry(_response([_row()]))
    assert result["effective_url"] == ENDPOINT
    assert result["json_root_type"] == "array" and result["root_row_count"] == 1
    assert len(result["response_sha256"]) == 64


def test_live_call_without_explicit_authority_is_rejected_before_transport() -> None:
    with pytest.raises(A5Error, match="live_authorization_missing_or_stale_head"):
        SingleUseAuthority({}, head="a" * 40)


def test_authorization_is_single_use() -> None:
    head = "a" * 40
    statement = (f"AUTHORIZE J-B04-A5 LIVE ON HEAD {head}:\nexactly 1 GET to\n{ENDPOINT},\n"
        "retry 0,\nno redirects,\ntarget TWSE:2330,\nno H3 live calls,\n"
        "no TWT49U/TPEx/browser fallback,\nno raw payload persistence,\n"
        "no H2 activation,\nno J-B04 closure,\nno Phase J start.")
    import hashlib
    token = SingleUseAuthority({"gate": "J-B04-A5", "authorized_head_sha": head, "statement": statement,
        "statement_sha256": hashlib.sha256(statement.encode()).hexdigest()}, head=head)
    token.consume()
    with pytest.raises(A5Error, match="single_use_live_authorization_consumed"):
        token.consume()


def test_authorized_transport_invokes_one_logical_get_with_zero_retries() -> None:
    import hashlib
    from scripts.phase_j_b04_a5_bounded_live_acceptance import execute_single_authorized_get
    head = "b" * 40
    statement = (f"AUTHORIZE J-B04-A5 LIVE ON HEAD {head}:\nexactly 1 GET to\n{ENDPOINT},\n"
        "retry 0,\nno redirects,\ntarget TWSE:2330,\nno H3 live calls,\n"
        "no TWT49U/TPEx/browser fallback,\nno raw payload persistence,\n"
        "no H2 activation,\nno J-B04 closure,\nno Phase J start.")
    token = SingleUseAuthority({"gate": "J-B04-A5", "authorized_head_sha": head,
        "statement": statement, "statement_sha256": hashlib.sha256(statement.encode()).hexdigest()}, head=head)
    calls = []
    telemetry, counts, _ = execute_single_authorized_get(token,
        get_once=lambda **kwargs: calls.append(kwargs) or _response([]))
    assert calls == [{"timeout_seconds": 15}]
    assert counts == {"logical_get_attempts": 1, "http_dispatch_attempts": 0}
    assert telemetry["root_row_count"] == 0
    with pytest.raises(A5Error, match="single_use_live_authorization_consumed"):
        execute_single_authorized_get(token, get_once=lambda **kwargs: pytest.fail("second GET invoked"))


@pytest.mark.parametrize("url", ["https://openapi.twse.com.tw/redirect", ENDPOINT + "?x=1"])
def test_redirect_or_wrong_effective_url_is_rejected(url: str) -> None:
    with pytest.raises(A5Error, match="effective_url_mismatch_or_redirect"):
        response_telemetry(_response([], url=url))


def test_response_over_4_mib_is_rejected() -> None:
    with pytest.raises(A5Error, match="response_ceiling_exceeded"):
        response_telemetry({"raw_bytes": b" " * (MAX_BYTES + 1), "status": 200,
            "content_type": "application/json", "effective_url": ENDPOINT})


def test_non_json_content_type_is_rejected() -> None:
    with pytest.raises(A5Error, match="http_or_content_type_invalid"):
        response_telemetry(_response([], content_type="text/html"))


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(A5Error, match="json_invalid"):
        response_telemetry({"raw_bytes": b"{bad", "status": 200, "content_type": "application/json", "effective_url": ENDPOINT})


def test_non_list_json_root_is_rejected() -> None:
    with pytest.raises(A5Error, match="json_root_not_array"):
        response_telemetry(_response({"rows": []}))


def test_exact_target_zero_rows_preserves_current_scope_no_evidence() -> None:
    normalized = normalize_twse_twt48u_all([], {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"},
        observed_at="2026-10-09T00:00:00Z", citation_id="fixture-citation")
    assert normalized["status"] == "no_evidence_in_covered_scope" and normalized["events"] == []
    assert "historical" not in " ".join(normalized["caveats"]).casefold()


def test_exact_target_one_row_preserves_preannouncement_and_scheduled() -> None:
    normalized = normalize_twse_twt48u_all([_row()], {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"},
        observed_at="2026-10-09T00:00:00Z", citation_id="fixture-citation")
    event = normalized["events"][0]
    assert (event["source_evidence_stage"], event["event_lifecycle"]) == ("preannouncement", "scheduled")
    assert event["official_reference_price"] == {"state": "not_announced", "value": None}
    assert event["revision_relation"]["status"] == "unresolved"


def test_duplicate_exact_rows_fail_closed_without_selecting_first_or_latest() -> None:
    with pytest.raises(ValueError, match="ambiguous_exact_target_rows"):
        normalize_twse_twt48u_all([_row(), _row()], {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"},
            observed_at="2026-10-09T00:00:00Z", citation_id="fixture-citation")


def test_h3_fixture_is_deterministic_acceptance_only_and_not_temporal_authority() -> None:
    from scripts.phase_j_b04_a5_bounded_live_acceptance import acceptance_h3_fixture
    target = {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}
    first, second = acceptance_h3_fixture(target), acceptance_h3_fixture(target)
    assert first == second
    assert first["baselines"][0]["start_observation_date"] == "2026-10-05"
    assert first["baselines"][0]["end_observation_date"] == "2026-10-06"
    assert first["observations"][0]["source_family"] == "TEST_ACCEPTANCE_ONLY_NOT_LIVE_H3"


def test_captured_fake_response_flows_through_production_h2_and_binds_fixture_window(tmp_path) -> None:
    from scripts.phase_j_b04_a5_bounded_live_acceptance import execute_primary_target
    response = {"raw_bytes": json.dumps([_row()]).encode(), "status": 200,
        "content_type": "application/json", "effective_url": ENDPOINT,
        "retrieved_at": "2026-10-09T00:00:00Z"}
    run = execute_primary_target(response, {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}, tmp_path)
    result = run["operation_result"]
    primary = next(item for item in result["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    evidence_bytes = (tmp_path / primary["relative_path"]).read_bytes()
    evidence = json.loads(evidence_bytes)
    assert evidence["coverage"]["requested_window"] == {"start": "2026-10-05", "end": "2026-10-06"}
    assert evidence["coverage"]["declared_scope_complete"] is False
    assert evidence["events"][0]["source_evidence_stage"] == "preannouncement"
    assert evidence["events"][0]["event_lifecycle"] == "scheduled"
    assert all(path.read_bytes() != response["raw_bytes"] for path in tmp_path.rglob("*" ) if path.is_file())


def test_p0_cli_has_no_implicit_live_mode(monkeypatch):
    from scripts.phase_j_b04_a5_bounded_live_acceptance import main
    with pytest.raises(SystemExit):
        main([])
    with pytest.raises(SystemExit, match="A5-L1 is disabled"):
        main(["--live-acceptance"])

