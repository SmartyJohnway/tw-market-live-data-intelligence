import argparse
import sys
import json
import uvicorn
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def run_startup_check():
    """
    Perform a bounded check to ensure assets are loaded correctly
    without starting the server.
    """
    try:
        from server.services.unified_mode_a import (
            CANONICAL_SCHEMA_PATH, 
            CANONICAL_CATALOG_PATH,
            PRODUCTION_SNAPSHOT_PATH,
            PRODUCTION_MANIFEST_PATH,
            _load_json
        )
        from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
        from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
        
        schema_loaded = CANONICAL_SCHEMA_PATH.exists()
        catalog_loaded = CANONICAL_CATALOG_PATH.exists()
        
        request_schema = _load_json(CANONICAL_SCHEMA_PATH) if schema_loaded else {}
        catalog = _load_json(CANONICAL_CATALOG_PATH) if catalog_loaded else {}
        
        # This will raise FileNotFoundError or ValueError if missing or invalid
        security_master = load_f3_verified_security_master(
            PRODUCTION_SNAPSHOT_PATH,
            PRODUCTION_MANIFEST_PATH,
            allow_fixture_snapshot=False
        )
        
        # Smoke test canonical validation
        smoke_request = {
            "schema_version": "unified_market_evidence_request.v1",
            "request_id": "startup-smoke-test",
            "execution_mode": "preview",
            "targets": [],
            "data_needs": []
        }
        validate_unified_market_evidence_request(
            request=smoke_request,
            security_master=security_master,
            capability_catalog=catalog,
            request_schema=request_schema,
            allow_fixture_snapshot=False
        )

        result = {
            "status": "ok",
            "mode": "mode_a",
            "host": "127.0.0.1",
            "network_on_startup": False,
            "canonical_schema_loaded": schema_loaded,
            "security_master_loaded": True,
            "capability_catalog_loaded": catalog_loaded
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"{type(e).__name__}: {str(e)}"}, indent=2))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Unified Market Evidence Operator Workbench Launcher")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to. Only localhost is allowed.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to.")
    parser.add_argument("--startup-check", action="store_true", help="Run offline startup check and exit.")
    
    args = parser.parse_args()

    if args.startup_check:
        run_startup_check()

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print("ERROR: Mode A Workbench explicitly forbids non-localhost bindings to guarantee offline boundaries.")
        sys.exit(1)

    print("Starting Unified Workbench (Mode A) on localhost...")
    uvicorn.run("server.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
