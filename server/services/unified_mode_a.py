import json
from pathlib import Path
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master

ROOT = Path(__file__).resolve().parent.parent.parent
CANONICAL_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_request.v1.schema.json"
CANONICAL_CATALOG_PATH = ROOT / "docs" / "data_capabilities" / "unified_market_evidence_capability_catalog.v1.json"

# Mode A uses the fixture snapshot if a production one is not strictly designated.
FIXTURE_SNAPSHOT_PATH = ROOT / "tests" / "fixtures" / "m8r_05a_f3" / "verified_security_master_snapshot.json"
FIXTURE_MANIFEST_PATH = ROOT / "tests" / "fixtures" / "m8r_05a_f3" / "verified_security_master_snapshot_manifest.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"canonical_dependency_missing: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"canonical_dependency_malformed: {path.name}") from e


def validate_mode_a_request(request: dict) -> dict:
    """
    Executes the canonical Mode A F3 validation.
    Enforces offline execution and deterministic outputs.
    """
    try:
        request_schema = _load_json(CANONICAL_SCHEMA_PATH)
        capability_catalog = _load_json(CANONICAL_CATALOG_PATH)
        
        # Security Master
        if not FIXTURE_SNAPSHOT_PATH.exists() or not FIXTURE_MANIFEST_PATH.exists():
            raise FileNotFoundError("canonical_dependency_missing: security_master_snapshot")
        
        security_master = load_f3_verified_security_master(
            FIXTURE_SNAPSHOT_PATH,
            FIXTURE_MANIFEST_PATH,
            allow_fixture_snapshot=True
        )

        return validate_unified_market_evidence_request(
            request=request,
            security_master=security_master,
            capability_catalog=capability_catalog,
            request_schema=request_schema,
            allow_fixture_snapshot=True
        )
    except FileNotFoundError as e:
        raise e
    except ValueError as e:
        raise e
    except Exception as e:
        # Prevent F3 traceback leakage
        raise RuntimeError(f"mode_a_internal_error: {str(e)}") from e
