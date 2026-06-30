from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.observation_contract import normalize_failure, normalize_taifex_row, normalize_twse_mis_row

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WATCHLIST_PATH = REPO_ROOT / "config/m5k_default_watchlist.json"
WATCHLIST_SCHEMA_VERSION = "m5n_watchlist.v1"
LEGACY_WATCHLIST_SCHEMA_VERSION = "m5k_watchlist.v1"
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


def watchlist_schema() -> dict[str, Any]:
    return {
        "schema_version": WATCHLIST_SCHEMA_VERSION,
        "format": "json",
        "future_formats": ["csv"],
        "required_item_fields": ["id", "symbol", "display_name", "market", "instrument_type", "adapter", "category", "enabled", "display_order", "tags", "notes"],
        "readonly_consumers": ["FastAPI", "MCP", "frontend", "AI conversation context builder"],
        "governance": governance() | {"network_calls": False, "writes": False},
    }


def normalize_watchlist(watchlist: dict[str, Any]) -> dict[str, Any]:
    """Return the single M5N watchlist shape while accepting the M5K category shape."""
    if not isinstance(watchlist, dict):
        return watchlist
    if watchlist.get("schema_version") == WATCHLIST_SCHEMA_VERSION and isinstance(watchlist.get("items"), list) and not isinstance(watchlist.get("categories"), list):
        return watchlist
    items: list[dict[str, Any]] = []
    order = 0
    for category in watchlist.get("categories", []):
        cat = category.get("category_id") or category.get("label") or "uncategorized"
        for item in category.get("instruments", []):
            order += 1
            sources = item.get("preferred_sources") or []
            adapter = item.get("adapter") or item.get("adapter_id") or (sources[0] if sources else "unplanned")
            symbol = item.get("symbol")
            items.append({
                "id": item.get("id") or f"{cat}:{symbol}",
                "symbol": symbol,
                "display_name": item.get("display_name") or item.get("name") or item.get("display_symbol") or symbol,
                "market": item.get("market"),
                "instrument_type": item.get("instrument_type"),
                "adapter": adapter,
                "preferred_sources": sources or ([adapter] if adapter != "unplanned" else []),
                "category": item.get("category") or cat,
                "enabled": item.get("enabled", True),
                "display_order": item.get("display_order", order),
                "tags": item.get("tags", []),
                "notes": item.get("notes", ""),
                **({"contract_code": item["contract_code"]} if "contract_code" in item else {}),
                **({"contract_selector": item["contract_selector"]} if "contract_selector" in item else {}),
            })
    return {
        "schema_version": WATCHLIST_SCHEMA_VERSION,
        "watchlist_id": watchlist.get("watchlist_id", "watchlist"),
        "name": watchlist.get("name", "Watchlist"),
        "description": watchlist.get("description", ""),
        "import_export": {"json": True, "csv_future": True},
        "governance": watchlist.get("governance", {}) | {"trading_signal": False, "recommendations_allowed": False},
        "items": sorted(items, key=lambda x: (x.get("display_order", 999999), str(x.get("symbol"))))
    }


def iter_instruments(watchlist: dict[str, Any], *, include_disabled: bool = False) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    normalized = normalize_watchlist(watchlist)
    for item in normalized.get("items", []):
        if item.get("enabled", True) is False and not include_disabled:
            continue
        merged = dict(item)
        merged.setdefault("enabled", True)
        merged.setdefault("category_id", item.get("category"))
        merged.setdefault("category_label", item.get("category"))
        merged.setdefault("name", item.get("display_name"))
        merged.setdefault("preferred_sources", [item.get("adapter")] if item.get("adapter") else [])
        out.append(merged)
    return out


def _reject_forbidden_keys(value: Any, path: str = "<root>") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_l = str(key).lower()
            safety_recommendation_assertion = path == "<root>.governance" and key_l == "recommendation" and child is False
            if key_l in FORBIDDEN_KEYS and not safety_recommendation_assertion:
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
    if watchlist.get("schema_version") not in {WATCHLIST_SCHEMA_VERSION, LEGACY_WATCHLIST_SCHEMA_VERSION}:
        errors.append("schema_version_must_be_m5n_watchlist_v1")
    normalized = normalize_watchlist(watchlist)
    if not isinstance(normalized.get("items"), list) or not normalized.get("items"):
        errors.append("items_required")
    instruments = iter_instruments(normalized, include_disabled=True)
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
        for field in ("id", "display_name", "adapter", "category", "display_order", "tags", "notes"):
            if field not in item:
                errors.append(f"missing_required_field:{symbol}:{field}")
        if not isinstance(item.get("tags"), list):
            errors.append(f"invalid_tags:{symbol}")
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
        "watchlist_id": normalize_watchlist(watchlist).get("watchlist_id") if isinstance(watchlist, dict) else None,
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
    return normalize_taifex_row(
        item,
        instrument,
        retrieved_at,
        caveats=governance()["caveats"] + ["official_browser_endpoint_not_openapi_contract", "no_realtime_sla_verified"],
    )


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
    parsed = normalize_twse_mis_row(
        item,
        instrument,
        retrieved_at,
        caveats=governance()["caveats"] + ["unofficial_source_risk", "fragile_frontend_contract", "not_official_realtime_api"],
    )
    if parsed.get("status") == "reference_value_only":
        parsed["caveats"] = sorted(set(parsed.get("caveats", []) + ["current_z_unavailable_y_reference_fallback_not_current_trade"]))
    return parsed


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
            payload["failures"].append(normalize_failure(symbol=plan["symbol"], source="TAIFEX", adapter_id="taifex_mis_tx_futures_quote", status="failed" if not evidence else evidence.get("status", "failed"), reason=(evidence or {}).get("reason", "no_supported_tx_observation"), investigation_summary=evidence, recommended_next_step="Use TAIFEX MIS getQuoteList with TXF and front-month normalization, or apply for licensed TAIFEX market data for SLA-backed production usage.", caveats=governance()["caveats"]))

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
            payload["failures"].append(normalize_failure(symbol=instrument["symbol"], source=plan.get("source"), adapter_id=plan.get("adapter_id"), status=plan.get("status", "failed"), reason=plan.get("reason", "unsupported_route"), extra={k: v for k, v in plan.items() if k not in {"instrument", "symbol", "source", "adapter_id", "status", "reason"}}, caveats=governance()["caveats"]))
            continue
        item = mis_by_channel.get(plan.get("ex_ch", ""))
        if item:
            parsed = _parse_mis_item(item, instrument | {"adapter_id": plan.get("adapter_id")}, retrieved_at)
            if parsed.get("status") == "ok":
                payload["observations"].append(parsed)
            else:
                payload["failures"].append(normalize_failure(symbol=instrument["symbol"], source=plan.get("source"), adapter_id=plan.get("adapter_id"), reason=parsed.get("status", "value_unavailable"), investigation_summary={"observation": parsed}, recommended_next_step="Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability.", caveats=governance()["caveats"]))
        else:
            payload["failures"].append(normalize_failure(symbol=instrument["symbol"], source=plan.get("source"), adapter_id=plan.get("adapter_id"), reason="missing_from_source_response:" + str(plan.get("ex_ch")), recommended_next_step="Verify symbol market route and retry a bounded explicit observation later.", caveats=governance()["caveats"]))
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


def watchlist_summary(watchlist: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_watchlist(watchlist)
    validation = validate_watchlist(normalized)
    items = iter_instruments(normalized, include_disabled=True)
    enabled = [i for i in items if i.get("enabled", True)]
    by_category: dict[str, int] = {}
    by_adapter: dict[str, int] = {}
    for item in enabled:
        by_category[item.get("category", "uncategorized")] = by_category.get(item.get("category", "uncategorized"), 0) + 1
        by_adapter[item.get("adapter", "unplanned")] = by_adapter.get(item.get("adapter", "unplanned"), 0) + 1
    return {
        "schema_version": "m5n_watchlist_summary.v1",
        "watchlist_id": normalized.get("watchlist_id"),
        "name": normalized.get("name"),
        "total_items": len(items),
        "enabled_items": len(enabled),
        "disabled_items": len(items) - len(enabled),
        "symbols": [i.get("symbol") for i in enabled],
        "by_category": by_category,
        "by_adapter": by_adapter,
        "validation": validation,
        "governance": governance() | {"network_calls": False, "artifact_writes": False},
    }


def _observation_by_symbol(latest_observation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(o.get("symbol")): o for o in latest_observation.get("observations", []) if isinstance(o, dict)}


def build_watchlist_rows(watchlist: dict[str, Any], latest_observation: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    obs_by_symbol = _observation_by_symbol(latest_observation or {})
    rows = []
    for item in iter_instruments(normalize_watchlist(watchlist), include_disabled=True):
        obs = obs_by_symbol.get(str(item.get("symbol")))
        rows.append({
            "symbol": item.get("symbol"),
            "display_name": item.get("display_name") or item.get("name"),
            "market": item.get("market"),
            "category": item.get("category"),
            "adapter": item.get("adapter"),
            "enabled": item.get("enabled", True),
            "display_order": item.get("display_order"),
            "last_observation": None if not obs else (obs.get("value") or obs.get("price_like_value") or obs.get("status")),
            "source": None if not obs else obs.get("source"),
            "freshness": None if not obs else (obs.get("freshness_assessment") or obs.get("delay_status")),
            "status": "observed" if obs else "no_observation_loaded",
        })
    return rows



def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _load_canonical_summary() -> dict[str, Any]:
    path = REPO_ROOT / "research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json"
    try:
        canonical = load_json(path)
    except Exception as exc:
        return {"status": "not_available", "reason": str(exc), "raw_endpoint_payload_included": False}
    symbols = _safe_list(canonical.get("symbols"))
    return {
        "status": "available",
        "distinction": "Canonical is reviewed Level 1 context and is not the same as Latest Observation Level 2 output.",
        "canonical_source": canonical.get("source"),
        "canonical_source_date": canonical.get("source_date"),
        "canonical_symbols": [s.get("symbol") for s in symbols if isinstance(s, dict)],
        "canonical_caveats": canonical.get("global_caveats", []),
        "package_id": canonical.get("package_id"),
        "schema_version": canonical.get("schema_version"),
        "generated_at_utc": canonical.get("generated_at_utc"),
        "raw_endpoint_payload_included": False,
    }


def _observation_status(row: dict[str, Any] | None, failure: dict[str, Any] | None) -> str:
    if failure:
        return failure.get("status") or "failed"
    if not row:
        return "unavailable"
    if row.get("reference_only") is True:
        return row.get("observation_status") or "reference_only"
    return row.get("status") or row.get("observation_status") or "ok"


def _source_health_checks_by_target() -> dict[str, dict[str, Any]]:
    try:
        from scripts.m5q_source_health import read_latest_source_health
        latest = read_latest_source_health()
    except Exception:
        return {}
    if latest.get("status") != "ok":
        return {}
    return {str(c.get("target")): c for c in _safe_list(latest.get("content", {}).get("checks")) if isinstance(c, dict)}


def _conversation_per_symbol_observations(watchlist: dict[str, Any], latest_observation: dict[str, Any]) -> list[dict[str, Any]]:
    obs_by_symbol = _observation_by_symbol(latest_observation)
    health_by_symbol = _source_health_checks_by_target()
    failures_by_symbol = {str(f.get("symbol")): f for f in _safe_list(latest_observation.get("failures")) if isinstance(f, dict)}
    rows = []
    for item in iter_instruments(normalize_watchlist(watchlist), include_disabled=True):
        symbol = str(item.get("symbol"))
        obs = obs_by_symbol.get(symbol)
        health = health_by_symbol.get(symbol)
        # If a newer M5Q source-health check exists for this symbol, surface its
        # normalized status/failure fields while retaining the M5K observation value
        # fields only when M5Q did not provide them. This aggregates governed outputs;
        # it does not execute or create observations.
        source_row = dict(obs or {})
        if health and health.get("status") in {"degraded", "failed", "unsupported"}:
            source_row.update({k: v for k, v in health.items() if v is not None})
            source_row.setdefault("source", (obs or {}).get("source"))
            source_row.setdefault("price_like_value", (obs or {}).get("price_like_value", (obs or {}).get("value")))
            source_row.setdefault("price_semantics", (obs or {}).get("price_semantics"))
        obs = source_row or None
        failure = failures_by_symbol.get(symbol)
        caveats = _safe_list((obs or {}).get("display_caveats")) or _safe_list((obs or {}).get("caveats"))
        failure_reason = (failure or {}).get("reason") or (failure or {}).get("failure_reason") or (obs or {}).get("failure_reason")
        value = (obs or {}).get("price_like_value", (obs or {}).get("value"))
        rows.append({
            "symbol": symbol,
            "display_name": item.get("display_name") or (obs or {}).get("display_symbol") or symbol,
            "market": item.get("market") or (obs or {}).get("market"),
            "instrument_type": item.get("instrument_type") or (obs or {}).get("instrument_type"),
            "status": _observation_status(obs, failure),
            "observation_status": (obs or {}).get("observation_status") or _observation_status(obs, failure),
            "adapter": item.get("adapter") or (obs or {}).get("adapter_id") or (failure or {}).get("adapter_id"),
            "source": (obs or {}).get("source") or (obs or {}).get("source_family") or (failure or {}).get("source"),
            "price_like_value": value,
            "price_semantics": (obs or {}).get("price_semantics") or (obs or {}).get("value_semantics"),
            "reference_only": bool((obs or {}).get("reference_only")),
            "value_present": value is not None,
            "source_timestamp": (obs or {}).get("source_timestamp"),
            "retrieved_at_utc": (obs or {}).get("retrieved_at_utc") or (obs or {}).get("retrieved_at") or (failure or {}).get("retrieved_at_utc"),
            "freshness": (obs or {}).get("freshness_assessment") or (obs or {}).get("freshness_status"),
            "delay": (obs or {}).get("delay_status") or (obs or {}).get("delay"),
            "failure_reason": failure_reason,
            "recommended_next_step": (obs or {}).get("recommended_next_step") or (failure or {}).get("recommended_next_step") or ("Inspect latest observation/source health or rerun a bounded explicit observation later." if not obs else "Review caveats before AI discussion."),
            "display_caveats": caveats,
        })
    return rows


def _conversation_observation_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"healthy": 0, "degraded": 0, "failed": 0, "unsupported": 0, "reference_only": 0}
    for r in rows:
        status = str(r.get("status") or "").lower()
        if r.get("reference_only") or "reference" in status:
            counts["reference_only"] += 1
            counts["degraded"] += 1
        elif status in {"ok", "healthy", "observed"}:
            counts["healthy"] += 1
        elif status in {"failed", "error"}:
            counts["failed"] += 1
        elif status in {"unsupported"}:
            counts["unsupported"] += 1
        else:
            counts["failed"] += 1
    return counts

def _conversation_source_health_summary() -> dict[str, Any]:
    try:
        from scripts.m5q_source_health import read_latest_source_health
        latest = read_latest_source_health()
    except Exception:
        return {"source_health_status": "not_available"}
    if latest.get("status") != "ok":
        return {"source_health_status": "not_available"}
    report = latest.get("content", {})
    checks = [c for c in report.get("checks", []) if isinstance(c, dict)]
    per_family: dict[str, dict[str, int]] = {}
    for c in checks:
        fam = c.get("source_family") or "unknown"
        status = c.get("status") or "unknown"
        per_family.setdefault(fam, {})[status] = per_family.setdefault(fam, {}).get(status, 0) + 1
    return {
        "source_health_status": "available",
        "generated_at_utc": report.get("generated_at_utc"),
        "summary": report.get("summary", {}),
        "per_source_family_status": per_family,
        "degraded_source_families": sorted([fam for fam, counts in per_family.items() if counts.get("degraded", 0) > 0]),
        "failed_source_families": sorted([fam for fam, counts in per_family.items() if counts.get("failed", 0) > 0]),
        "overall_summary": report.get("summary", {}),
        "per_source_family_summary": per_family,
        "degraded_or_failed_targets": [
            {"target": c.get("target"), "source_family": c.get("source_family"), "status": c.get("status"), "observation_status": c.get("observation_status"), "freshness_assessment": c.get("freshness_assessment")}
            for c in checks if c.get("status") in {"degraded", "failed"}
        ],
        "caveats": report.get("caveats", []),
        "raw_endpoint_payload_included": False,
    }


def build_conversation_context(watchlist: dict[str, Any], latest_observation: dict[str, Any] | None = None) -> dict[str, Any]:
    latest_observation = latest_observation or read_latest_observation()
    if isinstance(latest_observation, dict) and isinstance(latest_observation.get("content"), dict) and "observations" not in latest_observation:
        latest_observation = latest_observation["content"]
    failures = _safe_list(latest_observation.get("failures")) if isinstance(latest_observation, dict) else []
    per_symbol = _conversation_per_symbol_observations(watchlist, latest_observation if isinstance(latest_observation, dict) else {})
    obs_summary = _conversation_observation_summary(per_symbol)
    canonical_summary = _load_canonical_summary()
    source_health = _conversation_source_health_summary()
    unavailable = [r["symbol"] for r in per_symbol if r.get("status") in {"failed", "unavailable", "unsupported"}]
    reference_only = [r["symbol"] for r in per_symbol if r.get("reference_only") is True or "reference" in str(r.get("status", ""))]
    healthy = [r["symbol"] for r in per_symbol if r.get("status") in {"ok", "healthy", "observed"} and not r.get("reference_only")]
    return {
        "schema_version": "m5n_conversation_context.v1",
        "created_at_utc": utc_now(),
        "purpose": "Single governed AI conversation package for watchlist observation discussion; not canonical M5F and not raw endpoint payload.",
        "watchlist_summary": watchlist_summary(watchlist),
        "watchlist_rows": build_watchlist_rows(watchlist, latest_observation if isinstance(latest_observation, dict) else {}),
        "observation_summary": obs_summary,
        "per_symbol_observations": per_symbol,
        "successful_observations": len(_safe_list(latest_observation.get("observations"))) if isinstance(latest_observation, dict) else 0,
        "failed_observations": len(failures),
        "failures": [{"symbol": f.get("symbol"), "source": f.get("source"), "reason": f.get("reason") or f.get("failure_reason"), "status": f.get("status"), "recommended_next_step": f.get("recommended_next_step")} for f in failures if isinstance(f, dict)],
        "latest_observation_summary": {
            "schema_version": latest_observation.get("schema_version") if isinstance(latest_observation, dict) else None,
            "status": latest_observation.get("status") if isinstance(latest_observation, dict) else "not_available",
            "generated_at_utc": latest_observation.get("generated_at_utc") if isinstance(latest_observation, dict) else None,
            "watchlist_id": latest_observation.get("watchlist_id") if isinstance(latest_observation, dict) else None,
            "observation_count": len(_safe_list(latest_observation.get("observations"))) if isinstance(latest_observation, dict) else 0,
            "failure_count": len(failures),
            "raw_endpoint_payload_included": False,
        },
        "freshness": latest_observation.get("retrieved_at_utc") or latest_observation.get("generated_at_utc") if isinstance(latest_observation, dict) else None,
        "source_investigation_notes": latest_observation.get("source_investigation_notes", []) if isinstance(latest_observation, dict) else [],
        "source_health_summary": source_health,
        "source_health": source_health,
        "canonical_summary": canonical_summary,
        "ai_guidance_summary": {
            "current_observations_available": healthy,
            "reference_only_observations": reference_only,
            "unavailable_observations": unavailable,
            "canonical_package_covers": canonical_summary.get("canonical_symbols", []),
            "current_limitations": sorted(set(governance()["caveats"] + _safe_list(canonical_summary.get("canonical_caveats")) + _safe_list(source_health.get("caveats")))),
            "recommended_operator_workflow": ["Review Conversation Context JSON/Markdown as the AI handoff package.", "Treat Canonical Summary as Level 1 historical context, not Latest Observation.", "Treat reference-only or unavailable observations as not current price.", "If freshness is insufficient, run only the existing bounded explicit observation runner later."],
            "descriptive_only": True,
            "trading_recommendation": False,
        },
        "risk": ["not_realtime_guaranteed", "source_may_be_delayed_or_unavailable", "not_trading_signal", "no_automatic_refresh"],
        "caveats": governance()["caveats"],
        "governance": governance() | {"raw_endpoint_payload_included": False, "recommendation": False, "target_price": False, "ranking": False, "buy_sell_hold": False},
    }


def conversation_context_markdown(context: dict[str, Any]) -> str:
    wl = context.get("watchlist_summary", {})
    obs = context.get("observation_summary", {})
    canon = context.get("canonical_summary", {})
    health = context.get("source_health_summary", context.get("source_health", {}))
    rows = context.get("per_symbol_observations", [])
    lines = [
        "# M5N Conversation Context",
        "",
        "## Executive Summary",
        context.get("purpose", ""),
        "",
        "Canonical Summary is Level 1 reviewed context. Latest Observation Summary is Level 2 bounded observation state. They are not the same.",
        "",
        "## Watchlist Summary",
        f"- Watchlist: {wl.get('name')} ({wl.get('watchlist_id')})",
        f"- Total symbols: {wl.get('total_items')}",
        f"- Enabled symbols: {wl.get('enabled_items')}",
        f"- Categories: {', '.join((wl.get('by_category') or {}).keys())}",
        "",
        "## Canonical Summary",
        f"- Canonical source: {canon.get('canonical_source')}",
        f"- Canonical source date: {canon.get('canonical_source_date')}",
        f"- Canonical symbols: {', '.join(canon.get('canonical_symbols') or [])}",
        f"- Caveats: {', '.join(canon.get('canonical_caveats') or [])}",
        "",
        "## Latest Observation Summary",
        f"- healthy={obs.get('healthy', 0)} degraded={obs.get('degraded', 0)} failed={obs.get('failed', 0)} unsupported={obs.get('unsupported', 0)} reference_only={obs.get('reference_only', 0)}",
        "",
        "## Healthy Observations",
    ]
    for r in rows:
        if r.get("status") in {"ok", "healthy", "observed"} and not r.get("reference_only"):
            lines.append(f"- {r.get('symbol')} {r.get('display_name')}: {r.get('price_like_value')} ({r.get('price_semantics')}); source={r.get('source')}; freshness={r.get('freshness')}; delay={r.get('delay')}")
    lines += ["", "## Reference-only Observations"]
    for r in rows:
        if r.get("reference_only") or "reference" in str(r.get("status", "")):
            lines.append(f"- {r.get('symbol')} {r.get('display_name')}: value_present={r.get('value_present')}; reason={r.get('failure_reason')}; next={r.get('recommended_next_step')}")
    lines += ["", "## Failed Observations"]
    for r in rows:
        if r.get("status") in {"failed", "unavailable", "unsupported"}:
            lines.append(f"- {r.get('symbol')} {r.get('display_name')}: status={r.get('status')}; reason={r.get('failure_reason')}; next={r.get('recommended_next_step')}")
    lines += [
        "",
        "## Source Health",
        f"- Status: {health.get('source_health_status')}",
        f"- Summary: {health.get('summary')}",
        f"- Degraded source families: {', '.join(health.get('degraded_source_families') or []) or 'none'}",
        f"- Failed source families: {', '.join(health.get('failed_source_families') or []) or 'none'}",
        "",
        "## Current Caveats",
    ]
    lines.extend(f"- {c}" for c in context.get("ai_guidance_summary", {}).get("current_limitations", context.get("caveats", [])))
    lines += ["", "## Suggested Questions For AI"]
    lines.extend([
        "- 哪些資料目前可信？",
        "- 哪些 observation 是 reference-only？",
        "- 哪些 observation 不可視為 current price？",
        "- 哪些來源 degraded？",
        "- 哪些標的是 unavailable？",
        "- Canonical Package 包含哪些內容？",
        "- Latest Observation 包含哪些內容？",
        "- 目前最大的資料限制是什麼？",
        "- 下一步建議人工做什麼？",
    ])
    return "\n".join(lines) + "\n"
