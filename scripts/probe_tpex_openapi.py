import requests
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope

def probe():
    print("Probing TPEx OpenAPI...")
    url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
    headers = {"Accept": "application/json"}
    probe_id = f"tpex_openapi_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        status = response.status_code
        data = response.json()

        sample = data[0] if data and isinstance(data, list) else None
        normalized = None
        if sample:
            normalized = {
                "symbol": sample.get("SecuritiesCompanyCode"),
                "name": sample.get("CompanyName"),
                "price": sample.get("Close"),
                "change": sample.get("Change")
            }

        return generate_standard_envelope(
            probe_id=probe_id,
            source="TPEx_OpenAPI",
            source_type="official_openapi",
            contract_status="normalized_pass" if status == 200 and normalized else ("http_pass" if status == 200 else "failed"),
            http_status=status,
            url=url,
            headers_used=headers,
            raw_sample=sample,
            normalized_sample=normalized,
            freshness_status="eod_batch",
            delay_status="eod",
            risk_level="low",
            ai_suitability="historical_and_eod",
            unsupported_targets=["indices", "futures", "funds"]
        )
    except Exception as e:
        return generate_standard_envelope(
            probe_id=probe_id,
            source="TPEx_OpenAPI",
            source_type="official_openapi",
            contract_status="failed",
            http_status="Error",
            url=url,
            headers_used=headers,
            errors=[str(e)]
        )

if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2, ensure_ascii=False))
