"""Pure TAIFEX MIS source-specific M8 currentness bridge."""
from __future__ import annotations
from datetime import datetime
from typing import Any

SCHEMA_VERSION = "m8_taifex_mis_currentness_bridge.v1"
PHASE_LABELS = {"preopen", "indicative", "halted", "noncontinuous_phase"}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def _append_unique(items: list[Any], value: Any) -> None:
    if value and value not in items:
        items.append(value)


def _parse_tz_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _has_value_prerequisites(obs: dict) -> bool:
    return all(
        [
            _parse_tz_timestamp(obs.get("source_timestamp")),
            obs.get("source_timestamp_valid") is not False,
            obs.get("accepted_mode_1_present") is True,
            obs.get("session") == "regular",
        ]
    )


def _valid_active_fresh_axes(obs: dict, cur: dict) -> bool:
    return all(
        [
            _has_value_prerequisites(obs),
            cur.get("source_timestamp_state") == "resolved",
            cur.get("session_alignment") == "aligned",
            cur.get("market_phase") == "active_regular_trading",
            cur.get("quote_age_state") == "fresh",
        ]
    )


def _has_official_special_closure_evidence(cur: dict) -> bool:
    evidence = cur.get("special_closure_evidence")
    if not isinstance(evidence, dict):
        return False
    return (
        evidence.get("source_family") == "TAIFEX"
        and str(evidence.get("authority_level") or "").startswith("official")
        and evidence.get("evidence_type") == "market_closure"
        and evidence.get("target_date_matches") is True
        and _valid_iso_date(evidence.get("target_date"))
    )


def assess_taifex_mis_currentness(observation: dict, source_policy: dict | None = None, *, now_utc: str | None = None) -> dict:
    """Map M8C currentness to M8 roles without retrieved_at upgrades."""
    del now_utc
    obs = dict(observation or {})
    policy = dict(source_policy or {})
    cur = dict(obs.get("currentness") or {})
    status = cur.get("overall_ai_currentness") or "source_specific_currentness_unresolved"
    policy_allowed = bool(policy.get("ai_context_allowed"))
    observation_valid = bool(obs.get("observation_valid"))
    caveats = _as_list(policy.get("caveats")) + _as_list(obs.get("caveats"))
    _append_unique(caveats, "TAIFEX MIS retrieved_at_utc must never upgrade source currentness")
    _append_unique(caveats, "TAIFEX MIS bounded live-ish observation is not realtime guaranteed")

    role = "metadata_only"
    role_detail = "metadata_only"
    assessment = "source_specific_metadata_only"
    state_allowed = False
    primary = False
    metadata = True
    withhold_values = True

    value_prerequisites = _has_value_prerequisites(obs)
    if not observation_valid:
        _append_unique(caveats, "TAIFEX MIS observation failed adapter validation; fail closed")
    elif status == "active_session_fresh_liveish":
        if _valid_active_fresh_axes(obs, cur):
            assessment = "fresh_intraday_snapshot"
            role = "primary_current_liveish"
            role_detail = "active_fresh"
            state_allowed = True
            primary = True
            metadata = False
            withhold_values = False
        else:
            assessment = "source_specific_currentness_unresolved"
            role = "metadata_only"
            role_detail = "inconsistent_active_fresh_axes"
            _append_unique(caveats, "active_session_fresh_liveish axes inconsistent; market values withheld")
    elif status == "active_session_aging_liveish":
        role_detail = "active_aging"
        _append_unique(caveats, "TAIFEX MIS aging live-ish observation must not be described as current")
        if value_prerequisites:
            assessment = "caveated_intraday_snapshot"
            role = "supporting_caveated"
            state_allowed = True
            metadata = False
            withhold_values = False
        else:
            _append_unique(caveats, "TAIFEX MIS value prerequisites missing; market values withheld")
    elif status == "active_session_stale_liveish":
        role_detail = "active_stale"
        _append_unique(caveats, "TAIFEX MIS stale live-ish observation must not be described as current")
        if value_prerequisites:
            assessment = "caveated_intraday_snapshot"
            role = "supporting_caveated"
            state_allowed = True
            metadata = False
            withhold_values = False
        else:
            _append_unique(caveats, "TAIFEX MIS value prerequisites missing; market values withheld")
    elif status in PHASE_LABELS:
        role_detail = status
        _append_unique(caveats, f"TAIFEX MIS market phase is {status}; do not treat as continuous current trading")
        if value_prerequisites:
            assessment = "caveated_intraday_snapshot"
            role = "supporting_phase_caveated"
            state_allowed = True
            metadata = False
            withhold_values = False
        else:
            _append_unique(caveats, "TAIFEX MIS value prerequisites missing; market values withheld")
    elif status == "closed_session_latest_completed":
        role_detail = "closed_latest_completed"
        _append_unique(caveats, "TAIFEX MIS closed-session latest completed snapshot is not current and is not official EOD endpoint data")
        if value_prerequisites:
            assessment = "closed_session_reference"
            role = "supporting_closed_reference"
            state_allowed = True
            metadata = False
            withhold_values = False
        else:
            _append_unique(caveats, "TAIFEX MIS value prerequisites missing; market values withheld")
    elif status == "special_closure_latest_completed":
        if _has_official_special_closure_evidence(cur) and value_prerequisites:
            assessment = "closed_session_reference"
            role = "supporting_closed_reference"
            role_detail = "special_closure_latest_completed"
            state_allowed = True
            metadata = False
            withhold_values = False
        else:
            assessment = "source_specific_currentness_unresolved"
            role_detail = "special_closure_without_official_evidence"
            _append_unique(caveats, "special closure latest-completed status lacks TAIFEX-specific official closure evidence; fail closed")
    elif status == "closed_session_historical":
        role_detail = "closed_historical"
        _append_unique(caveats, "TAIFEX MIS historical closed-session context only")
        if value_prerequisites:
            assessment = "closed_session_reference"
            role = "supporting_historical"
            state_allowed = True
            metadata = False
            withhold_values = False
        else:
            _append_unique(caveats, "TAIFEX MIS value prerequisites missing; market values withheld")
    elif status in {"market_phase_unresolved", "session_alignment_unresolved"}:
        assessment = "source_specific_currentness_unresolved"
        role = "supporting_caveated" if value_prerequisites else "metadata_only"
        role_detail = status
        state_allowed = role != "metadata_only"
        metadata = role == "metadata_only"
        withhold_values = role == "metadata_only"
        _append_unique(caveats, "TAIFEX MIS currentness is unresolved")
    elif status == "source_timestamp_unresolved":
        assessment = "source_specific_currentness_unresolved"
        role_detail = "source_timestamp_unresolved"
        _append_unique(caveats, "TAIFEX MIS source timestamp unresolved; market values withheld from conversation projection")
    elif status in {"transport_completed_without_valid_snapshot", "no_accepted_mode_1"}:
        assessment = "source_unavailable"
        role_detail = status
        _append_unique(caveats, "TAIFEX MIS has no accepted mode=1 snapshot; market values are not exposed")
    else:
        role_detail = "unrecognized_currentness_status"
        _append_unique(caveats, "TAIFEX MIS currentness status is unrecognized; fail closed")

    safe_for_ai_context = policy_allowed and state_allowed and observation_valid
    if not safe_for_ai_context:
        withhold_values = True
        if not state_allowed or not observation_valid:
            metadata = True
            role = "metadata_only" if role != "supporting_caveated" else role
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": "TAIFEX_MIS",
        "source_family": "TAIFEX_MIS",
        "authority_level": policy.get("authority_level") or obs.get("authority_level") or "official_undocumented",
        "timing_class": "liveish_intraday_snapshot",
        "freshness_assessment": assessment,
        "freshness_reason": f"TAIFEX MIS source-specific currentness status: {status}",
        "ai_exposure_level": policy.get("ai_exposure_level") or "metadata_only",
        "safe_for_ai_context": safe_for_ai_context,
        "policy_ai_context_allowed": policy_allowed,
        "state_specific_context_allowed": state_allowed,
        "observation_valid": observation_valid,
        "primary_context_allowed": primary and safe_for_ai_context,
        "context_role": role,
        "taifex_mis_role_detail": role_detail,
        "metadata_only": metadata or not safe_for_ai_context,
        "withhold_market_values_from_conversation": withhold_values,
        "currentness": cur,
        "overall_ai_currentness": status,
        "caveats": list(dict.fromkeys(caveats)),
        "not_realtime_guaranteed": True,
        "not_trading_signal": True,
        "not_recommendation": True,
    }
