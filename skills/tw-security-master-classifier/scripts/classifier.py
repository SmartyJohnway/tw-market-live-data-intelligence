#!/usr/bin/env python3
"""Resolve and deterministically classify normalized Taiwan security records."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from common import normalize_name, normalize_text


MODE_MARKETS = {
    1: ("public_unlisted", "unlisted"),
    2: ("twse", "main"),
    3: ("listed_otc_bond", "bond_market"),
    4: ("tpex", "main"),
    5: ("emerging", "emerging"),
    6: ("derivatives", "derivatives"),
    7: ("fund_registry", "fund_registry"),
    8: ("gisa", "gisa"),
    9: ("tpex_gold_spot", "gold_spot"),
    10: ("ncd_registry", "ncd_registry"),
    11: ("index_registry", "index_registry"),
    12: ("sto_registry", "security_token"),
}

SECTION_RULES = (
    (("exchange traded note", "etn"), "etn"),
    (("exchange traded fund", "etf"), "etf"),
    (("臺灣存託憑證", "台灣存託憑證", "depositary receipt", "tdr"), "depositary_receipt"),
    (("認購(售)權證", "認購權證", "認售權證", "warrant"), "warrant"),
    (("轉換公司債", "convertible bond"), "convertible_bond"),
    (("特別股", "preferred share", "preferred stock"), "preferred_share"),
    (("普通股", "common stock", "ordinary share"), "common_share"),
    (("受益憑證", "fund"), "fund"),
    (("選擇權", "option"), "option"),
    (("期貨", "future"), "future"),
    (("黃金現貨", "gold spot"), "gold_spot"),
    (("指數", "index"), "index"),
    (("普通公司債", "政府公債", "government bond", "bond"), "bond"),
    (("sto", "security token", "證券型代幣", "具證券性質之虛擬通貨"), "security_token"),
)

CFI_MAPPING = {
    "version": "controlled-prefix-v1.1.0",
    "scope": "partial_controlled_prefixes_not_full_iso_10962",
    "decode_depth": "category_or_group_prefix_only",
}

IDENTITY_FIELDS = {"security_code", "isin"}
CLASSIFICATION_FIELDS = {"cfi", "str_mode", "market"}
DATE_FIELDS = {"issue_date", "listing_date", "registration_date", "maturity_date"}
MULTIVALUE_FIELDS = {"source_lane", "source_url", "source_family", "page_title", "section_heading", "industry", "remarks"}


def _identity_key(record: dict[str, Any]) -> str:
    isin = normalize_text(record.get("isin")).upper()
    if isin:
        return f"isin:{isin}"
    return "code:%s:%s" % (normalize_text(record.get("security_code")).upper(), record.get("str_mode"))


def merge_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge bilingual records without discarding lane-level evidence."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[_identity_key(record)].append(dict(record))

    merged: list[dict[str, Any]] = []
    for key in sorted(groups):
        members = groups[key]
        result: dict[str, Any] = {}
        conflicts: list[dict[str, Any]] = []
        fields = sorted({field for member in members for field in member})
        for field in fields:
            if field in {"row_hash", "raw_cells", "issues"}:
                continue
            values = [member.get(field) for member in members if member.get(field) not in (None, "", [])]
            distinct = list(dict.fromkeys(json.dumps(v, ensure_ascii=False, sort_keys=True) for v in values))
            decoded = [json.loads(v) for v in distinct]
            if len(decoded) == 1:
                result[field] = decoded[0]
            elif field in IDENTITY_FIELDS:
                conflicts.append({"category": "identity_conflict", "severity": "hard", "field": field, "values": decoded})
            elif field in CLASSIFICATION_FIELDS:
                conflicts.append({"category": "classification_conflict", "severity": "hard", "field": field, "values": decoded})
            elif field in DATE_FIELDS:
                source_dates = sorted({m.get("source_updated_date") for m in members if m.get("source_updated_date")})
                category = "observation_lag" if len(source_dates) > 1 else "date_semantic_conflict"
                conflicts.append({"category": category, "severity": "review", "field": field, "values": decoded, "source_updated_dates": source_dates})
                newest = max(members, key=lambda m: m.get("source_updated_date") or "")
                result[field] = newest.get(field)
            elif field in MULTIVALUE_FIELDS:
                result[f"{field}_values"] = decoded
            else:
                result[field] = decoded[0]
        result["evidence_records"] = members
        result["source_lanes"] = sorted({normalize_text(m.get("source_lane")) for m in members if m.get("source_lane")})
        result["conflicts"] = conflicts
        merged.append(result)
    return merged


def _evidence_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("section_heading", "section_heading_values", "page_title", "page_title_values", "market", "market_values", "remarks", "remarks_values"):
        value = record.get(key)
        parts.extend(value if isinstance(value, list) else [value])
    return normalize_text(" ".join(normalize_text(v) for v in parts)).casefold()


def _section_type(record: dict[str, Any]) -> tuple[str | None, str | None]:
    section_values = record.get("section_heading_values") or [record.get("section_heading")]
    texts = [normalize_text(" ".join(normalize_text(value) for value in section_values if value)).casefold(), _evidence_text(record)]
    for text in texts:
        for signals, instrument_type in SECTION_RULES:
            for signal in signals:
                if signal.casefold() in text:
                    return instrument_type, signal
    return None, None


def _cfi_type(cfi: str) -> tuple[str | None, str | None]:
    cfi = normalize_text(cfi).upper()
    if cfi.startswith("ES"):
        return "common_share", "CFI_ES_COMMON_SHARE"
    if cfi.startswith("EP"):
        return "preferred_share", "CFI_EP_PREFERRED_SHARE"
    if cfi.startswith("D"):
        return "bond", "CFI_D_DEBT"
    if cfi.startswith("C"):
        return "fund", "CFI_C_COLLECTIVE"
    if cfi.startswith("O"):
        return "option", "CFI_O_OPTION"
    if cfi.startswith("F"):
        return "future", "CFI_F_FUTURE"
    if cfi.startswith("R"):
        return "entitlement", "CFI_R_ENTITLEMENT"
    if cfi.startswith("M"):
        return None, "CFI_M_ROUTE_REQUIRED"
    return None, "UNKNOWN_CFI" if cfi else "MISSING_CFI"


def _dimensions(instrument_type: str) -> tuple[str, str, str | None]:
    if instrument_type in {"common_share", "preferred_share", "depositary_receipt"}:
        subtype = {"common_share": "ordinary", "preferred_share": "preferred", "depositary_receipt": "depositary_receipt"}[instrument_type]
        return "equity", "company_share", subtype
    if instrument_type in {"bond", "convertible_bond", "etn", "ncd", "security_token_debt"}:
        return "debt", "debt_security", None
    if instrument_type in {"etf", "fund"}:
        return "collective_investment", "fund_product", None
    if instrument_type in {"warrant", "future", "option"}:
        return "derivative", "derivative", None
    if instrument_type == "gold_spot":
        return "commodity", "spot_product", None
    if instrument_type == "index":
        return "reference", "index", None
    if instrument_type.startswith("security_token"):
        return "security_token", "tokenized_security", None
    if instrument_type == "issuer_record":
        return "issuer", "issuer", None
    return "other", "other", None


def classify_record(record: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    conflicts = list(record.get("conflicts") or [])
    mode = record.get("str_mode")
    market, board = MODE_MARKETS.get(mode, ("unknown", "unknown"))

    if record.get("issuer_level_record"):
        instrument_type = "issuer_record"
        reasons.append("ISSUER_GRAIN_NOT_SECURITY_IDENTITY")
    else:
        section_type, section_signal = _section_type(record)
        cfi_type, cfi_reason = _cfi_type(record.get("cfi", ""))
        reasons.append(f"MODE_{mode}_{market.upper()}" if mode else "MISSING_STR_MODE")
        if section_type:
            reasons.append(f"SECTION_{section_type.upper()}")
        reasons.append(cfi_reason)

        route_type = {3: "bond", 7: "fund", 9: "gold_spot", 10: "ncd", 11: "index", 12: "security_token"}.get(mode)
        if mode == 6:
            route_type = section_type if section_type in {"future", "option"} else cfi_type
        instrument_type = section_type or route_type or cfi_type

        governed_pairs = {
            ("common_share", "preferred_share"), ("preferred_share", "common_share"),
            ("etf", "common_share"), ("common_share", "fund"),
            ("gold_spot", "common_share"),
        }
        if section_type and cfi_type and (section_type, cfi_type) in governed_pairs:
            conflicts.append({"category": "classification_conflict", "severity": "hard", "field": "section_cfi", "values": [section_type, cfi_type]})
            reasons.append("SECTION_CFI_CONFLICT")
        if route_type and mode in {3, 9, 10, 11} and instrument_type != route_type:
            conflicts.append({"category": "classification_conflict", "severity": "hard", "field": "route_type", "values": [route_type, instrument_type]})
            reasons.append("MODE_SECTION_CONFLICT")
        if mode == 12:
            if cfi_type == "bond":
                instrument_type = "security_token_debt"
            elif cfi_type in {"common_share", "preferred_share"}:
                instrument_type = "security_token_equity"
            else:
                instrument_type = "security_token_unknown"
                reasons.append("STO_SUBTYPE_UNGOVERNED")
        if cfi_type == "entitlement" and section_type != "warrant":
            instrument_type = None
            reasons.append("CFI_R_REQUIRES_SECTION")
        if not instrument_type:
            instrument_type = "unknown"
            reasons.append("INSUFFICIENT_GOVERNED_EVIDENCE")

    asset_class, family, subtype = _dimensions(instrument_type)
    lanes = set(record.get("source_lanes") or ([record.get("source_lane")] if record.get("source_lane") else []))
    hard_conflicts = [conflict for conflict in conflicts if conflict.get("severity", "hard") == "hard"]
    if hard_conflicts:
        status = "quarantine_conflict"
    elif instrument_type in {"unknown", "security_token_unknown"}:
        status = "quarantine_unknown"
    elif {"zh", "en"}.issubset(lanes):
        status = "confirmed_dual_lane"
        reasons.append("DUAL_LANE_MATCH")
    elif lanes:
        status = "confirmed_official_single_lane" if instrument_type not in {"entitlement", "unknown"} else "provisional_single_lane"
        reasons.append("OFFICIAL_SINGLE_LANE")
    else:
        status = "provisional_single_lane"

    core = instrument_type == "common_share" and mode in {2, 4} and market in {"twse", "tpex"} and not hard_conflicts
    return {
        "asset_class": asset_class,
        "instrument_family": family,
        "instrument_type": instrument_type,
        "equity_subtype": subtype,
        "market": market,
        "board": board,
        "listed_common_stock_core_flag": core,
        "classification_status": status,
        "cfi_mapping_version": CFI_MAPPING["version"],
        "cfi_mapping_scope": CFI_MAPPING["scope"],
        "cfi_decode_depth": CFI_MAPPING["decode_depth"],
        "reason_codes": list(dict.fromkeys(reasons)),
        "conflicts": conflicts,
    }


def resolve(records: Iterable[dict[str, Any]], query: str, source_context: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = merge_records(records)
    raw = normalize_text(query)
    upper = raw.upper()
    normalized = normalize_name(raw)
    result_caveats = ["fixture_not_living_truth"] if source_context and source_context.get("fixture_version") else []
    tiers = (
        ("resolved_exact_isin", [r for r in merged if normalize_text(r.get("isin")).upper() == upper]),
        ("resolved_exact_code", [r for r in merged if normalize_text(r.get("security_code")).upper() == upper]),
        ("resolved_exact_name", [r for r in merged if normalized and normalized in {normalize_name(r.get(k)) for k in ("security_name_zh", "security_name_en", "security_short_name_zh")}]),
    )
    for status, matches in tiers:
        if matches:
            if len(matches) > 1:
                return {"operation": "resolve", "query": query, "resolution_status": "ambiguous", "candidate_count": len(matches), "candidates": [_present(r, source_context) for r in matches], "caveats": result_caveats}
            return {"operation": "resolve", "query": query, "resolution_status": status, "candidate_count": 1, "candidates": [_present(matches[0], source_context)], "caveats": result_caveats}
    partial = [r for r in merged if normalized and any(normalized in normalize_name(r.get(k)) for k in ("security_name_zh", "security_name_en", "security_short_name_zh"))]
    return {"operation": "resolve", "query": query, "resolution_status": "ambiguous" if partial else "not_found", "candidate_count": len(partial), "candidates": [_present(r, source_context) for r in partial], "caveats": result_caveats}


def _observation(record: dict[str, Any], source_context: dict[str, Any] | None) -> dict[str, Any]:
    context = source_context or {}
    if context.get("fixture_version"):
        return {"status": "fixture_observation_only", "observed_at": context.get("observed_at"), "source_updated_date": record.get("source_updated_date")}
    if context.get("observation_status") == "observed_in_latest_verified_snapshot" or context.get("fresh_probe") is True:
        return {"status": "observed_in_latest_verified_snapshot", "observed_at": context.get("observed_at"), "source_updated_date": record.get("source_updated_date")}
    if context.get("observation_status") == "historical_capture":
        return {"status": "historical_capture", "observed_at": context.get("observed_at"), "source_updated_date": record.get("source_updated_date")}
    return {"status": "observed_in_capture", "observed_at": context.get("observed_at"), "source_updated_date": record.get("source_updated_date")}


def _present(record: dict[str, Any], source_context: dict[str, Any] | None = None) -> dict[str, Any]:
    identity = {key: record.get(key) for key in ("security_code", "security_name_zh", "security_name_en", "isin", "cfi")}
    classification = classify_record(record)
    return {
        "identity": identity,
        "classification": classification,
        "dates": {key: record.get(key) for key in ("issue_date", "listing_date", "registration_date", "maturity_date") if record.get(key)},
        "observation": _observation(record, source_context),
        "lifecycle_events": record.get("lifecycle_events", []),
        "evidence": record.get("evidence_records", [record]),
        "conflicts": classification["conflicts"],
        "caveats": ["fixture_not_living_truth"] if source_context and source_context.get("fixture_version") else [],
    }


def classify_all(records: Iterable[dict[str, Any]], source_context: dict[str, Any] | None = None) -> dict[str, Any]:
    presented = [_present(record, source_context) for record in merge_records(records)]
    return {"operation": "classify_all", "record_count": len(presented), "records": presented, "caveats": ["fixture_not_living_truth"] if source_context and source_context.get("fixture_version") else []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON list or object containing records")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    loaded = json.loads(args.input.read_text(encoding="utf-8"))
    records = loaded.get("records", []) if isinstance(loaded, dict) else loaded
    source_context = {key: loaded.get(key) for key in ("fixture_version", "observed_at", "observation_status", "fresh_probe") if loaded.get(key) is not None} if isinstance(loaded, dict) else None
    result = resolve(records, args.query, source_context) if args.query else classify_all(records, source_context)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
