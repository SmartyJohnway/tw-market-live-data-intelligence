import requests
import time
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope

def _safe_float(val, data_quality_flags, field_name):
    if val is None or val == "" or val == "-":
        return None
    try:
        return float(val)
    except ValueError:
        data_quality_flags.append(f"malformed_{field_name}")
        return None

def _safe_int(val, data_quality_flags, field_name):
    if val is None or val == "" or val == "-":
        return None
    try:
        return int(val)
    except ValueError:
        data_quality_flags.append(f"malformed_{field_name}")
        return None

def _parse_ladder(price_str, vol_str, data_quality_flags, ladder_type):
    prices = []
    volumes = []

    if price_str is None and vol_str is None:
        return prices, volumes

    p_tokens = price_str.split("_") if price_str else []
    v_tokens = vol_str.split("_") if vol_str else []

    # Remove trailing empty tokens caused by final underscore
    if p_tokens and p_tokens[-1] == "":
        p_tokens.pop()
    if v_tokens and v_tokens[-1] == "":
        v_tokens.pop()

    length = max(len(p_tokens), len(v_tokens))
    if len(p_tokens) != len(v_tokens):
        data_quality_flags.append(f"mismatched_{ladder_type}_ladder_length")

    for i in range(length):
        p_tok = p_tokens[i] if i < len(p_tokens) else None
        v_tok = v_tokens[i] if i < len(v_tokens) else None

        if p_tok in ("-", "", "0", "0.0000", None):
            prices.append(None)
            volumes.append(None)
            if p_tok is not None:
                data_quality_flags.append(f"invalid_{ladder_type}_price_level")
        else:
            try:
                price_val = float(p_tok)
                prices.append(price_val)
            except ValueError:
                prices.append(None)
                volumes.append(None)
                data_quality_flags.append(f"malformed_{ladder_type}_price_level")
                continue

            if v_tok in ("-", "", None):
                volumes.append(None)
            else:
                try:
                    vol_val = int(v_tok)
                    volumes.append(vol_val)
                except ValueError:
                    volumes.append(None)
                    data_quality_flags.append(f"malformed_{ladder_type}_volume_level")

    return prices, volumes

def _classify_asset(row):
    it = row.get("it", "")
    c = row.get("c", "")
    ex = row.get("ex", "")

    if it == "02":
        return "etf"
    if it == "13":
        return "tdr"
    if it == "t" or c == "t00":
        return "index"

    # Heuristic for stock_like
    if c.isdigit() and ex in {"tse", "otc"}:
        return "stock_like"

    return "unknown"

def normalize_twse_mis_row(raw_row, retrieved_at_utc_dt, top_level_telemetry=None):
    if top_level_telemetry is None:
        top_level_telemetry = {}

    data_quality_flags = []

    # Asset type
    asset_type = _classify_asset(raw_row)

    # Parse core fields
    symbol = raw_row.get("c")
    exchange = raw_row.get("ex")
    name = raw_row.get("n")
    channel_suffix = raw_row.get("ch")
    channel = f"{exchange}_{channel_suffix}" if exchange and channel_suffix else None

    last_price = _safe_float(raw_row.get("z"), data_quality_flags, "last_price")
    if last_price is None and raw_row.get("z") == "-":
        data_quality_flags.append("missing_last_price")

    previous_close = _safe_float(raw_row.get("y"), data_quality_flags, "previous_close")
    open_price = _safe_float(raw_row.get("o"), data_quality_flags, "open")
    high = _safe_float(raw_row.get("h"), data_quality_flags, "high")
    low = _safe_float(raw_row.get("l"), data_quality_flags, "low")

    change = None
    change_pct = None
    if last_price is not None and previous_close is not None and previous_close != 0:
        change = round(last_price - previous_close, 4)
        change_pct = round((change / previous_close) * 100, 4)

    cumulative_volume = _safe_int(raw_row.get("v"), data_quality_flags, "cumulative_volume")
    current_volume = _safe_int(raw_row.get("tv"), data_quality_flags, "current_volume")

    bid_prices, bid_volumes = _parse_ladder(raw_row.get("b"), raw_row.get("g"), data_quality_flags, "bid")
    ask_prices, ask_volumes = _parse_ladder(raw_row.get("a"), raw_row.get("f"), data_quality_flags, "ask")

    # Index rows typically lack bid/ask, don't flag if it's an index
    if asset_type != "index" and not bid_prices and not ask_prices:
        data_quality_flags.append("missing_bid_ask")

    limit_up = _safe_float(raw_row.get("u"), data_quality_flags, "limit_up")
    limit_down = _safe_float(raw_row.get("w"), data_quality_flags, "limit_down")

    # Timestamps
    source_date = raw_row.get("d")
    source_time = raw_row.get("t")
    source_time_ms_str = raw_row.get("tlong")
    source_time_ms = _safe_int(source_time_ms_str, data_quality_flags, "source_time_ms")

    source_datetime_taipei = None
    if source_date and source_time:
        if len(source_date) == 8:
            source_datetime_taipei = f"{source_date[:4]}-{source_date[4:6]}-{source_date[6:]} {source_time}"

    # Parse query_sys_time from top level telemetry
    query_sys_time = top_level_telemetry.get("queryTime", {}).get("sysTime") if isinstance(top_level_telemetry.get("queryTime"), dict) else None

    # Calculate staleness
    staleness_seconds = None
    if source_time_ms is not None:
        source_ts_sec = source_time_ms // 1000
        current_ts_sec = int(retrieved_at_utc_dt.timestamp())
        staleness_seconds = current_ts_sec - source_ts_sec
        if staleness_seconds < 0:
            staleness_seconds = 0

    freshness_status = "realtime_candidate"
    delay_status = "unknown"
    if staleness_seconds is not None:
        if staleness_seconds < 300:
            delay_status = "realtime"
        elif staleness_seconds < 86400:
            delay_status = "delayed"
        else:
            delay_status = "stale"
            freshness_status = "stale"

    retrieved_at_utc = retrieved_at_utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    retrieved_at_taipei = (retrieved_at_utc_dt + timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

    source_risk_flags = [
        "unofficial_endpoint",
        "observed_contract",
        "not_official_realtime_api"
    ]

    # Optional fields mapping
    alternate_session_time = raw_row.get("ot")
    regular_trade_time = raw_row.get("t")
    snapshot_time = raw_row.get("%")

    # Map normalized fields
    normalized_row = {
        "symbol": symbol,
        "exchange": exchange,
        "name": name,
        "channel": channel,
        "channel_suffix": channel_suffix,
        "asset_type_candidate": asset_type,
        "last_price": last_price,
        "previous_close": previous_close,
        "open": open_price,
        "high": high,
        "low": low,
        "change": change,
        "change_pct": change_pct,
        "cumulative_volume": cumulative_volume,
        "current_volume": current_volume,
        "bid_prices": bid_prices,
        "bid_volumes": bid_volumes,
        "ask_prices": ask_prices,
        "ask_volumes": ask_volumes,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "source_date": source_date,
        "source_time": source_time,
        "source_time_ms": source_time_ms,
        "source_datetime_taipei": source_datetime_taipei,
        "regular_trade_time": regular_trade_time,
        "snapshot_time": snapshot_time,
        "alternate_session_time": alternate_session_time,
        "query_sys_time": query_sys_time,
        "retrieved_at_utc": retrieved_at_utc,
        "retrieved_at_taipei": retrieved_at_taipei,
        "staleness_seconds": staleness_seconds,
        "freshness_status": freshness_status,
        "delay_status": delay_status,
        "data_quality_flags": data_quality_flags,
        "source_risk_flags": source_risk_flags,
        "raw_identity": f"{exchange}_{symbol}" if exchange and symbol else None
    }

    # Strip some specific fields for index type as per requirements if they are empty
    if asset_type == "index":
        if not bid_prices:
            normalized_row["bid_prices"] = []
        if not bid_volumes:
            normalized_row["bid_volumes"] = []
        if not ask_prices:
            normalized_row["ask_prices"] = []
        if not ask_volumes:
            normalized_row["ask_volumes"] = []
        normalized_row["limit_up"] = None
        normalized_row["limit_down"] = None

    # Track unmapped fields
    mapped_keys = {
        "c", "ex", "n", "ch", "z", "y", "o", "h", "l", "v", "tv",
        "b", "g", "a", "f", "u", "w", "d", "t", "tlong",
        "ot", "%"
    }
    unmapped_raw_fields = {k: v for k, v in raw_row.items() if k not in mapped_keys}
    normalized_row["unmapped_raw_fields"] = unmapped_raw_fields

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
