import requests
import time
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope

def _is_missing_placeholder(val):
    return val is None or str(val).strip() in {"", "-", "--", "N/A", "null", "None"}


def _safe_float(val, data_quality_flags, field_name):
    if _is_missing_placeholder(val):
        return None
    try:
        return float(str(val).replace(",", ""))
    except (TypeError, ValueError):
        data_quality_flags.append(f"malformed_{field_name}")
        return None


def _safe_int(val, data_quality_flags, field_name):
    if _is_missing_placeholder(val):
        return None
    try:
        return int(float(str(val).replace(",", "")))
    except (TypeError, ValueError):
        data_quality_flags.append(f"malformed_{field_name}")
        return None


def _parse_ladder(price_str, vol_str, data_quality_flags, ladder_type):
    prices = []
    volumes = []

    if _is_missing_placeholder(price_str) and _is_missing_placeholder(vol_str):
        return prices, volumes

    p_tokens = [] if _is_missing_placeholder(price_str) else str(price_str).split("_")
    v_tokens = [] if _is_missing_placeholder(vol_str) else str(vol_str).split("_")

    while p_tokens and p_tokens[-1] == "":
        p_tokens.pop()
    while v_tokens and v_tokens[-1] == "":
        v_tokens.pop()

    length = max(len(p_tokens), len(v_tokens))
    if len(p_tokens) != len(v_tokens):
        data_quality_flags.append(f"mismatched_{ladder_type}_ladder_length")

    for i in range(length):
        p_tok = p_tokens[i] if i < len(p_tokens) else None
        v_tok = v_tokens[i] if i < len(v_tokens) else None
        level = {"level": i + 1, "price": None, "volume": None}

        if _is_missing_placeholder(p_tok) or str(p_tok).strip() in {"0", "0.0", "0.00", "0.0000"}:
            if p_tok is not None:
                data_quality_flags.append(f"invalid_{ladder_type}_price_level")
        else:
            try:
                level["price"] = float(str(p_tok).replace(",", ""))
            except (TypeError, ValueError):
                data_quality_flags.append(f"malformed_{ladder_type}_price_level")

        if _is_missing_placeholder(v_tok):
            pass
        else:
            try:
                level["volume"] = int(float(str(v_tok).replace(",", "")))
            except (TypeError, ValueError):
                data_quality_flags.append(f"malformed_{ladder_type}_volume_level")

        prices.append(level["price"])
        volumes.append(level["volume"])

    return prices, volumes


def _build_ladder(prices, volumes):
    return [
        {"level": i + 1, "price": price, "volume": volumes[i] if i < len(volumes) else None}
        for i, price in enumerate(prices)
    ]


def _classify_asset(row):
    it = row.get("it", "")
    c = row.get("c", "")
    ex = row.get("ex", "")
    ch = row.get("ch", "")

    if it == "02":
        return "etf"
    if it == "13":
        return "tdr"
    if it == "t" or c == "t00" or ch == "t00.tw":
        return "index"
    if c and str(c).isdigit() and ex in {"tse", "otc"}:
        return "stock_like"
    return "unknown"


def _parse_source_timestamp(source_date, source_time, source_time_ms, retrieved_at_utc_dt, data_quality_flags):
    if source_time_ms is not None:
        try:
            return datetime.fromtimestamp(source_time_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except (OSError, OverflowError, ValueError):
            data_quality_flags.append("malformed_source_timestamp")
            return None
    if source_date and source_time and len(str(source_date)) == 8 and not _is_missing_placeholder(source_time):
        try:
            taipei = timezone(timedelta(hours=8))
            dt = datetime.strptime(f"{source_date} {source_time}", "%Y%m%d %H:%M:%S").replace(tzinfo=taipei)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            data_quality_flags.append("malformed_source_date_time")
    elif _is_missing_placeholder(source_time):
        data_quality_flags.append("source_time_unavailable")
    return None


def _classify_freshness(staleness_seconds):
    if staleness_seconds is None:
        return "unknown", "unknown"
    if staleness_seconds <= 300:
        return "not_delayed_candidate", "live_candidate"
    if staleness_seconds <= 1200:
        return "delayed_candidate", "delayed"
    return "stale", "stale"


def normalize_twse_mis_row(raw_row, retrieved_at_utc_dt, top_level_telemetry=None):
    if top_level_telemetry is None:
        top_level_telemetry = {}
    if raw_row is None or not isinstance(raw_row, dict):
        return {
            "source_id": "twse_mis",
            "source_authority": "unofficial_frontend_source",
            "source_risk_flags": ["unofficial_source_risk", "fragile_frontend_contract", "not_official_realtime_api"],
            "symbol": None,
            "exchange": None,
            "instrument_type": "unknown",
            "name": None,
            "price": None,
            "open": None,
            "high": None,
            "low": None,
            "previous_close": None,
            "volume": None,
            "bid_ladder": [],
            "ask_ladder": [],
            "source_date": None,
            "source_time": None,
            "source_timestamp": None,
            "retrieved_at": retrieved_at_utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "staleness_seconds": None,
            "delay_status": "unknown",
            "freshness_status": "unknown",
            "price_semantics": "last_trade_price_when_available_else_null",
            "raw_fields_present": [],
            "data_quality_flags": ["malformed_row"],
            "normalization_version": "twse_mis_snapshot_v2_draft",
            "normalization_status": "invalid",
            "errors": ["raw_row_not_object"],
        }

    data_quality_flags = []
    errors = []
    instrument_type = _classify_asset(raw_row)

    symbol = raw_row.get("c")
    exchange = raw_row.get("ex")
    name = raw_row.get("n")
    channel_suffix = raw_row.get("ch")
    channel = f"{exchange}_{channel_suffix}" if exchange and channel_suffix else None
    if not symbol:
        data_quality_flags.append("missing_symbol")
        errors.append("missing_critical_symbol")
    if not exchange:
        data_quality_flags.append("missing_exchange")
        errors.append("missing_critical_exchange")

    price = _safe_float(raw_row.get("z"), data_quality_flags, "price")
    if price is None and _is_missing_placeholder(raw_row.get("z")):
        data_quality_flags.append("missing_price")
    previous_close = _safe_float(raw_row.get("y"), data_quality_flags, "previous_close")
    open_price = _safe_float(raw_row.get("o"), data_quality_flags, "open")
    high = _safe_float(raw_row.get("h"), data_quality_flags, "high")
    low = _safe_float(raw_row.get("l"), data_quality_flags, "low")
    volume = _safe_int(raw_row.get("v"), data_quality_flags, "volume")
    current_volume = _safe_int(raw_row.get("tv"), data_quality_flags, "current_volume")

    bid_prices, bid_volumes = _parse_ladder(raw_row.get("b"), raw_row.get("g"), data_quality_flags, "bid")
    ask_prices, ask_volumes = _parse_ladder(raw_row.get("a"), raw_row.get("f"), data_quality_flags, "ask")
    if instrument_type != "index" and not bid_prices and not ask_prices:
        data_quality_flags.append("missing_bid_ask")

    limit_up = _safe_float(raw_row.get("u"), data_quality_flags, "limit_up")
    limit_down = _safe_float(raw_row.get("w"), data_quality_flags, "limit_down")
    source_date = raw_row.get("d")
    source_time = raw_row.get("t")
    source_time_ms = _safe_int(raw_row.get("tlong"), data_quality_flags, "source_time_ms")
    source_timestamp = _parse_source_timestamp(source_date, source_time, source_time_ms, retrieved_at_utc_dt, data_quality_flags)

    staleness_seconds = None
    if source_timestamp:
        parsed_source_dt = datetime.strptime(source_timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        staleness_seconds = max(0, int(retrieved_at_utc_dt.timestamp()) - int(parsed_source_dt.timestamp()))
    delay_status, freshness_status = _classify_freshness(staleness_seconds)
    if freshness_status == "stale":
        data_quality_flags.append("stale_source_timestamp")
    elif freshness_status == "delayed":
        data_quality_flags.append("delayed_source_timestamp")

    if freshness_status == "stale":
        price_semantics = "stale_quote"
    elif freshness_status == "delayed":
        price_semantics = "delayed_quote"
    elif freshness_status == "live_candidate":
        price_semantics = "live_candidate"
    else:
        price_semantics = "unknown"

    retrieved_at = retrieved_at_utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    retrieved_at_taipei = (retrieved_at_utc_dt + timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    source_datetime_taipei = None
    if source_date and source_time and len(str(source_date)) == 8 and not _is_missing_placeholder(source_time):
        source_datetime_taipei = f"{str(source_date)[:4]}-{str(source_date)[4:6]}-{str(source_date)[6:]} {source_time}"

    change = None
    change_pct = None
    if price is not None and previous_close not in (None, 0):
        change = round(price - previous_close, 4)
        change_pct = round((change / previous_close) * 100, 4)

    if errors:
        normalization_status = "invalid"
    elif data_quality_flags:
        normalization_status = "partial"
    else:
        normalization_status = "ok"

    mapped_keys = {"c", "ex", "n", "ch", "z", "y", "o", "h", "l", "v", "tv", "b", "g", "a", "f", "u", "w", "d", "t", "tlong", "ot", "%"}
    source_risk_flags = ["unofficial_source_risk", "fragile_frontend_contract", "not_official_realtime_api", "not_production_current_market_state_by_itself"]

    normalized_row = {
        "source_id": "twse_mis",
        "source_authority": "unofficial_frontend_source",
        "source_risk_flags": source_risk_flags,
        "symbol": symbol,
        "exchange": exchange,
        "instrument_type": instrument_type,
        "name": name,
        "price": price,
        "open": open_price,
        "high": high,
        "low": low,
        "previous_close": previous_close,
        "volume": volume,
        "bid_ladder": _build_ladder(bid_prices, bid_volumes),
        "ask_ladder": _build_ladder(ask_prices, ask_volumes),
        "source_date": source_date,
        "source_time": source_time,
        "source_timestamp": source_timestamp,
        "retrieved_at": retrieved_at,
        "staleness_seconds": staleness_seconds,
        "delay_status": delay_status,
        "freshness_status": freshness_status,
        "price_semantics": price_semantics,
        "price_semantics_detail": "last_trade_price_when_available_else_null; unofficial frontend field z observed only",
        "raw_fields_present": sorted(raw_row.keys()),
        "data_quality_flags": sorted(set(data_quality_flags)),
        "normalization_version": "twse_mis_snapshot_v2_draft",
        "normalization_status": normalization_status,
        "errors": errors,
        # Backward-compatible v1 names retained for existing reports/tests.
        "channel": channel,
        "channel_suffix": channel_suffix,
        "asset_type_candidate": instrument_type,
        "last_price": price,
        "cumulative_volume": volume,
        "current_volume": current_volume,
        "bid_prices": bid_prices,
        "bid_volumes": bid_volumes,
        "ask_prices": ask_prices,
        "ask_volumes": ask_volumes,
        "limit_up": None if instrument_type == "index" else limit_up,
        "limit_down": None if instrument_type == "index" else limit_down,
        "source_time_ms": source_time_ms,
        "source_datetime_taipei": source_datetime_taipei,
        "regular_trade_time": source_time,
        "snapshot_time": raw_row.get("%"),
        "alternate_session_time": raw_row.get("ot"),
        "query_sys_time": top_level_telemetry.get("queryTime", {}).get("sysTime") if isinstance(top_level_telemetry.get("queryTime"), dict) else None,
        "retrieved_at_utc": retrieved_at,
        "retrieved_at_taipei": retrieved_at_taipei,
        "raw_identity": f"{exchange}_{symbol}" if exchange and symbol else None,
        "unmapped_raw_fields": {k: v for k, v in raw_row.items() if k not in mapped_keys},
    }
    return normalized_row


def probe(symbols=None):
    if not symbols:
        symbols = ["tse_2330.tw", "tse_0050.tw", "tse_t00.tw"]
    print(f"Probing TWSE MIS for {symbols}...")

    retrieved_at_utc_dt = datetime.now(timezone.utc)
    probe_id = f"twse_mis_{retrieved_at_utc_dt.strftime('%Y%m%d_%H%M%S')}"
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
            top_level_telemetry = {
                "queryTime": data.get("queryTime"),
                "userDelay": data.get("userDelay"),
                "cachedAlive": data.get("cachedAlive"),
                "rtcode": data.get("rtcode"),
                "rtmessage": data.get("rtmessage"),
                "exKey": data.get("exKey"),
                "referer": data.get("referer"),
            }

            raw_sample = data["msgArray"]
            normalized_rows = [normalize_twse_mis_row(row, retrieved_at_utc_dt, top_level_telemetry=top_level_telemetry) for row in raw_sample]
            normalized_sample = normalized_rows

            # Use the first row's staleness for the envelope level staleness metric to match older behavior
            first_row = normalized_rows[0]
            staleness_seconds = first_row.get("staleness_seconds")
            delay_status = first_row.get("delay_status")

            # Form raw evidence
            raw_evidence = {
                "_total_found": len(data.get("msgArray", [])),
                "sample": raw_sample,
                "telemetry": top_level_telemetry
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
            raw_sample=raw_evidence if success else None,
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
