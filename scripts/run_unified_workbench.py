import argparse
import sys
import json
import uvicorn
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def preload_governed_runtime() -> dict:
    """Activate accepted immutable Mode A authorities for this process only."""
    from server.services.unified_mode_a import (
        CANONICAL_SCHEMA_PATH,
        CANONICAL_CATALOG_PATH,
        PRODUCTION_POINTER_PATH,
        _load_json,
    )
    from scripts.m8r_06_01c2_mode_a_security_master_loader import (
        get_production_mode_a_security_master,
    )

    _load_json(CANONICAL_SCHEMA_PATH)
    _load_json(CANONICAL_CATALOG_PATH)
    security_master = get_production_mode_a_security_master(PRODUCTION_POINTER_PATH)
    if not security_master:
        raise RuntimeError("governed_security_master_unavailable")
    return {
        "status": "ok",
        "mode": "mode_a",
        "host": "127.0.0.1",
        "network_on_startup": False,
        "canonical_schema_loaded": True,
        "security_master_loaded": True,
        "capability_catalog_loaded": True,
    }


def run_startup_check() -> int:
    """Perform the same bounded preload used by normal server startup."""
    try:
        print(json.dumps(preload_governed_runtime(), indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "error", "message": f"governed_runtime_preload_failed:{type(exc).__name__}"}, indent=2))
        return 1


def main():
    parser = argparse.ArgumentParser(description="Unified Market Evidence Operator Workbench Launcher")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to. Only localhost is allowed.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to.")
    parser.add_argument("--startup-check", action="store_true", help="Run offline startup check and exit.")
    
    args = parser.parse_args()

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print("ERROR: Mode A Workbench explicitly forbids non-localhost bindings to guarantee offline boundaries.")
        sys.exit(1)

    if args.startup_check:
        sys.exit(run_startup_check())

    try:
        preload_governed_runtime()
    except Exception as exc:
        print(f"ERROR: governed_runtime_preload_failed:{type(exc).__name__}")
        sys.exit(1)

    print("Starting Unified Workbench (Mode A) on localhost...")
    uvicorn.run("server.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
