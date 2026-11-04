"""Production Mode B1 deterministic Preview service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scripts.m8r_05b_01.models import PlanningError
from scripts.m8r_06_01c2_mode_a_security_master_loader import (
    POINTER_PATH,
    get_production_mode_a_security_master,
)
from scripts.m8r_06_02_mode_b1_preview import (
    build_mode_b1_preview_package,
    load_planning_authorities,
)
from server.services.unified_mode_a import validate_mode_a_request


class ModeB1PlanningUnavailable(RuntimeError):
    """Bounded public planning-dependency failure without local path leakage."""


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def authorization_readiness_for_plan(plan: dict[str, Any] | None) -> dict[str, Any]:
    """Project pre-authorization prerequisites without inventing authority.

    The canonical I3 resolver/binder remains the only path that may create a
    TWSE source-date binding.  Generic Workbench planning must therefore stop
    before authorization when such a binding is absent.
    """
    operations = plan.get("operations", []) if isinstance(plan, dict) else []
    requires_i3_twse_binding = any(
        isinstance(operation, dict)
        and operation.get("capability_id") == "cash_institutional_flow_context"
        and operation.get("market") == "TWSE"
        and operation.get("operation_status") == "executable_pending_approval"
        for operation in operations
    )
    if not requires_i3_twse_binding:
        return {"status": "ready", "blocking_reasons": []}
    source_date = plan.get("resolved_source_trade_date") if isinstance(plan, dict) else None
    binding = plan.get("source_date_binding") if isinstance(plan, dict) else None
    if (
        isinstance(source_date, str)
        and isinstance(binding, dict)
        and binding.get("market") == "TWSE"
        and binding.get("resolved_source_trade_date") == source_date
    ):
        return {"status": "ready", "blocking_reasons": []}
    return {
        "status": "blocked",
        "blocking_reasons": [{
            "capability_id": "cash_institutional_flow_context",
            "market": "TWSE",
            "code": "i3_governed_source_date_authority_required",
        }],
        "operator_guidance": (
            "TWSE institutional flow requires a current governed source-date authority before authorization. "
            "This Workbench session will not guess a date. Review Evidence Needs and deselect TWSE institutional flow, "
            "then Compose Frozen Request and build Preview again."
        ),
    }


def build_mode_b1_preview(
    request: dict[str, Any], *, planning_timestamp: str | None = None
) -> dict[str, Any]:
    """Rerun production F3 and current deterministic planning for this request."""
    try:
        validation = validate_mode_a_request(request)
        security_master = get_production_mode_a_security_master(POINTER_PATH)
        # Explicit Request version remains authoritative even though V3 is the
        # preferred default. Compatibility V1/V2 requests continue to use the
        # frozen V2 Catalog/Route pair.
        authorities = load_planning_authorities(request.get("schema_version"))
        package = build_mode_b1_preview_package(
            request,
            validation,
            security_master,
            planning_timestamp=planning_timestamp or _utc_timestamp(),
            authorities=authorities,
        )
        package["authorization_readiness"] = authorization_readiness_for_plan(
            package.get("orchestration_plan")
        )
        return package
    except FileNotFoundError:
        raise
    except PlanningError as exc:
        if exc.code == "output_schema_invalid":
            raise RuntimeError("mode_b1_output_contract_invalid") from exc
        raise ModeB1PlanningUnavailable(exc.code) from exc
    except (KeyError, OSError, ValueError) as exc:
        raise ModeB1PlanningUnavailable("planning_dependency_invalid") from exc
