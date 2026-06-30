from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WATCHLIST_PATH = REPO_ROOT / "config/m5k_default_watchlist.json"
STATE_DIR = REPO_ROOT / "research/live_observation_runs/m5k"
LATEST_OBSERVATION_PATH = STATE_DIR / "latest_observation.json"
MAX_M5K_TARGETS = 25
FORBIDDEN_KEYS = {"buy", "sell", "hold", "target_price", "target price", "recommendation", "ranking", "rank", "broker", "order", "raw_fields_sample", "raw_payload", "response_sample"}
SUPPORTED_MARKETS = {"twse", "tpex", "otc", "taifex"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def governance() -> dict[str, Any]:
    return {
        "layer": "M5K Level 2 Live Observation Layer",
        "canonical": False,
        "m5f_modified": False,
        "promote_to_m5f": False,
        "network_free_startup": True,
        "explicit_execution_only": True,
        "bounded_watchlist_only": True,
        "full_market_scan": False,
        "polling": False,
        "scheduler": False,
        "trading_signal": False,
        "recommendation": False,
        "caveats": [
            "live_observation_not_canonical",
            "not_realtime_guaranteed",
            "freshness_must_be_displayed",
            "source_may_be_delayed_or_unavailable",
            "no_trading_signal",
        ],
    }


def iter_instruments(watchlist: dict[str, Any], *, include_disabled: bool = False) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for category in watchlist.get("categories", []):
        for item in category.get("instruments", []):
            if item.get("enabled", True) is False and not include_disabled:
                continue
            merged = dict(item)
            merged.setdefault("enabled", True)
            merged.setdefault("category_id", category.get("category_id"))
            merged.setdefault("category_label", category.get("label"))
            out.append(merged)
    return out


def _reject_forbidden_keys(value: Any, path: str = "<root>") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                errors.append(f"forbidden_field:{path}.{key}")
            errors.extend(_reject_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            errors.extend(_reject_forbidden_keys(child, f"{path}[{idx}]"))
    return errors


def validate_watchlist(watchlist: dict[str, Any], *, max_targets: int = MAX_M5K_TARGETS) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(watchlist, dict):
        return {"valid": False, "errors": ["watchlist_must_be_object"], "warnings": []}
    if watchlist.get("schema_version") != "m5k_watchlist.v1":
        errors.append("schema_version_must_be_m5k_watchlist_v1")
    categories = watchlist.get("categories")
    if not isinstance(categories, list) or not categories:
        errors.append("categories_required")
    instruments = iter_instruments(watchlist, include_disabled=True)
    if not instruments:
        errors.append("instruments_required")
    if len(instruments) > max_targets:
        errors.append("target_count_exceeds_bound")
    seen: set[str] = set()
    symbol_re = re.compile(r"^[A-Z0-9._-]{1,20}$")
    for item in instruments:
        symbol = item.get("symbol")
        if not isinstance(symbol, str) or not symbol_re.match(symbol):
            errors.append(f"invalid_symbol:{symbol}")
            continue
        if symbol in seen:
            errors.append(f"duplicate_symbol:{symbol}")
        seen.add(symbol)
        if item.get("enabled", True) not in {True, False}:
            errors.append(f"invalid_enabled_flag:{symbol}")
        if not isinstance(item.get("preferred_sources", []), list) or not item.get("preferred_sources"):
            warnings.append(f"missing_preferred_sources:{symbol}")
        market = item.get("market")
        if market not in SUPPORTED_MARKETS:
            errors.append(f"invalid_or_missing_market:{symbol}")
    errors.extend(_reject_forbidden_keys(watchlist))
    return {"valid": not errors, "errors": errors, "warnings": warnings, "target_count": len(instruments), "symbols": [i.get("symbol") for i in instruments]}


def conversation_handoff_from_watchlist(watchlist: dict[str, Any]) -> dict[str, Any]:
    validation = validate_watchlist(watchlist)
    return {
        "schema_version": "m5k_conversation_handoff.v1",
        "created_at_utc": utc_now(),
        "handoff_type": "ai_watchlist_to_frontend_to_live_observation",
        "watchlist": watchlist,
        "validation": validation,
        "governance": governance(),
        "frontend_actions": ["import_watchlist", "edit_watchlist", "export_watchlist", "execute_bounded_live_observation"],
    }


def source_plan_for_instrument(instrument: dict[str, Any]) -> dict[str, Any]:
    """Return the no-network M5K source route for one instrument."""
    symbol = instrument["symbol"]
    typ = instrument.get("instrument_type", "unknown")
    market = instrument.get("market")
    base = {
        "symbol": symbol,
        "display_symbol": instrument.get("display_symbol", symbol),
        "instrument_type": typ,
        "market": market,
        "category_id": instrument.get("category_id"),
        "category_label": instrument.get("category_label"),
    }
    if typ == "futures" or market == "taifex" or symbol == "TX":
        contract_code = instrument.get("contract_code", "TXF")
        contract_selector = instrument.get("contract_selector", "front_month")
        return {**base, "source": "TAIFEX", "adapter_id": "taifex_mis_tx_futures_quote", "source_type": "official_browser_json_endpoint", "status": "planned", "route": "taifex_mis_getQuoteList", "url": "https://mis.taifex.com.tw/futures/api/getQuoteList", "method": "POST", "contract_code": contract_code, "contract_selector": contract_selector, "request_body": {"MarketType": "0", "SymbolType": "F", "KindID": "1", "CID": contract_code}}
    if typ == "index" or symbol == "TAIEX":
        return {**base, "source": "TWSE_MIS", "adapter_id": "twse_mis_taiex_index_quote", "source_type": "official_browser_json_endpoint_candidate", "ex_ch": "tse_t00.tw", "status": "planned"}
    if market in {"tpex", "otc"}:
        return {**base, "source": "TWSE_MIS", "adapter_id": "twse_mis_equity_etf_quote", "source_type": "official_browser_json_endpoint_candidate", "ex_ch": f"otc_{symbol}.tw", "status": "planned"}
    if market == "twse":
        return {**base, "source": "TWSE_MIS", "adapter_id": "twse_mis_equity_etf_quote", "source_type": "official_browser_json_endpoint_candidate", "ex_ch": f"tse_{symbol}.tw", "status": "planned"}
    return {**base, "source": None, "status": "unsupported_market", "reason": "instrument market must be one of twse, tpex, otc, taifex"}


def plan_live_observation(watchlist: dict[str, Any]) -> dict[str, Any]:
    validation = validate_watchlist(watchlist)
    instruments = iter_instruments(watchlist) if isinstance(watchlist, dict) else []
    plans = [source_plan_for_instrument(i) for i in instruments if isinstance(i, dict) and isinstance(i.get("symbol"), str)]
    return {
        "schema_version": "m5k_live_observation_plan.v1",
        "generated_at_utc": utc_now(),
        "watchlist_id": watchlist.get("watchlist_id") if isinstance(watchlist, dict) else None,
        "validation": validation,
        "governance": governance() | {"network_calls": False, "artifact_writes": False, "plan_only": True},
        "planned_routes": plans,
        "request_plan": {
            "method": "GET",
            "bounded_symbols": [plan["symbol"] for plan in plans],
            "max_targets": MAX_M5K_TARGETS,
            "network_calls": False,
        },
    }



def _parse_taifex_price(value: Any) -> float | None:
    if value in (None, "", "NULL", "-"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _taifex_timestamp(date_text: str, time_text: str) -> str:
    if len(date_text) == 8 and len(time_text) == 6:
        return f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:8]}T{time_text[:2]}:{time_text[2:4]}:{time_text[4:6]}+08:00"
    return " ".join(part for part in [date_text, time_text] if part)


def _taifex_contract_month(item: dict[str, Any]) -> str | None:
    display = str(item.get("DispEName") or "")
    # TAIFEX MIS displays TX076 as July 2026 on 2026-06-29: TX + MM + Y.
    if display.startswith("TX") and len(display) >= 5 and display[2:5].isdigit():
        month = int(display[2:4])
        year = 2020 + int(display[4])
        if 1 <= month <= 12:
            return f"{year:04d}{month:02d}"
    cname = str(item.get("DispCName") or "")
    digits = "".join(ch for ch in cname if ch.isdigit())
    if len(digits) >= 3:
        month = int(digits[-3:-1])
        year = 2020 + int(digits[-1])
        if 1 <= month <= 12:
            return f"{year:04d}{month:02d}"
    return None


def _select_taifex_tx_contract(quote_list: list[dict[str, Any]], selector: str = "front_month") -> dict[str, Any] | None:
    contracts = [q for q in quote_list if str(q.get("SymbolID", "")).startswith("TXF") and str(q.get("SymbolID", "")).endswith("-F") and _taifex_contract_month(q)]
    if not contracts:
        return None
    if selector not in {"front_month", "nearest_month"}:
        return None
    return sorted(contracts, key=lambda q: (_taifex_contract_month(q) or "999999", str(q.get("SymbolID", ""))))[0]


def _parse_taifex_tx_item(item: dict[str, Any], instrument: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    symbol = instrument["symbol"]
    value = _parse_taifex_price(item.get("CLastPrice") or item.get("SettlementPrice") or item.get("CRefPrice"))
    source_ts = _taifex_timestamp(str(item.get("CDate") or ""), str(item.get("CTime") or ""))
    retrieved_dt = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
    freshness = "unknown"
    delay_seconds = None
    if source_ts and "+08:00" in source_ts:
        source_dt = datetime.fromisoformat(source_ts).astimezone(timezone.utc)
        delay_seconds = max(0, int((retrieved_dt - source_dt).total_seconds()))
        freshness = "fresh" if delay_seconds <= 900 else "stale_or_closed_session"
    return {
        "symbol": symbol,
        "display_symbol": instrument.get("display_symbol", symbol),
        "contract": item.get("SymbolID"),
        "contract_month": _taifex_contract_month(item),
        "contract_selector": instrument.get("contract_selector", "front_month"),
        "category_id": instrument.get("category_id"),
        "instrument_type": instrument.get("instrument_type"),
        "status": "ok" if value is not None else "missing_value",
        "source": "TAIFEX",
        "adapter_id": "taifex_mis_tx_futures_quote",
        "market": "taifex",
        "source_type": "official_browser_json_endpoint",
        "price_like_value": value,
        "value": value,
        "price_semantics": "last_trade_price_or_settlement_fallback_as_reported_by_taifex_mis",
        "source_timestamp": source_ts,
        "retrieved_at_utc": retrieved_at,
        "freshness_assessment": freshness,
        "delay_status": "delay_seconds_measured_from_source_timestamp_not_exchange_realtime_sla",
        "delay_seconds": delay_seconds,
        "source_status": item.get("Status"),
        "normalization": {"product_code": "TXF", "selector": "front_month", "source_contract_symbol": item.get("SymbolID"), "source_display_name": item.get("DispEName")},
        "caveats": governance()["caveats"] + ["official_browser_endpoint_not_openapi_contract", "no_realtime_sla_verified"],
    }


def fetch_taifex_tx_observation(instrument: dict[str, Any], retrieved_at: str, *, timeout: int = 12) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    body = {"MarketType": "0", "SymbolType": "F", "KindID": "1", "CID": instrument.get("contract_code", "TXF")}
    url = "https://mis.taifex.com.tw/futures/api/getQuoteList"
    headers = {"User-Agent": "Mozilla/5.0 tw-market-m5k-live-observation/1.0", "Accept": "application/json", "Content-Type": "application/json;charset=UTF-8", "Referer": "https://mis.taifex.com.tw/futures/RegularSession/EquityIndices/FuturesDomestic", "Origin": "https://mis.taifex.com.tw"}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status_code = resp.status
        data = json.loads(raw)
        quote_list = data.get("RtData", {}).get("QuoteList", [])
        item = _select_taifex_tx_contract([q for q in quote_list if isinstance(q, dict)], instrument.get("contract_selector", "front_month"))
        evidence = {"source": "TAIFEX", "url": url, "method": "POST", "request_body": body, "headers_required": list(headers), "status_code": status_code, "response_format": "application/json", "quote_count": data.get("RtData", {}).get("QuoteCount"), "rt_code": data.get("RtCode"), "sample_symbols": [q.get("SymbolID") for q in quote_list[:4] if isinstance(q, dict)], "selected_symbol": item.get("SymbolID") if item else None}
        if not item:
            return None, evidence | {"status": "no_tx_contract_selected"}
        return _parse_taifex_tx_item(item, instrument, retrieved_at), evidence | {"status": "accepted_for_bounded_observation"}
    except Exception as exc:
        return None, {"source": "TAIFEX", "url": url, "method": "POST", "request_body": body, "status": "request_failed", "reason": str(exc)}

def _parse_mis_numeric(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _select_mis_price(item: dict[str, Any]) -> tuple[float | None, str | None]:
    """Prefer numeric last price z, then numeric reference/previous value y."""
    z_price = _parse_mis_numeric(item.get("z"))
    if z_price is not None:
        return z_price, "z"
    y_price = _parse_mis_numeric(item.get("y"))
    if y_price is not None:
        return y_price, "y"
    return None, None


def _parse_mis_source_timestamp(item: dict[str, Any], retrieved_at: str) -> tuple[str | None, int | None, list[str]]:
    flags: list[str] = []
    tlong = item.get("tlong")
    if tlong not in (None, "", "-"):
        try:
            source_dt = datetime.fromtimestamp(int(str(tlong)) / 1000, tz=timezone.utc)
            retrieved_dt = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
            return source_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), max(0, int((retrieved_dt - source_dt).total_seconds())), flags
        except (TypeError, ValueError, OSError):
            flags.append("malformed_source_timestamp")
    source_date = str(item.get("d") or "")
    source_time = str(item.get("t") or "")
    if source_date and source_time and source_date != "-" and source_time != "-":
        try:
            source_dt = datetime.strptime(f"{source_date} {source_time}", "%Y%m%d %H:%M:%S").replace(tzinfo=timezone.utc)
            # raw d+t are Taipei exchange-local time; convert to UTC by attaching +08 manually.
            source_dt = source_dt.replace(tzinfo=timezone(timedelta(hours=8))).astimezone(timezone.utc)
            retrieved_dt = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
            return source_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), max(0, int((retrieved_dt - source_dt).total_seconds())), flags
        except ValueError:
            flags.append("malformed_source_date_time")
    flags.append("source_time_unavailable")
    return None, None, flags


def _parse_mis_item(item: dict[str, Any], instrument: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    symbol = instrument["symbol"]
    price, price_source_field = _select_mis_price(item)
    source_timestamp, delay_seconds, timestamp_flags = _parse_mis_source_timestamp(item, retrieved_at)
    data_quality_flags = list(timestamp_flags)
    caveats = governance()["caveats"] + ["unofficial_source_risk", "fragile_frontend_contract", "not_official_realtime_api"]
    if price_source_field == "z":
        status = "ok"
        price_semantics = "last_or_current_quote_as_reported_by_source"
    elif price_source_field == "y":
        status = "reference_value_only"
        price_semantics = "previous_close_or_reference_fallback_not_current_trade"
        data_quality_flags.append("current_z_unavailable_used_y_reference")
        caveats.append("current_z_unavailable_y_reference_fallback_not_current_trade")
    else:
        status = "value_unavailable"
        price_semantics = "value_unavailable_no_numeric_z_or_y"
        data_quality_flags.append("missing_price")
    source_risk_flags = ["unofficial_source_risk", "fragile_frontend_contract", "not_official_realtime_api"]
    return {
        "symbol": symbol,
        "display_symbol": instrument.get("display_symbol", symbol),
        "category_id": instrument.get("category_id"),
        "instrument_type": instrument.get("instrument_type"),
        "status": status,
        "source": "TWSE_MIS",
        "adapter_id": instrument.get("adapter_id") or ("twse_mis_taiex_index_quote" if symbol == "TAIEX" or instrument.get("instrument_type") == "index" else "twse_mis_equity_etf_quote"),
        "market": instrument.get("market"),
        "source_type": "official_browser_json_endpoint_candidate",
        "price_like_value": price,
        "price_source_field": price_source_field,
        "price_semantics": price_semantics,
        "source_timestamp": source_timestamp,
        "retrieved_at_utc": retrieved_at,
        "freshness_assessment": "current observation candidate; realtime status not guaranteed by M5K",
        "delay_status": "not_realtime_guaranteed",
        "delay_seconds": delay_seconds,
        "staleness_seconds": delay_seconds,
        "data_quality_flags": sorted(set(data_quality_flags)),
        "source_risk_flags": source_risk_flags,
        "caveats": sorted(set(caveats)),
    }


def execute_live_observation(watchlist: dict[str, Any], *, write_latest: bool = True, timeout: int = 12) -> dict[str, Any]:
    validation = validate_watchlist(watchlist)
    retrieved_at = utc_now()
    payload: dict[str, Any] = {
        "schema_version": "m5k_live_observation.v1",
        "generated_at_utc": retrieved_at,
        "watchlist_id": watchlist.get("watchlist_id"),
        "validation": validation,
        "governance": governance(),
        "request": {"method": "GET", "bounded_symbols": [], "max_targets": MAX_M5K_TARGETS},
        "observations": [],
        "failures": [],
        "source_investigation_notes": [],
    }
    if not validation["valid"]:
        payload["status"] = "failed_closed_invalid_watchlist"
        return payload

    instruments = iter_instruments(watchlist)
    plans = [source_plan_for_instrument(i) | {"instrument": i} for i in instruments]
    payload["planned_routes"] = [{k: v for k, v in p.items() if k != "instrument"} for p in plans]
    payload["request"]["bounded_symbols"] = [p["symbol"] for p in plans]
    taifex_plans = [p for p in plans if p.get("adapter_id") == "taifex_mis_tx_futures_quote"]
    for plan in taifex_plans:
        obs, evidence = fetch_taifex_tx_observation(plan["instrument"] | {"adapter_id": plan.get("adapter_id")}, retrieved_at, timeout=timeout)
        if evidence:
            payload["source_investigation_notes"].append(evidence)
        if obs and obs.get("status") == "ok":
            payload["observations"].append(obs)
        else:
            payload["failures"].append({"symbol": plan["symbol"], "source": "TAIFEX", "adapter_id": "taifex_mis_tx_futures_quote", "status": "failed" if not evidence else evidence.get("status", "failed"), "reason": (evidence or {}).get("reason", "no_supported_tx_observation"), "investigation_summary": evidence, "recommended_next_step": "Use TAIFEX MIS getQuoteList with TXF and front-month normalization, or apply for licensed TAIFEX market data for SLA-backed production usage."})

    mis_channels = [p["ex_ch"] for p in plans if p.get("source") == "TWSE_MIS" and p.get("ex_ch")]
    mis_by_channel: dict[str, dict[str, Any]] = {}
    if mis_channels:
        query = urllib.parse.urlencode({"ex_ch": "|".join(mis_channels), "json": "1", "delay": "0"})
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?{query}"
        payload["request"].update({"url": url, "headers": {"User-Agent": "Mozilla/5.0 tw-market-m5k-live-observation/1.0", "Referer": "https://mis.twse.com.tw/stock/fibest.jsp"}})
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 tw-market-m5k-live-observation/1.0", "Referer": "https://mis.twse.com.tw/stock/fibest.jsp"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
                payload["request"]["status_code"] = resp.status
            data = json.loads(body.strip())
            msg_array = data.get("msgArray", [])
            rtcode = str(data.get("rtcode") or data.get("rtCode") or "")
            if rtcode == "9999" or not isinstance(msg_array, list):
                raise ValueError(f"batch_request_failed:rtcode={rtcode or 'missing'}")
            for item in msg_array:
                if isinstance(item, dict):
                    mis_key = str(item.get("key") or "").rsplit("_", 1)[0] or str(item.get("ch") or "")
                    mis_by_channel[mis_key] = item
            payload["source_investigation_notes"].append({"source": "TWSE_MIS", "status": "accepted_for_bounded_observation", "batch_request_status": "accepted", "sample_retained": False})
        except Exception as exc:
            payload["source_investigation_notes"].append({"source": "TWSE_MIS", "status": "batch_request_failed", "reason": str(exc), "fallback": "individual_bounded_requests", "sample_retained": False})
            for ch in mis_channels:
                single_url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?{urllib.parse.urlencode({'ex_ch': ch, 'json': '1', 'delay': '0'})}"
                try:
                    req = urllib.request.Request(single_url, headers={"User-Agent": "Mozilla/5.0 tw-market-m5k-live-observation/1.0", "Referer": "https://mis.twse.com.tw/stock/fibest.jsp"})
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        body = resp.read().decode("utf-8", "replace")
                    data = json.loads(body.strip())
                    for item in data.get("msgArray", []):
                        if isinstance(item, dict):
                            mis_key = str(item.get("key") or "").rsplit("_", 1)[0] or str(item.get("ch") or "")
                            mis_by_channel[mis_key] = item
                except Exception:
                    continue
    for plan in plans:
        instrument = plan["instrument"]
        if plan.get("adapter_id") == "taifex_mis_tx_futures_quote":
            continue
        if plan.get("status") == "unsupported_in_m5k_initial":
            payload["failures"].append({"symbol": instrument["symbol"], **{k: v for k, v in plan.items() if k != "instrument"}})
            continue
        item = mis_by_channel.get(plan.get("ex_ch", ""))
        if item:
            parsed = _parse_mis_item(item, instrument | {"adapter_id": plan.get("adapter_id")}, retrieved_at)
            if parsed.get("status") == "ok":
                payload["observations"].append(parsed)
            else:
                payload["failures"].append({"symbol": instrument["symbol"], "source": plan.get("source"), "adapter_id": plan.get("adapter_id"), "status": "failed", "reason": parsed.get("status", "value_unavailable"), "observation": parsed, "recommended_next_step": "Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability."})
        else:
            payload["failures"].append({"symbol": instrument["symbol"], "source": plan.get("source"), "adapter_id": plan.get("adapter_id"), "status": "failed", "reason": "missing_from_source_response:" + str(plan.get("ex_ch")), "recommended_next_step": "Verify symbol market route and retry a bounded explicit observation later."})
    payload["status"] = "ok" if payload["observations"] else "completed_with_no_observations"
    if write_latest:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_OBSERVATION_PATH.write_text(dump_json(payload), encoding="utf-8", newline="\n")
    return payload


def read_latest_observation() -> dict[str, Any]:
    if not LATEST_OBSERVATION_PATH.exists():
        return {"status": "no_observation_available", "governance": governance(), "source_path": LATEST_OBSERVATION_PATH.relative_to(REPO_ROOT).as_posix()}
    return {"status": "ok", "source_path": LATEST_OBSERVATION_PATH.relative_to(REPO_ROOT).as_posix(), "content": load_json(LATEST_OBSERVATION_PATH), "governance": governance()}

ADAPTER_MATRIX_PATH = REPO_ROOT / "config/m5l_live_source_adapter_matrix.json"

def load_source_adapter_matrix() -> dict[str, Any]:
    return load_json(ADAPTER_MATRIX_PATH)


def source_capabilities() -> dict[str, Any]:
    matrix = load_source_adapter_matrix()
    capabilities = []
    for adapter in matrix.get("adapters", []):
        capabilities.append({
            "adapter_id": adapter.get("adapter_id"),
            "source": adapter.get("source"),
            "instrument_classes": adapter.get("instrument_classes", []),
            "supported_markets": adapter.get("supported_markets", []),
            "supports_live_observation": adapter.get("supports_live_observation"),
            "verification_status": adapter.get("verification_status"),
            "known_limitations": adapter.get("known_limitations", []),
            "freshness_semantics": adapter.get("freshness_semantics"),
            "delay_semantics": adapter.get("delay_semantics"),
        })
    return {"schema_version": "m5l_source_capabilities.v1", "generated_at_utc": utc_now(), "capabilities": capabilities, "governance": governance() | matrix.get("governance", {})}


def validate_source_adapter_matrix(matrix: dict[str, Any] | None = None) -> dict[str, Any]:
    matrix = matrix or load_source_adapter_matrix()
    required = {"adapter_id", "source", "instrument_classes", "supported_markets", "endpoint_family", "execution_mode", "bounded", "startup_network", "writes_m5f", "writes_frontend_public", "writes_research_generated", "supports_live_observation", "freshness_semantics", "delay_semantics", "raw_payload_policy", "known_limitations", "verification_status", "evidence_refs"}
    errors = []
    seen = set()
    for idx, adapter in enumerate(matrix.get("adapters", [])):
        missing = sorted(required - set(adapter))
        if missing:
            errors.append(f"adapter_{idx}_missing:{','.join(missing)}")
        adapter_id = adapter.get("adapter_id")
        if adapter_id in seen:
            errors.append(f"duplicate_adapter_id:{adapter_id}")
        seen.add(adapter_id)
        if adapter.get("execution_mode") != "explicit_only":
            errors.append(f"adapter_not_explicit_only:{adapter_id}")
        for forbidden in ("startup_network", "writes_m5f", "writes_frontend_public", "writes_research_generated"):
            if adapter.get(forbidden) is not False:
                errors.append(f"forbidden_true:{adapter_id}:{forbidden}")
    return {"valid": not errors, "errors": errors, "adapter_count": len(matrix.get("adapters", []))}
