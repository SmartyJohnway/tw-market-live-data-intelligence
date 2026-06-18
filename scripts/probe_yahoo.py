import requests
import time
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope

KNOWN_UNSUPPORTED_YAHOO_PLACEHOLDERS = {
    "TX.TW",
    "FUNDA.TW",
}

def probe(symbols=None):
    if not symbols:
        symbols = ["2330.TW", "0050.TW", "^TWII", "TX.TW"]

    print(f"Probing Yahoo Finance for {symbols}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    probe_id = f"yahoo_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    results = []
    success_count = 0
    raw_sample = None
    normalized_sample = None
    errors = []
    failed_targets = []
    unsupported_targets = []
    warnings = []

    for sym in symbols:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            status = response.status_code
            if status != 200:
                if status == 404 and sym in KNOWN_UNSUPPORTED_YAHOO_PLACEHOLDERS:
                    unsupported_targets.append(sym)
                    warnings.append(f"HTTP 404 for known unsupported placeholder {sym}")
                else:
                    errors.append(f"HTTP {status} for {sym}")
                    failed_targets.append(sym)
                continue

            data = response.json()
            # More robust check for success and non-empty result
            if "chart" in data and isinstance(data["chart"].get("result"), list) and len(data["chart"]["result"]) > 0:
                success = True
                result_data = data["chart"]["result"][0]
            else:
                success = False

            if success:
                success_count += 1
                if not raw_sample and "meta" in result_data:
                    raw_sample = result_data["meta"]
                    normalized_sample = {
                        "symbol": raw_sample.get("symbol"),
                        "price": raw_sample.get("regularMarketPrice"),
                        "source_time": raw_sample.get("regularMarketTime"),
                        "exchange": raw_sample.get("exchangeName")
                    }
            else:
                errors.append(f"Parse failed or empty result for {sym}")
                failed_targets.append(sym)
            results.append({"symbol": sym, "status": status, "success": bool(success)})
        except requests.exceptions.RequestException as e:
            errors.append(f"Network exception for {sym}: {str(e)}")
        except Exception as e:
            failed_targets.append(sym)
            errors.append(f"Exception for {sym}: {str(e)}")
        time.sleep(0.5)

    overall_success = success_count > 0

    # Calculate staleness for the first successful item
    staleness_seconds = None
    if raw_sample and raw_sample.get("regularMarketTime"):
        staleness_seconds = int(time.time()) - raw_sample.get("regularMarketTime")

    delay_status = "unknown"
    if staleness_seconds is not None:
        if staleness_seconds < 300:
            delay_status = "realtime"
        elif staleness_seconds < 86400:
            delay_status = "delayed"
        else:
            delay_status = "stale"

    return generate_standard_envelope(
        probe_id=probe_id,
        source="Yahoo_Finance",
        source_type="unofficial_api",
        contract_status="normalized_pass" if overall_success and normalized_sample else ("http_pass" if overall_success else "failed"),
        http_status=200 if overall_success else "Mixed/Failed",
        url="https://query1.finance.yahoo.com/v8/finance/chart/[symbol]",
        headers_used=headers,
        raw_sample={"meta": raw_sample, "_details": results} if raw_sample else None,
        normalized_sample=normalized_sample,
        freshness_status="realtime_candidate",
        staleness_seconds=staleness_seconds,
        delay_status=delay_status,
        risk_level="medium",
        risk_notes=["Rate limits apply", "Not an official data source", "Unofficial endpoint"],
        ai_suitability="live_watchlist",
        failed_targets=failed_targets,
        unsupported_targets=unsupported_targets,
        warnings=warnings,
        errors=errors
    )

if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2, ensure_ascii=False))
