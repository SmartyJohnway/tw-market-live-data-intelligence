import json
from pathlib import Path
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
from scripts.m8r_06_01c2_mode_a_security_master_loader import (
    POINTER_PATH,
    get_production_mode_a_security_master,
)
from server.services.unified_contract_versions import (
    PREFERRED_REQUEST_SCHEMA_VERSION,
    REQUEST_CAPABILITY_CATALOG_PATHS,
    REQUEST_SCHEMA_PATHS,
)

ROOT = Path(__file__).resolve().parent.parent.parent
# Backward-compatible preload seam now points at the preferred current
# Request authority; request validation itself still dispatches explicitly.
CANONICAL_SCHEMA_PATH = REQUEST_SCHEMA_PATHS[PREFERRED_REQUEST_SCHEMA_VERSION]
CANONICAL_CATALOG_PATH = REQUEST_CAPABILITY_CATALOG_PATHS[PREFERRED_REQUEST_SCHEMA_VERSION]

# The default loader interprets this historical path as the active-release
# selector.  Tests may still inject an explicit path through this seam.
PRODUCTION_POINTER_PATH = POINTER_PATH


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"canonical_dependency_missing: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"canonical_dependency_malformed: {path.name}") from e


def validate_mode_a_request(request: dict, allow_fixture_snapshot: bool = False) -> dict:
    """
    Executes the canonical Mode A F3 validation.
    Enforces offline execution and deterministic outputs.
    """
    try:
        schema_version = request.get("schema_version") if isinstance(request, dict) else None
        request_schema_path = REQUEST_SCHEMA_PATHS.get(schema_version)
        if request_schema_path is None:
            raise ValueError("unsupported_request_schema_version")
        request_schema = _load_json(request_schema_path)
        capability_catalog_path = REQUEST_CAPABILITY_CATALOG_PATHS.get(schema_version)
        if capability_catalog_path is None:
            raise ValueError("unsupported_request_schema_version")
        capability_catalog = _load_json(capability_catalog_path)
        
        if allow_fixture_snapshot:
            fixture_root = ROOT / "tests" / "fixtures" / "m8r_05a_f3"
            security_master = load_f3_verified_security_master(
                fixture_root / "verified_security_master_snapshot.json",
                fixture_root / "verified_security_master_snapshot_manifest.json",
                allow_fixture_snapshot=True,
            )
        else:
            security_master = get_production_mode_a_security_master(PRODUCTION_POINTER_PATH)

        return validate_unified_market_evidence_request(
            request=request,
            security_master=security_master,
            capability_catalog=capability_catalog,
            request_schema=request_schema,
            allow_fixture_snapshot=allow_fixture_snapshot
        )
    except FileNotFoundError as e:
        raise e
    except ValueError as e:
        raise e
    except Exception as e:
        # Prevent F3 traceback leakage
        raise RuntimeError(f"mode_a_internal_error: {type(e).__name__}") from e
