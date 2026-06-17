import requests
import json
import os
import time
from dotenv import load_dotenv

def probe(datasets=[("TaiwanStockPrice", "2330"), ("TaiwanStockPrice", "1435"), ("TaiwanStockPrice", "0050"), ("TaiwanStockPrice", "00929"), ("TaiwanStockPrice", "TAIEX"), ("TaiwanFutureDaily", "TX")]):
    print(f"Probing FinMind API for datasets: {datasets}...")
    load_dotenv()
    token = os.getenv("FINMIND_TOKEN", "")
    url = "https://api.finmindtrade.com/api/v4/data"

    success_count = 0
    results = []

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
            results.append({"dataset": dataset, "data_id": data_id, "status": status, "success": bool(success)})
        except Exception as e:
            results.append({"dataset": dataset, "data_id": data_id, "status": "Error", "success": False, "error": str(e)})
        time.sleep(0.5)

    overall_success = success_count > 0
    print(f"Status: {success_count}/{len(datasets)} successful.")
    return {"source": "FinMind", "url": url, "status": f"{success_count}/{len(datasets)} OK", "success": overall_success, "details": results}

if __name__ == "__main__":
    probe()
