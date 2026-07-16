from __future__ import annotations

import hashlib, json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Protocol

SCHEMA_VERSION = "m8r_derivatives_resolution_record.v1"
MAX_OPTION_CONTRACTS = 6


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rid(value: Any) -> str:
    return "m8r-res-" + hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def _dec(v: Any) -> Decimal:
    return Decimal(str(v))


def nearest_strikes(strikes: list[str], ref: str | int | Decimal, *, richer: bool = False) -> list[str]:
    vals = sorted({_dec(s) for s in strikes})
    if not vals:
        return []
    r = _dec(ref)
    mind = min(abs(v-r) for v in vals)
    selected = [v for v in vals if abs(v-r) == mind]
    if richer and len(selected) == 1:
        i = vals.index(selected[0])
        around = vals[max(0, i-1):i+2]
        selected = around
    return [format(v.normalize(), "f") for v in selected]


def _contract_type(expiry: str) -> str:
    return "weekly" if "W" in str(expiry).upper() else "monthly"


def _expiry_sort_key(expiry: str) -> tuple[str, int]:
    e = str(expiry).upper()
    if "W" in e:
        base, _, week = e.partition("W")
        return (base, int(week or 0))
    return (e, 99)


def select_expiry(expiries: list[str], pref: str) -> str | None:
    candidates = sorted({str(e).upper() for e in expiries}, key=_expiry_sort_key)
    if pref == "monthly_preferred":
        candidates = [e for e in candidates if _contract_type(e) == "monthly"]
    elif pref == "weekly_preferred":
        candidates = [e for e in candidates if _contract_type(e) == "weekly"]
    return candidates[0] if candidates else None


def _authority(value: Any, authority: str) -> dict[str, Any]:
    return {"value": value, "authority": authority}


class CurrentUniverseProvider(Protocol):
    def discover(self, intent: dict[str, Any]) -> dict[str, Any]: ...
    def reference(self, intent: dict[str, Any], universe: dict[str, Any]) -> dict[str, Any]: ...
    def freshness_check(self, targets: list[dict[str, Any]], universe: dict[str, Any]) -> dict[str, Any]: ...


class FixtureUniverseProvider:
    def __init__(self, universes: list[dict[str, Any]], reference_value: str = "45000", stale_first: bool = False):
        self.universes = list(universes)
        self.reference_value = reference_value
        self.calls = 0
        self.stale_first = stale_first
    def discover(self, intent):
        idx = min(self.calls, len(self.universes)-1)
        self.calls += 1
        return self.universes[idx]
    def reference(self, intent, universe):
        return {"reference_source": "fixture", "reference_value": self.reference_value, "reference_timestamp": utc_now(), "reference_currentness": "fixture_current"}
    def freshness_check(self, targets, universe):
        if self.stale_first:
            self.stale_first = False
            return {"valid": False, "reason": "resolved_expiry_no_longer_available"}
        return freshness_check_targets(targets, universe)


def freshness_check_targets(targets: list[dict[str, Any]], universe: dict[str, Any]) -> dict[str, Any]:
    contracts = universe.get("contracts") or []
    for target in targets:
        ok = any(all(str(c.get(k)) == str(target.get(k)) for k in ["product", "expiry", "contract_type", "session"] if target.get(k) is not None) and (target.get("instrument_type") != "option" or (str(c.get("strike")) == str(target.get("strike")) and str(c.get("call_put")) == str(target.get("call_put")))) for c in contracts)
        if not ok:
            return {"valid": False, "reason": "resolved_exact_identity_no_longer_available", "target": target}
    return {"valid": True, "reason": None}


def resolve_current_contracts(intent: dict[str, Any], provider: CurrentUniverseProvider, *, now_utc: str | None = None, allow_reresolution: bool = True) -> dict[str, Any]:
    if intent.get("intent_mode") == "exact":
        target = {"market":"TAIFEX", "instrument_type": intent.get("instrument_family"), "product": intent.get("product"), "underlying": intent.get("underlying"), "expiry": intent.get("expiry"), "strike": intent.get("strike"), "call_put": intent.get("call_put"), "contract_type": intent.get("contract_type"), "session": intent.get("session")}
        universe = provider.discover(intent)
        fresh = provider.freshness_check([target], universe)
        if not fresh.get("valid"):
            return _record(intent, universe, {}, [], ["exact_contract_unavailable"], 0, now_utc, status="exact_contract_unavailable", freshness=fresh)
        return _record(intent, universe, {}, [target], [], 0, now_utc, freshness=fresh)
    reres = 0
    while True:
        universe = provider.discover(intent)
        ref = provider.reference(intent, universe)
        targets, assumptions = _resolve_once(intent, universe, ref)
        fresh = provider.freshness_check(targets, universe)
        if fresh.get("valid") or not allow_reresolution or reres >= 1:
            if not fresh.get("valid"):
                assumptions.append({"code": "freshness_guard_failed", "reason": fresh.get("reason")})
            return _record(intent, universe, ref, targets, assumptions, reres, now_utc, freshness=fresh)
        reres += 1


def _resolve_once(intent: dict[str, Any], universe: dict[str, Any], ref: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contracts = [c for c in universe.get("contracts", []) if c.get("product") == intent.get("product") and c.get("instrument_type") == intent.get("instrument_family") and c.get("session", "regular") == "regular"]
    pref = intent.get("contract_type_preference") or "nearest_active"
    executable_pref = "monthly_preferred" if pref == "nearest_active" else pref
    expiry = select_expiry([c.get("expiry") for c in contracts if c.get("expiry")], executable_pref)
    if not expiry:
        return [], [{"code":"current_contract_universe_empty"}]
    chosen = [c for c in contracts if str(c.get("expiry")).upper() == expiry]
    if intent.get("instrument_family") == "future":
        t = {"market":"TAIFEX", "instrument_type":"future", "product":"TX", "underlying":"TX", "expiry": expiry, "contract_type": _contract_type(expiry), "session":"regular", "resolved_identity": {"product": _authority("TX", "explicit_user_text"), "expiry": _authority(expiry, "current_contract_resolution_policy"), "contract_type": _authority(_contract_type(expiry), "current_contract_resolution_policy"), "session": _authority("regular", "current_or_latest_regular_policy")}}
        return [t], [{"code":"nearest_active_future_selected", "expiry": expiry}]
    strikes = [str(c.get("strike")) for c in chosen if c.get("strike") is not None]
    anchor = intent.get("strike_anchor") or ref.get("reference_value")
    selected_strikes = nearest_strikes(strikes, anchor, richer=False)
    cp_scope = intent.get("call_put_scope") or "both"
    cps = ["C", "P"] if cp_scope == "both" else [cp_scope]
    out=[]
    for strike in selected_strikes:
        for cp in cps:
            if len(out) >= MAX_OPTION_CONTRACTS: break
            if any(str(c.get("strike")) == strike and c.get("call_put") == cp for c in chosen):
                out.append({"market":"TAIFEX", "instrument_type":"option", "product":"TXO", "underlying":"TX", "expiry":expiry, "strike":strike, "call_put":cp, "contract_type":_contract_type(expiry), "session":"regular", "resolved_identity":{"product":_authority("TXO", "explicit_user_text"), "expiry":_authority(expiry, "current_contract_resolution_policy"), "strike":_authority(strike, "nearest_listed_strike_to_reference" if not intent.get("strike_anchor") else "nearest_listed_strike_to_explicit_anchor"), "call_put":_authority(cp, "explicit_user_text" if (intent.get("explicit_constraints") or {}).get("call_put") else "conversational_default_both"), "contract_type":_authority(_contract_type(expiry), "explicit_user_text" if (intent.get("explicit_constraints") or {}).get("contract_type") else "current_contract_resolution_policy")}})
    assumptions=[{"code":"expiry_policy", "value": pref, "selected_expiry": expiry, "selected_contract_type": _contract_type(expiry)}, {"code":"strike_policy", "value":"nearest_listed_to_reference", "reference_value": str(anchor)}, {"code":"call_put_policy", "value": cp_scope}]
    return out, assumptions


def _record(intent, universe, ref, targets, assumptions, reres, now_utc, *, status="resolved", freshness=None):
    selected_expiry = targets[0].get("expiry") if targets else None
    record = {"schema_version": SCHEMA_VERSION, "resolution_id": _rid({"intent": intent, "targets": targets, "time": now_utc}), "original_user_text": intent.get("original_user_text"), "intent_mode": intent.get("intent_mode"), "resolution_status": status if targets or status != "resolved" else "no_current_contract_resolved", "parsed_intent": intent, "resolution_policy": {"expiry_policy": intent.get("expiry_preference", "nearest_active"), "strike_policy": "nearest_listed_to_reference", "call_put_policy": "both_when_unspecified", "maximum_contracts": MAX_OPTION_CONTRACTS}, "discovered_universe_summary": {"available_expiries": sorted({c.get("expiry") for c in universe.get("contracts", []) if c.get("expiry")}), "selected_expiry": selected_expiry, "selected_contract_type": _contract_type(selected_expiry) if selected_expiry else None, "contract_count": len(universe.get("contracts", []))}, "reference_observation": ref, "resolved_exact_targets": targets, "assumptions": assumptions, "freshness_check": freshness or {}, "reresolution_count": reres, "raw_payload_retained": False}
    return record

class TaifexOpenApiUniverseProvider:
    """One-shot current universe provider using official TAIFEX OpenAPI EOD rows.

    This is a bounded discovery provider for contract identities only. It retains
    normalized identities and aggregate metadata, not raw endpoint rows.
    """
    def __init__(self, fetcher=None):
        from scripts.m8b_taifex_openapi_client import fetch_endpoint
        self.fetcher = fetcher or fetch_endpoint
        self._last_reference = None
    def discover(self, intent):
        product = intent.get("product")
        typ = intent.get("instrument_family")
        endpoint = "DailyMarketReportFut" if typ == "future" else "DailyMarketReportOpt"
        data = self.fetcher(endpoint)
        rows = data.get("rows", data if isinstance(data, list) else [])
        contracts=[]
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict) or str(row.get("Contract") or "").strip().upper() != product:
                continue
            expiry = str(row.get("ContractMonth(Week)") or row.get("ContractMonth") or "").strip().upper()
            session_raw = str(row.get("TradingSession") or "regular").strip()
            session = "regular" if session_raw in {"一般", "regular", "Regular", ""} else session_raw.lower()
            if not expiry or session != "regular":
                continue
            base = {"instrument_type": typ, "product": product, "expiry": expiry, "contract_type": _contract_type(expiry), "session": "regular"}
            if typ == "future":
                contracts.append(base)
                last = row.get("ClosePrice") or row.get("LastPrice") or row.get("SettlementPrice")
                if last not in {None, "", "-"} and self._last_reference is None:
                    self._last_reference = str(last).replace(',', '')
            else:
                cp_raw = str(row.get("CallPut") or "").strip()
                cp = "C" if cp_raw in {"買權", "C", "call", "Call"} else "P" if cp_raw in {"賣權", "P", "put", "Put"} else None
                strike = str(row.get("StrikePrice") or "").replace(',', '').strip()
                if cp and strike:
                    contracts.append({**base, "strike": strike, "call_put": cp})
        dedup = {json.dumps(c, sort_keys=True): c for c in contracts}
        return {"source_family": "TAIFEX_OPENAPI", "discovered_at_utc": utc_now(), "contracts": list(dedup.values()), "raw_payload_retained": False}
    def reference(self, intent, universe):
        if self._last_reference:
            return {"reference_source":"TAIFEX_OPENAPI_futures_eod", "reference_value": self._last_reference, "reference_timestamp": universe.get("discovered_at_utc"), "reference_currentness":"official_eod_reference"}
        strikes = [c.get("strike") for c in universe.get("contracts", []) if c.get("strike")]
        if strikes:
            mid = sorted(_dec(s) for s in strikes)[len(strikes)//2]
            return {"reference_source":"listed_option_strike_midpoint_fallback", "reference_value": format(mid.normalize(), "f"), "reference_timestamp": universe.get("discovered_at_utc"), "reference_currentness":"fallback_not_market_price"}
        return {"reference_source":"unavailable", "reference_value":"0", "reference_timestamp": universe.get("discovered_at_utc"), "reference_currentness":"unavailable"}
    def freshness_check(self, targets, universe):
        return freshness_check_targets(targets, universe)
