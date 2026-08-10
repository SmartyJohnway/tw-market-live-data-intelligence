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


def build_mode_b1_preview(
    request: dict[str, Any], *, planning_timestamp: str | None = None
) -> dict[str, Any]:
    """Rerun production F3 and current deterministic planning for this request."""
    try:
        validation = validate_mode_a_request(request)
        security_master = get_production_mode_a_security_master(POINTER_PATH)
        return build_mode_b1_preview_package(
            request,
            validation,
            security_master,
            planning_timestamp=planning_timestamp or _utc_timestamp(),
            authorities=load_planning_authorities(),
        )
    except FileNotFoundError:
        raise
    except PlanningError as exc:
        raise ModeB1PlanningUnavailable(exc.code) from exc
    except (KeyError, OSError, ValueError) as exc:
        raise ModeB1PlanningUnavailable("planning_dependency_invalid") from exc
