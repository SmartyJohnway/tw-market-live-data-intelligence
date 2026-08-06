import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from .services.unified_mode_a import validate_mode_a_request

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
        return JSONResponse(status_code=409, content={"error": "canonical_dependency_unavailable", "detail": str(e)})
    except ValueError as e:
        # Note: If it's a domain failure, it shouldn't raise here, it returns in the validation_result. 
        # ValueError here indicates malformed canonical dependency or F3 invariant violation.
        return JSONResponse(status_code=500, content={"error": "mode_a_internal_error", "detail": str(e)})
    except RuntimeError as e:
        # Internal unexpected failure
        return JSONResponse(status_code=500, content={"error": "mode_a_internal_error", "detail": str(e)})

    # 5. Return canonical F3 result directly
    return JSONResponse(status_code=200, content=validation_result)
