"""Offline-preparable, dormant I3 authorization-to-request candidate path.

This module is intentionally not imported by the default runtime. It binds a
governed TWSE date before constructing authorization or execution requests.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_05b_03.request_projection import build_execution_request_projection
from scripts.m8r_05b_01.canonical import sha256_json
from scripts.m8r_05b_01.planner import build_plan
from scripts.m8r_06_02_mode_b1_preview import (
    build_planning_bindings, load_planning_authorities, project_canonical_preview,
)
from scripts.phase_i_i3_execution_date import resolve_and_bind_i3_twse_plan

ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_ID = "cash_institutional_flow_context"
EXECUTOR_ID = "phase_i_i3_cash_institutional_flow_context_executor"


def build_dormant_i3_candidate_preview(
    request: Mapping[str, Any], validation: Mapping[str, Any], security_master: Any, *,
    planning_timestamp: str,
) -> dict[str, Any]:
    """Build Unified V3 preview against isolated I3 candidate authorities.

    Candidate authority copies are promoted only in memory for this explicit
    offline acceptance path; the default catalog, route, and registry remain
    unchanged and non-executable.
    """
    authorities = copy.deepcopy(load_planning_authorities(str(request.get("schema_version"))))
    catalog = authorities["capability_catalog"]
    routes = authorities["routing_matrix"]
    matches = [item for item in routes.get("routes", []) if item.get("capability_id") == CAPABILITY_ID]
    if len(matches) != 1:
        raise ValueError("i3_candidate_route_authority_invalid")
    route = matches[0]
    route.update(routing_status="resolved", runtime_executable=True, provisional=False,
                 selected_executor_id=EXECUTOR_ID, blocking_reasons=[])
    candidate_inventory = authorities["executor_disposition"]
    surfaces = candidate_inventory.get("surfaces")
    if not isinstance(surfaces, list):
        raise ValueError("i3_candidate_executor_disposition_invalid")
    # Current runtime authority is active after A4 activation.  This legacy
    # offline candidate helper works only on its deep-copied authority, so
    # replace the copied active I3 row with the historical dormant projection.
    surfaces[:] = [item for item in surfaces
                   if not isinstance(item, dict) or item.get("surface_id") != EXECUTOR_ID]
    surfaces.append({"surface_id": EXECUTOR_ID, "path": "server/services/phase_i_i3_cash_institutional_flow_production_candidate.py",
                     "surface_type": "dormant_i3_production_candidate", "current_status": "isolated technical candidate",
                     "network_behavior": "one fixed GET per market batch; retry zero",
                     "input_contract": "execution_request.v3 cash_institutional_flow_context",
                     "output_contract": "cash_institutional_flow_context_evidence.v2",
                     "approval_boundary": "authorization and consumed request binding",
                     "authorization_binding": "plan, operation, target, date, executor",
                     "single_use_enforced": True, "supported_markets": ["TWSE", "TPEX"],
                     "supported_security_types": ["equity"], "supported_capabilities": [CAPABILITY_ID],
                     "batching_supported": True, "deterministic": False, "reusable_for_05b": True,
                     "reuse_mode": "adapter_required", "disposition": "adapter_required", "blocking_gaps": []})
    candidate_validation = copy.deepcopy(dict(validation))
    for item in candidate_validation.get("capability_results", []):
        if item.get("capability_id") == CAPABILITY_ID and item.get("status") == "contract_supported":
            item["status"] = "runtime_executable"
    bindings = build_planning_bindings(request, candidate_validation, security_master,
        capability_catalog=catalog, routing_matrix=routes,
        handoff_contract=authorities["handoff_contract"])
    bindings["f3_validation_output_hash"] = sha256_json(candidate_validation)
    plan = build_plan(candidate_validation, capability_catalog=catalog, routing_matrix=routes,
        handoff_contract=authorities["handoff_contract"], executor_disposition=candidate_inventory,
        input_bindings=bindings, planning_timestamp=planning_timestamp)
    preview = project_canonical_preview(candidate_validation, plan, capability_catalog=catalog,
        routing_matrix=routes, preview_schema=authorities["preview_schema"])
    return {"validation": candidate_validation, "preview": preview, "orchestration_plan": plan,
            "network_executed": False, "authorization_created": False,
            "authorization_consumed": False, "execution_performed": False,
            "candidate_authorities_isolated": True}


def prepare_dormant_i3_execution(
    preview_package: Mapping[str, Any], *, evaluation_time: str | datetime,
    official_calendar: Mapping[str, Any] | list[Mapping[str, Any]] | None,
    closure_events: list[dict[str, Any]] | None,
    calendar_authority_ref: str | None, closure_authority_ref: str | None,
    closure_authority_complete: bool,
    owner_identity_reference: str, owner_review_reference: str,
) -> dict[str, Any]:
    """Bind date, then build authorization and V3 requests; never dispatch.

    The input package must come from the existing Unified Request V3 validation
    and preview/planner path using the isolated candidate authorities. Resolver
    errors occur before authorization/request objects are constructed.
    """
    plan = preview_package.get("orchestration_plan") if isinstance(preview_package, Mapping) else None
    if not isinstance(plan, dict) or not isinstance(preview_package.get("validation"), dict):
        raise ValueError("i3_candidate_preview_package_invalid")
    operations = [op for op in plan.get("operations", [])
                  if isinstance(op, dict) and op.get("capability_id") == CAPABILITY_ID]
    if not operations or any(op.get("operation_status") != "executable_pending_approval"
                             or op.get("executor_id") != EXECUTOR_ID for op in operations):
        raise ValueError("i3_candidate_plan_not_authorizable")
    markets = {op.get("market") for op in operations}
    if not markets.issubset({"TWSE", "TPEX"}):
        raise ValueError("i3_candidate_market_unsupported")
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

    issued = evaluation_time if isinstance(evaluation_time, datetime) else datetime.fromisoformat(
        evaluation_time.replace("Z", "+00:00"))
    if issued.tzinfo is None or issued.utcoffset() is None:
        raise ValueError("i3_authorization_time_timezone_required")
    issued = issued.astimezone(timezone.utc).replace(microsecond=0)
    zulu = lambda value: value.isoformat().replace("+00:00", "Z")
    decision = {
        "decision": "approved", "decision_reason": "offline dormant I3 candidate authorization projection",
        "owner_identity_reference": owner_identity_reference,
        "owner_review_reference": owner_review_reference,
        "reviewed_at": zulu(issued), "issued_at": zulu(issued),
        "expires_at": zulu(issued + timedelta(minutes=15)),
        "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
        "approval_scope_mode": "selected_operations",
        "approved_operation_ids": sorted(op["operation_id"] for op in operations),
        "approved_batch_group_ids": [], "approved_batch_membership": {},
    }
    authorization = build_execution_authorization(plan, decision)
    consumption = build_consumption_binding(authorization)
    registry_raw = json.loads((ROOT / "docs/data_capabilities/phase_i_i3_executor_metadata_candidate.v1.json").read_text(encoding="utf-8"))
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
            "network_dispatched": False, "executor_id": EXECUTOR_ID}
