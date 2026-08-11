"""Bounded parent boundary for the fixed Mode B2 execute-once child."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from server.services.unified_mode_b2 import ModeB2Error


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts" / "m8r_06_03_execute_once.py"
FIXED_OVERHEAD_SECONDS = 10
MAX_CHILD_TIMEOUT_SECONDS = 70


def _timeout_seconds(payload: dict[str, Any]) -> int:
    # Four committed routes permit at most 15 seconds each; no browser value is used.
    return min(MAX_CHILD_TIMEOUT_SECONDS, (4 * 15) + FIXED_OVERHEAD_SECONDS)


def execute_mode_b2_once(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ModeB2Error("invalid_api_envelope")
    forbidden = {
        "plan", "authorization", "consumption_binding", "output_root", "command",
        "cmd", "shell", "script", "module", "adapter", "registry_path", "source_url", "executable",
    }
    if forbidden & set(payload):
        raise ModeB2Error("privileged_field_forbidden")
    allowed = {"control_package_id", "authorization_id", "confirm_execution", "operator_confirmation_reference", "confirm_network_execution"}
    if set(payload) - allowed:
        raise ModeB2Error("privileged_field_forbidden")
    control_id = payload.get("control_package_id", payload.get("authorization_id"))
    if not isinstance(control_id, str) or payload.get("authorization_id", control_id) != control_id:
        raise ModeB2Error("control_package_id_invalid")
    if payload.get("confirm_execution") is not True:
        raise ModeB2Error("execution_confirmation_required")
    reference = payload.get("operator_confirmation_reference")
    if not isinstance(reference, str) or not reference.strip() or len(reference) > 128:
        raise ModeB2Error("operator_confirmation_reference_invalid")
    if type(payload.get("confirm_network_execution")) is not bool:
        raise ModeB2Error("network_execution_confirmation_required")
    command = [
        sys.executable, str(WRAPPER), "--authorization-id", control_id,
        "--confirm-execution", "--operator-confirmation-reference", reference.strip(),
    ]
    if payload["confirm_network_execution"]:
        command.append("--confirm-network-execution")
    environment = os.environ.copy()
    try:
        child = subprocess.run(
            command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=_timeout_seconds(payload), env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise ModeB2Error("mode_b2_execution_timeout") from exc
    try:
        result = json.loads(child.stdout)
    except json.JSONDecodeError as exc:
        raise ModeB2Error("mode_b2_execution_child_protocol_invalid") from exc
    if not isinstance(result, dict):
        raise ModeB2Error("mode_b2_execution_child_protocol_invalid")
    if child.returncode == 2:
        raise ModeB2Error(str(result.get("error") or "mode_b2_execution_unavailable"))
    required = {"schema_version", "authorization_id", "consumption_state", "operation_statuses", "aggregation_status", "execution_receipt_id", "evidence_bundle_id", "external_market_network_executed"}
    if child.returncode != 0 or set(result) != required or result.get("authorization_id") != control_id:
        raise ModeB2Error("mode_b2_execution_child_protocol_invalid")
    return result
