from __future__ import annotations

import inspect
import hashlib
import json
from pathlib import Path
import sys

import pytest

from scripts import run_phase_h_h_act_h3_live_acceptance as runner
from server.services import unified_mode_b2
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from tests.unit.m8r_05b_03_test_helpers import build_valid_preflight


ROOT = Path(__file__).resolve().parents[2]
EXACT_REFERENCE = "TEST_OWNER_AUTHORIZATION_REFERENCE_EXACT"


def _rebuilt_preview_and_plan():
    plan = json.loads(
        (ROOT / "tests/fixtures/m8r_05b_01/golden/single_executable_plan.json")
        .read_text(encoding="utf-8")
    )
    preview = {
        "status": "ready_for_confirmation",
        "internal_execution_reference": {"preview_id": "umepreview-v1-test"},
    }
    return preview, plan


def test_missing_cli_authority_reference_fails_before_run_or_identity_creation(monkeypatch):
    called = False

    def forbidden_run(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(runner, "run", forbidden_run)
    monkeypatch.setattr(sys, "argv", ["runner", "--confirm-bounded-live"])
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    assert called is False


@pytest.mark.parametrize("reference", ["", "   ", "\t\r\n"])
def test_blank_authority_reference_fails_before_filesystem_or_network(monkeypatch, tmp_path, reference):
    monkeypatch.setenv("H_ACT_H3_OWNER_AUTHORIZED", "YES")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "runner",
            "--confirm-bounded-live",
            "--owner-authorization-reference",
            reference,
        ],
    )
    mkdir_calls = []
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: mkdir_calls.append((args, kwargs)))

    with pytest.raises(RuntimeError, match="OWNER_AUTHORIZATION_REFERENCE_REQUIRED"):
        runner.main()

    assert mkdir_calls == []
    assert list(tmp_path.iterdir()) == []


def test_authority_reference_is_persisted_exactly_in_new_authorization(tmp_path, monkeypatch):
    preview, plan = _rebuilt_preview_and_plan()
    monkeypatch.setattr(unified_mode_b2, "CONTROL_ROOT", tmp_path)
    monkeypatch.setattr(
        unified_mode_b2,
        "build_mode_b1_preview",
        lambda _request: {"preview": preview, "orchestration_plan": plan},
    )
    payload = runner._authorization_payload(
        request={"schema_version": "unified_market_evidence_request.v1", "request_id": "runner-unit-test"},
        preview=preview,
        plan=plan,
        owner_authorization_reference=EXACT_REFERENCE,
    )

    result = unified_mode_b2.build_mode_b2_authorization(payload)
    authorization_path = (
        tmp_path / result["authorization_id"] / "control" / "authorization.json"
    )
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))

    assert authorization["owner_review_reference"] == EXACT_REFERENCE
    assert payload["owner_review_reference"] == EXACT_REFERENCE
    assert result["network_executed"] is False


def test_legacy_hardcoded_reference_is_not_in_runner_execution_source():
    source = inspect.getsource(runner)
    assert "H_ACT_H3_OWNER_AUTHORIZED_H0H_LIVE_003" not in source
    assert '"owner_review_reference"' in source


def test_bounded_live_controls_and_production_dispatch_path_remain_fixed():
    source = inspect.getsource(runner)
    assert runner.TARGET == "TWSE:1423"
    assert runner.LOOKBACK == 20
    assert runner.MAX_UNIQUE_MONTH_GETS == 3
    assert runner.EXECUTOR_ID == "phase_h_h3_twse_recent_performance_executor"
    assert runner.SOURCE_ID == "H3-TWSE-DEFAULT-BOUNDED"
    assert "--confirm-bounded-live" in source
    assert "--owner-authorization-reference" in source
    assert "H_ACT_H3_OWNER_AUTHORIZED" in source
    assert "mode_b2.build_mode_b2_authorization" in source
    assert "execute_once(" in source
    assert "production_adapter.fetch_twse_stock_day_month" in source
    assert '"lookback_trading_days": LOOKBACK' in source
    assert '"retry_count": 0' in source
    assert "fetch_twse_stock_day_month(" not in source


def test_reference_with_whitespace_or_over_b2_bound_is_rejected_not_normalized():
    with pytest.raises(RuntimeError, match="OWNER_AUTHORIZATION_REFERENCE_INVALID"):
        runner._require_owner_authorization_reference(" padded ")
    with pytest.raises(RuntimeError, match="OWNER_AUTHORIZATION_REFERENCE_INVALID"):
        runner._require_owner_authorization_reference("x" * 241)


def _durable_bridge_fixture(tmp_path: Path):
    operation_id = "umeop-op-v1-" + "a" * 20
    execution_request = {
        "schema_version": "unified_market_evidence_execution_request.v2",
        "operation_id": operation_id,
        "execution_request_id": "umereq-v2-" + "b" * 20,
        "execution_request_hash": "c" * 64,
    }
    values = {
        f"evidence/phase_h/h3/{operation_id}.json": {
            "schema_version": "recent_performance_evidence.v1",
            "target": {"canonical_target_id": "TWSE:1423"},
        },
        f"evidence/phase_h/governance/{operation_id}.json": {
            "schema_version": "phase_h_source_attempt_governance.v1",
            "canonical_target_id": "TWSE:1423",
        },
    }
    inventory = []
    refs = []
    for path, value in values.items():
        raw = (json.dumps(value, sort_keys=True) + "\n").encode()
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        schema = value["schema_version"]
        entry = {
            "relative_path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "schema_version": schema,
            "evidence_contract": schema,
            "byte_size": len(raw),
            "item_count": 1,
        }
        inventory.append(entry)
        refs.append({key: entry[key] for key in ("relative_path", "sha256", "schema_version", "byte_size", "item_count")})
    receipt = {
        "schema_version": "unified_market_evidence_execution_receipt.v1",
        "overall_status": "succeeded",
        "operation_receipts": [{
            "operation_id": operation_id,
            "execution_request_id": execution_request["execution_request_id"],
            "execution_request_hash": execution_request["execution_request_hash"],
            "status": "succeeded",
            "evidence_artifacts": refs,
        }],
    }
    bundle = {
        "schema_version": "unified_market_evidence_bundle.v1",
        "overall_status": "succeeded",
        "operation_evidence_entries": [{
            "operation_id": operation_id, "status": "succeeded", "artifacts": refs,
        }],
        "artifact_inventory": inventory,
    }
    return execution_request, receipt, bundle


def test_durable_v2_bridge_passes_without_standalone_operation_result(tmp_path):
    request, receipt, bundle = _durable_bridge_fixture(tmp_path)
    assert not list(tmp_path.rglob("*operation-result*.json"))

    verified = runner._verify_h3_durable_v2_bridge(tmp_path, request, receipt, bundle)

    assert {item["evidence_contract"] for item in verified.values()} == {
        "recent_performance_evidence.v1",
        "phase_h_source_attempt_governance.v1",
    }


def test_durable_v2_bridge_rejects_wrong_supporting_artifact_contract(tmp_path):
    request, receipt, bundle = _durable_bridge_fixture(tmp_path)
    bundle["artifact_inventory"][1]["evidence_contract"] = "recent_performance_evidence.v1"

    with pytest.raises(RuntimeError, match="h3_live_artifact_contract_mismatch"):
        runner._verify_h3_durable_v2_bridge(tmp_path, request, receipt, bundle)


def test_v1_aggregation_cannot_masquerade_as_distinct_contract_v2_bridge(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    operation_id = preflight["approved_operation_order"][0]
    request = preflight["bounded_execution_requests"][0]
    binding = preflight["resolved_operation_bindings"][operation_id]
    binding["expected_evidence_contract"] = "recent_performance_evidence.v1"
    artifacts = [
        {
            "relative_path": "evidence/phase_h/h3/op.json", "sha256": "1" * 64,
            "schema_version": "recent_performance_evidence.v1", "evidence_contract": "recent_performance_evidence.v1",
            "byte_size": 1, "item_count": 1, "artifact_role": "primary_evidence",
        },
        {
            "relative_path": "evidence/phase_h/governance/op.json", "sha256": "2" * 64,
            "schema_version": "phase_h_source_attempt_governance.v1", "evidence_contract": "phase_h_source_attempt_governance.v1",
            "byte_size": 1, "item_count": 1, "artifact_role": "supporting_governance",
        },
    ]
    outcome = {
        "schema_version": "unified_market_evidence_operation_result.v1",
        "operation_id": operation_id,
        "execution_request_id": request["execution_request_id"],
        "execution_request_hash": request["execution_request_hash"],
        "executor_id": request["executor_id"],
        "capability_id": request["capability_id"],
        "evidence_contract": "recent_performance_evidence.v1",
        "status": "succeeded", "error_code": None, "result_item_count": 1,
        "evidence_artifacts": artifacts, "warnings": [],
    }

    aggregated = aggregate_dispatch_outcomes(preflight, [outcome])

    contracts = {item["evidence_contract"] for item in aggregated["artifact_inventory"]}
    assert contracts == {"recent_performance_evidence.v1"}
    assert "phase_h_source_attempt_governance.v1" not in contracts
