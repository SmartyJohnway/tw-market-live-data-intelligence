from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import json

# Ensure scripts directory can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from run_all_probes import load_targets, extract_symbols, extract_finmind_datasets
from probe_twse_openapi import probe as probe_twse
from probe_tpex_openapi import probe as probe_tpex
from probe_yahoo import probe as probe_yahoo
from probe_twse_mis import probe as probe_mis
from probe_finmind import probe as probe_finmind
from probe_fugle_fubon import probe as probe_fugle_fubon

app = FastAPI(
    title="TW-Market Live Data Intelligence API",
    description="API for probing Taiwan equity market data sources locally. Not intended for public exposure.",
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

targets = load_targets()

MANUAL_PROBE_CONFIRMATION_DESCRIPTION = (
    "Set to true to acknowledge this is a manual legacy probe surface. "
    "Probe endpoints do not refresh production artifacts or frontend state."
)


def governance_caveats():
    return [
        "manual_legacy_probe_surface",
        "not_controlled_refresh_bridge",
        "no_production_artifact_refresh",
        "no_frontend_artifact_refresh",
        "bounded_local_workbench_only",
        "not_trading_or_execution_signal",
    ]


def require_manual_probe_confirmation(confirm_manual_probe: bool) -> None:
    if not confirm_manual_probe:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "manual_probe_confirmation_required",
                "required_query": "confirm_manual_probe=true",
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
            "status": "manual_legacy_surface",
            "requires_query": "confirm_manual_probe=true",
            "production_refresh": False,
            "frontend_refresh": False,
            "caveats": governance_caveats(),
        },
        "readonly_context": {
            "matrix_endpoint": "/api/matrix",
            "production_refresh": False,
        },
    }

@app.get("/api/probe/twse")
def get_twse_probe(confirm_manual_probe: bool = Query(False, description=MANUAL_PROBE_CONFIRMATION_DESCRIPTION)):
    require_manual_probe_confirmation(confirm_manual_probe)
    try:
        return governed_probe_response("TWSE_OpenAPI", probe_twse())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/tpex")
def get_tpex_probe(confirm_manual_probe: bool = Query(False, description=MANUAL_PROBE_CONFIRMATION_DESCRIPTION)):
    require_manual_probe_confirmation(confirm_manual_probe)
    try:
        return governed_probe_response("TPEx_OpenAPI", probe_tpex())
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/yahoo")
def get_yahoo_probe(confirm_manual_probe: bool = Query(False, description=MANUAL_PROBE_CONFIRMATION_DESCRIPTION)):
    require_manual_probe_confirmation(confirm_manual_probe)
    try:
        yahoo_symbols = extract_symbols(targets, "yahoo")
        return governed_probe_response("Yahoo_Finance", probe_yahoo(symbols=yahoo_symbols))
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/twse_mis")
def get_twse_mis_probe(confirm_manual_probe: bool = Query(False, description=MANUAL_PROBE_CONFIRMATION_DESCRIPTION)):
    require_manual_probe_confirmation(confirm_manual_probe)
    try:
        mis_symbols = extract_symbols(targets, "twse_mis")
        return governed_probe_response("TWSE_MIS", probe_mis(symbols=mis_symbols))
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/finmind")
def get_finmind_probe(confirm_manual_probe: bool = Query(False, description=MANUAL_PROBE_CONFIRMATION_DESCRIPTION)):
    require_manual_probe_confirmation(confirm_manual_probe)
    try:
        finmind_datasets = extract_finmind_datasets(targets)
        return governed_probe_response("FinMind", probe_finmind(datasets=finmind_datasets))
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/feasibility")
def get_feasibility_probe(confirm_manual_probe: bool = Query(False, description=MANUAL_PROBE_CONFIRMATION_DESCRIPTION)):
    require_manual_probe_confirmation(confirm_manual_probe)
    try:
        return governed_probe_response("Fugle_Fubon_Feasibility", probe_fugle_fubon())
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/matrix")
def get_matrix():
    # Returns the statically generated matrix json
    matrix_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'matrix.json')
    if os.path.exists(matrix_path):
        with open(matrix_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="matrix.json not found. Run probe scripts first.")

# M5FGH readonly canonical market context endpoints.
from pathlib import Path
from copy import deepcopy

REPO_ROOT = Path(__file__).resolve().parents[1]
M5F_PACKAGE_DIR = REPO_ROOT / "research/staging/m5f/m5f_canonical_market_context_01"


def _m5f_governance():
    return {
        "surface": "FastAPI readonly M5F canonical market context",
        "execution_mode": "readonly_local_artifact_read",
        "network_calls": False,
        "artifact_writes": False,
        "live_probe_execution": False,
        "historical_evidence_snapshot": True,
        "stale_status": "stale",
        "badge": "historical/stale",
        "current_realtime": False,
        "production_current_state": False,
        "production_ready": False,
        "realtime_guaranteed": False,
        "trading_signal": False,
        "readonly_only": True,
        "caveats": [
            "not_realtime_guaranteed",
            "not_trading_signal",
            "not_production_current_state",
            "source_risk_present",
            "freshness_must_be_displayed",
        ],
    }


def _read_m5f_artifact(filename: str, *, text: bool = False):
    path = M5F_PACKAGE_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail={"error": "m5f_artifact_missing", "source_path": str(path.relative_to(REPO_ROOT)), "governance": _m5f_governance()})
    try:
        if text:
            return {"source_path": str(path.relative_to(REPO_ROOT)), "content": path.read_text(encoding="utf-8"), "governance": _m5f_governance()}
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail={"error": "m5f_artifact_malformed", "source_path": str(path.relative_to(REPO_ROOT)), "message": exc.msg, "governance": _m5f_governance()})
    return {"source_path": str(path.relative_to(REPO_ROOT)), "content": deepcopy(data), "governance": _m5f_governance()}


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
