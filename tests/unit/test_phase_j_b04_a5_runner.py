"""Network-denied unit coverage for the J-B04-A5 acceptance-only runner."""
from __future__ import annotations

import json
import socket
from types import SimpleNamespace

import pytest

from scripts.phase_j_b04_a5_bounded_live_acceptance import (
    A5Error, ENDPOINT, MAX_BYTES, SingleUseAuthority, response_telemetry,
    resolve_predeclared_target, resolve_execution_target, run_p0_preflight, expected_owner_statement,
    predeclared_source_target, select_offline_stage_witness,
)
from server.services.phase_h_corporate_action_adapters import normalize_twse_twt48u_all


@pytest.fixture(autouse=True)
def deny_sockets(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("network access forbidden in A5-P0 tests")
    monkeypatch.setattr(socket, "create_connection", denied)


@pytest.fixture(autouse=True)
def reset_mode_a_cache():
    from scripts.m8r_06_01c2_mode_a_security_master_loader import reset_production_mode_a_security_master_for_tests
    reset_production_mode_a_security_master_for_tests()
    yield
    reset_production_mode_a_security_master_for_tests()


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
    assert "rows" not in result and "rows_in_memory" not in result and "raw_bytes" not in result


def test_live_call_without_explicit_authority_is_rejected_before_transport() -> None:
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_INVALID"):
        SingleUseAuthority({}, head="a" * 40)


def test_authorization_is_single_use() -> None:
    head = "a" * 40
    statement = expected_owner_statement(head)
    import hashlib
    token = SingleUseAuthority({"gate": "J-B04-A5", "authorized_head_sha": head, "authorized_tree_sha": "t" * 40,
        "execution_environment_class": "cloud_clean_source_acceptance", "statement": statement,
        "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(), "consumed": False}, head=head)
    token.consume()
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_ALREADY_CONSUMED"):
        token.consume()


@pytest.mark.parametrize("url", ["https://openapi.twse.com.tw/redirect", ENDPOINT + "?x=1"])
def test_redirect_or_wrong_effective_url_is_rejected(url: str) -> None:
    from scripts.phase_j_b04_a5_bounded_live_acceptance import _safe_capture_response
    assert _safe_capture_response(_response([], url=url)).parse_error == "effective_url_mismatch_or_redirect"


def test_response_over_4_mib_is_rejected() -> None:
    from scripts.phase_j_b04_a5_bounded_live_acceptance import _safe_capture_response
    assert _safe_capture_response({"raw_bytes": b" " * (MAX_BYTES + 1), "status": 200,
        "content_type": "application/json", "effective_url": ENDPOINT}).parse_error == "response_ceiling_exceeded"


def test_non_json_content_type_is_rejected() -> None:
    from scripts.phase_j_b04_a5_bounded_live_acceptance import _safe_capture_response
    assert _safe_capture_response(_response([], content_type="text/html")).parse_error == "content_type_not_json"


def test_invalid_json_is_rejected() -> None:
    from scripts.phase_j_b04_a5_bounded_live_acceptance import _safe_capture_response
    assert _safe_capture_response({"raw_bytes": b"{bad", "status": 200, "content_type": "application/json", "effective_url": ENDPOINT}).parse_error == "json_invalid"


def test_non_list_json_root_is_rejected() -> None:
    from scripts.phase_j_b04_a5_bounded_live_acceptance import _safe_capture_response
    assert _safe_capture_response(_response({"rows": []})).parse_error == "json_root_not_array"


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


def test_live_cli_requires_external_authorization_file(monkeypatch):
    from scripts.phase_j_b04_a5_bounded_live_acceptance import main
    with pytest.raises(SystemExit):
        main([])
    with pytest.raises(SystemExit):
        main(["--preflight"])
    assert main(["--live-acceptance", "--execution-environment", "cloud_clean_source_acceptance",
        "--owner-authorization-json", "/tmp/not-present-owner-auth.json"]) == 3


def _release_record(*, canonical="TWSE:2330", market="TWSE", code="2330", family="company_share",
                    instrument_type="common_share", eligible="allowed"):
    return {
        "canonical_target_id": canonical,
        "identity": {"security_code": code, "isin": "TW0002330008"},
        "classification": {"market": market, "instrument_family": family, "instrument_type": instrument_type},
        "lifecycle": {"state": "listed", "resolution_status": "resolved", "basis_event_ids": [], "events": []},
        "execution_eligibility": {"status": eligible, "reason_codes": []},
    }


def _activate_local_release(root):
    from scripts.m8r_08g_security_master_releases import build_candidate_release, qualify_candidate_release, activate_qualified_release
    rid = "security-master-20261009T010203Z"
    provenance = {"source_type": "test", "snapshot_id": "fixture", "source_content_hashes": {"fixture": "a" * 64},
        "producer_skill": {"name": "test", "skill_version": "1", "skill_contract_hash": "b" * 64}}
    build_candidate_release(root=root, release_id=rid, records=[_release_record()], source_provenance=provenance)
    qualified, report = qualify_candidate_release(root=root, release_id=rid)
    assert qualified and report["status"] == "PASS"
    activate_qualified_release(root=root, release_id=rid)
    return rid


def test_valid_installation_local_release_resolves_without_legacy_candidate_artifacts(tmp_path, monkeypatch):
    from scripts.m8r_06_01c2_mode_a_security_master_loader import POINTER_PATH
    rid = _activate_local_release(tmp_path)
    monkeypatch.setenv("TW_MARKET_SECURITY_MASTER_ROOT", str(tmp_path))
    legacy = json.loads(POINTER_PATH.read_text())
    assert not (POINTER_PATH.parents[1] / legacy["index_path"]).exists()
    assert not (POINTER_PATH.parents[1] / legacy["manifest_path"]).exists()
    identity = resolve_predeclared_target()
    assert identity["canonical_target_id"] == "TWSE:2330"
    assert identity["resolution_reason"] == "exact_listing_id"
    assert identity["security_master_release_id"] == rid
    assert identity["canonical_identity_authority"] == "installation_local_security_master_release"
    assert identity["environment_root_selected"] is True
    target = resolve_execution_target("installation_bound")
    assert target["identity_assurance_level"] == "production_identity_verified"
    assert target["production_identity_verified"] is True
    assert target["A6_identity_reverification_required"] is False


def test_environment_selected_root_is_used_by_production_mode_a_loader(tmp_path, monkeypatch):
    rid = _activate_local_release(tmp_path)
    monkeypatch.setenv("TW_MARKET_SECURITY_MASTER_ROOT", str(tmp_path))
    preflight = run_p0_preflight("cloud_clean_source_acceptance")
    assert preflight["preflight_status"] == "J_B04_A5_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW"
    assert preflight["security_master_status"] == "ACTIVE"
    assert preflight["identity_assurance_level"] == "production_identity_verified"
    assert preflight["production_identity_verified"] is True
    assert preflight["A6_identity_reverification_required"] is False
    assert preflight["TW_MARKET_SECURITY_MASTER_ROOT_selected"] is True
    assert preflight["identity_resolution"]["security_master_release_id"] == rid


def test_canonical_not_initialized_does_not_fallback_or_make_market_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("TW_MARKET_SECURITY_MASTER_ROOT", str(tmp_path / "empty-root"))
    record = run_p0_preflight("cloud_clean_source_acceptance")
    assert record["preflight_status"] == "J_B04_A5_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW"
    assert record["security_master_status"] == "NOT_INITIALIZED"
    assert record["identity_assurance_level"] == "acceptance_only_predeclared_source_target"
    assert record["production_identity_verified"] is False
    assert record["A6_identity_reverification_required"] is True
    assert record["predeclared_source_target"] == {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}
    assert record["identity_resolution"]["security_master_release_id"] is None
    assert record["legacy_candidate_fallback"] is False
    assert record["fixture_identity_fallback"] is False
    assert record["company_name_fallback"] is False
    assert record["live_security_master_bootstrap_performed"] is False
    assert record["network_calls_so_far"] == {"market_GET": 0, "market_HEAD": 0, "market_POST": 0,
        "security_master_live_acquisition": 0}


def test_installation_bound_not_initialized_remains_blocked(tmp_path, monkeypatch):
    monkeypatch.setenv("TW_MARKET_SECURITY_MASTER_ROOT", str(tmp_path / "empty-root"))
    state = resolve_execution_target("installation_bound")
    assert state["preflight_status"] == "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_NOT_INITIALIZED"
    assert state["identity_assurance_level"] is None
    assert state["target_binding"] is None


def test_execution_environment_is_explicit_and_unknown_values_rejected():
    with pytest.raises(A5Error, match="execution_environment_class_required_or_invalid"):
        resolve_execution_target("")
    with pytest.raises(A5Error, match="execution_environment_class_required_or_invalid"):
        resolve_execution_target("guessed_from_cloud")


def test_invalid_active_release_fails_closed(tmp_path, monkeypatch):
    (tmp_path / "active.json").write_text("{bad", encoding="utf-8")
    monkeypatch.setenv("TW_MARKET_SECURITY_MASTER_ROOT", str(tmp_path))
    record = run_p0_preflight("cloud_clean_source_acceptance")
    assert record["preflight_status"] == "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID"
    assert record["security_master_status"] == "INVALID"
    assert record["identity_resolution"]["security_master_release_id"] is None
    assert record["network_calls_so_far"] == {"market_GET": 0, "market_HEAD": 0, "market_POST": 0,
        "security_master_live_acquisition": 0}


@pytest.mark.parametrize("mutation", [
    {"canonical": "TWSE:2331"}, {"market": "TPEX"}, {"code": "2331"},
    {"family": "etf"}, {"instrument_type": "preferred_share"}, {"eligible": "blocked"},
])
def test_target_scope_mutations_block(mutation, monkeypatch):
    from scripts import m8r_06_01c2_mode_a_security_master_loader as loader
    record = _release_record(**mutation)
    selected = {**record}
    resolved = SimpleNamespace(status="resolved", reason_codes=["exact_listing_id"], selected=selected)
    service = SimpleNamespace(resolve=lambda query, market_hint=None: resolved, release_id="release-x", manifest_hash="a" * 64)
    runtime = SimpleNamespace(identity_service=service, pointer={"release_id": "release-x",
        "release_manifest_sha256": "a" * 64, "release_index_sha256": "b" * 64})
    monkeypatch.setattr(loader, "get_production_mode_a_security_master", lambda: runtime)
    with pytest.raises(A5Error, match="TARGET_IDENTITY_SCOPE_INVALID"):
        resolve_predeclared_target()


def test_name_only_result_is_never_accepted(monkeypatch):
    from scripts import m8r_06_01c2_mode_a_security_master_loader as loader
    calls = []
    resolution = SimpleNamespace(status="not_found", reason_codes=["exact_normalized_name"], selected=None)
    service = SimpleNamespace(resolve=lambda query, market_hint=None: calls.append((query, market_hint)) or resolution)
    runtime = SimpleNamespace(identity_service=service, pointer={})
    monkeypatch.setattr(loader, "get_production_mode_a_security_master", lambda: runtime)
    with pytest.raises(A5Error, match="TARGET_IDENTITY_SCOPE_INVALID"):
        resolve_predeclared_target()
    assert calls == [("TWSE:2330", "TWSE")]


def test_a5_validator_accepts_canonical_not_initialized_record_and_rejects_legacy_authority():
    import copy
    from scripts.validate_phase_j_b04_a5_bounded_live_acceptance import RECORD, validate_contract
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert validate_contract(record)["status"] == "READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW"
    mutated = copy.deepcopy(record)
    mutated["canonical_identity_authority"] = "config/m8r_06_mode_a_security_master_pointer.json"
    with pytest.raises(AssertionError):
        validate_contract(mutated)
    mutated = copy.deepcopy(record)
    mutated["identity_resolution"]["security_master_release_id"] = "fake-release"
    with pytest.raises(AssertionError):
        validate_contract(mutated)


def test_predeclared_source_target_hash_is_immutable(monkeypatch):
    from scripts import phase_j_b04_a5_bounded_live_acceptance as runner
    target, digest = predeclared_source_target()
    assert target == {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}
    assert len(digest) == 64
    monkeypatch.setitem(runner.PREDECLARED_SOURCE_TARGET, "security_code", "2331")
    with pytest.raises(A5Error, match="predeclared_source_target_authority_corrupt"):
        predeclared_source_target()


def test_mutating_source_target_after_authority_construction_is_rejected():
    from scripts.phase_j_b04_a5_bounded_live_acceptance import (
        PREDECLARED_SOURCE_TARGET_SHA256, PredeclaredSourceTargetAuthority,
        _canonical_target_bytes,
    )
    authority = PredeclaredSourceTargetAuthority(
        _canonical_target_bytes({"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}).decode(),
        PREDECLARED_SOURCE_TARGET_SHA256,
    )
    mutated = authority.descriptor()
    mutated["security_code"] = "2331"
    with pytest.raises(A5Error, match="predeclared_source_target_mutated"):
        authority.bind(mutated)


def test_cloud_clean_descriptor_contains_no_fabricated_identity_fields():
    target, _ = predeclared_source_target()
    assert set(target) == {"canonical_target_id", "market", "security_code"}
    assert not {"isin", "instrument_family", "instrument_type", "execution_eligibility"}.intersection(target)


def test_offline_stage_witness_selects_deterministically_without_identity_lookup():
    rows = [_row("2317", Date="2026-10-07"), _row("1101", Date="2026-10-08")]
    first = select_offline_stage_witness(rows, observed_at="2026-10-09T00:00:00Z")
    second = select_offline_stage_witness(list(reversed(rows)), observed_at="2026-10-09T00:00:00Z")
    assert first == second
    assert first["source_target"] == {"canonical_target_id": "TWSE:1101", "market": "TWSE", "security_code": "1101"}
    assert first["product_scope_identity_verified"] is False
    assert first["source_stage_witness_only"] is True
    assert first["normalized_evidence"]["events"][0]["source_evidence_stage"] == "preannouncement"
    assert first["normalized_evidence"]["events"][0]["event_lifecycle"] == "scheduled"


def test_offline_stage_witness_prefers_normalizable_primary_target():
    rows = [_row("1101", Date="2026-10-07"), _row("2330", Date="2026-10-08")]
    selected = select_offline_stage_witness(rows, observed_at="2026-10-09T00:00:00Z")
    assert selected["source_target"] == {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}
    assert selected["product_scope_identity_verified"] is False

