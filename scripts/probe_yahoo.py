import requests
import time
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from datetime import timedelta
from probe_utils import generate_standard_envelope

KNOWN_UNSUPPORTED_YAHOO_PLACEHOLDERS = {
    "TX.TW",
    "FUNDA.TW",
}

def detect_yahoo_identity_mismatch(requested_symbol, raw_meta):
    """
    Pure helper to detect if Yahoo returned a completely different asset.
    Returns (bool, str) -> (is_mismatch, reason)
    """
    exchange_name = raw_meta.get("exchangeName", "")
    exchange_tz = raw_meta.get("exchangeTimezoneName", "") or raw_meta.get("timezone", "")
    returned_symbol = raw_meta.get("symbol", "")

    # 1. Check Japan OTC / Tokyo indicators
    if exchange_name == "JSD" or "Japan" in exchange_name:
        return True, f"Exchange is {exchange_name} (Japan OTC indicator)"
    if "Tokyo" in exchange_tz or "Japan" in exchange_tz:
        return True, f"Timezone is {exchange_tz} (Japan indicator)"

    # 2. Check name metadata for known mismatches
    name_fields = [
        raw_meta.get("shortName", ""),
        raw_meta.get("longName", ""),
        raw_meta.get("displayName", ""),
        raw_meta.get("name", ""),
        raw_meta.get("fullName", ""),
        raw_meta.get("fullExchangeName", "")
    ]
    for name_val in name_fields:
        if name_val and isinstance(name_val, str) and "For-side.com" in name_val:
            return True, "Name contains For-side.com (Japan OTC indicator)"

    # 3. Check suffix drop (e.g. requested 2330.TW but got 2330)
    # Don't apply to indices like ^TWII
    if requested_symbol.endswith(".TW") or requested_symbol.endswith(".TWO"):
        expected_base = requested_symbol.split(".")[0]
        if returned_symbol == expected_base:
            return True, f"Returned symbol {returned_symbol} dropped requested suffix from {requested_symbol}"

    return False, ""

def normalize_yahoo_chart_result(result_data, requested_symbol, retrieved_at_utc_dt):
    data_quality_flags = []

    if not result_data:
        return {
            "symbol": requested_symbol,
            "requested_symbol": requested_symbol,
            "source": "Yahoo_Finance",
            "source_type": "unofficial_api",
            "currency": None,
            "exchange_name": None,
            "exchange_timezone_name": None,
            "gmtoffset": None,
            "regular_market_price": None,
            "regular_market_time": None,
            "regular_market_time_utc": None,
            "regular_market_time_local": None,
            "chart_range": None,
            "data_granularity": None,
            "valid_ranges": [],
            "first_trade_date": None,
            "retrieved_at_utc": retrieved_at_utc_dt.isoformat(),
            "staleness_seconds": None,
            "freshness_status": "unknown",
            "delay_status": "unknown",
            "source_risk_flags": [
                "unofficial_source",
                "rate_limits_apply",
                "no_execution_guarantees"
            ],
            "data_quality_flags": ["empty_chart_result"],
            "coverage_status": "unknown",
            "series": {
                "timestamps": [],
                "timestamps_utc": [],
                "timestamps_local": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": [],
                "adjclose": []
            },
            "raw_meta": {},
            "unmapped_meta_fields": {}
        }

    meta = result_data.get("meta", {})
    if not meta:
        data_quality_flags.append("missing_meta")

    # Target Identity Validation
    is_mismatch, mismatch_reason = detect_yahoo_identity_mismatch(requested_symbol, meta)
    if is_mismatch:
        data_quality_flags.append("identity_mismatch")

    gmtoffset = meta.get("gmtoffset")

    regular_market_time = meta.get("regularMarketTime")
    if regular_market_time is None:
        data_quality_flags.append("missing_regular_market_time")
        regular_market_time_utc = None
        regular_market_time_local = None
        staleness_seconds = None
        delay_status = "unknown"
    else:
        try:
            dt_utc = datetime.fromtimestamp(regular_market_time, tz=timezone.utc)
            regular_market_time_utc = dt_utc.isoformat()
            staleness_seconds = max(0, int((retrieved_at_utc_dt - dt_utc).total_seconds()))

            if staleness_seconds < 300:
                delay_status = "realtime"
            elif staleness_seconds < 86400:
                delay_status = "delayed"
            else:
                delay_status = "stale"

            if gmtoffset is not None:
                dt_local = datetime.fromtimestamp(regular_market_time, tz=timezone(timedelta(seconds=gmtoffset)))
                regular_market_time_local = dt_local.isoformat()
            else:
                regular_market_time_local = regular_market_time_utc
                data_quality_flags.append("missing_gmtoffset_for_local_time")
        except Exception:
            data_quality_flags.append("malformed_regular_market_time")
            regular_market_time_utc = None
            regular_market_time_local = None
            staleness_seconds = None
            delay_status = "unknown"

    timestamps = result_data.get("timestamp", [])
    if not timestamps:
        data_quality_flags.append("missing_timestamp_array")

    timestamps_utc = []
    timestamps_local = []

    for ts in timestamps:
        if ts is not None:
            try:
                dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
                timestamps_utc.append(dt_utc.isoformat())
                if gmtoffset is not None:
                    dt_local = datetime.fromtimestamp(ts, tz=timezone(timedelta(seconds=gmtoffset)))
                    timestamps_local.append(dt_local.isoformat())
                else:
                    timestamps_local.append(dt_utc.isoformat())
            except Exception:
                timestamps_utc.append(None)
                timestamps_local.append(None)
                data_quality_flags.append("malformed_timestamp")
        else:
            timestamps_utc.append(None)
            timestamps_local.append(None)
            data_quality_flags.append("malformed_timestamp")

    if not gmtoffset and timestamps and "missing_gmtoffset_for_local_time" not in data_quality_flags:
         data_quality_flags.append("missing_gmtoffset_for_local_time")

    indicators = result_data.get("indicators", {})
    quote_blocks = indicators.get("quote", [])
    if not quote_blocks or not isinstance(quote_blocks, list):
        data_quality_flags.append("missing_quote_block")
        quote = {}
    else:
        quote = quote_blocks[0]

    open_arr = quote.get("open", [])
    high_arr = quote.get("high", [])
    low_arr = quote.get("low", [])
    close_arr = quote.get("close", [])
    volume_arr = quote.get("volume", [])

    if open_arr is None or not isinstance(open_arr, list):
        open_arr = []
    if high_arr is None or not isinstance(high_arr, list):
        high_arr = []
    if low_arr is None or not isinstance(low_arr, list):
        low_arr = []
    if close_arr is None or not isinstance(close_arr, list):
        close_arr = []
    if volume_arr is None or not isinstance(volume_arr, list):
        volume_arr = []

    if not open_arr: data_quality_flags.append("missing_open_array")
    if not high_arr: data_quality_flags.append("missing_high_array")
    if not low_arr: data_quality_flags.append("missing_low_array")
    if not close_arr: data_quality_flags.append("missing_close_array")
    if not volume_arr: data_quality_flags.append("missing_volume_array")

    # check array mismatches
    quote_lens = [len(x) for x in [open_arr, high_arr, low_arr, close_arr, volume_arr] if x]
    if quote_lens and any(l != len(timestamps) for l in quote_lens):
        data_quality_flags.append("timestamp_quote_length_mismatch")

    adjclose_blocks = indicators.get("adjclose", [])
    if not adjclose_blocks or not isinstance(adjclose_blocks, list):
        data_quality_flags.append("missing_adjclose_array")
        adjclose_arr = []
    else:
        adjclose_arr = adjclose_blocks[0].get("adjclose", [])
        if adjclose_arr is None or not isinstance(adjclose_arr, list):
            adjclose_arr = []
        if adjclose_arr and len(adjclose_arr) != len(timestamps):
            data_quality_flags.append("timestamp_adjclose_length_mismatch")

    raw_meta = meta.copy()

    mapped_keys = {"symbol", "regularMarketPrice", "regularMarketTime", "exchangeName", "exchangeTimezoneName", "timezone", "currency", "gmtoffset", "chartPreviousClose", "previousClose", "scale", "priceHint", "currentTradingPeriod", "tradingPeriods", "dataGranularity", "range", "validRanges", "firstTradeDate"}
    unmapped_meta_fields = {k: v for k, v in meta.items() if k not in mapped_keys}

    return {
        "symbol": meta.get("symbol", requested_symbol),
        "requested_symbol": requested_symbol,
        "source": "Yahoo_Finance",
        "source_type": "unofficial_api",
        "currency": meta.get("currency"),
        "exchange_name": meta.get("exchangeName"),
        "exchange_timezone_name": meta.get("exchangeTimezoneName") or meta.get("timezone"),
        "gmtoffset": gmtoffset,
        "regular_market_price": meta.get("regularMarketPrice"),
        "regular_market_time": regular_market_time,
        "regular_market_time_utc": regular_market_time_utc,
        "regular_market_time_local": regular_market_time_local,
        "chart_range": meta.get("range"),
        "data_granularity": meta.get("dataGranularity"),
        "valid_ranges": meta.get("validRanges", []),
        "first_trade_date": meta.get("firstTradeDate"),
        "retrieved_at_utc": retrieved_at_utc_dt.isoformat(),
        "staleness_seconds": staleness_seconds,
        "freshness_status": "realtime_candidate",
        "delay_status": delay_status,
        "source_risk_flags": [
            "unofficial_source",
            "rate_limits_apply",
            "no_execution_guarantees"
        ],
        "data_quality_flags": data_quality_flags,
        "coverage_status": "observed_supported",
        "series": {
            "timestamps": timestamps,
            "timestamps_utc": timestamps_utc,
            "timestamps_local": timestamps_local,
            "open": open_arr,
            "high": high_arr,
            "low": low_arr,
            "close": close_arr,
            "volume": volume_arr,
            "adjclose": adjclose_arr
        },
        "raw_meta": raw_meta,
        "unmapped_meta_fields": unmapped_meta_fields
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

    retrieved_at_utc_dt = datetime.now(timezone.utc)
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
                if not normalized_sample:
                    normalized_sample = normalize_yahoo_chart_result(result_data, sym, retrieved_at_utc_dt)
                    if "meta" in result_data:
                        raw_sample = result_data["meta"]
            else:
                errors.append(f"Parse failed or empty result for {sym}")
                failed_targets.append(sym)
            results.append({"symbol": sym, "status": status, "success": bool(success)})
        except requests.exceptions.RequestException as e:
            failed_targets.append(sym)
            errors.append(f"Network exception for {sym}: {str(e)}")
        except Exception as e:
            failed_targets.append(sym)
            errors.append(f"Exception for {sym}: {str(e)}")
        time.sleep(0.5)

    overall_success = success_count > 0

    staleness_seconds = None
    delay_status = "unknown"
    contract_status = "failed"
    is_usable_now = False

    if normalized_sample:
        staleness_seconds = normalized_sample.get("staleness_seconds")
        delay_status = normalized_sample.get("delay_status", "unknown")

        contract_status = "normalized_pass" if overall_success else "failed"
        is_usable_now = True

        if normalized_sample and "identity_mismatch" in normalized_sample.get("data_quality_flags", []):
            contract_status = "identity_mismatch"
            is_usable_now = False
            req_sym = normalized_sample.get("requested_symbol")
            if req_sym not in failed_targets:
                failed_targets.append(req_sym)

            # Re-run detect to get the specific reason for the error message
            _, mismatch_reason = detect_yahoo_identity_mismatch(req_sym, normalized_sample.get("raw_meta", {}))
            errors.append(f"Identity mismatch for {req_sym}: {mismatch_reason}")

    envelope = generate_standard_envelope(
        probe_id=probe_id,
        source="Yahoo_Finance",
        source_type="unofficial_api",
        contract_status=contract_status,
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

    if not is_usable_now:
        envelope["is_usable_now"] = False

    return envelope

if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2, ensure_ascii=False))
