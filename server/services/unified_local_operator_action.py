"""Thin Local Service composition for one truthful local-operator MCP action."""
from __future__ import annotations

from typing import Any

from server.services.unified_mode_b2 import ModeB2Error, build_local_operator_execution_ticket
from server.services.unified_mode_b2_execution import execute_local_operator_ticket
from server.services.unified_mode_c import ModeCError, build_mode_c_ai_handoff


class LocalOperatorActionError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def fetch_market_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate/plan/ticket/claim/execute/project through existing authorities."""
    if not isinstance(payload, dict) or set(payload) != {"request"} or not isinstance(payload.get("request"), dict):
        raise LocalOperatorActionError("invalid_api_envelope")
    request = payload["request"]
    # This is an action-precondition, not a mutation or alternate Request schema.
    if request.get("execution_mode") != "execute":
        raise LocalOperatorActionError("market_fetch_requires_execute_mode")
    try:
        ticket = build_local_operator_execution_ticket(request)
        execution = execute_local_operator_ticket(
            ticket["control_package_id"], network_required=ticket["network_required"]
        )
        handoff = build_mode_c_ai_handoff(ticket["control_package_id"])
    except ModeB2Error as exc:
        raise LocalOperatorActionError(exc.code) from exc
    except ModeCError as exc:
        raise LocalOperatorActionError(exc.code) from exc
    return {
        "service_contract_version": "unified_market_evidence_local_service.v1",
        "action_contract_version": "m8r_08e_local_operator_fetch.v1",
        "control_package_id": ticket["control_package_id"],
        "authorization_id": ticket["authorization_id"],
        "authorization_hash": ticket["authorization_hash"],
        "execution_outcome": execution["aggregation_status"],
        "market_network_attempted": execution["external_market_network_attempted"],
        "market_network_executed": execution["external_market_network_executed"],
        **handoff,
    }
