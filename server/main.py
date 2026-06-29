from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import json

# Product server intentionally avoids importing live probe modules.
# Future market-data execution belongs behind M5I authorization in a separate legacy/refresh app.

app = FastAPI(
    title="TW-Market Readonly Context API",
    description="Readonly local M5F market-context API. Legacy live probes are disabled pending M5I authorization.",
    version="1.0.0"
)

# Local-first CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "http://127.0.0.1", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

MANUAL_PROBE_CONFIRMATION_DESCRIPTION = (
    "Set to true to acknowledge this is a manual legacy probe surface. "
    "Probe endpoints do not refresh production artifacts or frontend state."
)


def governance_caveats():
    return [
        "legacy_probe_surface_disabled_pending_m5i",
        "not_controlled_refresh_bridge",
        "no_production_artifact_refresh",
        "no_frontend_artifact_refresh",
        "bounded_local_workbench_only",
        "not_trading_or_execution_signal",
    ]


def require_manual_probe_confirmation(confirm_manual_probe: bool) -> None:
    raise HTTPException(
        status_code=410,
        detail={
            "error": "legacy_probe_endpoint_disabled_pending_m5i_authorization",
            "message": "FastAPI product server does not execute live probes; future refresh requires M5I authorization.",
            "required_query": None,
            "caveats": governance_caveats(),
        },
    )


def governed_probe_response(source_id: str, result: dict) -> dict:
    return {
        "governance": {
            "surface": "FastAPI manual probe endpoint",
            "source_id": source_id,
            "execution_mode": "manual_explicit_probe",
            "production_refresh": False,
            "frontend_refresh": False,
            "caveats": governance_caveats(),
        },
        "result": result,
    }


@app.get("/")
def read_root():
    return {"status": "ok", "message": "TW-Market Live Data Intelligence API is running locally."}

@app.get("/api/health")
def read_health():
    return {"status": "healthy"}


@app.get("/api/governance")
def read_governance():
    return {
        "api_mode": "local_first_governed_workbench",
        "probe_endpoints": {
            "status": "disabled_pending_m5i_authorization",
            "requires_query": None,
            "production_refresh": False,
            "frontend_refresh": False,
            "caveats": governance_caveats(),
        },
        "readonly_context": {
            "matrix_endpoint": "/api/matrix",
            "production_refresh": False,
        },
    }

@app.get("/api/probe/twse", include_in_schema=False)
def get_twse_probe():
    require_manual_probe_confirmation(False)

@app.get("/api/probe/tpex", include_in_schema=False)
def get_tpex_probe():
    require_manual_probe_confirmation(False)

@app.get("/api/probe/yahoo", include_in_schema=False)
def get_yahoo_probe():
    require_manual_probe_confirmation(False)

@app.get("/api/probe/twse_mis", include_in_schema=False)
def get_twse_mis_probe():
    require_manual_probe_confirmation(False)

@app.get("/api/probe/finmind", include_in_schema=False)
def get_finmind_probe():
    require_manual_probe_confirmation(False)

@app.get("/api/probe/feasibility", include_in_schema=False)
def get_feasibility_probe():
    require_manual_probe_confirmation(False)

@app.get("/api/matrix")
def get_matrix():
    # Backward-compatible path now returns the validated M5F capability summary.
    return _read_m5f_artifact("capability_summary.json")

# M5FGH readonly canonical market context endpoints.
from pathlib import Path
from copy import deepcopy
from scripts.validate_m5f_canonical_market_context_package import validate_package as _validate_m5f_package

REPO_ROOT = Path(__file__).resolve().parents[1]
M5F_PACKAGE_DIR = REPO_ROOT / "research/staging/m5f/m5f_canonical_market_context_01"


def _canonical_governance(canonical: dict | None = None):
    canonical = canonical or {}
    gov = canonical.get("governance", {}) if isinstance(canonical, dict) else {}
    caveats = canonical.get("global_caveats") if isinstance(canonical, dict) else None
    return {
        "surface": "FastAPI readonly M5F canonical market context",
        "execution_mode": "readonly_local_artifact_read",
        "network_calls": False,
        "artifact_writes": False,
        "live_probe_execution": False,
        "historical_evidence_snapshot": gov.get("historical_evidence_snapshot", True),
        "stale_status": gov.get("stale_status", "unknown"),
        "badge": gov.get("badge", "historical/unknown"),
        "current_realtime": gov.get("current_realtime", False),
        "production_current_state": gov.get("production_current_state", False),
        "production_ready": gov.get("production_ready", False),
        "realtime_guaranteed": gov.get("realtime_guaranteed", False),
        "trading_signal": gov.get("trading_signal", False),
        "readonly_only": gov.get("readonly_only", True),
        "caveats": list(caveats or [
            "not_realtime_guaranteed",
            "not_trading_signal",
            "not_production_current_state",
            "source_risk_present",
            "freshness_must_be_displayed",
        ]),
    }


def _load_validated_canonical(package_dir: Path) -> dict:
    _validate_m5f_package(package_dir)
    return json.loads((package_dir / "canonical_market_context.json").read_text(encoding="utf-8"))

def _read_m5f_artifact(filename: str, *, text: bool = False):
    try:
        canonical = _load_validated_canonical(M5F_PACKAGE_DIR)
    except Exception as exc:
        raise HTTPException(status_code=409, detail={"error": "m5f_package_validation_failed", "message": str(exc), "governance": _canonical_governance()})
    governance = _canonical_governance(canonical)
    path = M5F_PACKAGE_DIR / filename
    source_path = path.relative_to(REPO_ROOT).as_posix() if path.is_relative_to(REPO_ROOT) else path.as_posix()
    if not path.is_file():
        raise HTTPException(status_code=404, detail={"error": "m5f_artifact_missing", "source_path": source_path, "governance": governance})
    try:
        if text:
            return {"source_path": source_path, "content": path.read_text(encoding="utf-8"), "governance": governance}
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail={"error": "m5f_artifact_malformed", "source_path": source_path, "message": exc.msg, "governance": governance})
    return {"source_path": source_path, "content": deepcopy(data), "governance": governance}


@app.get("/api/context/canonical")
def get_context_canonical():
    return _read_m5f_artifact("canonical_market_context.json")


@app.get("/api/context/snapshot")
def get_context_snapshot():
    return _read_m5f_artifact("latest_market_snapshot.json")


@app.get("/api/context/source-health")
def get_context_source_health():
    return _read_m5f_artifact("source_health.json")


@app.get("/api/context/capability-summary")
def get_context_capability_summary():
    return _read_m5f_artifact("capability_summary.json")


@app.get("/api/context/briefing")
def get_context_briefing():
    return _read_m5f_artifact("chatgpt_briefing.md", text=True)
