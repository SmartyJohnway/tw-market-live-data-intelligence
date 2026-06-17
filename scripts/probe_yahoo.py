import requests
import time
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope

def probe(symbols=["2330.TW", "1435.TW", "0050.TW", "00929.TW", "^TWII", "TWD=X"]):
    print(f"Probing Yahoo Finance for {symbols}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    probe_id = f"yahoo_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    results = []
    success_count = 0
    raw_sample = None
    normalized_sample = None

    for sym in symbols:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            status = response.status_code
            data = response.json()
            success = status == 200 and "chart" in data and data["chart"].get("result")
            if success:
                success_count += 1
                if not raw_sample:
                     raw_sample = data["chart"]["result"][0]["meta"]
                     normalized_sample = {
                          "symbol": raw_sample.get("symbol"),
                          "price": raw_sample.get("regularMarketPrice"),
                          "source_time": raw_sample.get("regularMarketTime"),
                          "exchange": raw_sample.get("exchangeName")
                     }
            results.append({"symbol": sym, "status": status, "success": bool(success)})
        except Exception as e:
            results.append({"symbol": sym, "status": "Error", "success": False, "error": str(e)})
        time.sleep(0.5)

    overall_success = success_count > 0

    # Calculate staleness for the first successful item
    staleness_seconds = None
    if raw_sample and raw_sample.get("regularMarketTime"):
         staleness_seconds = int(time.time()) - raw_sample.get("regularMarketTime")

    return generate_standard_envelope(
         probe_id=probe_id,
         source="Yahoo_Finance",
         source_type="public_api",
         contract_status="normalized_pass" if overall_success and normalized_sample else ("http_pass" if overall_success else "failed"),
         http_status=200 if overall_success else "Mixed/Failed",
         url="https://query1.finance.yahoo.com/v8/finance/chart/",
         headers_used=headers,
         raw_sample={"meta": raw_sample, "_details": results},
         normalized_sample=normalized_sample,
         freshness_status="realtime_candidate",
         staleness_seconds=staleness_seconds,
         risk_level="medium",
         risk_notes=["Rate limits apply", "Not an official data source"],
         ai_suitability="live_watchlist"
    )

if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2, ensure_ascii=False))
