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
    match = next((o for o in observations if str(o.get("symbol")) == str(target.get("symbol"))), None)
    if not match:
        return _failed("target_not_present_in_source_result", grouping=grouping)
    ctx = observation_to_context_observation(match, currentness_status="official_eod_reference")
    ctx["context_type"] = "official_eod_reference"
    ctx["source_family"] = source
    ctx["source_id"] = source
    ctx.setdefault("timing_class", "official_eod")
    ctx.setdefault("authority_level", "official_documented")
    ctx["currentness"] = {"currentness_status": "official_eod_reference"}
    ctx.setdefault("caveats", []).append("official EOD/reference; not intraday")
    return _ok(ctx, identity={"symbol": target.get("symbol"), "market": target.get("market")}, grouping=grouping)


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


def _returned_identity(ctx: dict[str, Any], instrument: str) -> dict[str, Any]:
    ci = ((ctx.get("safe_fields") or {}).get("contract_identity") or {})
    out = {"expiry": ci.get("contract_month_or_week"), "contract_type": "monthly" if ci.get("contract_month_or_week") else None, "session": ci.get("session")}
    if instrument == "option":
        out.update({"underlying": None, "strike": ci.get("strike_price"), "call_put": {"call": "C", "put": "P"}.get(ci.get("option_type"))})
    return {k: v for k, v in out.items() if v is not None}


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
    identity = _returned_identity(ctx, target.get("instrument_type"))
    if not identity.get("expiry") or identity.get("session") != "regular":
        return _failed("source_identity_mismatch", count=2)
    if target.get("instrument_type") == "option":
        identity["underlying"] = (target.get("derivative_identity") or {}).get("underlying") if identity.get("strike") and identity.get("call_put") else None
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
    obs = next((o for o in result.get("observations", []) if str(o.get("symbol") or o.get("product_id") or o.get("product")) in {str(target.get("symbol")), "None"}), None)
    if not obs:
        return _failed("target_not_present_in_source_result")
    obs = dict(obs); obs.setdefault("source_id", "TAIFEX_OPENAPI"); obs.setdefault("source_family", "TAIFEX_OPENAPI"); obs["context_type"] = operation.get("context_type") or obs.get("context_type"); obs.setdefault("timing_class", "official_statistics_eod"); obs.setdefault("authority_level", "official_documented"); obs.setdefault("currentness", {"currentness_status": "official_statistics_eod"}); obs.setdefault("safe_fields", {})["identity_level"] = "contract_level" if selector.get("contract_month_or_week") else "product_level"
    identity = {"expiry": selector.get("contract_month_or_week"), "contract_type": "monthly", "session": "regular"}
    if target.get("instrument_type") == "option": identity.update({"strike": selector.get("strike_price"), "call_put": "C" if selector.get("option_type") == "call" else "P"})
    return _ok(obs, identity=identity)


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
