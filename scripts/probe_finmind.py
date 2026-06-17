import requests
import time
import os
from datetime import datetime, timezone
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope

def probe(datasets=None):
    from probe_utils import load_targets
    if datasets is None:
        targets = load_targets()
        datasets = [("TaiwanStockPrice", s) for s in targets.get("twse_large_caps", [])[:2]] + \
                   [("TaiwanStockPrice", s) for s in targets.get("thinly_traded_stocks", [])[:1]] + \
                   [("TaiwanStockPrice", s) for s in targets.get("etfs", [])[:2]] + \
                   [("TaiwanStockPrice", "TAIEX")] + \
                   [("TaiwanFutureDaily", s) for s in targets.get("futures_candidates", [])[:1]]

    print(f"Probing FinMind API for datasets: {datasets}...")
    load_dotenv()
    token = os.getenv("FINMIND_TOKEN", "")
    url = "https://api.finmindtrade.com/api/v4/data"
    probe_id = f"finmind_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    success_count = 0
    results = []
    raw_sample = None
    normalized_sample = None

    for dataset, data_id in datasets:
        params = {
            "dataset": dataset,
            "start_date": "2024-01-01",
        }
        if data_id:
            params["data_id"] = data_id
        if token:
            params["token"] = token

        try:
            response = requests.get(url, params=params, timeout=10)
            status = response.status_code
            data = response.json()
            success = status == 200 and data.get("msg") == "success"

            if success:
                success_count += 1
                if not raw_sample and data.get("data") and len(data["data"]) > 0:
                     raw_sample = data["data"][-1] # get latest
                     normalized_sample = {
                          "dataset": dataset,
                          "symbol": data_id,
                          "date": raw_sample.get("date"),
                          "price": raw_sample.get("close") or raw_sample.get("settlement_price"),
                          "volume": raw_sample.get("Trading_Volume") or raw_sample.get("trading_volume")
                     }

            results.append({"dataset": dataset, "data_id": data_id, "status": status, "success": bool(success)})
        except Exception as e:
            results.append({"dataset": dataset, "data_id": data_id, "status": "Error", "success": False, "error": str(e)})
        time.sleep(0.5)

    overall_success = success_count > 0

    # Calculate staleness based on latest date string if available
    staleness_seconds = None
    if raw_sample and raw_sample.get("date"):
         try:
             record_date = datetime.strptime(raw_sample["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
             staleness_seconds = int((datetime.now(timezone.utc) - record_date).total_seconds())
         except:
             pass

    failed_targets = [r["data_id"] for r in results if not r["success"]]
    unsupported_targets = ["funds"] # Finmind has limited fund support in free api usually

    return generate_standard_envelope(
         probe_id=probe_id,
         source="FinMind",
         source_type="commercial_api",
         contract_status="normalized_pass" if overall_success and normalized_sample else ("http_pass" if overall_success else "failed"),
         http_status=200 if overall_success else "Mixed/Failed",
         url=url,
         requires_auth=True, # Optional but expected for reliability
         raw_sample={"sample": raw_sample, "_details": results},
         normalized_sample=normalized_sample,
         freshness_status="eod_batch",
         staleness_seconds=staleness_seconds,
         risk_level="low",
         risk_notes=["Free tier rate limits apply"],
         ai_suitability="historical_and_eod",
         failed_targets=failed_targets,
         unsupported_targets=unsupported_targets
    )

if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2, ensure_ascii=False))
