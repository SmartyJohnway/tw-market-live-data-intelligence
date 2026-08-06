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
        
        schema_loaded = CANONICAL_SCHEMA_PATH.exists()
        catalog_loaded = CANONICAL_CATALOG_PATH.exists()
        security_master_loaded = PRODUCTION_SNAPSHOT_PATH.exists() and PRODUCTION_MANIFEST_PATH.exists()
        
        if not security_master_loaded:
            raise FileNotFoundError("canonical_security_master_unavailable")
        
        if schema_loaded: _load_json(CANONICAL_SCHEMA_PATH)
        if catalog_loaded: _load_json(CANONICAL_CATALOG_PATH)

        result = {
            "status": "ok",
            "mode": "mode_a",
            "host": "127.0.0.1",
            "network_on_startup": False,
            "canonical_schema_loaded": schema_loaded,
            "security_master_loaded": security_master_loaded,
            "capability_catalog_loaded": catalog_loaded
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=2))
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
