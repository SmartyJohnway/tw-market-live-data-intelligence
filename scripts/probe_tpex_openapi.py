import requests
import json

def probe():
    print("Probing TPEx OpenAPI...")
    url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
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
        return {"source": "TPEx OpenAPI", "url": url, "status": status, "success": status == 200 and isinstance(data, list) and len(data) > 0}
    except Exception as e:
        print(f"Failed: {e}")
        return {"source": "TPEx OpenAPI", "url": url, "status": "Error", "success": False, "error": str(e)}

if __name__ == "__main__":
    probe()
