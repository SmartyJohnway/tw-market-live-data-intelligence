"""Pure TAIFEX MIS source-specific M8 currentness bridge."""
from __future__ import annotations
from typing import Any

SCHEMA_VERSION = "m8_taifex_mis_currentness_bridge.v1"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def assess_taifex_mis_currentness(observation: dict, source_policy: dict | None = None, *, now_utc: str | None = None) -> dict:
    """Map M8C currentness to M8 roles without retrieved_at upgrades."""
    del now_utc
    obs = dict(observation or {})
    policy = dict(source_policy or {})
    cur = dict(obs.get("currentness") or {})
    status = cur.get("overall_ai_currentness") or "source_specific_currentness_unresolved"
    caveats = _as_list(policy.get("caveats")) + _as_list(obs.get("caveats"))
    caveats.append("TAIFEX MIS retrieved_at_utc must never upgrade source currentness")
    caveats.append("TAIFEX MIS bounded live-ish observation is not realtime guaranteed")
    role = "metadata_only"
    assessment = "source_specific_currentness_unresolved"
    safe = bool(policy.get("ai_context_allowed"))
    primary = False
    metadata = False
    withhold_values = False

    if status == "active_session_fresh_liveish":
        assessment = "fresh_intraday_snapshot"; role = "primary_current_liveish"; primary = True
    elif status in {"active_session_aging_liveish", "active_session_stale_liveish"}:
        assessment = "caveated_intraday_snapshot"; role = "supporting_caveated"; safe = True
        caveats.append("TAIFEX MIS aging/stale live-ish observation must not be described as current")
    elif status in {"preopen", "indicative", "halted", "noncontinuous_phase"}:
        assessment = "caveated_intraday_snapshot"; role = "supporting_phase_caveated"; safe = True
        caveats.append(f"TAIFEX MIS market phase is {status}; do not treat as continuous current trading")
    elif status in {"closed_session_latest_completed", "special_closure_latest_completed"}:
        assessment = "closed_session_reference"; role = "supporting_closed_reference"; safe = True
        caveats.append("TAIFEX MIS closed-session latest completed snapshot is not current and is not official EOD endpoint data")
    elif status == "closed_session_historical":
        assessment = "closed_session_reference"; role = "supporting_historical"; safe = True
        caveats.append("TAIFEX MIS historical closed-session context only")
    elif status in {"market_phase_unresolved", "session_alignment_unresolved"}:
        assessment = "source_specific_currentness_unresolved"; role = "supporting_caveated" if obs.get("source_timestamp") else "metadata_only"; safe = bool(obs.get("source_timestamp"))
        caveats.append("TAIFEX MIS currentness is unresolved")
    elif status == "source_timestamp_unresolved":
        assessment = "source_specific_currentness_unresolved"; role = "metadata_only"; metadata = True; safe = True; withhold_values = True
        caveats.append("TAIFEX MIS source timestamp unresolved; market values withheld from conversation projection")
    elif status in {"transport_completed_without_valid_snapshot", "no_accepted_mode_1"}:
        assessment = "source_unavailable"; role = "metadata_only"; metadata = True; safe = False; withhold_values = True
        caveats.append("TAIFEX MIS has no accepted mode=1 snapshot; market values are not exposed")
    else:
        metadata = True; safe = False; withhold_values = True
        caveats.append("TAIFEX MIS currentness status is unrecognized; fail closed")

    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": "TAIFEX_MIS",
        "source_family": "TAIFEX_MIS",
        "authority_level": policy.get("authority_level") or obs.get("authority_level") or "official_undocumented",
        "timing_class": "liveish_intraday_snapshot",
        "freshness_assessment": assessment,
        "freshness_reason": f"TAIFEX MIS source-specific currentness status: {status}",
        "ai_exposure_level": policy.get("ai_exposure_level") or "controlled_caveated_safe_fields",
        "safe_for_ai_context": safe,
        "primary_context_allowed": primary,
        "context_role": role,
        "metadata_only": metadata,
        "withhold_market_values_from_conversation": withhold_values,
        "currentness": cur,
        "overall_ai_currentness": status,
        "caveats": list(dict.fromkeys(caveats)),
        "not_realtime_guaranteed": True,
        "not_trading_signal": True,
        "not_recommendation": True,
    }
