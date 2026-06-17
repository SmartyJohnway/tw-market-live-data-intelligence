import requests
import json
from datetime import datetime

def probe():
    print("Probing TWSE OpenAPI...")
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        status = response.status_code
        data = response.json()
        print(f"Status: {status}")
        if data and isinstance(data, list) and len(data) > 0:
            print(f"Success! Sample: {json.dumps(data[0], ensure_ascii=False)}")
        else:
            print("No data or unexpected format.")
        return {"source": "TWSE OpenAPI", "url": url, "status": status, "success": status == 200 and isinstance(data, list) and len(data) > 0}
    except Exception as e:
        print(f"Failed: {e}")
        return {"source": "TWSE OpenAPI", "url": url, "status": "Error", "success": False, "error": str(e)}

if __name__ == "__main__":
    probe()
