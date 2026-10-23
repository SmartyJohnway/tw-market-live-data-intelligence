import argparse
import sys
import json
import os
import uvicorn
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.tw_market_installation import InstallationError, resolve_installation
from server.local_network_boundary import DOCKER_PROFILE, NETWORK_PROFILE_ENV

def preload_governed_runtime() -> dict:
    """Activate accepted immutable Mode A authorities for this process only."""
    from server.services.unified_mode_a import (
        CANONICAL_SCHEMA_PATH,
        CANONICAL_CATALOG_PATH,
        PRODUCTION_POINTER_PATH,
        _load_json,
    )
    from scripts.m8r_06_01c2_mode_a_security_master_loader import (
        ModeASecurityMasterUnavailable,
        get_production_mode_a_security_master,
    )

    _load_json(CANONICAL_SCHEMA_PATH)
    _load_json(CANONICAL_CATALOG_PATH)
    try:
        security_master = get_production_mode_a_security_master(PRODUCTION_POINTER_PATH)
    except ModeASecurityMasterUnavailable as exc:
        if exc.reason_code != "NOT_INITIALIZED":
            raise
        # A fresh installation is a supported local-service state. Identity
        # operations fail closed at their public boundary, but `/api/health`,
        # the Workbench, and MCP startup must not require a hidden fixture or
        # a startup acquisition.
        return {
            "status": "not_initialized",
            "mode": "mode_a",
            "host": "127.0.0.1",
            "network_on_startup": False,
            "canonical_schema_loaded": True,
            "security_master_loaded": False,
            "security_master_status": "NOT_INITIALIZED",
            "capability_catalog_loaded": True,
        }
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
    parser.add_argument("--host", type=str, help="Host to bind to. Only localhost is allowed.")
    parser.add_argument("--port", type=int, help="Port to bind to.")
    parser.add_argument("--home")
    parser.add_argument("--state-root")
    parser.add_argument("--startup-check", action="store_true", help="Run offline startup check and exit.")
    
    args = parser.parse_args()
    try:
        installation = resolve_installation(home=args.home, state_root=args.state_root, host=args.host, port=args.port)
        installation.require_initialized()
        os.environ["TW_MARKET_HOME"] = str(installation.home)
        os.environ["TW_MARKET_STATE_ROOT"] = str(installation.state_root)
        os.environ.setdefault("TW_MARKET_OPERATIONAL_EVENT_PATH", str(installation.operational_event_path))
        args.host = installation.effective_service_host
        args.port = installation.effective_service_port
    except InstallationError as exc:
        print(json.dumps({"status": "error", "reason_code": exc.code}))
        raise SystemExit(1)

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
    # The Docker profile is an explicit Compose-only opt-in. Persisted service
    # settings and the native CLI remain loopback-only; the network middleware
    # separately admits only the container's bridge gateway.
    bind_host = "0.0.0.0" if os.environ.get(NETWORK_PROFILE_ENV) == DOCKER_PROFILE else args.host
    uvicorn.run("server.main:app", host=bind_host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
