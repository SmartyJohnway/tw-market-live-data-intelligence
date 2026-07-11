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
DEFAULT_BOUNDED_SEED_PATH = REPO_ROOT / "config/m8a_official_eod_security_master.json"
DEFAULT_WATCHLIST_PATH = REPO_ROOT / "config/m5k_default_watchlist.json"
CANONICAL_SECURITY_MASTER_CANDIDATES = (
    REPO_ROOT / "config/canonical_security_master.json",
    REPO_ROOT / "docs/data_capabilities/canonical_security_master.json",
    REPO_ROOT / "research/generated/canonical_security_master.json",
)
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


def _canonical_path() -> Path | None:
    return next((p for p in CANONICAL_SECURITY_MASTER_CANDIDATES if p.exists()), None)

def _metadata(mode: str, path: Path | None) -> dict:
    return {"coverage_mode": mode, "production_classification_completeness": "complete" if mode == "canonical_security_master" else "incomplete", "artifact_path": str(path.relative_to(REPO_ROOT)) if path else None}

def _add_entry(lookup: dict, market: str, symbol: str, typ: str, *, provenance: str, source: str, metadata: dict) -> None:
    lookup[(market, symbol)] = {"instrument_type": typ, "classification_status": "classified", "provenance": provenance, "source": source, **metadata}

def build_security_master_lookup(*, security_master_path: Path | None = None, watchlist_path: Path = DEFAULT_WATCHLIST_PATH) -> dict[tuple[str, str], dict]:
    lookup: dict[tuple[str, str], dict] = {}
    canonical = _canonical_path()
    if canonical is not None and security_master_path is None:
        security_master_path = canonical
        metadata = _metadata("canonical_security_master", canonical)
    else:
        security_master_path = security_master_path or DEFAULT_BOUNDED_SEED_PATH
        metadata = _metadata("bounded_seed_only", security_master_path)
    if watchlist_path.exists() and metadata["coverage_mode"] != "canonical_security_master":
        for item in _iter_watchlist_items(_load_json(watchlist_path)):
            market = normalize_market(item.get("market"))
            symbol = str(item.get("symbol") or "").strip()
            typ = normalize_instrument_type(item.get("instrument_type"))
            if market and symbol and typ:
                _add_entry(lookup, market, symbol, typ, provenance=f"{watchlist_path.relative_to(REPO_ROOT)}:{item.get('id')}", source="repository_watchlist_bounded_seed", metadata=metadata)
    if security_master_path and security_master_path.exists():
        master = _load_json(security_master_path)
        if master.get("coverage_mode") == "bounded_seed_only" or "bounded_seed" in str(master.get("schema_version", "")):
            metadata = _metadata("bounded_seed_only", security_master_path)
        for item in master.get("instruments", []):
            if not isinstance(item, dict):
                continue
            market = normalize_market(item.get("market"))
            symbol = str(item.get("symbol") or "").strip()
            typ = normalize_instrument_type(item.get("instrument_type"))
            if market and symbol and typ:
                _add_entry(lookup, market, symbol, typ, provenance=item.get("provenance") or str(security_master_path.relative_to(REPO_ROOT)), source="repository_security_master" if metadata["coverage_mode"] == "canonical_security_master" else "repository_bounded_security_seed", metadata=metadata)
    return lookup


def classify_official_eod_instrument(market: str, symbol: str, security_master: dict | None = None) -> dict:
    market = normalize_market(market)
    symbol = str(symbol or "").strip()
    try:
        lookup = security_master if security_master is not None else build_security_master_lookup()
    except Exception as exc:
        return {"instrument_type": "unknown", "classification_status": "classification_unavailable", "source": "repository_security_master", "provenance": None, "coverage_mode": "unavailable", "production_classification_completeness": "incomplete", "artifact_path": None, "caveat": f"security master unavailable; fail closed: {str(exc)[:80]}"}
    entry = None
    if isinstance(lookup, dict):
        entry = lookup.get((market, symbol)) or lookup.get(f"{market}:{symbol}") or lookup.get(symbol)
    if isinstance(entry, str):
        entry = {"instrument_type": normalize_instrument_type(entry) or "unknown", "classification_status": "classified", "source": "injected_security_master", "provenance": "test_injected", "coverage_mode": "test_injected", "production_classification_completeness": "test_only", "artifact_path": None}
    if isinstance(entry, dict) and normalize_instrument_type(entry.get("instrument_type")):
        return {**entry, "instrument_type": normalize_instrument_type(entry.get("instrument_type")), "classification_status": entry.get("classification_status") or "classified"}
    coverage = "test_injected" if security_master is not None else ("bounded_seed_only" if _canonical_path() is None else "canonical_security_master")
    return {"instrument_type": "unknown", "classification_status": "unclassified", "source": "repository_security_master_miss", "provenance": None, "coverage_mode": coverage, "production_classification_completeness": "incomplete" if coverage != "canonical_security_master" else "complete", "artifact_path": str(DEFAULT_BOUNDED_SEED_PATH.relative_to(REPO_ROOT)) if coverage == "bounded_seed_only" else None, "caveat": "unclassified rows are excluded from deterministic metrics and AI context by default"}
