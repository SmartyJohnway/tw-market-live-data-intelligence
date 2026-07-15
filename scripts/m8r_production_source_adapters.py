from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from scripts.m8a_official_eod_observation import observation_to_context_observation
from scripts.m8a_tpex_official_eod_adapter import execute_tpex_official_eod_adapter
from scripts.m8a_twse_official_eod_adapter import execute_twse_official_eod_adapter
from scripts.m8b_taifex_openapi_execution import execute_taifex_openapi_refresh
from scripts.m8c_taifex_mis_context_adapter import adapt_taifex_mis_observation
from scripts.m8c_taifex_mis_execution import execute_taifex_mis_snapshot
from scripts.probe_twse_mis_rich_fields import fetch_twse_mis_rows

NETWORK_CLASS = "planned_network_fetch"


def _issue(code: str, severity: str = "warning") -> dict[str, Any]:
    return {"code": code, "severity": severity}


def _blocked(code: str) -> dict[str, Any]:
    return {"status": "blocked", "network_attempted": False, "adapter_invocation_count": 1, "network_request_count": 0, "source_observation": {}, "returned_identity": {}, "source_health": {}, "currentness": {}, "issues": [_issue(code)], "retained_artifacts": [], "grouping": {"grouped": False}}


def _failed(code: str, *, network_attempted: bool = True, count: int = 1, grouping: dict | None = None) -> dict[str, Any]:
    return {"status": "failed", "network_attempted": network_attempted, "adapter_invocation_count": 1, "network_request_count": count if network_attempted else 0, "source_observation": {}, "returned_identity": {}, "source_health": {}, "currentness": {}, "issues": [_issue(code)], "retained_artifacts": [], "grouping": grouping or {"grouped": False}}


def _ok(obs: dict[str, Any], *, identity: dict | None = None, count: int = 1, grouping: dict | None = None) -> dict[str, Any]:
    return {"status": "succeeded", "network_attempted": True, "adapter_invocation_count": 1, "network_request_count": count, "source_observation": obs, "returned_identity": identity or {}, "source_health": {}, "currentness": obs.get("currentness") or {}, "issues": [], "retained_artifacts": [], "grouping": grouping or {"grouped": False}}


def _exception_result(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, TimeoutError):
        return _failed("source_timeout")
    if isinstance(exc, ConnectionError):
        return _failed("source_connection_failed")
    return _failed("source_payload_invalid")


def _require_network(allow_network: bool) -> dict[str, Any] | None:
    return None if allow_network is True else _blocked("network_execution_not_enabled")


def _twse_query_id(target: dict[str, Any], route: str | None) -> str | None:
    market = target.get("market")
    typ = target.get("instrument_type")
    symbol = target.get("symbol")
    if market == "TWSE" and typ in {"equity", "etf"} and route == f"tse_{str(symbol).lower()}.tw":
        return route
    if market == "TPEX" and typ in {"equity", "etf"} and route == f"otc_{str(symbol).lower()}.tw":
        return route
    if market == "TWSE" and typ == "index" and symbol == "TAIEX" and route == "tse_t00.tw":
        return route
    return None


def execute_twse_mis_operation(*, operation: dict[str, Any], target: dict[str, Any], plan: dict[str, Any], execution_time_utc: str, allow_network: bool) -> dict[str, Any]:
    if (gate := _require_network(allow_network)):
        return gate
    qid = _twse_query_id(target or {}, operation.get("route"))
    if not qid:
        return _blocked("approved_target_route_not_supported")
    try:
        rows, failures, telemetry = fetch_twse_mis_rows([qid])
    except Exception as exc:
        return _exception_result(exc)
    if failures or not rows:
        return _failed("source_payload_invalid")
    row = rows[0]
    if str(row.get("key") or row.get("ex") + "_" + row.get("ch", "") if row.get("ex") else "") not in {qid, ""} and str(row.get("key")) != qid:
        return _failed("source_identity_mismatch")
    if str(row.get("c") or row.get("ch") or "").split(".")[0].upper() not in {str(target.get("symbol")).upper(), "T00"}:
        return _failed("source_identity_mismatch")
    obs = {"source_id": "TWSE_MIS", "source_family": "TWSE_MIS", "authority_level": "official_undocumented", "timing_class": "liveish_intraday_snapshot", "market": target.get("market"), "symbol": target.get("symbol"), "instrument_type": target.get("instrument_type"), "context_type": "liveish_observation", "source_timestamp": " ".join(x for x in [row.get("d"), row.get("t")] if x) or None, "retrieved_at_utc": execution_time_utc, "safe_fields": {"query_id": qid, "last_price": row.get("z"), "previous_close": row.get("y"), "open": row.get("o"), "high": row.get("h"), "low": row.get("l"), "volume": row.get("v")}, "currentness": {"currentness_status": "source_specific_currentness_unresolved"}, "caveats": ["live-ish snapshot; not exchange-guaranteed realtime"]}
    return _ok(obs, identity={"query_id": qid, "symbol": target.get("symbol"), "market": target.get("market")})


def _openapi_result(source: str, target: dict[str, Any], executor: Callable[[list[str]], dict[str, Any]]) -> dict[str, Any]:
    grouping = {"grouped": True, "network_scope": "whole_market_endpoint", "retention_scope": "approved_targets_only"}
    try:
        result = executor([target.get("symbol")])
    except Exception as exc:
        out = _exception_result(exc); out["grouping"] = grouping; return out
    observations = result.get("observations") or []
    symbol_matches = [o for o in observations if str(o.get("symbol")) == str(target.get("symbol"))]
    if not symbol_matches:
        return _failed("target_not_present_in_source_result", grouping=grouping)
    expected_market = "listed" if source == "TWSE_OPENAPI" else "tpex_otc"
    expected_target_market = "TWSE" if source == "TWSE_OPENAPI" else "TPEX"
    for match in symbol_matches:
        if match.get("source_id") != source:
            return _failed("source_identity_mismatch", grouping=grouping)
        if match.get("market") not in {expected_market, expected_target_market}:
            return _failed("source_market_mismatch", grouping=grouping)
        if match.get("instrument_type") != target.get("instrument_type"):
            return _failed("source_instrument_type_mismatch", grouping=grouping)
        ctx = observation_to_context_observation(match, currentness_status="official_eod_reference")
        ctx["context_type"] = "official_eod_reference"
        ctx.setdefault("timing_class", "official_eod")
        ctx.setdefault("authority_level", "official_documented")
        ctx["currentness"] = {"currentness_status": "official_eod_reference"}
        ctx.setdefault("caveats", []).append("official EOD/reference; not intraday")
        return _ok(ctx, identity={"symbol": target.get("symbol"), "market": target.get("market"), "source_id": source}, grouping=grouping)
    return _failed("source_identity_mismatch", grouping=grouping)

def execute_twse_openapi_operation(*, operation, target, plan, execution_time_utc, allow_network):
    if (gate := _require_network(allow_network)):
        return gate
    if target.get("market") != "TWSE":
        return _blocked("approved_target_route_not_supported")
    return _openapi_result("TWSE_OPENAPI", target, lambda syms: execute_twse_official_eod_adapter(syms))


def execute_tpex_openapi_operation(*, operation, target, plan, execution_time_utc, allow_network):
    if (gate := _require_network(allow_network)):
        return gate
    if target.get("market") != "TPEX":
        return _blocked("approved_target_route_not_supported")
    return _openapi_result("TPEX_OPENAPI", target, lambda syms: execute_tpex_official_eod_adapter(syms))


def _strike(v: Any) -> str | None:
    try: return format(Decimal(str(v)).normalize(), "f")
    except (InvalidOperation, ValueError): return None



TAIFEX_OPTION_UNDERLYING_BY_PRODUCT = {"TXO": "TX"}


def _norm_call_put(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if text in {"c", "call", "買權"}:
        return "C"
    if text in {"p", "put", "賣權"}:
        return "P"
    return None


def _obs_contract_identity(obs: dict[str, Any]) -> dict[str, Any]:
    safe = obs.get("safe_fields") if isinstance(obs.get("safe_fields"), dict) else {}
    ci = obs.get("contract_identity") if isinstance(obs.get("contract_identity"), dict) else None
    if ci is None:
        ci = safe.get("contract_identity") if isinstance(safe.get("contract_identity"), dict) else {}
    return dict(ci or {})


def _obs_aggregate_identity(obs: dict[str, Any]) -> dict[str, Any]:
    safe = obs.get("safe_fields") if isinstance(obs.get("safe_fields"), dict) else {}
    ai = obs.get("aggregate_identity") if isinstance(obs.get("aggregate_identity"), dict) else None
    if ai is None:
        ai = safe.get("aggregate_identity") if isinstance(safe.get("aggregate_identity"), dict) else {}
    return dict(ai or {})


def _taifex_product(obs: dict[str, Any], ci: dict[str, Any], ai: dict[str, Any]) -> str | None:
    for value in (ci.get("product_id"), obs.get("product_id"), obs.get("symbol"), obs.get("product"), ai.get("product_id")):
        if value:
            return str(value)
    return None


def _taifex_returned_contract_identity(obs: dict[str, Any], instrument_type: str) -> tuple[str, dict[str, Any], str]:
    ci = _obs_contract_identity(obs)
    ai = _obs_aggregate_identity(obs)
    product = _taifex_product(obs, ci, ai)
    if ci:
        expiry = ci.get("contract_month_or_week") or ci.get("contract_month") or ci.get("delivery_month") or ci.get("settlement_month")
        session = ci.get("session") or obs.get("session")
        returned = {"product": product, "expiry": expiry, "contract_type": "monthly" if expiry and str(expiry).isdigit() and len(str(expiry)) == 6 else None}
        if session and session != "not_applicable":
            returned["session"] = session
        if instrument_type == "option":
            returned.update({"strike": _strike(ci.get("strike_price")), "call_put": _norm_call_put(ci.get("option_type")), "underlying": ci.get("underlying") or ci.get("series")})
        return "contract_level", {k: v for k, v in returned.items() if v is not None}, "contract_identity_returned"
    if product or ai:
        returned = {"product": product or ai.get("product_id")}
        return "aggregate_level" if ai and not product else "product_level", {k: v for k, v in returned.items() if v is not None}, "product_or_aggregate_identity_returned"
    return "missing", {}, "identity_not_returned"


def _approved_identity(target: dict[str, Any]) -> dict[str, Any]:
    di = target.get("derivative_identity") or {}
    out = {"product": target.get("symbol"), "expiry": di.get("expiry"), "contract_type": di.get("contract_type"), "session": di.get("session")}
    if target.get("instrument_type") == "option":
        out.update({"underlying": di.get("underlying"), "strike": _strike(di.get("strike")), "call_put": _norm_call_put(di.get("call_put"))})
    return out


def _identity_matches_approved(returned: dict[str, Any], approved: dict[str, Any], required: tuple[str, ...]) -> bool:
    for key in required:
        rv = _strike(returned.get(key)) if key == "strike" else returned.get(key)
        av = _strike(approved.get(key)) if key == "strike" else approved.get(key)
        if rv != av:
            return False
    return True

def _taifex_selector(target: dict[str, Any]) -> dict[str, Any] | None:
    di = target.get("derivative_identity") or {}
    if target.get("market") != "TAIFEX" or di.get("contract_type") != "monthly" or di.get("session") != "regular":
        return None
    if target.get("instrument_type") == "future":
        return {"instrument_type": "future", "requested_product_id": target.get("symbol"), "contract_month_or_week": di.get("expiry"), "session": "regular"}
    if target.get("instrument_type") == "option":
        cp = {"C": "call", "P": "put", "CALL": "call", "PUT": "put"}.get(str(di.get("call_put")).upper())
        return {"instrument_type": "option", "requested_product_id": target.get("symbol"), "contract_month_or_week": di.get("expiry"), "session": "regular", "strike_price": _strike(di.get("strike")), "option_type": cp}
    return None


def _m8c_returned_identity(ctx: dict[str, Any], target: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    ci = ((ctx.get("safe_fields") or {}).get("contract_identity") or {})
    product = ci.get("requested_product_id")
    expiry = ci.get("contract_month_or_week")
    session = ci.get("session")
    runtime_symbol = ci.get("runtime_symbol_id")
    returned = {"product": product, "expiry": expiry, "contract_type": "monthly" if expiry else None, "session": session}
    approved = _approved_identity(target)
    if target.get("instrument_type") == "option":
        call_put = _norm_call_put(ci.get("option_type"))
        strike = _strike(ci.get("strike_price"))
        underlying = TAIFEX_OPTION_UNDERLYING_BY_PRODUCT.get(str(product or "").upper())
        returned.update({"strike": strike, "call_put": call_put})
        if underlying:
            returned["underlying"] = underlying
        if not (isinstance(runtime_symbol, str) and runtime_symbol.startswith(str(product or "")) and str(expiry or "") in runtime_symbol):
            return {}, "source_identity_mismatch"
        required = ("product", "expiry", "strike", "call_put", "session")
        cleaned = {k: v for k, v in returned.items() if v is not None}
        if not _identity_matches_approved(cleaned, approved, required):
            return {}, "source_identity_mismatch"
        if cleaned.get("underlying") != approved.get("underlying"):
            return {}, "exact_option_underlying_not_returned"
        return cleaned, None
    cleaned = {k: v for k, v in returned.items() if v is not None}
    if not _identity_matches_approved(cleaned, approved, ("product", "expiry", "session")):
        return {}, "source_identity_mismatch"
    return cleaned, None

def execute_taifex_mis_operation(*, operation, target, plan, execution_time_utc, allow_network):
    if (gate := _require_network(allow_network)):
        return gate
    selector = _taifex_selector(target or {})
    if not selector or (target.get("instrument_type") == "option" and not selector.get("strike_price")):
        return _blocked("exact_contract_not_supported")
    try:
        result = execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[selector], evaluation_time_asia_taipei=None)
    except Exception as exc:
        return _exception_result(exc)
    if result.get("status") not in {"successful_liveish_snapshot", "partial_source_success"} or not result.get("observations"):
        return _failed("source_payload_invalid", count=2)
    ctx = adapt_taifex_mis_observation(result["observations"][0])
    identity, issue = _m8c_returned_identity(ctx, target)
    if issue:
        return _failed(issue, count=2)
    ctx.setdefault("safe_fields", {})["contract_identity"] = identity
    return _ok(ctx, identity=identity, count=2)


setattr(execute_taifex_mis_operation, "supports_exact_derivative_identity", True)


def execute_taifex_openapi_operation(*, operation, target, plan, execution_time_utc, allow_network):
    if (gate := _require_network(allow_network)):
        return gate
    selector = _taifex_selector(target or {})
    if not selector:
        return _blocked("exact_contract_not_supported")
    context = "futures_eod" if target.get("instrument_type") == "future" else "options_eod"
    try:
        result = execute_taifex_openapi_refresh(operator_confirmed=True, requested_contexts=[context], requested_products=[target.get("symbol")], requested_contracts=[selector], requested_sessions=["regular"])
    except Exception as exc:
        return _exception_result(exc)
    observations = result.get("observations", [])
    candidates = []
    for item in observations:
        if not isinstance(item, dict):
            continue
        ci = _obs_contract_identity(item)
        ai = _obs_aggregate_identity(item)
        product = _taifex_product(item, ci, ai)
        if product == target.get("symbol"):
            candidates.append(item)
    if not candidates:
        return _failed("target_not_present_in_source_result")
    obs = dict(candidates[0])
    identity_level, returned_identity, verification = _taifex_returned_contract_identity(obs, target.get("instrument_type"))
    exact_required = operation.get("context_type") in {"official_eod_reference", "liveish_observation"}
    if identity_level != "contract_level":
        obs.setdefault("safe_fields", {})["identity_level"] = identity_level if identity_level != "missing" else "missing"
        obs["safe_fields"]["identity_verification_status"] = verification
        obs["safe_fields"]["requested_identity"] = _approved_identity(target)
        if exact_required:
            return _failed("exact_contract_identity_not_returned")
        obs.setdefault("source_id", "TAIFEX_OPENAPI"); obs.setdefault("source_family", "TAIFEX_OPENAPI"); obs["context_type"] = operation.get("context_type") or obs.get("context_type"); obs.setdefault("timing_class", "official_statistics_eod"); obs.setdefault("authority_level", "official_documented"); obs.setdefault("currentness", {"currentness_status": "official_statistics_eod"})
        return _ok(obs, identity=returned_identity)
    approved = _approved_identity(target)
    required = ("product", "expiry", "contract_type")
    if target.get("instrument_type") == "option":
        required = ("product", "expiry", "strike", "call_put", "contract_type")
    if returned_identity.get("session") or approved.get("session"):
        required = tuple(list(required) + ["session"])
    if not _identity_matches_approved(returned_identity, approved, required):
        return _failed("source_identity_mismatch")
    obs.setdefault("source_id", "TAIFEX_OPENAPI"); obs.setdefault("source_family", "TAIFEX_OPENAPI"); obs["context_type"] = operation.get("context_type") or obs.get("context_type"); obs.setdefault("timing_class", "official_statistics_eod"); obs.setdefault("authority_level", "official_documented"); obs.setdefault("currentness", {"currentness_status": "official_statistics_eod"})
    obs.setdefault("safe_fields", {})["identity_level"] = "contract_level"
    obs["safe_fields"]["identity_verification_status"] = "matched_approved_target"
    obs["safe_fields"]["requested_identity"] = approved
    obs["safe_fields"]["contract_identity"] = returned_identity
    return _ok(obs, identity=returned_identity)


setattr(execute_taifex_openapi_operation, "supports_exact_derivative_identity", True)


def build_production_executor_registry(local_source_health_executor: Callable[..., Any] | None = None, local_market_clock_executor: Callable[..., Any] | None = None) -> dict[tuple[str, str | None], Callable[..., Any]]:
    reg = {
        (NETWORK_CLASS, "TWSE_MIS"): execute_twse_mis_operation,
        (NETWORK_CLASS, "TWSE_OPENAPI"): execute_twse_openapi_operation,
        (NETWORK_CLASS, "TPEX_OPENAPI"): execute_tpex_openapi_operation,
        (NETWORK_CLASS, "TAIFEX_MIS"): execute_taifex_mis_operation,
        (NETWORK_CLASS, "TAIFEX_OPENAPI"): execute_taifex_openapi_operation,
    }
    if local_source_health_executor: reg[("local_source_health_read", None)] = local_source_health_executor
    if local_market_clock_executor: reg[("local_market_clock_evaluation", None)] = local_market_clock_executor
    return reg
