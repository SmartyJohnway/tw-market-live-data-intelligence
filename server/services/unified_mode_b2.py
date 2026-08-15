"""Server-owned Mode B2 authorization authority (offline by construction)."""
from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.m8r_05b_02.authorization import MAX_LIFETIME_SECONDS, build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding, validate_consumption_binding
from scripts.m8r_05b_02.models import AuthorizationError
from scripts.m8r_05b_02.validator import validate_execution_authorization
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight, validate_preflight_hashes
from scripts.m8r_06_03_production_adapter import load_production_executor_metadata
from scripts.m8r_filesystem_safety import atomic_write_text, safe_destination
from server.services.unified_mode_b1 import ModeB1PlanningUnavailable, build_mode_b1_preview


ROOT = Path(__file__).resolve().parents[2]
# This is process configuration only.  It permits an isolated local test/server
# run without allowing any API payload to select an output location.
CONTROL_ROOT = Path(os.environ.get("M8R_06_03_CONTROL_ROOT", str(ROOT / "artifacts" / "m8r_06_03_workbench"))).resolve()
DEFAULT_TTL_SECONDS = 900
_LOCAL_ACTION_ISSUANCE_LOCK = threading.Lock()
_last_local_action_issued_at: datetime | None = None


class ModeB2Error(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _zulu(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _next_local_action_issuance_time() -> datetime:
    """Return a process-monotonic timestamp for a new local MCP invocation.

    Workbench authorization retains its established second-granularity clock.
    The local action needs a distinct existing B2 ticket for every invocation,
    including identical requests received in one wall-clock second.
    """
    global _last_local_action_issued_at
    now = _utc_now()
    with _LOCAL_ACTION_ISSUANCE_LOCK:
        if _last_local_action_issued_at is not None and now <= _last_local_action_issued_at:
            now = _last_local_action_issued_at + timedelta(microseconds=1)
        _last_local_action_issued_at = now
        return now


def _unused_state(binding: dict[str, Any]) -> dict[str, Any]:
    return {
        "authorization_id": binding["authorization_id"],
        "authorization_hash": binding["authorization_hash"],
        "consumption_binding_id": binding["consumption_binding_id"],
        "consumption_binding_hash": binding["consumption_binding_hash"],
        "registry_contract_version": "m8r_05b_03.v1",
        "state": "unused",
    }


def _json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _write_control_package(package_root: Path, artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manifest_path = safe_destination(package_root, "control/manifest.json", create_parent=True).path
    control_root = manifest_path.parent
    if manifest_path.exists():
        raise ModeB2Error("control_package_already_finalized")
    if any(control_root.iterdir()):
        raise ModeB2Error("control_package_partial_conflict")
    hashes: dict[str, str] = {}
    for name, artifact in artifacts.items():
        text = _json_text(artifact)
        atomic_write_text(package_root, f"control/{name}.json", text, allow_overwrite=False)
        hashes[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    manifest = {
        "schema_version": "m8r_06_03_control_package.v1",
        "authorization_id": artifacts["authorization"]["authorization_id"],
        "authorization_hash": artifacts["authorization"]["authorization_hash"],
        "plan_id": artifacts["plan"]["plan_id"],
        "plan_hash": artifacts["plan"]["plan_hash"],
        "preflight_id": artifacts["preflight"]["preflight_id"],
        "preflight_hash": artifacts["preflight"]["preflight_hash"],
        "artifact_hashes": hashes,
    }
    text = _json_text(manifest)
    atomic_write_text(package_root, "control/manifest.json", text, allow_overwrite=False)
    return manifest | {"manifest_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def _materialize_execution_ticket(
    request: dict[str, Any], plan: dict[str, Any], decision: dict[str, Any]
) -> dict[str, Any]:
    """Persist one existing 05B execution ticket from an already-governed plan."""
    try:
        authorization = build_execution_authorization(plan, decision)
        validate_execution_authorization(authorization, plan)
        binding = build_consumption_binding(authorization)
        validate_consumption_binding(binding, authorization, plan)
    except AuthorizationError as exc:
        raise ModeB2Error(exc.code) from exc
    unused_state = _unused_state(binding)
    package_root = CONTROL_ROOT / authorization["authorization_id"]
    safe_destination(CONTROL_ROOT, f"{authorization['authorization_id']}/control/manifest.json", create_parent=True)
    preflight = build_orchestrator_preflight(
        plan, authorization, binding,
        supplied_consumption_state=unused_state,
        evaluation_timestamp=decision["issued_at"],
        executor_registry_metadata=load_production_executor_metadata(),
        output_root=str(package_root),
    )
    validate_preflight_hashes(preflight)
    manifest = _write_control_package(package_root, {
        "request": request, "plan": plan, "authorization": authorization,
        "consumption_binding": binding, "unused_consumption_state": unused_state,
        "preflight": preflight,
    })
    return {
        "authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
        "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "scope_hash": authorization["scope_hash"],
        "approved_operation_ids": authorization["approved_operation_ids"],
        "approved_capability_ids": authorization["approved_capability_ids"],
        "approved_executor_ids": authorization["approved_executor_ids"],
        "issued_at": authorization["issued_at"], "expires_at": authorization["expires_at"],
        "single_use": True, "network_required": preflight["network_required"],
        "preflight_id": preflight["preflight_id"], "preflight_hash": preflight["preflight_hash"],
        "control_package_id": authorization["authorization_id"], "control_package_manifest_hash": manifest["manifest_hash"],
        "execution_ready": True, "authorization_created": True, "authorization_consumed": False,
        "execution_performed": False, "network_executed": False,
    }


def _authorizable_preview(
    request: dict[str, Any], *, preserve_domain_failure: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        rebuilt = build_mode_b1_preview(request)
    except ModeB1PlanningUnavailable as exc:
        raise ModeB2Error("mode_b1_planning_dependency_unavailable") from exc
    preview, plan = rebuilt.get("preview"), rebuilt.get("orchestration_plan")
    if not isinstance(preview, dict) or not isinstance(plan, dict):
        raise ModeB2Error(_non_actionable_preview_code(rebuilt) if preserve_domain_failure else "preview_not_authorizable")
    if preview.get("status") not in {"ready_for_confirmation", "partial_possible"}:
        raise ModeB2Error(_non_actionable_preview_code(rebuilt) if preserve_domain_failure else "preview_not_authorizable")
    if not any(item.get("operation_status") == "executable_pending_approval" for item in plan.get("operations", [])):
        raise ModeB2Error(_non_actionable_preview_code(rebuilt) if preserve_domain_failure else "preview_not_authorizable")
    return preview, plan


def _non_actionable_preview_code(rebuilt: dict[str, Any]) -> str:
    """Project existing F3/B1 refusal semantics without adding a resolver."""
    preview = rebuilt.get("preview") if isinstance(rebuilt, dict) else None
    validation = rebuilt.get("validation") if isinstance(rebuilt, dict) else None
    plan = rebuilt.get("orchestration_plan") if isinstance(rebuilt, dict) else None
    if isinstance(preview, dict):
        status = preview.get("status")
        if status == "ambiguous_target":
            return "ambiguous_target"
        if status == "rejected_resource_bound":
            return "rejected_resource_bound"
        if status == "target_not_plannable" and isinstance(validation, dict):
            statuses = {
                target.get("resolution_status")
                for target in validation.get("target_results", [])
                if isinstance(target, dict)
            }
            for status, code in (
                ("not_found", "target_not_found"),
                ("market_mismatch", "market_hint_conflict"),
                ("unsupported_security_type", "unsupported_security_type"),
                ("duplicate", "duplicate_target"),
            ):
                if status in statuses:
                    return code
            return "target_not_plannable"
        if status == "unsupported_capability":
            if isinstance(plan, dict):
                blocked = plan.get("blocked_operations", [])
                if isinstance(blocked, list) and blocked:
                    return "required_capability_blocked"
                operations = plan.get("operations", [])
                if isinstance(operations, list) and any(
                    isinstance(operation, dict)
                    and operation.get("operation_status") == "plan_only_not_executable"
                    for operation in operations
                ):
                    return "required_capability_plan_only_not_executable"
            return "unsupported_capability"
        if isinstance(status, str):
            return status
    if isinstance(validation, dict):
        statuses = {
            target.get("resolution_status")
            for target in validation.get("target_results", [])
            if isinstance(target, dict)
        }
        for status, code in (
            ("ambiguous", "ambiguous_target"),
            ("not_found", "target_not_found"),
            ("market_mismatch", "market_hint_conflict"),
            ("unsupported_security_type", "unsupported_security_type"),
            ("duplicate", "duplicate_target"),
        ):
            if status in statuses:
                return code
        blockers = {
            issue.get("code")
            for issue in validation.get("blocking_issues", [])
            if isinstance(issue, dict)
        }
        if "TARGET_LIMIT_EXCEEDED" in blockers:
            return "rejected_resource_bound"
    return "preview_not_authorizable"


def build_mode_b2_authorization(payload: dict[str, Any]) -> dict[str, Any]:
    """Rebuild B1 authority and persist a bounded, non-executing package."""
    if not isinstance(payload, dict) or not isinstance(payload.get("request"), dict):
        raise ModeB2Error("invalid_api_envelope")
    forbidden = {"output_root", "command", "cmd", "shell", "script", "module", "adapter", "registry_path", "source_url", "executable"}
    if forbidden & set(payload):
        raise ModeB2Error("privileged_field_forbidden")
    if payload.get("confirm_authorization") is not True:
        raise ModeB2Error("authorization_confirmation_required")

    preview, plan = _authorizable_preview(payload["request"])
    expected = {
        "expected_preview_id": preview.get("internal_execution_reference", {}).get("preview_id"),
        "expected_plan_id": plan.get("plan_id"),
        "expected_plan_hash": plan.get("plan_hash"),
    }
    if any(not isinstance(payload.get(key), str) or payload[key] != value for key, value in expected.items()):
        raise ModeB2Error("mode_b2_preview_stale")

    scope_mode = payload.get("approval_scope_mode", "whole_plan_executable_scope")
    if scope_mode not in {"whole_plan_executable_scope", "selected_operations", "selected_batches"}:
        raise ModeB2Error("approval_scope_mode_invalid")
    operation_ids = payload.get("approved_operation_ids", [])
    batch_ids = payload.get("approved_batch_group_ids", [])
    batch_membership = payload.get("approved_batch_membership", {})
    if scope_mode == "whole_plan_executable_scope":
        if operation_ids not in (None, []) or batch_ids not in (None, []) or batch_membership not in (None, {}):
            raise ModeB2Error("approval_scope_input_conflict")
        operation_ids, batch_ids, batch_membership = [], [], {}
    elif scope_mode == "selected_operations":
        if not isinstance(operation_ids, list) or not operation_ids or batch_ids != [] or batch_membership != {}:
            raise ModeB2Error("approval_scope_input_conflict")
    else:
        if operation_ids != [] or not isinstance(batch_ids, list) or not batch_ids or not isinstance(batch_membership, dict) or not batch_membership:
            raise ModeB2Error("approval_scope_input_conflict")
    requested_ttl = payload.get("ttl_seconds", DEFAULT_TTL_SECONDS)
    if type(requested_ttl) is not int or not 1 <= requested_ttl <= min(DEFAULT_TTL_SECONDS, MAX_LIFETIME_SECONDS):
        raise ModeB2Error("authorization_ttl_invalid")
    now = _utc_now()
    decision = {
        "decision": "approved",
        "decision_reason": str(payload.get("decision_reason") or "workbench operator authorization")[:240],
        "owner_identity_reference": "workbench_operator",
        "owner_review_reference": str(payload.get("owner_review_reference") or "workbench")[:240],
        "reviewed_at": _zulu(now),
        "issued_at": _zulu(now),
        "expires_at": _zulu(now + timedelta(seconds=requested_ttl)),
        "single_use": True,
        "replay_policy": "deny_replay",
        "maximum_use_count": 1,
        "approval_scope_mode": scope_mode,
        "approved_operation_ids": operation_ids,
        "approved_batch_group_ids": batch_ids,
        "approved_batch_membership": batch_membership,
    }
    return _materialize_execution_ticket(payload["request"], plan, decision)


def build_local_operator_execution_ticket(request: dict[str, Any]) -> dict[str, Any]:
    """Create the existing single-use ticket with truthful MCP-action provenance."""
    if not isinstance(request, dict):
        raise ModeB2Error("invalid_api_envelope")
    # The action path is only defined for the canonical execute request mode.
    if request.get("execution_mode") != "execute":
        raise ModeB2Error("market_fetch_requires_execute_mode")
    _preview, plan = _authorizable_preview(request, preserve_domain_failure=True)
    now = _next_local_action_issuance_time()
    decision = {
        "decision": "approved",
        "decision_reason": "conversation-triggered local-operator one-shot retrieval",
        "owner_identity_reference": "local_operator_mcp",
        "owner_review_reference": "local_operator_mcp_action",
        "reviewed_at": _zulu(now), "issued_at": _zulu(now),
        "expires_at": _zulu(now + timedelta(seconds=DEFAULT_TTL_SECONDS)),
        "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
        "approval_scope_mode": "whole_plan_executable_scope",
        "approved_operation_ids": [], "approved_batch_group_ids": [], "approved_batch_membership": {},
    }
    return _materialize_execution_ticket(request, plan, decision)
