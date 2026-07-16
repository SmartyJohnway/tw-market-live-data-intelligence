"""Pure adapter from M8C-01 TAIFEX MIS observations to M8 builder observations.

The adapter is intentionally fail-closed: malformed or incomplete runtime
observations are converted to metadata-only contexts, never defaulted into a
market-valued futures/options snapshot.
"""
from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Any

SCHEMA_VERSION = "m8c_taifex_mis_context_adapter.v1"
MONTHLY_YYYYMM_RE = re.compile(r"^\d{6}$")
WEEKLY_YYYYMM_MARKER_RE = re.compile(r"^\d{6}[WF]\d{1,2}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_.:/=+-]{1,96}$")
VALID_CURRENTNESS = {
    "active_session_fresh_liveish",
    "active_session_aging_liveish",
    "active_session_stale_liveish",
    "preopen",
    "indicative",
    "halted",
    "noncontinuous_phase",
    "closed_session_latest_completed",
    "special_closure_latest_completed",
    "closed_session_historical",
    "market_phase_unresolved",
    "session_alignment_unresolved",
    "source_timestamp_unresolved",
    "transport_completed_without_valid_snapshot",
    "no_accepted_mode_1",
}
FORBIDDEN_RECURSIVE_KEYS = {"raw_payload", "trueValues", "truevalues", "raw_mode_1_dictionary", "raw_rest_records", "rest_rows", "sockjs_frames", "full_option_chain", "option_chain", "raw_qid_map", "cookies", "cookie", "session_ids", "session_id"}
RECOGNIZED_MODE1_PROVENANCE_KEYS = {"last_price", "reference_price", "total_volume", "status", "source_status_code", "raw_CDate", "raw_CTime", "bid_family_1", "ask_family_1", "bid_size_family_1", "ask_size_family_1", "bid_family_2", "ask_family_2", "bid_size_family_2", "ask_size_family_2"}
ALLOWED_PROVENANCE_SOURCES = {None, "sockjs_mode_1", "exact_detail_fallback", "quote_list_fallback"}
CURRENTNESS_ALLOWED_AXES = {"overall_ai_currentness", "transport_state", "session_alignment", "market_phase", "source_timestamp_state", "quote_age_state", "calendar_evidence", "currentness_confidence", "retrieved_at_freshness_ignored_for_upgrade", "special_closure_evidence"}
OMITTED_FIELDS = [
    "numeric_qid_keys",
    "trueValues",
    "raw_mode_1_dictionary",
    "raw_rest_records",
    "raw_payload",
    "full_option_chain",
    "raw_qid_map",
    "competing_top_of_book_families",
    "cookies",
    "session_ids",
]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def _append_unique(items: list[Any], value: Any) -> None:
    if value and value not in items:
        items.append(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_value(v) for v in value]
    return value


def _provenance_source(prov: Any) -> Any:
    if isinstance(prov, dict):
        return prov.get("source")
    return None


def _is_identity_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float)) and not isinstance(value, bool)


def _is_numeric_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, Decimal)) and not isinstance(value, bool)


def _is_scalar(value: Any) -> bool:
    return _is_identity_scalar(value)


def _safe_scalar(value: Any) -> Any:
    return value if _is_identity_scalar(value) else None


def _safe_text(value: Any) -> str | None:
    value = _safe_scalar(value)
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _is_bounded_string(value: Any, *, max_length: int = 96) -> bool:
    return isinstance(value, str) and value == value.strip() and 0 < len(value) <= max_length and bool(IDENTIFIER_RE.match(value))


def _safe_bounded_text(value: Any, *, max_length: int = 96) -> str | None:
    return value if _is_bounded_string(value, max_length=max_length) else None


def _decimal_text(value: Any, *, non_negative: bool = False, positive: bool = False) -> str | None:
    if not _is_numeric_scalar(value):
        return None
    try:
        text = str(value).replace(",", "").strip()
        d = Decimal(text)
    except Exception:
        return None
    if not d.is_finite():
        return None
    if positive and d <= 0:
        return None
    if non_negative and d < 0:
        return None
    return str(d)


def _normalize_option_type(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if text in {"c", "call"}:
        return "call"
    if text in {"p", "put"}:
        return "put"
    return None


def _valid_yyyymm(value: Any) -> bool:
    if not isinstance(value, str) or not MONTHLY_YYYYMM_RE.match(value):
        return False
    try:
        datetime.strptime(value + "01", "%Y%m%d")
    except ValueError:
        return False
    return True


def _valid_contract_month_or_week(value: Any) -> bool:
    if _valid_yyyymm(value):
        return True
    if not isinstance(value, str) or not WEEKLY_YYYYMM_MARKER_RE.match(value):
        return False
    try:
        datetime.strptime(value[:6] + "01", "%Y%m%d")
    except ValueError:
        return False
    return True


def _parse_tz_timestamp_text(value: Any) -> str | None:
    value = _safe_text(value)
    if not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return value


def _source_timestamp_valid(obs: dict) -> bool:
    return _parse_tz_timestamp_text(obs.get("source_timestamp_asia_taipei")) is not None


def _canonicalization_status(value: Any) -> str:
    if isinstance(value, str) and value in {"candidate_families_agree", "top_of_book_field_family_unresolved"}:
        return value
    return "top_of_book_field_family_unresolved"


def _contract_identity_valid(obs: dict) -> bool:
    instrument = obs.get("instrument_type")
    if instrument not in {"future", "option"}:
        return False
    if obs.get("session") != "regular" or not _valid_contract_month_or_week(obs.get("contract_month_or_week")):
        return False
    for field in ("requested_product_id", "mis_cid", "runtime_symbol_id"):
        if not _is_bounded_string(obs.get(field)):
            return False
    if not _valid_contract_month_or_week(obs.get("contract_month_or_week")):
        return False
    symbol = obs.get("runtime_symbol_id")
    suffix = "-F" if instrument == "future" else "-O"
    if not isinstance(symbol, str) or not symbol.endswith(suffix):
        return False
    if instrument == "option":
        return _decimal_text(obs.get("strike_price"), positive=True) is not None and _normalize_option_type(obs.get("option_type")) in {"call", "put"}
    return True


def _stable_identity(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, (list, tuple)):
        return ":".join(_stable_identity(v) or "" for v in value)
    if isinstance(value, dict):
        parts = [f"{k}={_stable_identity(value[k]) or ''}" for k in sorted(value)]
        return ";".join(parts)
    return str(value)


def _safe_identifier(value: Any) -> str | None:
    return _safe_bounded_text(_stable_identity(value))


def _contains_forbidden_nested(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_RECURSIVE_KEYS or key_text.isdigit():
                return True
            if _contains_forbidden_nested(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_nested(item) for item in value)
    return False


def _sanitize_currentness(currentness: Any) -> dict:
    if not isinstance(currentness, dict):
        return {}
    out = {}
    for key in CURRENTNESS_ALLOWED_AXES:
        value = currentness.get(key)
        if key == "special_closure_evidence" and isinstance(value, dict):
            allowed = {"source_family", "authority_level", "target_date", "closure_date", "target_date_matches", "evidence_type"}
            out[key] = {k: v for k, v in value.items() if k in allowed and (_is_scalar(v) or isinstance(v, bool))}
        elif _is_scalar(value) or isinstance(value, bool):
            out[key] = value
    return out


def _contract_identity(obs: dict) -> dict:
    instrument = obs.get("instrument_type")
    option_type = _normalize_option_type(obs.get("option_type")) if instrument == "option" else None
    month = obs.get("contract_month_or_week") if _valid_contract_month_or_week(obs.get("contract_month_or_week")) else None
    return {
        "requested_product_id": _safe_bounded_text(obs.get("requested_product_id")),
        "mis_cid": _safe_bounded_text(obs.get("mis_cid")),
        "runtime_symbol_id": _safe_bounded_text(obs.get("runtime_symbol_id")),
        "contract_month_or_week": month,
        "strike_price": _decimal_text(obs.get("strike_price"), positive=True) if instrument == "option" else None,
        "option_type": option_type,
        "session": "regular" if obs.get("session") == "regular" else None,
    }


def _source_time(obs: dict) -> dict:
    return {
        "source_timestamp": _parse_tz_timestamp_text(obs.get("source_timestamp_asia_taipei")),
        "cdate_raw": _safe_text(obs.get("raw_CDate")),
        "ctime_raw": _safe_text(obs.get("raw_CTime")),
    }


def _accepted_mode_1_present(obs: dict) -> bool:
    if obs.get("_accepted_mode_1_from_execution") is True:
        return True
    provenance = obs.get("field_provenance") or {}
    if not isinstance(provenance, dict):
        return False
    for key in RECOGNIZED_MODE1_PROVENANCE_KEYS:
        item = provenance.get(key)
        if isinstance(item, dict) and item.get("source") == "sockjs_mode_1":
            return True
    return False


def validate_taifex_mis_runtime_observation(observation: dict) -> dict:
    """Validate one normalized M8C-01 observation for value projection eligibility."""
    obs = dict(observation or {})
    errors: list[str] = []
    source_id = obs.get("source_id")
    if source_id != "TAIFEX_MIS":
        errors.append("source_id_not_taifex_mis")
    instrument = obs.get("instrument_type")
    if instrument not in {"future", "option"}:
        errors.append("unsupported_or_missing_instrument_type")
    if obs.get("session") != "regular":
        errors.append("session_not_regular")
    month = obs.get("contract_month_or_week")
    if not _valid_contract_month_or_week(month):
        errors.append("contract_month_or_week_not_real_monthly_or_weekly")
    symbol = obs.get("runtime_symbol_id")
    suffix = "-F" if instrument == "future" else "-O" if instrument == "option" else None
    if not isinstance(symbol, str) or not suffix or not symbol.endswith(suffix):
        errors.append("runtime_symbol_suffix_mismatch")
    for field in ("requested_product_id", "mis_cid", "runtime_symbol_id"):
        if not obs.get(field):
            errors.append(f"missing_{field}")
        if not _is_bounded_string(obs.get(field)):
            errors.append(f"invalid_bounded_string_{field}")
    if not obs.get("contract_month_or_week"):
        errors.append("missing_contract_month_or_week")
    if not _is_identity_scalar(obs.get("contract_month_or_week")):
        errors.append("non_scalar_contract_month_or_week")
    if instrument == "option" and (obs.get("strike_price") in (None, "") or _normalize_option_type(obs.get("option_type")) not in {"call", "put"}):
        errors.append("incomplete_option_identity")
    for field in ("option_type", "session", "raw_CDate", "raw_CTime", "source_timestamp_asia_taipei", "source_status_code"):
        if not _is_identity_scalar(obs.get(field)):
            errors.append(f"non_scalar_{field}")
    if obs.get("strike_price") is not None and not _is_numeric_scalar(obs.get("strike_price")):
        errors.append("non_numeric_scalar_strike_price")
    if instrument == "option" and _decimal_text(obs.get("strike_price"), positive=True) is None:
        errors.append("invalid_positive_strike_price")
    candidates = obs.get("normalized_field_candidates") or {}
    if not isinstance(candidates, dict):
        errors.append("normalized_field_candidates_not_dict")
        candidates = {}
    for field in ("last_price", "reference_price", "best_bid", "best_ask"):
        if field in candidates and candidates.get(field) not in (None, "") and _decimal_text(candidates.get(field)) is None:
            errors.append(f"invalid_decimal_{field}")
    for field in ("total_volume", "best_bid_size", "best_ask_size"):
        if field in candidates and candidates.get(field) not in (None, "") and _decimal_text(candidates.get(field), non_negative=True) is None:
            errors.append(f"invalid_non_negative_{field}")
    provenance = obs.get("field_provenance") or {}
    if isinstance(provenance, dict):
        for key, item in provenance.items():
            if item is not None and (not isinstance(item, dict) or item.get("source") not in ALLOWED_PROVENANCE_SOURCES):
                errors.append(f"invalid_provenance_source_{key}")
    elif provenance not in (None, {}):
        errors.append("field_provenance_not_dict")
    if obs.get("raw_payload_retained") is not False:
        errors.append("raw_payload_retained_not_false")
    if _contains_forbidden_nested(obs):
        errors.append("forbidden_nested_source_field_present")
    currentness = obs.get("currentness") or {}
    sanitized_currentness = _sanitize_currentness(currentness)
    overall = sanitized_currentness.get("overall_ai_currentness")
    if overall not in VALID_CURRENTNESS:
        errors.append("unknown_currentness_status")
    accepted_mode_1 = _accepted_mode_1_present(obs)
    if not accepted_mode_1:
        errors.append("accepted_mode_1_provenance_missing")
    source_timestamp_valid = _source_timestamp_valid(obs)
    source_timestamp_raw = obs.get("source_timestamp_asia_taipei")
    source_timestamp_present = source_timestamp_raw not in (None, "")
    if source_timestamp_present and not source_timestamp_valid:
        errors.append("source_timestamp_malformed")
    if sanitized_currentness.get("source_timestamp_state") == "resolved" and not source_timestamp_valid:
        errors.append("source_timestamp_axis_resolved_without_valid_timestamp")
    contract_identity_valid = _contract_identity_valid(obs)
    return {
        "schema_version": "m8c_taifex_mis_adapter_validation.v1",
        "valid": not errors,
        "errors": errors,
        "accepted_mode_1_present": accepted_mode_1,
        "currentness_status": overall,
        "source_timestamp_valid": source_timestamp_valid,
        "contract_identity_valid": contract_identity_valid,
    }


def _metadata_safe_fields(obs: dict) -> dict:
    return {
        "contract_identity": _contract_identity(obs),
        "source_time": _source_time(obs),
        "source_status_code": _safe_text(obs.get("source_status_code")),
        "currentness": _sanitize_currentness(obs.get("currentness")),
    }


def _valued_safe_fields(obs: dict) -> dict:
    cands = dict(obs.get("normalized_field_candidates") or {})
    canon_status = _canonicalization_status(cands.get("canonicalization_status"))
    top = {
        "best_bid": _decimal_text(cands.get("best_bid")) if canon_status == "candidate_families_agree" else None,
        "best_ask": _decimal_text(cands.get("best_ask")) if canon_status == "candidate_families_agree" else None,
        "best_bid_size": _decimal_text(cands.get("best_bid_size"), non_negative=True) if canon_status == "candidate_families_agree" else None,
        "best_ask_size": _decimal_text(cands.get("best_ask_size"), non_negative=True) if canon_status == "candidate_families_agree" else None,
        "canonicalization_status": canon_status,
    }
    prov = obs.get("field_provenance") or {}
    fields = _metadata_safe_fields(obs)
    fields.update(
        {
            "price": {"last": _decimal_text(cands.get("last_price")), "reference": _decimal_text(cands.get("reference_price"))},
            "activity": {"total_volume": _decimal_text(cands.get("total_volume"), non_negative=True)},
            "top_of_book": top,
            "field_provenance": {
                "last": _provenance_source(prov.get("last_price")),
                "reference": _provenance_source(prov.get("reference_price")),
                "total_volume": _provenance_source(prov.get("total_volume")),
            },
        }
    )
    return fields


def adapt_taifex_mis_observation(observation: dict) -> dict:
    obs = dict(observation or {})
    validation = validate_taifex_mis_runtime_observation(obs)
    inst = obs.get("instrument_type")
    context_type = None
    builder_inst = inst
    if inst == "future":
        context_type = "official_derivatives_futures_liveish_snapshot"
        builder_inst = "futures"
    elif inst == "option":
        context_type = "official_derivatives_options_liveish_snapshot"
        builder_inst = "options"
    safe_fields = _valued_safe_fields(obs) if validation["valid"] and validation["source_timestamp_valid"] else _metadata_safe_fields(obs)
    caveats = _as_list(obs.get("caveats"))
    for caveat in [
        "regular session only",
        "monthly YYYYMM contracts only",
        "mode=1 initial state only",
        "no delta merge",
        "no reconnect",
        "no raw payload",
        "no full option chain",
        "directional interpretation forbidden",
    ]:
        _append_unique(caveats, caveat)
    if not validation["valid"]:
        _append_unique(caveats, "TAIFEX MIS observation failed strict adapter validation; market values withheld")
    return {
        "source_id": "TAIFEX_MIS",
        "source_family": "TAIFEX_MIS",
        "authority_level": "official_undocumented",
        "timing_class": "liveish_intraday_snapshot",
        "market": "taifex",
        "symbol": _safe_identifier(obs.get("runtime_symbol_id") or obs.get("symbol")),
        "instrument_type": builder_inst,
        "context_type": context_type,
        "source_timestamp": _parse_tz_timestamp_text(obs.get("source_timestamp_asia_taipei")),
        "retrieved_at_utc": _safe_text(obs.get("retrieved_at_utc")),
        "session": "regular" if obs.get("session") == "regular" else None,
        "currentness": _sanitize_currentness(obs.get("currentness")),
        "safe_fields": safe_fields,
        "omitted_fields": OMITTED_FIELDS,
        "caveats": list(dict.fromkeys(caveats)),
        "provenance": {"adapter_schema_version": SCHEMA_VERSION, "runtime_source": "M8C-01 TAIFEX MIS bounded runtime", "raw_payload_retained": False},
        "adapter_validation": validation,
        "observation_valid": validation["valid"],
        "accepted_mode_1_present": validation["accepted_mode_1_present"],
        "source_timestamp_valid": validation["source_timestamp_valid"],
        "contract_identity_valid": validation["contract_identity_valid"],
        "withhold_market_values_from_conversation": not validation["valid"],
    }


def _failure_observation(selector_result: dict, execution_result: dict, reason: str) -> dict:
    selector = _safe_identifier(selector_result.get("selector")) if isinstance(selector_result, dict) else None
    symbol = _safe_identifier(selector_result.get("runtime_symbol_id")) if isinstance(selector_result, dict) else None
    currentness = {
        "overall_ai_currentness": "transport_completed_without_valid_snapshot",
        "transport_state": execution_result.get("status"),
        "source_timestamp_state": "unresolved",
        "retrieved_at_freshness_ignored_for_upgrade": True,
    }
    return {
        "source_id": "TAIFEX_MIS",
        "source_family": "TAIFEX_MIS",
        "authority_level": "official_undocumented",
        "timing_class": "liveish_intraday_snapshot",
        "market": "taifex",
        "symbol": symbol or selector,
        "instrument_type": None,
        "context_type": None,
        "source_timestamp": None,
        "retrieved_at_utc": None,
        "session": "regular",
        "currentness": currentness,
        "safe_fields": {
            "contract_identity": {"runtime_symbol_id": symbol, "selector": selector, "session": "regular"},
            "source_time": {"source_timestamp": None, "cdate_raw": None, "ctime_raw": None},
            "source_status_code": None,
            "currentness": currentness,
        },
        "omitted_fields": OMITTED_FIELDS,
        "caveats": [reason, "metadata-only failed/missing TAIFEX MIS selector; no market values exposed"],
        "provenance": {"adapter_schema_version": SCHEMA_VERSION, "runtime_source": "M8C-01 TAIFEX MIS bounded runtime", "raw_payload_retained": False},
        "adapter_validation": {"schema_version": "m8c_taifex_mis_adapter_validation.v1", "valid": False, "errors": [reason], "accepted_mode_1_present": False, "currentness_status": "transport_completed_without_valid_snapshot", "source_timestamp_valid": False, "contract_identity_valid": False},
        "observation_valid": False,
        "accepted_mode_1_present": False,
        "source_timestamp_valid": False,
        "contract_identity_valid": False,
        "source_unavailable": True,
        "source_unavailable_reason": reason,
        "withhold_market_values_from_conversation": True,
    }


def build_taifex_mis_m8_observations(execution_result_or_observations: Any) -> list[dict]:
    if not isinstance(execution_result_or_observations, dict):
        return [adapt_taifex_mis_observation(o) for o in (execution_result_or_observations or []) if isinstance(o, dict)]
    execution_result = execution_result_or_observations
    accepted_symbols = { _stable_identity(r.get("runtime_symbol_id")) for r in execution_result.get("selector_results", []) or [] if isinstance(r, dict) and r.get("status") == "ok" and r.get("runtime_symbol_id") }
    accepted_symbols.update(_stable_identity(s) for s in (execution_result.get("transport_summary") or {}).get("accepted_symbols", []) or [])
    accepted_symbols.update(_stable_identity(s) for s in (execution_result.get("transport_summary") or {}).get("accepted_initial_state_symbols", []) or [])
    accepted_states = (execution_result.get("transport_summary") or {}).get("accepted_initial_states") or execution_result.get("accepted_initial_states") or {}
    if isinstance(accepted_states, dict):
        accepted_symbols.update(_stable_identity(s) for s in accepted_states.keys())
    raw_observations = []
    for o in execution_result.get("observations", []) or []:
        if isinstance(o, dict):
            item = dict(o)
            if _stable_identity(item.get("runtime_symbol_id")) in accepted_symbols:
                item["_accepted_mode_1_from_execution"] = True
            raw_observations.append(item)
    output = [adapt_taifex_mis_observation(o) for o in raw_observations]
    observed_symbols = {obs.get("symbol") for obs in output if obs.get("symbol")}
    for result in execution_result.get("selector_results", []) or []:
        if not isinstance(result, dict):
            continue
        symbol = _stable_identity(result.get("runtime_symbol_id"))
        if result.get("status") == "ok" or (symbol and symbol in observed_symbols):
            continue
        output.append(_failure_observation(result, execution_result, f"selector_result_{result.get('status') or 'missing'}"))
    for symbol in (execution_result.get("transport_summary") or {}).get("missing_symbols", []) or []:
        symbol = _stable_identity(symbol)
        if symbol not in observed_symbols:
            output.append(_failure_observation({"runtime_symbol_id": symbol, "status": "missing_initial_state"}, execution_result, "transport_missing_symbol"))
    return output
