"""Pure M8-00-05 multi-source market context builder.

Combines caller-provided observations, caller-provided source registry policy,
and M8-00-04 freshness assessments without filesystem, network, runtime,
UI, tool-server, or model access.
"""

from collections import OrderedDict, defaultdict
import re
from datetime import datetime, timezone
from typing import Any

from scripts.m8_source_freshness_evaluator import build_source_freshness_assessment
from scripts.m8_taifex_mis_currentness_bridge import assess_taifex_mis_currentness

MULTI_SOURCE_CONTEXT_SCHEMA_VERSION = "m8_00_multi_source_market_context.v1"

FORBIDDEN_SAFE_FIELD_KEYS = {
    "raw_payload",
    "raw_payload_sample",
    "source_investigation_notes",
    "bid_prices",
    "ask_prices",
    "bid_volumes",
    "ask_volumes",
    "raw_bid_ask_ladder",
    "order_book_truth",
    "trueValues",
    "truevalues",
    "raw_mode_1_dictionary",
    "raw_rest_records",
    "rest_rows",
    "sockjs_frames",
    "full_option_chain",
    "option_chain",
    "raw_qid_map",
    "cookies",
    "cookie",
    "session_ids",
    "session_id",
}

TAIFEX_MIS_ADAPTER_SCHEMA_VERSION = "m8c_taifex_mis_context_adapter.v1"
TAIFEX_MIS_ADAPTER_VALIDATION_SCHEMA_VERSION = "m8c_taifex_mis_adapter_validation.v1"
TAIFEX_MIS_METADATA_SAFE_FIELD_KEYS = {"contract_identity", "source_time", "source_status_code", "currentness"}
TAIFEX_MIS_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_.:/=+-]{1,96}$")

FORBIDDEN_INTERPRETATIONS = [
    "trading advice",
    "trading signal",
    "recommendation",
    "target price",
    "support/resistance",
    "ranking",
    "bullish/bearish recommendation",
    "capital-flow interpretation",
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


def _extend_unique(items: list[Any], values: list[Any]) -> None:
    for value in values:
        _append_unique(items, value)


def _utc_now_text(now_utc: str | None) -> str:
    return now_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _policy_lookup(source_registry: dict) -> tuple[dict[str, dict], bool]:
    if not isinstance(source_registry, dict):
        return {}, False
    sources = source_registry.get("sources")
    if not isinstance(sources, list):
        return {}, False
    lookup = {}
    for source in sources:
        if isinstance(source, dict) and source.get("source_id"):
            lookup[source["source_id"]] = source
    return lookup, bool(lookup)


def _safe_taifex_identifier(value: Any) -> str | None:
    if not isinstance(value, str) or value != value.strip() or not TAIFEX_MIS_IDENTIFIER_RE.match(value):
        return None
    return value


def _scrub_nested_safe_value(value: Any, omitted: list[str]) -> tuple[Any, bool]:
    found_forbidden = False
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_SAFE_FIELD_KEYS or key_text.isdigit():
                found_forbidden = True
                _append_unique(omitted, key_text)
                continue
            cleaned, nested_forbidden = _scrub_nested_safe_value(item, omitted)
            found_forbidden = found_forbidden or nested_forbidden
            out[key] = cleaned
        return out, found_forbidden
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            cleaned, nested_forbidden = _scrub_nested_safe_value(item, omitted)
            found_forbidden = found_forbidden or nested_forbidden
            out.append(cleaned)
        return out, found_forbidden
    return value, False


def _scrub_safe_fields(observation: dict, caveats: list[str]) -> tuple[dict, list[str], bool]:
    safe_fields = observation.get("safe_fields") or {}
    if not isinstance(safe_fields, dict):
        safe_fields = {}
    omitted = _as_list(observation.get("omitted_fields"))
    found_forbidden = False
    scrubbed = {}
    for key, value in safe_fields.items():
        key_text = str(key)
        if key_text in FORBIDDEN_SAFE_FIELD_KEYS or key_text.isdigit():
            found_forbidden = True
            _append_unique(omitted, key_text)
        else:
            cleaned, nested_forbidden = _scrub_nested_safe_value(value, omitted)
            found_forbidden = found_forbidden or nested_forbidden
            scrubbed[key] = cleaned
    if found_forbidden:
        _append_unique(caveats, "forbidden field omitted from safe_fields")
    return scrubbed, omitted, found_forbidden


def _taifex_adapter_envelope_valid(observation: dict) -> bool:
    provenance = observation.get("provenance") or {}
    validation = observation.get("adapter_validation") or {}
    if not isinstance(provenance, dict) or not isinstance(validation, dict):
        return False
    if provenance.get("adapter_schema_version") != TAIFEX_MIS_ADAPTER_SCHEMA_VERSION or provenance.get("raw_payload_retained") is not False:
        return False
    if validation.get("schema_version") != TAIFEX_MIS_ADAPTER_VALIDATION_SCHEMA_VERSION:
        return False
    bool_pairs = [
        (validation.get("valid"), observation.get("observation_valid")),
        (validation.get("accepted_mode_1_present"), observation.get("accepted_mode_1_present")),
        (validation.get("source_timestamp_valid"), observation.get("source_timestamp_valid")),
        (validation.get("contract_identity_valid"), observation.get("contract_identity_valid")),
    ]
    return all(isinstance(a, bool) and isinstance(b, bool) and a is b for a, b in bool_pairs)


def _taifex_fail_closed_bypass(observation: dict, caveats: list[str]) -> dict:
    safe_fields = observation.get("safe_fields") if isinstance(observation.get("safe_fields"), dict) else {}
    sanitized_safe_fields = {k: v for k, v in safe_fields.items() if k in TAIFEX_MIS_METADATA_SAFE_FIELD_KEYS}
    currentness = {"overall_ai_currentness": "source_specific_currentness_unresolved"}
    validation = dict(observation.get("adapter_validation") or {})
    validation.setdefault("schema_version", TAIFEX_MIS_ADAPTER_VALIDATION_SCHEMA_VERSION)
    validation.update({"valid": False, "accepted_mode_1_present": False, "source_timestamp_valid": False, "contract_identity_valid": False, "currentness_status": "source_specific_currentness_unresolved"})
    errors = _as_list(validation.get("errors"))
    _append_unique(errors, "taifex_mis_adapter_envelope_missing_or_invalid")
    validation["errors"] = errors
    obs = {
        "source_id": "TAIFEX_MIS",
        "source_family": "TAIFEX_MIS",
        "authority_level": "official_undocumented",
        "timing_class": "liveish_intraday_snapshot",
        "market": "taifex" if observation.get("market") == "taifex" else None,
        "symbol": _safe_taifex_identifier(observation.get("symbol")),
        "instrument_type": observation.get("instrument_type") if observation.get("instrument_type") in {"futures", "options", None} else None,
        "context_type": observation.get("context_type") if observation.get("context_type") in {"official_derivatives_futures_liveish_snapshot", "official_derivatives_options_liveish_snapshot", None} else None,
        "source_timestamp": None,
        "retrieved_at_utc": None,
        "session": "regular" if observation.get("session") == "regular" else None,
        "currentness": currentness,
        "safe_fields": sanitized_safe_fields,
        "omitted_fields": _as_list(observation.get("omitted_fields")),
        "caveats": _as_list(observation.get("caveats")),
        "provenance": {"adapter_schema_version": TAIFEX_MIS_ADAPTER_SCHEMA_VERSION, "raw_payload_retained": False},
        "adapter_validation": validation,
        "observation_valid": False,
        "accepted_mode_1_present": False,
        "source_timestamp_valid": False,
        "contract_identity_valid": False,
        "safe_for_ai_context": False,
        "withhold_market_values_from_conversation": True,
    }
    _append_unique(caveats, "TAIFEX MIS adapter envelope missing or invalid; market values withheld")
    return obs


def _parse_utc_timestamp_for_sort(value: Any) -> tuple[datetime | None, bool]:
    if not isinstance(value, str) or not value:
        return None, False
    text = value
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None, False
    if parsed.tzinfo is None:
        return None, False
    utc_value = parsed.astimezone(timezone.utc)
    if utc_value.utcoffset() != timezone.utc.utcoffset(utc_value):
        return None, False
    return utc_value, True


def _context_group(obs: dict) -> str | None:
    context_type = obs.get("context_type")
    if context_type in {"official_derivatives_futures_liveish_snapshot", "official_derivatives_options_liveish_snapshot"}:
        return "derivatives_liveish"
    if context_type in {"official_derivatives_futures_eod_reference", "official_derivatives_options_eod_reference"}:
        return "derivatives_official_eod"
    if context_type == "official_derivatives_large_trader_open_interest_reference" or context_type == "official_derivatives_put_call_ratio_reference":
        return "derivatives_statistics"
    if context_type == "official_derivatives_final_settlement_reference":
        return "derivatives_final_settlement"
    if context_type == "official_derivatives_block_trade_reference":
        return "derivatives_block_trade"
    if context_type in {"official_equity_eod_reference", "official_etf_eod_reference", "official_market_eod_reference"}:
        return "cash_market_official_eod"
    if obs.get("source_id") == "TWSE_MIS":
        return "cash_market_liveish"
    return None

def _unknown_assessment(observation: dict) -> dict:
    return {
        "source_id": observation.get("source_id"),
        "source_family": observation.get("source_family"),
        "authority_level": "unknown",
        "timing_class": "unknown",
        "freshness_assessment": "unknown",
        "ai_exposure_level": "metadata_only",
        "runtime_executable": False,
        "requires_caveats": True,
        "safe_for_ai_context": False,
        "caveats": ["unknown source_id was included only as caveated metadata"],
    }


def _has_official_same_group(contexts: list[dict]) -> bool:
    return any(str(ctx.get("authority_level", "")).startswith("official") for ctx in contexts)


def _classify_context_flags(ctx: dict, has_official_group_source: bool) -> None:
    freshness = ctx["freshness_assessment"]
    timing = ctx["timing_class"]
    unavailable = bool(ctx["source_unavailable"])
    primary = False
    supporting = False
    metadata = False
    if freshness == "fresh_intraday_snapshot" and ctx["source_id"] == "TWSE_MIS":
        primary = True
    elif freshness == "stale_intraday_snapshot":
        _append_unique(ctx["caveats"], "stale source must not be described as current market")
    elif freshness == "official_eod_reference":
        primary = True
        _append_unique(ctx["caveats"], "EOD source must not be described as realtime or current price")
    elif freshness == "official_statistics_eod":
        primary = True
        _append_unique(ctx["caveats"], "official statistics EOD must not be described as live derivatives signal or leading indicator")
    elif freshness == "manual_snapshot":
        _append_unique(ctx["caveats"], "manual evidence cannot override official source")
        if has_official_group_source:
            supporting = True
    elif freshness == "validation_only":
        supporting = True
        _append_unique(ctx["caveats"], "validation-only source cannot be primary context")
    elif freshness == "credential_gated_metadata_only" or timing == "credential_gated_research":
        metadata = True
        _append_unique(ctx["caveats"], "credential-gated source is metadata-only and not runtime dependency")
    elif freshness == "source_unavailable" or unavailable:
        metadata = True
        _append_unique(ctx["caveats"], "source unavailable; context is metadata-only")
    elif freshness == "unknown":
        metadata = True
        _append_unique(ctx["caveats"], "unknown source_id was included only as caveated metadata")
    if unavailable:
        primary = False
        metadata = True
    if freshness in {"stale_intraday_snapshot", "manual_snapshot", "validation_only", "credential_gated_metadata_only", "unknown", "source_unavailable"}:
        primary = False
    ctx["primary_context_allowed"] = primary
    ctx["supporting_context_only"] = supporting or freshness == "validation_only"
    ctx["metadata_only"] = metadata


def _label(summary: dict) -> str:
    if summary["has_unknown_sources"]:
        return "contains_unknown_sources"
    if summary["has_unavailable_sources"]:
        return "contains_unavailable_sources"
    if summary.get("has_taifex_mis_stale_liveish"):
        return "contains_taifex_mis_stale_liveish"
    if summary["has_stale_sources"]:
        return "contains_stale_sources"
    if summary["has_liveish_intraday_snapshot"] and (summary["has_official_eod_reference"] or summary["has_official_statistics_eod"]):
        return "mixed_liveish_and_eod_context"
    if summary["has_liveish_intraday_snapshot"]:
        return "liveish_intraday_snapshot_only"
    if summary["has_official_eod_reference"] and not summary["has_official_statistics_eod"]:
        return "official_eod_reference_only"
    if summary["has_official_statistics_eod"] and not summary["has_official_eod_reference"]:
        return "official_statistics_eod_only"
    if summary["has_official_eod_reference"] or summary["has_official_statistics_eod"] or summary["has_regulatory_reference"]:
        return "mixed_reference_context"
    if summary["has_manual_snapshot"] or summary["has_validation_only"]:
        return "manual_or_validation_only_context"
    if summary["has_credential_gated_metadata_only"]:
        return "credential_gated_metadata_only"
    if summary.get("has_taifex_mis_aging_liveish"):
        return "taifex_mis_aging_liveish_context"
    if summary.get("has_taifex_mis_phase_caveated"):
        return "taifex_mis_phase_caveated_context"
    if summary.get("has_taifex_mis_closed_reference"):
        return "taifex_mis_closed_reference_context"
    if summary.get("has_taifex_mis_unresolved"):
        return "taifex_mis_unresolved_context"
    if summary.get("has_taifex_mis_metadata_only"):
        return "taifex_mis_metadata_only_context"
    if summary.get("has_taifex_mis_observation"):
        return "taifex_mis_caveated_context"
    return "empty_context"


def build_multi_source_market_context(observations: list[dict], source_registry: dict, *, now_utc: str | None = None) -> dict:
    observations = list(observations or [])
    generated_at = _utc_now_text(now_utc)
    lookup, registry_valid = _policy_lookup(source_registry)
    cross_caveats: list[str] = ["retrieved_at_utc is not exchange timestamp"]
    if not observations:
        cross_caveats = []

    source_summaries: OrderedDict[str, dict] = OrderedDict()
    grouped: OrderedDict[tuple[Any, Any, Any], dict] = OrderedDict()
    all_contexts: list[dict] = []
    forbidden_scrubbed = False

    for obs in observations:
        obs = dict(obs or {})
        sid = obs.get("source_id")
        policy = lookup.get(sid)
        known = policy is not None
        caveats = []
        _extend_unique(caveats, _as_list(obs.get("caveats")))
        if known and sid == "TAIFEX_MIS" and not _taifex_adapter_envelope_valid(obs):
            obs = _taifex_fail_closed_bypass(obs, caveats)
        if known and sid == "TAIFEX_MIS":
            assessment = assess_taifex_mis_currentness(obs, policy, now_utc=now_utc)
        else:
            assessment = build_source_freshness_assessment(obs, policy, now_utc=now_utc) if known else _unknown_assessment(obs)
        _extend_unique(caveats, _as_list(assessment.get("caveats")))
        safe_fields, omitted_fields, did_scrub = _scrub_safe_fields(obs, caveats)
        forbidden_scrubbed = forbidden_scrubbed or did_scrub
        ctx = {
            "source_id": sid,
            "source_family": obs.get("source_family") or (policy or {}).get("source_family"),
            "context_type": obs.get("context_type"),
            "authority_level": assessment.get("authority_level") or (policy or {}).get("authority_level") or "unknown",
            "timing_class": assessment.get("timing_class") or (policy or {}).get("timing_class") or "unknown",
            "freshness_assessment": assessment.get("freshness_assessment", "unknown"),
            "ai_exposure_level": assessment.get("ai_exposure_level") or (policy or {}).get("ai_exposure_level") or "metadata_only",
            "source_timestamp": obs.get("source_timestamp"),
            "retrieved_at_utc": obs.get("retrieved_at_utc"),
            "market_date": obs.get("market_date"),
            "symbol": obs.get("symbol"),
            "market": obs.get("market"),
            "instrument_type": obs.get("instrument_type"),
            "context_role": assessment.get("context_role"),
            "overall_ai_currentness": assessment.get("overall_ai_currentness"),
            "withhold_market_values_from_conversation": bool(assessment.get("withhold_market_values_from_conversation")),
            "safe_for_ai_context": bool(assessment.get("safe_for_ai_context")),
            "policy_ai_context_allowed": bool(assessment.get("policy_ai_context_allowed", (policy or {}).get("ai_context_allowed"))),
            "state_specific_context_allowed": bool(assessment.get("state_specific_context_allowed", True)),
            "observation_valid": bool(assessment.get("observation_valid", True)),
            "taifex_mis_role_detail": assessment.get("taifex_mis_role_detail"),
            "trading_date": obs.get("trading_date"),
            "session_state": obs.get("session_state"),
            "endpoint_contract_id": obs.get("endpoint_contract_id"),
            "trade_date": obs.get("trade_date"),
            "currentness": obs.get("currentness"),
            "session": obs.get("session"),
            "provenance": obs.get("provenance"),
            "context_group": _context_group(obs),
            "safe_fields": safe_fields,
            "omitted_fields": omitted_fields,
            "caveats": caveats,
            "primary_context_allowed": False,
            "supporting_context_only": False,
            "metadata_only": False,
            "source_unavailable": bool(obs.get("source_unavailable")),
            "source_unavailable_reason": obs.get("source_unavailable_reason"),
            "not_trading_signal": True,
            "not_recommendation": True,
        }
        if not known:
            _append_unique(ctx["caveats"], "unknown source_id was included only as caveated metadata")
        key = (obs.get("symbol") or (obs.get("aggregate_identity") or {}).get("context_type"), obs.get("market"), obs.get("instrument_type"))
        if key not in grouped:
            grouped[key] = {"symbol": obs.get("symbol"), "name": obs.get("name"), "market": obs.get("market"), "instrument_type": obs.get("instrument_type"), "context_group": _context_group(obs), "contexts": []}
        grouped[key]["contexts"].append(ctx)
        all_contexts.append(ctx)
        summary = source_summaries.setdefault(sid, {"source_id": sid, "source_family": ctx["source_family"], "authority_level": ctx["authority_level"], "timing_class": ctx["timing_class"], "freshness_assessments": [], "ai_exposure_level": ctx["ai_exposure_level"], "runtime_executable": bool((policy or {}).get("runtime_executable")), "observation_count": 0, "has_stale_observation": False, "has_unavailable_observation": False, "caveats": []})
        summary["observation_count"] += 1
        _append_unique(summary["freshness_assessments"], ctx["freshness_assessment"])
        summary["has_stale_observation"] |= ctx["freshness_assessment"] == "stale_intraday_snapshot" or ctx.get("taifex_mis_role_detail") == "active_stale"
        summary["has_unavailable_observation"] |= ctx["freshness_assessment"] == "source_unavailable" or ctx["source_unavailable"]
        _extend_unique(summary["caveats"], ctx["caveats"])

    for group in grouped.values():
        has_official = _has_official_same_group(group["contexts"])
        for ctx in group["contexts"]:
            _classify_context_flags(ctx, has_official)
            if ctx.get("source_id") == "TAIFEX_MIS":
                role = ctx.get("context_role")
                ctx["primary_context_allowed"] = role == "primary_current_liveish" and ctx.get("safe_for_ai_context")
                ctx["supporting_context_only"] = role in {"supporting_caveated", "supporting_phase_caveated", "supporting_closed_reference", "supporting_historical"}
                ctx["metadata_only"] = role == "metadata_only" or ctx.get("freshness_assessment") == "source_unavailable" or not ctx.get("safe_for_ai_context")

    assessments = [ctx["freshness_assessment"] for ctx in all_contexts]
    parsed_retrieved_values = []
    retrieved_parse_failed = False
    for ctx in all_contexts:
        original = ctx.get("retrieved_at_utc")
        if not original:
            continue
        parsed, ok = _parse_utc_timestamp_for_sort(original)
        if ok and parsed is not None:
            parsed_retrieved_values.append((parsed, original))
        else:
            retrieved_parse_failed = True
    most_recent_retrieved_at_utc = max(parsed_retrieved_values, key=lambda item: item[0])[1] if parsed_retrieved_values else None
    freshness_summary = {
        "has_liveish_source_family_observation": any(ctx["timing_class"] == "liveish_intraday_snapshot" for ctx in all_contexts),
        "has_liveish_intraday_snapshot": "fresh_intraday_snapshot" in assessments,
        "has_official_eod_reference": "official_eod_reference" in assessments,
        "has_official_statistics_eod": "official_statistics_eod" in assessments,
        "has_regulatory_reference": "regulatory_reference" in assessments,
        "has_manual_snapshot": "manual_snapshot" in assessments,
        "has_validation_only": "validation_only" in assessments,
        "has_credential_gated_metadata_only": "credential_gated_metadata_only" in assessments,
        "has_stale_sources": any(ctx["freshness_assessment"] == "stale_intraday_snapshot" or ctx.get("taifex_mis_role_detail") == "active_stale" for ctx in all_contexts),
        "has_taifex_mis_observation": any(ctx["source_id"] == "TAIFEX_MIS" for ctx in all_contexts),
        "has_taifex_mis_primary_current": any(ctx["source_id"] == "TAIFEX_MIS" and ctx.get("primary_context_allowed") for ctx in all_contexts),
        "has_taifex_mis_caveated_liveish": any(ctx["source_id"] == "TAIFEX_MIS" and ctx["freshness_assessment"] == "caveated_intraday_snapshot" for ctx in all_contexts),
        "has_taifex_mis_aging_liveish": any(ctx["source_id"] == "TAIFEX_MIS" and ctx.get("taifex_mis_role_detail") == "active_aging" for ctx in all_contexts),
        "has_taifex_mis_stale_liveish": any(ctx["source_id"] == "TAIFEX_MIS" and ctx.get("taifex_mis_role_detail") == "active_stale" for ctx in all_contexts),
        "has_taifex_mis_phase_caveated": any(ctx["source_id"] == "TAIFEX_MIS" and ctx.get("taifex_mis_role_detail") in {"preopen", "indicative", "halted", "noncontinuous_phase"} for ctx in all_contexts),
        "has_taifex_mis_closed_reference": any(ctx["source_id"] == "TAIFEX_MIS" and ctx["freshness_assessment"] == "closed_session_reference" for ctx in all_contexts),
        "has_taifex_mis_unresolved": any(ctx["source_id"] == "TAIFEX_MIS" and ctx["freshness_assessment"] == "source_specific_currentness_unresolved" for ctx in all_contexts),
        "has_taifex_mis_metadata_only": any(ctx["source_id"] == "TAIFEX_MIS" and ctx.get("metadata_only") for ctx in all_contexts),
        "has_taifex_mis_policy_blocked": any(ctx["source_id"] == "TAIFEX_MIS" and not ctx.get("policy_ai_context_allowed") for ctx in all_contexts),
        "taifex_mis_role_details": sorted({ctx.get("taifex_mis_role_detail") for ctx in all_contexts if ctx["source_id"] == "TAIFEX_MIS" and ctx.get("taifex_mis_role_detail")}),
        "taifex_mis_currentness_statuses": sorted({ctx.get("overall_ai_currentness") for ctx in all_contexts if ctx["source_id"] == "TAIFEX_MIS" and ctx.get("overall_ai_currentness")}),
        "has_unavailable_sources": any(ctx["source_unavailable"] or ctx["freshness_assessment"] == "source_unavailable" for ctx in all_contexts),
        "has_unknown_sources": "unknown" in assessments,
        "most_recent_retrieved_at_utc": most_recent_retrieved_at_utc,
        "caveated_currentness_label": "empty_context",
    }
    freshness_summary["caveated_currentness_label"] = _label(freshness_summary)

    if retrieved_parse_failed:
        _append_unique(cross_caveats, "one or more retrieved_at_utc values could not be parsed for most-recent comparison")
    if freshness_summary["has_official_eod_reference"]:
        _append_unique(cross_caveats, "EOD source must not be described as realtime")
    if freshness_summary["has_official_statistics_eod"]:
        _append_unique(cross_caveats, "official statistics EOD must not be described as live derivatives signal or leading indicator")
    if freshness_summary["has_stale_sources"]:
        _append_unique(cross_caveats, "stale source must not be described as current market")
    if freshness_summary["has_manual_snapshot"]:
        _append_unique(cross_caveats, "manual evidence cannot override official source")
    if freshness_summary["has_validation_only"]:
        _append_unique(cross_caveats, "validation-only source cannot be primary context")
    if freshness_summary["has_credential_gated_metadata_only"]:
        _append_unique(cross_caveats, "credential-gated source is metadata-only and not runtime dependency")
    if freshness_summary["has_liveish_intraday_snapshot"] and (freshness_summary["has_official_eod_reference"] or freshness_summary["has_official_statistics_eod"]):
        _append_unique(cross_caveats, "mixed live-ish and EOD sources require caveated wording")
    if freshness_summary["has_unknown_sources"]:
        _append_unique(cross_caveats, "unknown source_id was included only as caveated metadata")
    if forbidden_scrubbed:
        _append_unique(cross_caveats, "forbidden raw fields were omitted from safe_fields")

    usable = any(ctx["safe_fields"] and ctx["freshness_assessment"] not in {"unknown", "source_unavailable", "credential_gated_metadata_only"} and not ctx.get("metadata_only") and (ctx.get("source_id") != "TAIFEX_MIS" or ctx.get("safe_for_ai_context")) for ctx in all_contexts)
    all_blocked = bool(all_contexts) and all(ctx["freshness_assessment"] in {"unknown", "source_unavailable", "credential_gated_metadata_only"} for ctx in all_contexts)
    safe_to_include = registry_valid and usable and not all_blocked
    requires_caveats = bool(cross_caveats) or any(ctx["caveats"] for ctx in all_contexts)
    status = "empty_context" if not observations else ("candidate_built_with_caveats" if requires_caveats else "candidate_built")

    return {
        "schema_version": MULTI_SOURCE_CONTEXT_SCHEMA_VERSION,
        "context_status": status,
        "generated_at_utc": generated_at,
        "market_scope": {},
        "sources": list(source_summaries.values()),
        "freshness_summary": freshness_summary,
        "instrument_contexts": list(grouped.values()),
        "cross_source_caveats": cross_caveats,
        "ai_exposure_policy": {
            "safe_to_include_in_conversation_context": safe_to_include,
            "requires_caveats": requires_caveats,
            "blocked_fields": sorted(FORBIDDEN_SAFE_FIELD_KEYS),
            "forbidden_interpretations": FORBIDDEN_INTERPRETATIONS,
            "not_trading_signal": True,
            "not_recommendation": True,
            "not_realtime_unless_source_policy_allows": True,
            "eod_not_realtime": True,
            "retrieved_at_not_exchange_timestamp": True,
            "manual_evidence_not_official_source": True,
            "validation_only_not_primary_source": True,
        },
        "not_trading_signal": True,
        "not_recommendation": True,
    }
