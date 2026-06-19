import requests
from datetime import datetime, timezone
import os
import sys

# Ensure utility can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope
from probe_openapi_utils import safe_parse_float, safe_parse_int

def normalize_twse_openapi_row(row, retrieved_at_utc_dt):
    flags = []

    symbol = row.get("Code", "").strip() if row.get("Code") else ""
    if not symbol:
        flags.append("missing_symbol")

    name = row.get("Name", "").strip() if row.get("Name") else ""
    if not name:
        flags.append("missing_name")

    trade_date = row.get("Date")
    if not trade_date or str(trade_date).strip() == "":
        trade_date = None
        flags.append("missing_trade_date")
    else:
        trade_date = str(trade_date).strip()

    close_val = row.get("ClosingPrice")
    if close_val is None or str(close_val).strip() in ("", "-", "--", "---"):
        flags.append("missing_close")
        close_parsed = None
    else:
        close_parsed = safe_parse_float(close_val, flags, "close")

    normalized = {
        "source": "TWSE_OpenAPI",
        "source_type": "official_openapi",
        "official_status": "official_public_openapi",
        "market": "TWSE",
        "exchange": "TWSE",
        "symbol": symbol,
        "name": name,
        "trade_date": trade_date,
        "open": safe_parse_float(row.get("OpeningPrice"), flags, "open"),
        "high": safe_parse_float(row.get("HighestPrice"), flags, "high"),
        "low": safe_parse_float(row.get("LowestPrice"), flags, "low"),
        "close": close_parsed,
        "change": safe_parse_float(row.get("Change"), flags, "change"),
        "trade_volume": safe_parse_int(row.get("TradeVolume"), flags, "trade_volume"),
        "trade_value": safe_parse_float(row.get("TradeValue"), flags, "trade_value"),
        "transaction_count": safe_parse_int(row.get("Transaction"), flags, "transaction_count"),
        "currency": "TWD",
        "freshness_status": "eod_batch",
        "delay_status": "eod",
        "coverage_status": "observed_supported",
        "source_risk_flags": [
            "official_eod_reference_source",
            "not_intraday_live_feed",
            "not_execution_grade",
            "public_endpoint_rate_limits_apply",
            "schema_drift_possible"
        ],
        "data_quality_flags": flags,
        "raw_row": row,
        "unmapped_raw_fields": {},
        "retrieved_at_utc": retrieved_at_utc_dt.isoformat()
    }

    mapped_keys = {"Code", "Name", "Date", "OpeningPrice", "HighestPrice", "LowestPrice", "ClosingPrice", "Change", "TradeVolume", "TradeValue", "Transaction"}
    for k, v in row.items():
        if k not in mapped_keys:
            normalized["unmapped_raw_fields"][k] = v

    return normalized

def probe():
    print("Probing TWSE OpenAPI...")
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    headers = {"Accept": "application/json"}
    probe_id = f"twse_openapi_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        status = response.status_code
        data = response.json()

        sample = data[0] if data and isinstance(data, list) else None
        normalized = None
        if sample:
            retrieved_at_utc_dt = datetime.now(timezone.utc)
            normalized = normalize_twse_openapi_row(sample, retrieved_at_utc_dt)

        return generate_standard_envelope(
            probe_id=probe_id,
            source="TWSE_OpenAPI",
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
            source="TWSE_OpenAPI",
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
