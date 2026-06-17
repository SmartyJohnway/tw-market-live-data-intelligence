import requests
import json
import time

def probe(symbols=["2330.TW", "1435.TW", "0050.TW", "00929.TW", "^TWII", "TWD=X"]):
    # TWD=X for currency, ^TWII for index, 2330 for large cap, 1435 for cold stock, 0050/00929 for ETFs
    print(f"Probing Yahoo Finance for {symbols}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    results = []
    success_count = 0

    for sym in symbols:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            status = response.status_code
            data = response.json()
            success = status == 200 and "chart" in data and data["chart"].get("result")
            if success:
                success_count += 1
            results.append({"symbol": sym, "status": status, "success": bool(success)})
        except Exception as e:
            results.append({"symbol": sym, "status": "Error", "success": False, "error": str(e)})
        time.sleep(0.5) # respect rate limit

    overall_success = success_count > 0
    print(f"Status: {success_count}/{len(symbols)} successful.")
    return {"source": "Yahoo Finance (TW)", "url": "https://query1.finance.yahoo.com/v8/finance/chart/", "status": f"{success_count}/{len(symbols)} OK", "success": overall_success, "details": results}

if __name__ == "__main__":
    probe()
