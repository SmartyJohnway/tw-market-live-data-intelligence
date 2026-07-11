"""Read-only M8A official EOD instrument classifier.

Loads repository security-master evidence and performs exact (market, symbol)
classification only.  It intentionally does not use symbol-length or name
heuristics as authoritative classification.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECURITY_MASTER_PATH = REPO_ROOT / "config/m8a_official_eod_security_master.json"
DEFAULT_WATCHLIST_PATH = REPO_ROOT / "config/m5k_default_watchlist.json"
TAXONOMY = {
    "listed_etf": "etf",
    "etf": "etf",
    "listed_equity": "equity",
    "listed_or_otc_equity": "equity",
    "equity": "equity",
    "listed_stock": "equity",
    "stock_like": "equity",
    "etn": "etn",
    "preferred_share": "preferred_share",
    "tdr": "tdr",
    "warrant": "warrant",
    "bond": "bond",
    "convertible_bond": "convertible_bond",
    "index": "index",
}
MARKET_ALIASES = {"twse": "listed", "listed": "listed", "tpex": "tpex_otc", "otc": "tpex_otc", "tpex_otc": "tpex_otc"}


def normalize_market(market: Any) -> str:
    return MARKET_ALIASES.get(str(market or "").strip().lower(), str(market or "").strip())


def normalize_instrument_type(value: Any) -> str | None:
    return TAXONOMY.get(str(value or "").strip().lower())


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_watchlist_items(watchlist: dict) -> list[dict]:
    items = []
    for category in watchlist.get("categories", []):
        if isinstance(category, dict):
            for item in category.get("instruments", []):
                if isinstance(item, dict):
                    items.append(item)
    return items


def build_security_master_lookup(*, security_master_path: Path = DEFAULT_SECURITY_MASTER_PATH, watchlist_path: Path = DEFAULT_WATCHLIST_PATH) -> dict[tuple[str, str], dict]:
    lookup: dict[tuple[str, str], dict] = {}
    if watchlist_path.exists():
        for item in _iter_watchlist_items(_load_json(watchlist_path)):
            market = normalize_market(item.get("market"))
            symbol = str(item.get("symbol") or "").strip()
            typ = normalize_instrument_type(item.get("instrument_type"))
            if market and symbol and typ:
                lookup[(market, symbol)] = {"instrument_type": typ, "classification_status": "classified", "provenance": f"{watchlist_path.relative_to(REPO_ROOT)}:{item.get('id')}", "source": "repository_watchlist_security_master"}
    if security_master_path.exists():
        master = _load_json(security_master_path)
        for item in master.get("instruments", []):
            if not isinstance(item, dict):
                continue
            market = normalize_market(item.get("market"))
            symbol = str(item.get("symbol") or "").strip()
            typ = normalize_instrument_type(item.get("instrument_type"))
            if market and symbol and typ:
                lookup[(market, symbol)] = {"instrument_type": typ, "classification_status": "classified", "provenance": item.get("provenance") or str(security_master_path.relative_to(REPO_ROOT)), "source": "repository_security_master"}
    return lookup


def classify_official_eod_instrument(market: str, symbol: str, security_master: dict | None = None) -> dict:
    market = normalize_market(market)
    symbol = str(symbol or "").strip()
    try:
        lookup = security_master if security_master is not None else build_security_master_lookup()
    except Exception as exc:
        return {"instrument_type": "unknown", "classification_status": "classification_unavailable", "source": "repository_security_master", "provenance": None, "caveat": f"security master unavailable; fail closed: {str(exc)[:80]}"}
    entry = None
    if isinstance(lookup, dict):
        entry = lookup.get((market, symbol)) or lookup.get(f"{market}:{symbol}") or lookup.get(symbol)
    if isinstance(entry, str):
        entry = {"instrument_type": normalize_instrument_type(entry) or "unknown", "classification_status": "classified", "source": "injected_security_master", "provenance": "test_injected"}
    if isinstance(entry, dict) and normalize_instrument_type(entry.get("instrument_type")):
        return {**entry, "instrument_type": normalize_instrument_type(entry.get("instrument_type")), "classification_status": entry.get("classification_status") or "classified"}
    return {"instrument_type": "unknown", "classification_status": "unclassified", "source": "repository_security_master_miss", "provenance": None, "caveat": "unclassified rows are excluded from deterministic metrics and AI context by default"}
