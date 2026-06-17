import requests
import json
import time

def probe(symbols=["tse_2330.tw", "tse_1435.tw", "tse_0050.tw", "tse_00929.tw", "tse_t00.tw", "otc_o00.tw"]):
    print(f"Probing TWSE MIS for {symbols}...")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    })

    # 1. Get session cookies to avoid being blocked by TWSE
    try:
        index_url = "https://mis.twse.com.tw/stock/index.jsp"
        session.get(index_url, timeout=10)
    except Exception as e:
        print(f"Failed to get session: {e}")
        return {"source": "TWSE MIS", "url": "https://mis.twse.com.tw", "status": "Session Error", "success": False, "error": str(e)}

    # 2. Query data for multiple asset classes
    timestamp = int(time.time() * 1000)
    ex_ch = "|".join(symbols)
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ex_ch}&json=1&delay=0&_={timestamp}"

    try:
        response = session.get(url, timeout=10)
        status = response.status_code
        data = response.json()
        print(f"Status: {status}")
        success = status == 200 and "msgArray" in data and len(data["msgArray"]) > 0
        if success:
             print(f"Success! Found {len(data['msgArray'])} items.")
        return {"source": "TWSE MIS", "url": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp", "status": status, "success": success}
    except Exception as e:
        print(f"Failed: {e}")
        return {"source": "TWSE MIS", "url": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp", "status": "Error", "success": False, "error": str(e)}

if __name__ == "__main__":
    probe()
