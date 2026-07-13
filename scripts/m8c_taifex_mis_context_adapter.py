"""Pure adapter from M8C-01 TAIFEX MIS observations to M8 builder observations."""
from __future__ import annotations
from decimal import Decimal
from typing import Any

SCHEMA_VERSION = "m8c_taifex_mis_context_adapter.v1"

OMITTED_FIELDS = ["numeric_qid_keys", "trueValues", "raw_mode_1_dictionary", "raw_rest_records", "raw_payload", "full_option_chain", "raw_qid_map", "competing_top_of_book_families", "cookies", "session_ids"]


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


def adapt_taifex_mis_observation(observation: dict) -> dict:
    obs = dict(observation or {})
    inst = obs.get("instrument_type")
    context_type = "official_derivatives_options_liveish_snapshot" if inst == "option" else "official_derivatives_futures_liveish_snapshot"
    cands = dict(obs.get("normalized_field_candidates") or {})
    canon_status = cands.get("canonicalization_status") or "top_of_book_field_family_unresolved"
    top = {
        "best_bid": _json_value(cands.get("best_bid")) if canon_status == "candidate_families_agree" else None,
        "best_ask": _json_value(cands.get("best_ask")) if canon_status == "candidate_families_agree" else None,
        "best_bid_size": _json_value(cands.get("best_bid_size")) if canon_status == "candidate_families_agree" else None,
        "best_ask_size": _json_value(cands.get("best_ask_size")) if canon_status == "candidate_families_agree" else None,
        "canonicalization_status": canon_status,
    }
    prov = obs.get("field_provenance") or {}
    safe_fields = {
        "contract_identity": {
            "requested_product_id": obs.get("requested_product_id"),
            "mis_cid": obs.get("mis_cid"),
            "runtime_symbol_id": obs.get("runtime_symbol_id"),
            "contract_month_or_week": obs.get("contract_month_or_week"),
            "strike_price": obs.get("strike_price"),
            "option_type": obs.get("option_type"),
            "session": obs.get("session"),
        },
        "source_time": {"source_timestamp": obs.get("source_timestamp_asia_taipei"), "cdate_raw": obs.get("raw_CDate"), "ctime_raw": obs.get("raw_CTime")},
        "source_status_code": obs.get("source_status_code"),
        "currentness": obs.get("currentness"),
        "price": {"last": _json_value(cands.get("last_price")), "reference": _json_value(cands.get("reference_price"))},
        "activity": {"total_volume": _json_value(cands.get("total_volume"))},
        "top_of_book": top,
        "field_provenance": {"last": _provenance_source(prov.get("last_price")), "reference": _provenance_source(prov.get("reference_price")), "total_volume": _provenance_source(prov.get("total_volume"))},
    }
    source_ts = obs.get("source_timestamp_asia_taipei")
    return {
        "source_id": "TAIFEX_MIS", "source_family": "TAIFEX_MIS", "authority_level": "official_undocumented", "timing_class": "liveish_intraday_snapshot",
        "market": "taifex", "symbol": obs.get("runtime_symbol_id"), "instrument_type": "options" if inst == "option" else "futures", "context_type": context_type,
        "source_timestamp": source_ts, "retrieved_at_utc": obs.get("retrieved_at_utc"), "session": obs.get("session"), "currentness": obs.get("currentness"),
        "safe_fields": safe_fields, "omitted_fields": OMITTED_FIELDS, "caveats": list(dict.fromkeys((obs.get("caveats") or []) + ["regular session only", "monthly YYYYMM contracts only", "mode=1 initial state only", "no delta merge", "no reconnect", "no raw payload", "no full option chain", "directional interpretation forbidden"])),
        "provenance": {"adapter_schema_version": SCHEMA_VERSION, "runtime_source": "M8C-01 TAIFEX MIS bounded runtime", "raw_payload_retained": False},
    }


def build_taifex_mis_m8_observations(execution_result_or_observations: Any) -> list[dict]:
    observations = execution_result_or_observations.get("observations", []) if isinstance(execution_result_or_observations, dict) else execution_result_or_observations
    return [adapt_taifex_mis_observation(o) for o in (observations or []) if isinstance(o, dict)]
