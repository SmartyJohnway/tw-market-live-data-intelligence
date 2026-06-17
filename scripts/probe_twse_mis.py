import requests
import time
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope

def probe(symbols=None):
    if not symbols:
        symbols = ["tse_2330.tw", "tse_0050.tw", "tse_t00.tw"]
    print(f"Probing TWSE MIS for {symbols}...")

    probe_id = f"twse_mis_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    session.headers.update(headers)

    # 1. Get session cookies to avoid being blocked by TWSE
    try:
        index_url = "https://mis.twse.com.tw/stock/index.jsp"
        session.get(index_url, timeout=10)
    except Exception as e:
        return generate_standard_envelope(
            probe_id=probe_id,
            source="TWSE_MIS",
            source_type="unofficial_frontend_endpoint",
            contract_status="blocked",
            http_status="Session Error",
            url="https://mis.twse.com.tw",
            requires_session=True,
            errors=[str(e)]
        )

    # 2. Query data for multiple asset classes
    timestamp_ms = int(time.time() * 1000)
    ex_ch = "|".join(symbols)
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ex_ch}&json=1&delay=0&_={timestamp_ms}"

    try:
        response = session.get(url, timeout=10)
        status = response.status_code
        if status != 200:
             return generate_standard_envelope(
                probe_id=probe_id,
                source="TWSE_MIS",
                source_type="unofficial_frontend_endpoint",
                contract_status="failed",
                http_status=status,
                url=url,
                headers_used=headers,
                requires_session=True,
                errors=[f"HTTP {status}"]
             )

        data = response.json()
        success = "msgArray" in data and len(data["msgArray"]) > 0

        raw_sample = None
        normalized_sample = None
        staleness_seconds = None
        delay_status = "unknown"

        if success:
            raw_sample = data["msgArray"][0]
            # Parse source timestamp correctly
            source_timestamp = int(raw_sample.get("tlong", 0)) // 1000
            staleness_seconds = int(time.time()) - source_timestamp if source_timestamp > 0 else None

            if staleness_seconds is not None:
                if staleness_seconds < 300:
                    delay_status = "realtime"
                elif staleness_seconds < 86400:
                    delay_status = "delayed"
                else:
                    delay_status = "stale"

            normalized_sample = {
                "symbol": raw_sample.get("c"),
                "name": raw_sample.get("n"),
                "price": raw_sample.get("z"),
                "exchange": raw_sample.get("ex"),
                "source_time_ms": raw_sample.get("tlong"),
                "retrieved_at_taipei": raw_sample.get("d") + " " + raw_sample.get("t")
            }

        return generate_standard_envelope(
            probe_id=probe_id,
            source="TWSE_MIS",
            source_type="unofficial_frontend_endpoint",
            contract_status="normalized_pass" if success and normalized_sample else ("http_pass" if success else "failed"),
            http_status=status,
            url=url,
            headers_used=headers,
            requires_session=True,
            raw_sample={"_total_found": len(data.get("msgArray", [])), "sample": raw_sample} if success else None,
            normalized_sample=normalized_sample,
            freshness_status="realtime_candidate",
            staleness_seconds=staleness_seconds,
            delay_status=delay_status,
            risk_level="high",
            risk_notes=["Strict rate limiting", "Requires index.jsp visit for cookies", "Not designed for API use", "Unofficial endpoint"],
            ai_suitability="live_watchlist",
            unsupported_targets=["futures", "funds"], # MIS mainly handles TWSE/TPEx stocks/ETFs
            failed_targets=[] if success else symbols
        )
    except Exception as e:
        return generate_standard_envelope(
            probe_id=probe_id,
            source="TWSE_MIS",
            source_type="unofficial_frontend_endpoint",
            contract_status="failed",
            http_status="Error",
            url=url,
            headers_used=headers,
            requires_session=True,
            errors=[str(e)]
        )

if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2, ensure_ascii=False))
