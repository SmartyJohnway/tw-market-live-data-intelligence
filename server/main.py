from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ensure scripts directory can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from probe_twse_openapi import probe as probe_twse
from probe_tpex_openapi import probe as probe_tpex
from probe_yahoo import probe as probe_yahoo
from probe_twse_mis import probe as probe_mis
from probe_finmind import probe as probe_finmind
from probe_fugle_fubon import probe as probe_fugle_fubon

app = FastAPI(
    title="TW-Market Live Data Intelligence API",
    description="API for probing Taiwan equity market data sources. Designed for AI and MCP integration.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "TW-Market Live Data Intelligence API is running."}

@app.get("/api/probe/twse")
def get_twse_probe():
    return probe_twse()

@app.get("/api/probe/tpex")
def get_tpex_probe():
    return probe_tpex()

@app.get("/api/probe/yahoo")
def get_yahoo_probe():
    yahoo_symbols = ["2330.TW", "1435.TW", "0050.TW", "00929.TW", "^TWII", "TWD=X"]
    return probe_yahoo(symbols=yahoo_symbols)

@app.get("/api/probe/twse_mis")
def get_twse_mis_probe():
    mis_symbols = ["tse_2330.tw", "tse_1435.tw", "tse_0050.tw", "tse_00929.tw", "tse_t00.tw", "otc_o00.tw"]
    return probe_mis(symbols=mis_symbols)

@app.get("/api/probe/finmind")
def get_finmind_probe():
    finmind_datasets = [
        ("TaiwanStockPrice", "2330"),
        ("TaiwanStockPrice", "1435"),
        ("TaiwanStockPrice", "0050"),
        ("TaiwanStockPrice", "00929"),
        ("TaiwanStockPrice", "TAIEX"),
        ("TaiwanFutureDaily", "TX"),
    ]
    return probe_finmind(datasets=finmind_datasets)

@app.get("/api/probe/feasibility")
def get_feasibility_probe():
    return probe_fugle_fubon()

@app.get("/api/probe/all")
def get_all_probes():
    yahoo_symbols = ["2330.TW", "1435.TW", "0050.TW", "00929.TW", "^TWII", "TWD=X"]
    mis_symbols = ["tse_2330.tw", "tse_1435.tw", "tse_0050.tw", "tse_00929.tw", "tse_t00.tw", "otc_o00.tw"]
    finmind_datasets = [
        ("TaiwanStockPrice", "2330"),
        ("TaiwanStockPrice", "1435"),
        ("TaiwanStockPrice", "0050"),
        ("TaiwanStockPrice", "00929"),
        ("TaiwanStockPrice", "TAIEX"),
        ("TaiwanFutureDaily", "TX"),
    ]
    return [
        probe_twse(),
        probe_tpex(),
        probe_yahoo(symbols=yahoo_symbols),
        probe_mis(symbols=mis_symbols),
        probe_finmind(datasets=finmind_datasets),
        *probe_fugle_fubon()
    ]
