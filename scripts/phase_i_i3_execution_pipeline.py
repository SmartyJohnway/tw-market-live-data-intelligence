"""Production I3 pre-authorization date binding and execution-request projection.

The caller supplies the reviewed Unified V3 preview and governed calendar
artifacts.  This pure preparation path binds TWSE date identity before it
creates authorization or execution requests; it performs no network I/O.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_05b_03.request_projection import build_execution_request_projection
from scripts.phase_i_i3_execution_date import resolve_and_bind_i3_twse_plan

ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_ID = "cash_institutional_flow_context"
EXECUTOR_ID = "phase_i_i3_cash_institutional_flow_context_executor"


def prepare_i3_authorized_execution(
    preview_package: Mapping[str, Any], *, evaluation_time: str | datetime,
    official_calendar: Mapping[str, Any] | list[Mapping[str, Any]] | None,
    closure_events: list[dict[str, Any]] | None,
    calendar_authority_ref: str | None, closure_authority_ref: str | None,
    closure_authority_complete: bool,
    decision_input: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind governed date, then construct approval-bound V3 requests.

    ``decision_input`` represents the existing external owner approval
    decision; this helper does not invent or grant approval.  Resolver errors
    happen before any authorization or execution-request object is created.
    """
    plan = preview_package.get("orchestration_plan") if isinstance(preview_package, Mapping) else None
    if not isinstance(plan, dict) or not isinstance(preview_package.get("validation"), dict):
        raise ValueError("i3_preview_package_invalid")
    operations = [op for op in plan.get("operations", [])
                  if isinstance(op, dict) and op.get("capability_id") == CAPABILITY_ID]
    if not operations or any(op.get("operation_status") != "executable_pending_approval"
                             or op.get("executor_id") != EXECUTOR_ID for op in operations):
        raise ValueError("i3_plan_not_authorizable")
    markets = {op.get("market") for op in operations}
    if not markets.issubset({"TWSE", "TPEX"}):
        raise ValueError("i3_market_unsupported")
    if "TWSE" in markets:
        if official_calendar is None or closure_events is None or not calendar_authority_ref or not closure_authority_ref:
            raise ValueError("i3_governed_date_authority_required")
        plan = resolve_and_bind_i3_twse_plan(
            plan, evaluation_time=evaluation_time, official_calendar=official_calendar,
            closure_events=closure_events, calendar_authority_ref=calendar_authority_ref,
            closure_authority_ref=closure_authority_ref,
            closure_authority_complete=closure_authority_complete,
        )
    elif any("resolved_source_trade_date" in op.get("parameters", {}) for op in operations):
        raise ValueError("i3_tpex_query_date_forbidden")

    selected_ids = sorted(op["operation_id"] for op in operations)
    decision = dict(decision_input)
    if decision.get("decision") != "approved" or decision.get("approval_scope_mode") not in {
        "selected_operations", "whole_plan_executable_scope", "selected_batches"
    }:
        raise ValueError("i3_approval_decision_invalid")
    if decision.get("approval_scope_mode") == "selected_operations":
        if sorted(decision.get("approved_operation_ids", [])) != selected_ids:
            raise ValueError("i3_approval_scope_mismatch")

    authorization = build_execution_authorization(plan, decision)
    consumption = build_consumption_binding(authorization)
    registry_raw = json.loads((ROOT / "config/m8r_06_03_executor_registry_metadata.json").read_text(encoding="utf-8"))
    registry = ExecutorMetadataRegistry.from_json(registry_raw)
    requests = []
    for operation in operations:
        market = operation["market"]
        binding = {"capability_id": CAPABILITY_ID, "market": market, "executor_id": EXECUTOR_ID,
                   "expected_evidence_contract": operation["expected_evidence_contract"]}
        executor = registry.get_route(EXECUTOR_ID, CAPABILITY_ID, market)
        request, _warnings = build_execution_request_projection(
            plan=plan, authorization=authorization, consumption_binding=consumption,
            operation=operation, binding=binding, executor=executor, network_authorized=True,
        )
        requests.append(request)
    return {"plan": copy.deepcopy(plan), "authorization": authorization,
            "consumption_binding": consumption, "execution_requests": requests,
            "resolved_source_trade_date": plan.get("resolved_source_trade_date"),
            "network_dispatched": False, "executor_id": EXECUTOR_ID}
