from __future__ import annotations

import inspect
import json
from pathlib import Path
import sys

import pytest

from scripts import run_phase_h_h_act_h3_live_acceptance as runner
from server.services import unified_mode_b2


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
