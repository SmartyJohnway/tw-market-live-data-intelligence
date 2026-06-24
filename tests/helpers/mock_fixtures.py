import json
import os
from datetime import datetime, timezone
import sys

# Ensure scripts can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from probe_twse_mis import normalize_twse_mis_row
from probe_twse_openapi import normalize_twse_openapi_row
from probe_tpex_openapi import normalize_tpex_openapi_row
from probe_yahoo import normalize_yahoo_chart_result

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "market_sources")

def load_fixture(source, filename="success.json"):
    path = os.path.join(FIXTURES_DIR, source, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_mock_inputs_from_fixtures(retrieved_at_utc_dt=None):
    """
    Loads success.json fixtures for TWSE_MIS, TWSE_OpenAPI, TPEx_OpenAPI, Yahoo_Finance
    and normalizes them into the format expected by build_snapshot's mock_inputs.
    mock_inputs should be: { "SourceName": { "symbol": normalized_data } }
    """
    if not retrieved_at_utc_dt:
        retrieved_at_utc_dt = datetime.now(timezone.utc)

    mock_inputs = {
        "TWSE_MIS": {},
        "TWSE_OpenAPI": {},
        "TPEx_OpenAPI": {},
        "Yahoo_Finance": {}
    }

    # TWSE_MIS
    twse_mis_data = load_fixture("twse_mis", "success.json")
    if twse_mis_data and "msgArray" in twse_mis_data:
        for row in twse_mis_data["msgArray"]:
            norm = normalize_twse_mis_row(row, retrieved_at_utc_dt, top_level_telemetry=twse_mis_data)
            symbol = row.get("c")
            if symbol == "t00":
                symbol = "TAIEX"
            if symbol:
                mock_inputs["TWSE_MIS"][symbol] = norm

    # TWSE_OpenAPI
    twse_openapi_data = load_fixture("twse_openapi", "success.json")
    if twse_openapi_data:
        for row in twse_openapi_data:
            norm = normalize_twse_openapi_row(row, retrieved_at_utc_dt)
            symbol = row.get("Code")
            if symbol:
                mock_inputs["TWSE_OpenAPI"][symbol] = norm

    # TPEx_OpenAPI
    tpex_openapi_data = load_fixture("tpex_openapi", "success.json")
    if tpex_openapi_data:
        for row in tpex_openapi_data:
            norm = normalize_tpex_openapi_row(row, retrieved_at_utc_dt)
            symbol = row.get("SecuritiesCompanyCode")
            if symbol:
                mock_inputs["TPEx_OpenAPI"][symbol] = norm

    # Yahoo_Finance
    yahoo_data = load_fixture("yahoo_finance", "success.json")
    if yahoo_data and "chart" in yahoo_data and yahoo_data["chart"].get("result"):
        result_data = yahoo_data["chart"]["result"][0]
        # In Yahoo, we only stored one symbol per response usually, let's parse symbol from meta
        meta = result_data.get("meta", {})
        sym_raw = meta.get("symbol")
        # map yahoo symbol back to standard config symbol if needed (e.g., 2330.TW -> 2330)
        symbol = sym_raw.replace(".TW", "").replace(".TWO", "").replace("^TWII", "TAIEX") if sym_raw else "2330"
        norm = normalize_yahoo_chart_result(result_data, sym_raw, retrieved_at_utc_dt)

        # Test-only mapping to bridge Yahoo_Finance payload to build_snapshot expectations
        mapped_norm = {
            "last_price": norm.get("regular_market_price"),
            "previous_close": norm.get("raw_meta", {}).get("previousClose"),
            "source_time": norm.get("regular_market_time_utc"),
            "retrieved_time": norm.get("retrieved_at_utc"),
            "open": norm.get("series", {}).get("open", [None])[0] if norm.get("series", {}).get("open") else None,
            "high": norm.get("series", {}).get("high", [None])[0] if norm.get("series", {}).get("high") else None,
            "low": norm.get("series", {}).get("low", [None])[0] if norm.get("series", {}).get("low") else None,
            "volume": norm.get("series", {}).get("volume", [None])[0] if norm.get("series", {}).get("volume") else None,
            "exchange": norm.get("exchange_name"),
            "price_semantics": "live_candidate" # This is mapped by apply_source_priority_policy usually, but we help it out
        }

        if mapped_norm["last_price"] is not None and mapped_norm["previous_close"] is not None and mapped_norm["previous_close"] > 0:
            mapped_norm["change"] = mapped_norm["last_price"] - mapped_norm["previous_close"]
            mapped_norm["change_pct"] = (mapped_norm["change"] / mapped_norm["previous_close"]) * 100

        # Merge back in so the norm structure has expected generator keys
        norm.update(mapped_norm)

        if symbol:
            mock_inputs["Yahoo_Finance"][symbol] = norm

    return mock_inputs
