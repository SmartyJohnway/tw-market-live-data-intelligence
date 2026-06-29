from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
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
        return {**base, "source": "TAIFEX", "status": "unsupported_in_m5k_initial", "reason": "TAIFEX futures quote endpoint requires separate contract mapping and was not adopted for initial M5K execution"}
    if typ == "index" or symbol == "TAIEX":
        return {**base, "source": "TWSE_MIS", "source_type": "official_browser_json_endpoint_candidate", "ex_ch": "tse_t00.tw", "status": "planned"}
    if market in {"tpex", "otc"}:
        return {**base, "source": "TWSE_MIS", "source_type": "official_browser_json_endpoint_candidate", "ex_ch": f"otc_{symbol}.tw", "status": "planned"}
    if market == "twse":
        return {**base, "source": "TWSE_MIS", "source_type": "official_browser_json_endpoint_candidate", "ex_ch": f"tse_{symbol}.tw", "status": "planned"}
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


def _parse_mis_item(item: dict[str, Any], instrument: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    symbol = instrument["symbol"]
    raw_price = item.get("z") or item.get("y") or "-"
    try:
        price = None if raw_price in ("-", "", None) else float(str(raw_price).replace(",", ""))
    except ValueError:
        price = None
    source_date = str(item.get("d") or "")
    source_time = str(item.get("t") or "")
    return {
        "symbol": symbol,
        "display_symbol": instrument.get("display_symbol", symbol),
        "category_id": instrument.get("category_id"),
        "instrument_type": instrument.get("instrument_type"),
        "status": "ok" if item else "missing",
        "source": "TWSE_MIS",
        "source_type": "official_browser_json_endpoint_candidate",
        "price_like_value": price,
        "price_semantics": "last_or_reference_value_as_reported_by_source",
        "source_timestamp": f"{source_date} {source_time}".strip(),
        "retrieved_at_utc": retrieved_at,
        "freshness_assessment": "current observation candidate; realtime status not guaranteed by M5K",
        "delay_status": "not_realtime_guaranteed",
        "caveats": governance()["caveats"],
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
            for item in data.get("msgArray", []):
                if isinstance(item, dict):
                    mis_key = str(item.get("key") or "").rsplit("_", 1)[0] or str(item.get("ch") or "")
                    mis_by_channel[mis_key] = item
            payload["source_investigation_notes"].append({"source": "TWSE_MIS", "status": "accepted_for_bounded_observation", "sample_retained": False})
        except Exception as exc:
            payload["failures"].append({"source": "TWSE_MIS", "status": "batch_request_failed", "reason": str(exc)})
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
        if plan.get("status") == "unsupported_in_m5k_initial":
            payload["failures"].append({"symbol": instrument["symbol"], **{k: v for k, v in plan.items() if k != "instrument"}})
            continue
        item = mis_by_channel.get(plan.get("ex_ch", ""))
        if item:
            payload["observations"].append(_parse_mis_item(item, instrument, retrieved_at))
        else:
            payload["failures"].append({"symbol": instrument["symbol"], "source": plan.get("source"), "status": "missing_from_source_response", "ex_ch": plan.get("ex_ch")})
    payload["status"] = "ok" if payload["observations"] else "completed_with_no_observations"
    if write_latest:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_OBSERVATION_PATH.write_text(dump_json(payload), encoding="utf-8", newline="\n")
    return payload


def read_latest_observation() -> dict[str, Any]:
    if not LATEST_OBSERVATION_PATH.exists():
        return {"status": "no_observation_available", "governance": governance(), "source_path": LATEST_OBSERVATION_PATH.relative_to(REPO_ROOT).as_posix()}
    return {"status": "ok", "source_path": LATEST_OBSERVATION_PATH.relative_to(REPO_ROOT).as_posix(), "content": load_json(LATEST_OBSERVATION_PATH), "governance": governance()}
