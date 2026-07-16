from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "m8r_derivatives_conversational_intent.v1"
EXACT_SCHEMA_VERSION = "m8r_derivatives_exact_intent.v1"

PRODUCT_ALIASES = {
    "台指期": ("future", "TX", "TX"), "台指期貨": ("future", "TX", "TX"), "大台": ("future", "TX", "TX"),
    "tx": ("future", "TX", "TX"), "taiex futures": ("future", "TX", "TX"),
    "台指選": ("option", "TXO", "TX"), "台指選擇權": ("option", "TXO", "TX"),
    "txo": ("option", "TXO", "TX"), "taiex options": ("option", "TXO", "TX"),
    "週選": ("option", "TXO", "TX"), "月選": ("option", "TXO", "TX"),
}
CURRENT_WORDS = ("現在", "目前", "當下", "最新", "current", "now", "latest")
NEAR_EXPIRY_WORDS = ("近月", "最近月", "最近到期", "front month", "nearest expiry", "next expiry")
MONTHLY_WORDS = ("月選", "monthly")
WEEKLY_WORDS = ("週選", "weekly")
AROUND_WORDS = ("附近", "價平", "平值", "atm", "around market", "near reference")
CALL_WORDS = ("買權", " call", "call", " c ")
PUT_WORDS = ("賣權", " put", "put", " p ")
BOTH_WORDS = ("call跟put", "call 跟 put", "買賣權", "both", "兩邊", "買權賣權")


def _contains(text: str, words: tuple[str, ...]) -> bool:
    low = f" {text.lower()} "
    return any(w in text or w in low for w in words)


def _product(text: str) -> tuple[str | None, str | None, str | None, bool]:
    low = text.lower()
    for alias, value in sorted(PRODUCT_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in text or alias in low:
            return (*value, True)
    return None, None, None, False


def _call_put(text: str) -> tuple[str, bool]:
    low = f" {text.lower()} "
    if _contains(text, BOTH_WORDS):
        return "both", True
    has_call = "買權" in text or re.search(r"\bcall\b|\bC\b", text, re.I) is not None
    has_put = "賣權" in text or re.search(r"\bput\b|\bP\b", text, re.I) is not None
    if has_call and has_put:
        return "both", True
    if has_call:
        return "C", True
    if has_put:
        return "P", True
    return "both", False


def _strike_anchor(text: str) -> tuple[str | None, bool]:
    m = re.search(r"(\d{4,6})(?:\s*)附近", text)
    if m:
        return m.group(1), True
    bounded = {"四萬五": "45000", "4萬5": "45000", "四萬六": "46000", "四萬": "40000"}
    for k, v in bounded.items():
        if k in text and "附近" in text:
            return v, True
    m = re.search(r"\b(\d{4,6})\b", text)
    if m:
        return m.group(1), True
    return None, False


def parse_derivatives_intent(text: str) -> dict[str, Any]:
    original = str(text or "").strip()
    instrument, product, underlying, product_explicit = _product(original)
    exact = parse_exact_contract_intent(original)
    if exact.get("intent_mode") == "exact":
        return exact
    cp, cp_explicit = _call_put(original)
    strike, strike_explicit = _strike_anchor(original)
    monthly = _contains(original, MONTHLY_WORDS)
    weekly = _contains(original, WEEKLY_WORDS)
    near = _contains(original, NEAR_EXPIRY_WORDS)
    current = _contains(original, CURRENT_WORDS) or near
    expiry_pref = "nearest_active"
    contract_pref = "monthly_preferred" if monthly else "weekly_preferred" if weekly else "nearest_active"
    clarification = instrument is None
    explicit_constraints = {"product": product_explicit, "expiry": False, "strike": strike_explicit, "call_put": cp_explicit, "contract_type": monthly or weekly}
    inferred = {}
    if current or near or not explicit_constraints["expiry"]:
        inferred["expiry_preference"] = {"value": expiry_pref, "reason": "user said current/near/latest or omitted expiry"}
    if instrument == "option" and not cp_explicit:
        inferred["call_put_scope"] = {"value": "both", "reason": "balanced conversational option discussion default"}
    if instrument == "option" and not strike_explicit:
        inferred["strike_preference"] = {"value": "around_reference", "reason": "option strike omitted in current conversational mode"}
    return {
        "schema_version": SCHEMA_VERSION,
        "original_user_text": original,
        "intent_mode": "resolve_current",
        "market": "TAIFEX",
        "instrument_family": instrument,
        "product": product,
        "underlying": underlying,
        "time_scope": "current" if current or not clarification else None,
        "expiry_preference": expiry_pref,
        "contract_type_preference": contract_pref,
        "strike_preference": "explicit_anchor" if strike_explicit else "around_reference",
        "strike_anchor": strike,
        "call_put_scope": cp if instrument == "option" else None,
        "session_preference": "current_or_latest_regular",
        "requested_context_types": ["liveish_observation", "official_eod_reference"],
        "explicit_constraints": explicit_constraints,
        "inferred_preferences": inferred,
        "clarification_required": clarification,
        "clarification_reason": "product_not_identified" if clarification else None,
        "forbidden_fallbacks": ["trade_execution", "broker_instruction", "investment_intent_inference"],
    }


def parse_exact_contract_intent(text: str) -> dict[str, Any]:
    t = str(text or "").strip()
    parts = re.split(r"[\s/,]+", t)
    if len(parts) >= 4 and parts[0].upper() in {"TXO", "TX"}:
        product = parts[0].upper()
        if product == "TXO" and re.fullmatch(r"\d{6}(?:W\d)?", parts[1].upper() or "") and re.fullmatch(r"\d+(?:\.\d+)?", parts[2] or "") and parts[3].upper() in {"C", "P", "CALL", "PUT"}:
            ctype = "weekly" if "W" in parts[1].upper() else "monthly"
            if len(parts) > 4 and parts[4].lower() in {"monthly", "weekly"}:
                ctype = parts[4].lower()
            return {"schema_version": EXACT_SCHEMA_VERSION, "original_user_text": t, "intent_mode": "exact", "market": "TAIFEX", "instrument_family": "option", "product": "TXO", "underlying": "TX", "expiry": parts[1].upper(), "strike": parts[2], "call_put": "C" if parts[3].upper() in {"C", "CALL"} else "P", "contract_type": ctype, "session": "regular", "explicit_constraints": {"product": True, "expiry": True, "strike": True, "call_put": True, "contract_type": True}}
        if product == "TX" and re.fullmatch(r"\d{6}", parts[1] if len(parts)>1 else ""):
            return {"schema_version": EXACT_SCHEMA_VERSION, "original_user_text": t, "intent_mode": "exact", "market": "TAIFEX", "instrument_family": "future", "product": "TX", "underlying": "TX", "expiry": parts[1], "contract_type": "monthly", "session": "regular", "explicit_constraints": {"product": True, "expiry": True, "contract_type": True}}
    return {"intent_mode": "not_exact"}
