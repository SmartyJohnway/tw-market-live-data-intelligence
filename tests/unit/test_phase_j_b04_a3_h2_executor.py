"""Network-free tests for the J-B04-A3 TWSE H2 executor candidate."""
from __future__ import annotations

import hashlib
import json
import copy
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker

from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.validate_phase_h_v3_contracts import validate_corporate_action_context_semantics
from scripts.validate_phase_h_v3_contracts import validate_discontinuity_safety_semantics, validate_h2_h3_h4_cross_evidence
from server.services.phase_h_h2_twse_exright_executor import (
    ENDPOINT,
    _phase_h_artifact_record,
    derive_h4_for_completed_plan,
    execute_h2_twse_exright_pre,
)
from server.services.phase_h_recent_performance import build_recent_performance_evidence
from server.services.phase_h_discontinuity_safety import derive_discontinuity_safety

ROOT = Path(__file__).resolve().parents[2]
TARGET = {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}
WINDOW = {"start": "2026-08-27", "end": "2026-08-28"}
CONTRACT_EXAMPLES = json.loads((ROOT / "tests/fixtures/phase_h_contract_v3/contract_examples.json").read_text(encoding="utf-8"))
H4_SCHEMA = json.loads((ROOT / "schemas/discontinuity_safety_evidence.v1.schema.json").read_text(encoding="utf-8"))


def _h3() -> dict:
    schema = json.loads((ROOT / "schemas/recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8"))

    def row(day: str, close: int) -> dict:
        return {
            **TARGET,
            "trade_date": day,
            "close": close,
            "volume": 1000,
            "source_family": "OFFICIAL_FIXTURE_ONLY",
            "source_contract_id": "a3-test-h3-fixture",
            "retrieved_at": "2026-10-08T00:00:00Z",
            "citation_ids": [f"cit-{day}"],
        }

    return build_recent_performance_evidence(
        target=TARGET,
        observations=[row(WINDOW["start"], 100)],
        governed_end_observation=row(WINDOW["end"], 101),
        requested_observations=1,
        baseline_lookbacks=[1],
        current_volume_basis="completed_session",
        schema=schema,
    )


def _request() -> dict:
    return {
        "schema_version": "unified_market_evidence_execution_request.v1",
        "operation_id": "a3-h2-operation",
        "execution_request_id": "a3-h2-request",
        "execution_request_hash": "a" * 64,
        "executor_id": "phase_h_h2_twse_exright_pre_executor",
        "capability_id": "corporate_action_context",
        "market": "TWSE",
        "approved_security_identifiers": ["TWSE:2330"],
        "timeout_seconds": 15,
    }


def _h3_dependency(output_root: Path, *, status: str = "succeeded", alter=None) -> dict:
    evidence = _h3()
    if alter:
        alter(evidence)
    rel = "evidence/phase_h/h3/a3-h3-operation.json"
    content = (canonical_json(evidence) + "\n").encode()
    atomic_write_bytes(str(output_root), rel, content)
    artifact = {
        "relative_path": rel,
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
        "schema_version": "recent_performance_evidence.v1",
        "evidence_contract": "recent_performance_evidence.v1",
        "artifact_role": "primary_evidence",
    }
    op = {
        "operation_id": "a3-h3-operation",
        "capability_id": "recent_performance",
        "executor_id": "phase_h_h3_twse_recent_performance_executor",
        "market": "TWSE",
        "canonical_target_ids": [TARGET["canonical_target_id"]],
        "dependency_operation_ids": [],
    }
    result = {
        "operation_id": "a3-h3-operation",
        "status": status,
        "capability_id": "recent_performance",
        "executor_id": "phase_h_h3_twse_recent_performance_executor",
        "evidence_contract": "recent_performance_evidence.v1",
        "evidence_artifacts": [artifact] if status == "succeeded" else [],
    }
    return {"dependencies": [{"operation_id": op["operation_id"], "operation": op, "result": result}]}


def _row(code: str = "2330", **updates) -> dict:
    row = {
        "Code": code,
        "Date": "2026-08-28",
        "Exdividend": "2",
        "StockDividendRatio": "0",
        "SubscriptionRatio": "0",
        "SubscriptionPricePerShare": "尚未公告",
        "CashDividend": "2",
    }
    row.update(updates)
    return row


def _response(rows: list[dict]) -> dict:
    return {
        "raw_bytes": json.dumps(rows, ensure_ascii=False).encode("utf-8"),
        "status": 200,
        "content_type": "application/json; charset=utf-8",
        "effective_url": ENDPOINT,
        "retrieved_at": "2026-10-08T00:00:00Z",
    }


def _context(tmp_path: Path, dependency_context: dict | None = None) -> DispatchRuntimeContext:
    return DispatchRuntimeContext(str(tmp_path), "execute-approved", dependency_context)


def _validate_h2(result: dict, tmp_path: Path) -> dict:
    primary = next(item for item in result["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    value = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/corporate_action_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(value))
    validate_corporate_action_context_semantics(value)
    sidecar = next(item for item in result["evidence_artifacts"] if item["schema_version"] == "phase_h_source_attempt_governance.v1")
    gov_schema = json.loads((ROOT / "schemas/phase_h_source_attempt_governance.v1.schema.json").read_text(encoding="utf-8"))
    gov = json.loads((tmp_path / sidecar["relative_path"]).read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(gov_schema, format_checker=FormatChecker()).iter_errors(gov))
    return value


def test_one_target_row_binds_exact_h3_window_and_preserves_scheduled_stage(tmp_path: Path) -> None:
    calls = []

    def fetch_response(**kwargs):
        calls.append(kwargs)
        return _response([_row()])

    result = execute_h2_twse_exright_pre(
        _request(), _context(tmp_path, _h3_dependency(tmp_path)), fetch_response=fetch_response,
    )
    evidence = _validate_h2(result, tmp_path)
    assert result["status"] == "succeeded"
    assert len(calls) == 1 and calls[0] == {"timeout_seconds": 15}
    assert evidence["coverage"]["requested_window"] == WINDOW
    assert evidence["coverage"]["declared_scope_complete"] is False
    assert evidence["events"][0]["source_evidence_stage"] == "preannouncement"
    assert evidence["events"][0]["event_lifecycle"] == "scheduled"
    assert evidence["events"][0]["official_reference_price"] == {"state": "not_announced", "value": None}
    assert "h3_dependency_operation:a3-h3-operation" in result["warnings"]


def test_no_exact_row_is_source_scope_no_evidence_not_historical_clearance(tmp_path: Path) -> None:
    calls = []
    result = execute_h2_twse_exright_pre(
        _request(), _context(tmp_path, _h3_dependency(tmp_path)),
        fetch_response=lambda **kwargs: calls.append(kwargs) or _response([_row("0050")]),
    )
    evidence = _validate_h2(result, tmp_path)
    assert len(calls) == 1
    assert evidence["status"] == "partial"
    assert evidence["events"] == []
    assert evidence["coverage"]["status"] == "partial"
    assert evidence["coverage"]["requested_window"] == WINDOW
    assert evidence["coverage"]["declared_scope_complete"] is False


@pytest.mark.parametrize("value,state", [("0", "value"), ("", "blank"), ("尚未公告", "not_announced")])
def test_zero_blank_and_not_announced_do_not_get_collapsed(tmp_path: Path, value: str, state: str) -> None:
    calls = []
    result = execute_h2_twse_exright_pre(
        _request(), _context(tmp_path, _h3_dependency(tmp_path)),
        fetch_response=lambda **kwargs: calls.append(kwargs) or _response([_row(SubscriptionPricePerShare=value)]),
    )
    assert len(calls) == 1
    evidence = _validate_h2(result, tmp_path)
    assert evidence["events"][0]["event_lifecycle"] == "scheduled"
    assert evidence["events"][0]["subscription_price"]["state"] == state
    assert evidence["coverage"]["declared_scope_complete"] is False


@pytest.mark.parametrize("rows,code", [
    ([_row("0050")], None),
    ([_row(), _row()], "binding_failed"),
])
def test_wrong_target_and_duplicate_exact_target_fail_closed(tmp_path: Path, rows: list[dict], code: str | None) -> None:
    result = execute_h2_twse_exright_pre(
        _request(), _context(tmp_path, _h3_dependency(tmp_path)), fetch_response=lambda **kwargs: _response(rows),
    )
    evidence = _validate_h2(result, tmp_path)
    if code:
        assert evidence["status"] == code
        assert "ambiguous_exact_target_rows" in evidence["caveats"][0]
    else:
        assert evidence["status"] == "partial" and not evidence["events"]


@pytest.mark.parametrize("response", [
    {"raw_bytes": b"{broken", "status": 200, "content_type": "application/json", "effective_url": ENDPOINT},
    {"raw_bytes": b"[{}]", "status": 200, "content_type": "application/json", "effective_url": ENDPOINT},
])
def test_source_contract_failures_remain_typed_source_failure(tmp_path: Path, response: dict) -> None:
    result = execute_h2_twse_exright_pre(
        _request(), _context(tmp_path, _h3_dependency(tmp_path)), fetch_response=lambda **kwargs: response,
    )
    evidence = _validate_h2(result, tmp_path)
    assert result["status"] == "failed"
    assert evidence["status"] == "source_failed"


def test_expected_timeout_is_source_failure_but_internal_bug_propagates(tmp_path: Path) -> None:
    import urllib.error

    timeout_result = execute_h2_twse_exright_pre(
        _request(), _context(tmp_path, _h3_dependency(tmp_path)),
        fetch_response=lambda **kwargs: (_ for _ in ()).throw(urllib.error.URLError(TimeoutError("timeout"))),
    )
    assert timeout_result["status"] == "failed"
    assert timeout_result["error_code"] == "source_failed"

    with pytest.raises(TypeError, match="synthetic_internal_bug"):
        execute_h2_twse_exright_pre(
            _request(), _context(tmp_path, _h3_dependency(tmp_path)),
            fetch_response=lambda **kwargs: (_ for _ in ()).throw(TypeError("synthetic_internal_bug")),
        )


def test_h3_dependency_unavailable_means_zero_h2_calls_and_no_artifact(tmp_path: Path) -> None:
    calls = []
    result = execute_h2_twse_exright_pre(
        _request(), _context(tmp_path, _h3_dependency(tmp_path, status="failed")),
        fetch_response=lambda **kwargs: calls.append(kwargs) or _response([_row()]),
    )
    assert result["status"] == "failed"
    assert result["error_code"] == "h3_dependency_unusable"
    assert "h2_source_not_attempted" in result["warnings"]
    assert "h4_not_derived_no_clearance_implied" in result["warnings"]
    assert calls == []
    assert not list(tmp_path.glob("evidence/phase_h/h2/*.json"))


def test_real_partial_h2_derives_verified_h4_coverage_incomplete(tmp_path: Path) -> None:
    h3_context = _h3_dependency(tmp_path)
    h3_result = h3_context["dependencies"][0]["result"]
    h2_result = execute_h2_twse_exright_pre(
        _request(), _context(tmp_path, h3_context), fetch_response=lambda **kwargs: _response([_row()]),
    )
    plan = {"operations": [{"operation_id": "a3-h3-operation", "capability_id": "recent_performance", "market": "TWSE", "operation_status": "executable_pending_approval", "executor_invocation_eligible": True, "canonical_target_ids": [TARGET["canonical_target_id"]]}, {"operation_id": "a3-h2-operation", "capability_id": "corporate_action_context", "market": "TWSE", "operation_status": "executable_pending_approval", "canonical_target_ids": [TARGET["canonical_target_id"]], "dependency_operation_ids": ["a3-h3-operation"]}]}
    h2_result["operation_id"] = "a3-h2-operation"
    artifacts = derive_h4_for_completed_plan(plan, [h3_result, h2_result], output_root=str(tmp_path))
    assert len(artifacts) == 1
    ref = artifacts[0]
    raw = (tmp_path / ref["relative_path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ref["sha256"]
    value = json.loads(raw)
    assert value["state"] == "coverage_incomplete"
    assert value["ordinary_return_interpretation"] == "blocked"
    assert value["interpretation_guard"] == "CORPORATE_ACTION_COVERAGE_INCOMPLETE"


@pytest.mark.parametrize(
    ("has_reference", "expected_state"),
    [
        (True, "discontinuity_detected_reference_available"),
        (False, "discontinuity_detected_reference_unavailable"),
    ],
)
def test_governed_h4_positive_states_remain_deterministic_fixture_only(has_reference: bool, expected_state: str) -> None:
    h3 = copy.deepcopy(CONTRACT_EXAMPLES["h3_1d"])
    h2 = copy.deepcopy(CONTRACT_EXAMPLES["h2_preannouncement_and_final"])
    event = copy.deepcopy(h2["events"][1])
    event.update({
        "effective_date": "2026-08-20",
        "event_lifecycle": "effective",
        "official_reference_price": {"state": "value", "value": 95} if has_reference else {"state": "unavailable", "value": None},
        "revision_relation": {"status": "officially_linked", "relation_type": "supersedes", "related_official_reference": "fixture-pre"},
    })
    h2["events"] = [event]
    h2["coverage"].update({
        "status": "complete", "declared_scope_complete": True,
        "requested_window": {"start": "2026-08-01", "end": "2026-08-28"},
        "declared_event_subtypes": ["ex_dividend"], "covered_event_subtypes": ["ex_dividend"],
        "uncovered_event_subtypes": [], "failed_source_families": [],
        "retrieval_succeeded": True, "source_contract_validated": True,
        "exact_target_search_succeeded": True,
    })
    refs = {"event_evidence_references": {0: "fixture-h2-event"}}
    if has_reference:
        refs["official_reference_evidence_references"] = {0: "fixture-reference"}
    h4 = derive_discontinuity_safety(
        h2_evidence=h2, h3_evidence=h3,
        h2_evidence_reference="fixture-h2", h3_evidence_reference="fixture-h3", **refs,
    )
    assert h4["state"] == expected_state
    assert h4["ordinary_return_interpretation"] == "blocked"
    assert not list(Draft7Validator(H4_SCHEMA).iter_errors(h4))
    validate_discontinuity_safety_semantics(h4)
    validate_h2_h3_h4_cross_evidence(h2, h3, h4)
