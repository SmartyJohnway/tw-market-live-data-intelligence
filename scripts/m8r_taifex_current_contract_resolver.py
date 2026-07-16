from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

SCHEMA_VERSION = "m8r_derivatives_resolution_record.v1"
MAX_OPTION_CONTRACTS = 6


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rid(value: Any) -> str:
    return "m8r-res-" + hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _dec(v: Any) -> Decimal | None:
    try:
        return Decimal(str(v).replace(',', '').strip())
    except (InvalidOperation, ValueError, AttributeError):
        return None


def _fmt(v: Decimal) -> str:
    return format(v.normalize(), "f")


def _contract_type(expiry: Any) -> str:
    text = str(expiry or "").upper()
    return "weekly" if "W" in text or "F" in text else "monthly"


def _expiry_sort_key(expiry: Any) -> tuple[str, int, str]:
    e = str(expiry or "").upper()
    marker = 99
    if "W" in e:
        base, _, tail = e.partition("W"); marker = int("".join(ch for ch in tail if ch.isdigit()) or 0); return (base, marker, e)
    if "F" in e:
        base, _, tail = e.partition("F"); marker = int("".join(ch for ch in tail if ch.isdigit()) or 0); return (base, marker, e)
    return (e, marker, e)


def select_expiry(expiries: list[str], pref: str) -> str | None:
    candidates = sorted({str(e).upper() for e in expiries if e}, key=_expiry_sort_key)
    if pref == "monthly_preferred":
        candidates = [e for e in candidates if _contract_type(e) == "monthly"]
    elif pref == "weekly_preferred":
        candidates = [e for e in candidates if _contract_type(e) == "weekly"]
    return candidates[0] if candidates else None


def nearest_strikes(strikes: list[str], ref: str | int | Decimal, *, richer: bool = False) -> list[str]:
    r = _dec(ref)
    vals = sorted({_dec(s) for s in strikes if _dec(s) is not None})
    if r is None or not vals:
        return []
    mind = min(abs(v-r) for v in vals)
    selected = [v for v in vals if abs(v-r) == mind]
    if richer and len(selected) == 1:
        i = vals.index(selected[0]); selected = vals[max(0, i-1):i+2]
    return [_fmt(v) for v in selected]


def _authority(value: Any, authority: str) -> dict[str, Any]:
    return {"value": value, "authority": authority}


class CurrentUniverseProvider(Protocol):
    def discover(self, intent: dict[str, Any]) -> dict[str, Any]: ...
    def reference(self, intent: dict[str, Any], universe: dict[str, Any]) -> dict[str, Any]: ...


class FixtureUniverseProvider:
    def __init__(self, universes: list[dict[str, Any]], reference_value: str | None = "45000", reference_source: str = "fixture_mis_tx", reference_sequence: list[str | None] | None = None):
        self.universes = list(universes)
        self.reference_value = reference_value
        self.reference_source = reference_source
        self.reference_sequence = list(reference_sequence or [])
        self.calls = 0
        self.reference_calls = 0
    def discover(self, intent):
        idx = min(self.calls, len(self.universes)-1)
        self.calls += 1
        out = dict(self.universes[idx])
        out.setdefault("discovered_at_utc", utc_now())
        out.setdefault("source_family", "fixture")
        out.setdefault("raw_payload_retained", False)
        return out
    def reference(self, intent, universe):
        if self.reference_sequence:
            value = self.reference_sequence[min(self.reference_calls, len(self.reference_sequence)-1)]
            self.reference_calls += 1
        else:
            value = self.reference_value
        if value is None:
            return {"reference_source": "unavailable", "reference_value": None, "reference_timestamp": utc_now(), "reference_currentness": "unavailable"}
        return {"reference_source": self.reference_source, "reference_value": value, "reference_timestamp": utc_now(), "reference_currentness": "fixture_current"}


def target_exists(target: dict[str, Any], universe: dict[str, Any]) -> bool:
    for c in universe.get("contracts") or []:
        if not all(str(c.get(k)) == str(target.get(k)) for k in ["instrument_type", "product", "expiry", "contract_type", "session"] if target.get(k) is not None):
            continue
        if target.get("instrument_type") == "option":
            if str(c.get("strike")) != str(target.get("strike")) or str(c.get("call_put")) != str(target.get("call_put")):
                continue
        return True
    return False


def freshness_check_targets(targets: list[dict[str, Any]], universe: dict[str, Any]) -> dict[str, Any]:
    missing = [t for t in targets if not target_exists(t, universe)]
    return {"valid": not missing, "reason": None if not missing else "resolved_exact_identity_no_longer_available", "missing_targets": missing, "checked_at_utc": universe.get("discovered_at_utc") or utc_now()}


def resolve_current_contracts(intent: dict[str, Any], provider: CurrentUniverseProvider, *, now_utc: str | None = None, allow_reresolution: bool = True) -> dict[str, Any]:
    now = now_utc or utc_now()
    if intent.get("intent_mode") == "exact":
        universe_a = provider.discover(intent)
        target = {"market":"TAIFEX", "instrument_type": intent.get("instrument_family"), "product": intent.get("product"), "underlying": intent.get("underlying"), "expiry": intent.get("expiry"), "strike": intent.get("strike"), "call_put": intent.get("call_put"), "contract_type": intent.get("contract_type"), "session": intent.get("session")}
        universe_b = provider.discover(intent)
        fresh = freshness_check_targets([target], universe_b)
        if not fresh["valid"]:
            return _record(intent, universe_a, universe_b, {}, [], ["exact_contract_unavailable"], 0, now, status="exact_contract_unavailable", freshness=fresh, original_targets=[target])
        return _record(intent, universe_a, universe_b, {}, [target], [], 0, now, freshness=fresh, original_targets=[target])

    reres = 0
    original_targets: list[dict[str, Any]] | None = None
    universe_a = provider.discover(intent)
    while True:
        ref = provider.reference(intent, universe_a)
        targets, assumptions, status = _resolve_once(intent, universe_a, ref)
        if original_targets is None:
            original_targets = list(targets)
        universe_b = provider.discover(intent)
        fresh = freshness_check_targets(targets, universe_b) if targets else {"valid": False, "reason": status, "checked_at_utc": universe_b.get("discovered_at_utc") or utc_now(), "missing_targets": []}
        if status != "resolved":
            return _record(intent, universe_a, universe_b, ref, targets, assumptions, reres, now, status=status, freshness=fresh, original_targets=original_targets)
        if fresh["valid"]:
            return _record(intent, universe_a, universe_b, ref, targets, assumptions, reres, now, freshness=fresh, original_targets=original_targets)
        if not allow_reresolution or reres >= 1:
            assumptions.append({"code": "freshness_guard_failed_after_bounded_reresolution", "reason": fresh.get("reason")})
            return _record(intent, universe_a, universe_b, ref, targets, assumptions, reres, now, status="freshness_check_failed", freshness=fresh, original_targets=original_targets)
        reres += 1
        universe_a = universe_b


def _resolve_once(intent: dict[str, Any], universe: dict[str, Any], ref: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    contracts = [c for c in universe.get("contracts", []) if c.get("product") == intent.get("product") and c.get("instrument_type") == intent.get("instrument_family") and c.get("session", "regular") == "regular"]
    pref = intent.get("contract_type_preference") or "nearest_active"
    expiry = select_expiry([c.get("expiry") for c in contracts if c.get("expiry")], pref)
    if not expiry:
        return [], [{"code":"current_contract_universe_empty"}], "no_current_contract_resolved"
    chosen = [c for c in contracts if str(c.get("expiry")).upper() == expiry]
    if intent.get("instrument_family") == "future":
        t = {"market":"TAIFEX", "instrument_type":"future", "product":"TX", "underlying":"TX", "expiry": expiry, "contract_type": _contract_type(expiry), "session":"regular", "resolved_identity": {"product": _authority("TX", "explicit_user_text"), "expiry": _authority(expiry, "current_contract_resolution_policy"), "contract_type": _authority(_contract_type(expiry), "current_contract_resolution_policy"), "session": _authority("regular", "current_or_latest_regular_policy")}}
        return [t], [{"code":"nearest_active_future_selected", "expiry": expiry}], "resolved"
    if intent.get("strike_anchor"):
        anchor = intent.get("strike_anchor"); strike_authority = "nearest_listed_strike_to_explicit_anchor"; ref_status = "explicit_anchor"
    else:
        if not ref.get("reference_value") or ref.get("reference_source") == "unavailable":
            return [], [{"code":"reference_unavailable", "reference_source": ref.get("reference_source")}], "reference_unavailable"
        anchor = ref.get("reference_value"); strike_authority = "nearest_listed_strike_to_reference"; ref_status = ref.get("reference_source")
    selected_strikes = nearest_strikes([str(c.get("strike")) for c in chosen if c.get("strike") is not None], anchor)
    cp_scope = intent.get("call_put_scope") or "both"
    cps = ["C", "P"] if cp_scope == "both" else [cp_scope]
    out=[]
    for strike in selected_strikes:
        for cp in cps:
            if len(out) >= MAX_OPTION_CONTRACTS: break
            if any(str(c.get("strike")) == strike and c.get("call_put") == cp for c in chosen):
                out.append({"market":"TAIFEX", "instrument_type":"option", "product":"TXO", "underlying":"TX", "expiry":expiry, "strike":strike, "call_put":cp, "contract_type":_contract_type(expiry), "session":"regular", "resolved_identity":{"product":_authority("TXO", "explicit_user_text"), "expiry":_authority(expiry, "current_contract_resolution_policy"), "strike":_authority(strike, strike_authority), "call_put":_authority(cp, "explicit_user_text" if (intent.get("explicit_constraints") or {}).get("call_put") else "conversational_default_both"), "contract_type":_authority(_contract_type(expiry), "explicit_user_text" if (intent.get("explicit_constraints") or {}).get("contract_type") else "current_contract_resolution_policy")}})
    return out, [{"code":"expiry_policy", "value": pref, "selected_expiry": expiry, "selected_contract_type": _contract_type(expiry)}, {"code":"strike_policy", "value":"nearest_listed_to_reference", "reference_value": str(anchor), "reference_source": ref_status}, {"code":"call_put_policy", "value": cp_scope}], "resolved" if out else "no_current_contract_resolved"


def _record(intent, universe_a, universe_b, ref, targets, assumptions, reres, now_utc, *, status="resolved", freshness=None, original_targets=None):
    selected_expiry = targets[0].get("expiry") if targets else None
    return {"schema_version": SCHEMA_VERSION, "resolution_id": _rid({"intent": intent, "targets": targets, "time": now_utc}), "original_user_text": intent.get("original_user_text"), "intent_mode": intent.get("intent_mode"), "resolution_status": status if targets or status != "resolved" else "no_current_contract_resolved", "parsed_intent": intent, "resolution_policy": {"expiry_policy": intent.get("expiry_preference", "nearest_active"), "strike_policy": "nearest_listed_to_reference", "call_put_policy": "both_when_unspecified", "maximum_contracts": MAX_OPTION_CONTRACTS}, "first_resolution_time": universe_a.get("discovered_at_utc") or now_utc, "freshness_check_time": universe_b.get("discovered_at_utc") or now_utc, "second_discovery_performed": True, "discovered_universe_summary": {"available_expiries": sorted({c.get("expiry") for c in universe_a.get("contracts", []) if c.get("expiry")}), "freshness_available_expiries": sorted({c.get("expiry") for c in universe_b.get("contracts", []) if c.get("expiry")}), "selected_expiry": selected_expiry, "selected_contract_type": _contract_type(selected_expiry) if selected_expiry else None, "contract_count": len(universe_a.get("contracts", [])), "freshness_contract_count": len(universe_b.get("contracts", [])), "source_family": universe_a.get("source_family")}, "reference_observation": ref, "original_resolved_identity": original_targets or [], "final_resolved_identity": targets, "resolved_exact_targets": targets, "assumptions": assumptions, "freshness_check": freshness or {}, "reresolution_count": reres, "raw_payload_retained": False}


def _row_value(row: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if row.get(k) not in (None, "", "-"):
            return row.get(k)
    return None


def _cp(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    if text in {"C", "CALL", "買權"}: return "C"
    if text in {"P", "PUT", "賣權"}: return "P"
    return None


class TaifexMisCurrentUniverseProvider:
    """Current TAIFEX MIS universe provider retaining only normalized identities."""
    def __init__(self, *, session_factory=None, max_total_execution_seconds: int = 20):
        self.session_factory = session_factory
        self.max_total_execution_seconds = max_total_execution_seconds
        self._last_tx_reference: dict[str, Any] | None = None
        self.diagnostics: list[dict[str, Any]] = []
    def _client(self):
        import requests
        from scripts.m8c_taifex_mis_limits import RuntimeBudget
        from scripts.m8c_taifex_mis_rest_client import TaifexMisRestClient
        session = (self.session_factory or requests.Session)()
        budget = RuntimeBudget(max_total_execution_seconds=self.max_total_execution_seconds, max_accounted_payload_bytes=2_000_000, max_bootstrap_rows=2_000, max_option_chain_rows=2_000, max_frames=1, max_decoded_messages=1, max_retained_observations=1)
        return session, TaifexMisRestClient(session, budget)
    def discover(self, intent: dict[str, Any]) -> dict[str, Any]:
        session, rest = self._client(); contracts=[]; counts={"products":0,"months":0,"option_rows_examined":0,"contracts":0}
        try:
            typ = intent.get("instrument_family"); product = intent.get("product")
            symtype = "F" if typ == "future" else "O"; cid = "TXF" if product == "TX" else "TXO"
            products = rest.products('0', symtype); counts["products"] = len(products)
            if cid not in {str(r.get('CID')) for r in products}: return self._universe([], counts)
            months = rest.months(cid, '0', symtype); counts["months"] = len(months)
            expiries = [str(r.get('item') or r.get('ExpireMonth') or r.get('ContractMonth') or '').upper() for r in months]
            for expiry in [e for e in expiries if e]:
                if typ == "future":
                    try:
                        rows = rest.quote_list(cid, expiry, 'F')
                    except Exception:
                        continue
                    for row in rows:
                        symbol = str(row.get('SymbolID') or '')
                        if symbol.endswith('-F'):
                            contracts.append({"instrument_type":"future","product":"TX","expiry":expiry,"contract_type":_contract_type(expiry),"session":"regular"})
                            val = _row_value(row, 'CLastPrice', 'LastPrice', 'Last', 'ClosePrice', 'SettlementPrice')
                            if val is not None and self._last_tx_reference is None:
                                self._last_tx_reference = {"reference_source":"TAIFEX_MIS_TX_current_reference", "reference_value":str(val).replace(',',''), "reference_timestamp":utc_now(), "reference_currentness":"liveish_intraday_snapshot"}
                else:
                    # Options are bounded to the selected expiry only.  Do not scan all chains.
                    continue
            if typ == "option":
                pref = intent.get("contract_type_preference") or "nearest_active"
                selected_expiry = select_expiry([e for e in expiries if e], pref)
                counts["selected_expiry"] = selected_expiry
                counts["selected_contract_type"] = _contract_type(selected_expiry) if selected_expiry else None
                if selected_expiry:
                    try:
                        rows = rest.option_chain(cid, selected_expiry)
                        counts["selected_chain_request_status"] = "succeeded"
                    except Exception as exc:
                        rows = []
                        counts["selected_chain_request_status"] = "failed"
                        counts["selected_chain_failure_reason"] = exc.__class__.__name__
                    counts["option_chain_fetch_count"] = 1 if selected_expiry else 0
                    counts["option_rows_examined"] += len(rows)
                    for row in rows:
                        symbol = str(row.get('SymbolID') or '')
                        strike = _dec(_row_value(row, 'StrikePrice', 'Strike'))
                        cp = _cp(_row_value(row, 'CP', 'CallPut', 'OptionType'))
                        if symbol.endswith('-O') and strike is not None and cp:
                            contracts.append({"instrument_type":"option","product":"TXO","underlying":"TX","expiry":selected_expiry,"contract_type":_contract_type(selected_expiry),"session":"regular","strike":_fmt(strike),"call_put":cp})
            return self._universe(contracts, counts)
        finally:
            close=getattr(session,'close',None)
            if close: close()
    def _universe(self, contracts, counts):
        dedup = {json.dumps(c, sort_keys=True): c for c in contracts}
        out = list(dedup.values()); counts["contracts"] = len(out)
        strikes = sorted([_dec(c.get("strike")) for c in out if c.get("strike") and _dec(c.get("strike")) is not None])
        counts["strike_count"] = len({str(c.get("strike")) for c in out if c.get("strike")})
        counts["strike_min"] = _fmt(strikes[0]) if strikes else None
        counts["strike_max"] = _fmt(strikes[-1]) if strikes else None
        counts["call_count"] = sum(1 for c in out if c.get("call_put") == "C")
        counts["put_count"] = sum(1 for c in out if c.get("call_put") == "P")
        universe = {"source_family":"TAIFEX_MIS", "discovered_at_utc":utc_now(), "contracts":out, "counts":counts, "raw_payload_retained":False, "full_option_chain_retained":False, "sockjs_frames_retained":False}
        self.diagnostics.append({"stage":"discover", "source_family":"TAIFEX_MIS", "discovered_at_utc":universe["discovered_at_utc"], "counts":dict(counts), "available_expiries": sorted({c.get("expiry") for c in out if c.get("expiry")}), "raw_payload_retained": False, "full_option_chain_retained": False, "sockjs_frames_retained": False})
        return universe
    def _fetch_tx_reference(self) -> dict[str, Any]:
        session, rest = self._client()
        try:
            products = rest.products('0', 'F')
            if 'TXF' not in {str(r.get('CID')) for r in products}:
                return {"reference_source":"unavailable", "reference_value":None, "reference_timestamp":utc_now(), "reference_currentness":"unavailable", "reason":"tx_product_unavailable"}
            months = rest.months('TXF', '0', 'F')
            expiry = select_expiry([str(r.get('item') or r.get('ExpireMonth') or r.get('ContractMonth') or '').upper() for r in months], 'nearest_active')
            if not expiry:
                return {"reference_source":"unavailable", "reference_value":None, "reference_timestamp":utc_now(), "reference_currentness":"unavailable", "reason":"tx_month_unavailable"}
            rows = rest.quote_list('TXF', expiry, 'F')
            for row in rows:
                if not str(row.get('SymbolID') or '').endswith('-F'):
                    continue
                val = _row_value(row, 'CLastPrice', 'LastPrice', 'Last', 'ClosePrice', 'SettlementPrice', 'ReferencePrice')
                if val is not None:
                    return {"reference_source":"TAIFEX_MIS_TX_current_reference", "reference_value":str(val).replace(',',''), "reference_timestamp":utc_now(), "reference_currentness":"liveish_intraday_snapshot", "reference_expiry": expiry}
            return {"reference_source":"unavailable", "reference_value":None, "reference_timestamp":utc_now(), "reference_currentness":"unavailable", "reason":"tx_reference_field_unavailable"}
        except Exception as exc:
            return {"reference_source":"unavailable", "reference_value":None, "reference_timestamp":utc_now(), "reference_currentness":"unavailable", "reason":exc.__class__.__name__}
        finally:
            close=getattr(session,'close',None)
            if close: close()
    def reference(self, intent, universe):
        if intent.get("instrument_family") == "option":
            ref = self._fetch_tx_reference()
            self.diagnostics.append({"stage":"reference", "reference_acquisition_result": ref, "raw_payload_retained": False})
            if ref.get("reference_value") is not None:
                self._last_tx_reference = ref
                return ref
        if self._last_tx_reference:
            return dict(self._last_tx_reference)
        return {"reference_source":"unavailable", "reference_value":None, "reference_timestamp":utc_now(), "reference_currentness":"unavailable"}


class CompositeReferenceUniverseProvider:
    def __init__(self, primary: CurrentUniverseProvider, *, twse_reference_fetcher=None, openapi_reference_fetcher=None):
        self.primary = primary; self.twse_reference_fetcher = twse_reference_fetcher; self.openapi_reference_fetcher = openapi_reference_fetcher
    def discover(self, intent): return self.primary.discover(intent)
    def reference(self, intent, universe):
        ref = self.primary.reference(intent, universe)
        if ref.get("reference_value") is not None: return ref
        if self.twse_reference_fetcher:
            value = self.twse_reference_fetcher()
            if value is not None: return {"reference_source":"TWSE_MIS_TAIEX_current_reference", "reference_value":str(value), "reference_timestamp":utc_now(), "reference_currentness":"liveish_intraday_snapshot"}
        if self.openapi_reference_fetcher:
            value = self.openapi_reference_fetcher()
            if value is not None: return {"reference_source":"TAIFEX_OPENAPI_TX_latest_eod_reference", "reference_value":str(value), "reference_timestamp":utc_now(), "reference_currentness":"official_eod_reference"}
        return {"reference_source":"unavailable", "reference_value":None, "reference_timestamp":utc_now(), "reference_currentness":"unavailable"}


class TaifexOpenApiUniverseProvider:
    """Official EOD identity provider for enrichment/fixtures; not live availability."""
    def __init__(self, fetcher=None):
        from scripts.m8b_taifex_openapi_client import fetch_endpoint
        self.fetcher = fetcher or fetch_endpoint
    def discover(self, intent):
        product = intent.get("product"); typ = intent.get("instrument_family"); endpoint = "DailyMarketReportFut" if typ == "future" else "DailyMarketReportOpt"
        data = self.fetcher(endpoint); rows = data.get("rows", data if isinstance(data, list) else []); contracts=[]; ref=None
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict) or str(row.get("Contract") or "").strip().upper() != product: continue
            expiry = str(row.get("ContractMonth(Week)") or row.get("ContractMonth") or "").strip().upper(); session_raw = str(row.get("TradingSession") or "regular").strip(); session = "regular" if session_raw in {"一般","regular","Regular",""} else session_raw.lower()
            if not expiry or session != "regular": continue
            base={"instrument_type":typ,"product":product,"expiry":expiry,"contract_type":_contract_type(expiry),"session":"regular"}
            if typ == "future":
                contracts.append(base); ref = ref or _row_value(row, 'ClosePrice', 'LastPrice', 'Last', 'SettlementPrice')
            else:
                cp = _cp(row.get("CallPut")); strike = _dec(row.get("StrikePrice"))
                if cp and strike is not None: contracts.append({**base,"underlying":"TX","strike":_fmt(strike),"call_put":cp})
        dedup={json.dumps(c,sort_keys=True):c for c in contracts}
        return {"source_family":"TAIFEX_OPENAPI", "discovered_at_utc":utc_now(), "contracts":list(dedup.values()), "raw_payload_retained":False, "eod_reference_value": str(ref).replace(',','') if ref is not None else None}
    def reference(self, intent, universe):
        if universe.get("eod_reference_value"):
            return {"reference_source":"TAIFEX_OPENAPI_TX_latest_eod_reference", "reference_value":universe["eod_reference_value"], "reference_timestamp":universe.get("discovered_at_utc"), "reference_currentness":"official_eod_reference"}
        return {"reference_source":"unavailable", "reference_value":None, "reference_timestamp":universe.get("discovered_at_utc"), "reference_currentness":"unavailable"}
