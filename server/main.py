from fastapi import FastAPI, HTTPException
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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "TW-Market Live Data Intelligence API is running locally."}

@app.get("/api/health")
def read_health():
    return {"status": "healthy"}

@app.get("/api/probe/twse")
def get_twse_probe():
    try:
        return probe_twse()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/tpex")
def get_tpex_probe():
    try:
        return probe_tpex()
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/yahoo")
def get_yahoo_probe():
    try:
        yahoo_symbols = extract_symbols(targets, "yahoo")
        return probe_yahoo(symbols=yahoo_symbols)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/twse_mis")
def get_twse_mis_probe():
    try:
        mis_symbols = extract_symbols(targets, "twse_mis")
        return probe_mis(symbols=mis_symbols)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/finmind")
def get_finmind_probe():
    try:
        finmind_datasets = extract_finmind_datasets(targets)
        return probe_finmind(datasets=finmind_datasets)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Probe failed: {e}")

@app.get("/api/probe/feasibility")
def get_feasibility_probe():
    try:
        return probe_fugle_fubon()
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
