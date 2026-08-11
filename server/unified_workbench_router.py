import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from .services.unified_mode_a import validate_mode_a_request
from .services.unified_mode_b1 import (
    ModeB1PlanningUnavailable,
    build_mode_b1_preview,
)
from .services.unified_mode_b2 import ModeB2Error, build_mode_b2_authorization
from .services.unified_mode_b2_execution import execute_mode_b2_once
import uuid

router = APIRouter(
    prefix="/api/unified",
    tags=["unified-workbench-mode-a"]
)

MAX_BODY_SIZE = 1 * 1024 * 1024  # 1 MiB


@router.post("/validate-request")
async def validate_request(request: Request):
    """
    Canonical F3 validation endpoint for Mode A.
    """
    # 1. Limit body size
    body = await request.body()
    if len(body) > MAX_BODY_SIZE:
        raise HTTPException(status_code=413, detail="request_too_large")

    # 2. Parse JSON
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="malformed_json_body")

    # 3. Extract request envelope Option A
    if not isinstance(payload, dict) or "request" not in payload:
        raise HTTPException(status_code=422, detail="invalid_api_envelope: missing 'request' key")

    target_request = payload["request"]
    
    # 4. Invoke Mode A adapter
    try:
        validation_result = validate_mode_a_request(target_request)
    except FileNotFoundError as e:
        error_msg = str(e)
        if "security_master_snapshot" in error_msg:
            return JSONResponse(status_code=409, content={"error": "canonical_security_master_unavailable", "trace_id": str(uuid.uuid4())})
        return JSONResponse(status_code=500, content={"error": "canonical_dependency_missing", "trace_id": str(uuid.uuid4())})
    except ValueError as e:
        return JSONResponse(status_code=500, content={"error": "canonical_dependency_malformed", "trace_id": str(uuid.uuid4())})
    except RuntimeError as e:
        return JSONResponse(status_code=500, content={"error": "mode_a_internal_error", "trace_id": str(uuid.uuid4())})

    # 5. Return canonical F3 result directly
    return JSONResponse(status_code=200, content=validation_result)


@router.post("/preview-request")
async def preview_request(request: Request):
    """Offline Mode B1 planning endpoint; never authorizes or executes."""
    body = await request.body()
    if len(body) > MAX_BODY_SIZE:
        raise HTTPException(status_code=413, detail="request_too_large")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="malformed_json_body")
    if (
        not isinstance(payload, dict)
        or "request" not in payload
        or not isinstance(payload["request"], dict)
    ):
        raise HTTPException(
            status_code=422,
            detail="invalid_api_envelope: missing or invalid 'request' key",
        )
    try:
        result = build_mode_b1_preview(payload["request"])
    except FileNotFoundError:
        return JSONResponse(
            status_code=409,
            content={
                "error": "canonical_security_master_unavailable",
                "trace_id": str(uuid.uuid4()),
            },
        )
    except ModeB1PlanningUnavailable:
        return JSONResponse(
            status_code=409,
            content={
                "error": "mode_b1_planning_dependency_unavailable",
                "trace_id": str(uuid.uuid4()),
            },
        )
    except RuntimeError:
        return JSONResponse(
            status_code=500,
            content={"error": "mode_b1_internal_error", "trace_id": str(uuid.uuid4())},
        )
    return JSONResponse(status_code=200, content=result)


@router.post("/authorizations")
async def create_authorization(request: Request):
    """Create an offline, server-owned canonical 05B authorization."""
    body = await request.body()
    if len(body) > MAX_BODY_SIZE:
        raise HTTPException(status_code=413, detail="request_too_large")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="malformed_json_body")
    try:
        result = build_mode_b2_authorization(payload)
    except ModeB2Error as exc:
        status = 422 if exc.code in {
            "invalid_api_envelope", "privileged_field_forbidden",
            "authorization_confirmation_required", "authorization_ttl_invalid",
            "approval_scope_mode_invalid", "approval_scope_input_conflict",
        } else 409
        return JSONResponse(status_code=status, content={"error": exc.code, "trace_id": str(uuid.uuid4())})
    except FileNotFoundError:
        return JSONResponse(status_code=409, content={"error": "canonical_security_master_unavailable", "trace_id": str(uuid.uuid4())})
    except Exception:
        return JSONResponse(status_code=500, content={"error": "mode_b2_internal_error", "trace_id": str(uuid.uuid4())})
    return JSONResponse(status_code=200, content=result)


@router.post("/executions")
async def execute_authorization(request: Request):
    """Execute exactly one server-owned package through the fixed child protocol."""
    body = await request.body()
    if len(body) > MAX_BODY_SIZE:
        raise HTTPException(status_code=413, detail="request_too_large")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="malformed_json_body")
    try:
        result = execute_mode_b2_once(payload)
    except ModeB2Error as exc:
        status = 422 if exc.code in {
            "invalid_api_envelope", "privileged_field_forbidden", "control_package_id_invalid",
            "execution_confirmation_required", "operator_confirmation_reference_invalid",
            "network_execution_confirmation_required",
        } else 409
        return JSONResponse(status_code=status, content={"error": exc.code, "trace_id": str(uuid.uuid4())})
    except Exception:
        return JSONResponse(status_code=500, content={"error": "mode_b2_execution_internal_error", "trace_id": str(uuid.uuid4())})
    return JSONResponse(status_code=200, content=result)
