"""Pure M8-00-06 controlled conversation context projection.

Projects M8-00-05 multi-source market context into a caveated, AI-readable
conversation payload. No filesystem, network, runtime, UI, MCP, or model access.
"""

from copy import deepcopy
from typing import Any

CONTROLLED_CONVERSATION_CONTEXT_SCHEMA_VERSION = "m8_controlled_conversation_context.v1"
M8_CONVERSATION_SECTION_ID = "m8_multi_source_market_context"
SOURCE_CONTEXT_SCHEMA_VERSION = "m8_00_multi_source_market_context.v1"

FORBIDDEN_CONVERSATION_TERMS = {
    "buy",
    "sell",
    "hold",
    "bullish",
    "bearish",
    "target price",
    "support",
    "resistance",
    "support/resistance",
    "ranking",
    "top movers",
    "strongest",
    "weakest",
}

FORBIDDEN_RAW_KEYS = {
    "raw_payload",
    "bid_prices",
    "ask_prices",
    "bid_volumes",
    "ask_volumes",
    "raw_bid_ask_ladder",
    "order_book_truth",
    "source_investigation_notes",
}

TRUSTED_SOURCE_IDS = {
    "TWSE_MIS",
    "TWSE_OPENAPI",
    "TPEX_OPENAPI",
    "TAIFEX_OPENAPI",
    "MANUAL_OPERATOR_EVIDENCE",
    "EXTERNAL_VALIDATION_ONLY",
    "CREDENTIAL_GATED_PROVIDER",
}

GUARDRAIL_LINE = "This context is not trading advice, not a recommendation, and not a trading signal."


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


def _scrub_safe_fields(safe_fields: Any) -> tuple[dict, list[str]]:
    if not isinstance(safe_fields, dict):
        return {}, []
    projected = {}
    omitted = []
    for key, value in safe_fields.items():
        if key in FORBIDDEN_RAW_KEYS:
            omitted.append(key)
        else:
            projected[key] = deepcopy(value)
    return projected, omitted




def _text_tokens(value: str) -> set[str]:
    normalized = []
    for char in value.lower():
        normalized.append(char if char.isalnum() else " ")
    return set("".join(normalized).split())


def _contains_forbidden_conversation_term(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        tokens = _text_tokens(value)
        for term in FORBIDDEN_CONVERSATION_TERMS:
            if " " in term or "/" in term:
                if term in lowered:
                    return True
            elif term in tokens:
                return True
        return False
    if isinstance(value, dict):
        return any(_contains_forbidden_conversation_term(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_conversation_term(item) for item in value)
    return False


def _scrub_forbidden_conversation_terms(safe_fields: dict, omitted: list[str], caveats: list[str]) -> dict:
    projected = {}
    found_forbidden_term = False
    for key, value in safe_fields.items():
        if _contains_forbidden_conversation_term(value):
            found_forbidden_term = True
            _append_unique(omitted, key)
        else:
            projected[key] = value
    if found_forbidden_term:
        _append_unique(caveats, "forbidden trading interpretation term omitted from conversation safe_fields")
    return projected


def _policy_caveats(ctx: dict) -> list[str]:
    caveats: list[str] = []
    freshness = ctx.get("freshness_assessment")
    timing = ctx.get("timing_class")
    source_id = ctx.get("source_id")
    if freshness == "unknown" or source_id not in TRUSTED_SOURCE_IDS:
        _append_unique(caveats, "unknown source safe_fields withheld from conversation context")
    if freshness == "stale_intraday_snapshot":
        _append_unique(caveats, "stale source must not be described as current market")
    if freshness in {"official_eod_reference", "official_statistics_eod"} or timing in {"official_eod", "official_statistics_eod"}:
        _append_unique(caveats, "EOD/reference context is not realtime and not current price")
    if freshness == "manual_snapshot" or source_id == "MANUAL_OPERATOR_EVIDENCE":
        _append_unique(caveats, "manual evidence is not official source and cannot override official source")
    if freshness == "validation_only" or source_id == "EXTERNAL_VALIDATION_ONLY":
        _append_unique(caveats, "validation-only source cannot be primary context")
    if freshness == "credential_gated_metadata_only" or timing == "credential_gated_research" or source_id == "CREDENTIAL_GATED_PROVIDER":
        _append_unique(caveats, "credential-gated source is metadata-only and not runtime dependency")
    if timing == "liveish_intraday_snapshot":
        _append_unique(caveats, "retrieved_at_utc is not exchange timestamp unless source_timestamp proves it")
        _append_unique(caveats, "live-ish observation is not streaming or realtime guaranteed")
    return caveats


def _project_context(ctx: dict, top_level_safe: bool) -> dict:
    freshness = ctx.get("freshness_assessment")
    source_id = ctx.get("source_id")
    caveats = []
    _extend_unique(caveats, _as_list(ctx.get("caveats")))
    _extend_unique(caveats, _policy_caveats(ctx))
    unknown = freshness == "unknown" or source_id not in TRUSTED_SOURCE_IDS
    credential = freshness == "credential_gated_metadata_only" or ctx.get("timing_class") == "credential_gated_research" or source_id == "CREDENTIAL_GATED_PROVIDER"
    allow_fields = top_level_safe and not unknown and not credential
    safe_fields, omitted = _scrub_safe_fields(ctx.get("safe_fields"))
    safe_fields = _scrub_forbidden_conversation_terms(safe_fields, omitted, caveats)
    if unknown and safe_fields:
        omitted.extend(k for k in safe_fields if k not in omitted)
        safe_fields = {}
    if credential:
        safe_fields = {k: v for k, v in safe_fields.items() if k == "provider_name"}
    if not allow_fields:
        safe_fields = safe_fields if credential and source_id == "CREDENTIAL_GATED_PROVIDER" else {}
    projected = {
        "source_id": source_id,
        "symbol": ctx.get("symbol"),
        "market": ctx.get("market"),
        "instrument_type": ctx.get("instrument_type"),
        "authority_level": ctx.get("authority_level"),
        "timing_class": ctx.get("timing_class"),
        "freshness_assessment": freshness,
        "source_timestamp": ctx.get("source_timestamp"),
        "retrieved_at_utc": ctx.get("retrieved_at_utc"),
        "market_date": ctx.get("market_date"),
        "trading_date": ctx.get("trading_date"),
        "safe_fields": safe_fields,
        "omitted_fields": sorted(set(_as_list(ctx.get("omitted_fields")) + omitted)),
        "caveats": caveats,
        "primary_context_allowed": bool(ctx.get("primary_context_allowed")) and allow_fields and freshness != "stale_intraday_snapshot",
        "supporting_context_only": bool(ctx.get("supporting_context_only")) or freshness == "validation_only",
        "metadata_only": bool(ctx.get("metadata_only")) or not allow_fields,
    }
    if freshness in {"stale_intraday_snapshot", "manual_snapshot", "validation_only", "credential_gated_metadata_only", "unknown"}:
        projected["primary_context_allowed"] = False
    return projected


def _iter_projected_contexts(instruments: list[dict]) -> list[dict]:
    return [ctx for inst in instruments for ctx in inst.get("contexts", [])]


def _contains_raw_key(projected_instruments: list[dict], markdown: str) -> bool:
    lower_markdown = markdown.lower()
    if any(key in lower_markdown for key in FORBIDDEN_RAW_KEYS):
        return True
    for ctx in _iter_projected_contexts(projected_instruments):
        if any(key in ctx.get("safe_fields", {}) for key in FORBIDDEN_RAW_KEYS):
            return True
    return False


def _markdown_contains_forbidden_conversation_term(markdown: str) -> bool:
    markdown_without_guardrail = markdown.replace(GUARDRAIL_LINE, "")
    return _contains_forbidden_conversation_term(markdown_without_guardrail)


def _build_markdown(status: str, summary: dict, sources: list[dict], instruments: list[dict], caveats: list[str]) -> str:
    lines = ["### M8 multi-source market context", f"- Status: {status}", f"- Freshness summary: {summary}"]
    if caveats:
        lines.append("- Caveats:")
        for caveat in caveats:
            lines.append(f"  - {caveat}")
    if sources:
        lines.append("- Sources:")
        for src in sources:
            lines.append(f"  - {src.get('source_id')}: {src.get('timing_class')} / {src.get('freshness_assessments')}")
    if instruments:
        lines.append("- Instrument contexts:")
        for inst in instruments:
            lines.append(f"  - {inst.get('symbol')} {inst.get('market')} {inst.get('instrument_type')}")
            for ctx in inst.get("contexts", []):

                if ctx.get('timing_class') == 'official_eod':
                    lines.append(f"    - Official EOD reference — {ctx.get('source_id')}: market={ctx.get('market')} trade_date={ctx.get('trading_date') or ctx.get('market_date')} currentness={ctx.get('safe_fields', {}).get('currentness_status')} authority={ctx.get('authority_level')} instrument={ctx.get('instrument_type')} safe_fields={ctx.get('safe_fields')}")
                else:
                    lines.append(f"    - {ctx.get('source_id')}: {ctx.get('timing_class')} / {ctx.get('freshness_assessment')} / safe_fields={ctx.get('safe_fields')}")
    lines.append(f"- {GUARDRAIL_LINE}")
    return "\n".join(lines)


def build_controlled_conversation_context(multi_source_context: dict, *, include_markdown: bool = True) -> dict:
    if not isinstance(multi_source_context, dict) or multi_source_context.get("schema_version") != SOURCE_CONTEXT_SCHEMA_VERSION:
        caveats = ["wrong schema_version for controlled conversation context projection"]
        section = {
            "section_id": M8_CONVERSATION_SECTION_ID,
            "safe_to_include": False,
            "requires_caveats": True,
            "summary": {},
            "sources": [],
            "instrument_contexts": [],
            "caveats": caveats,
            "forbidden_interpretations": [],
            "markdown": "" if include_markdown else None,
        }
        return {
            "schema_version": CONTROLLED_CONVERSATION_CONTEXT_SCHEMA_VERSION,
            "context_status": "blocked",
            "source_context_schema_version": multi_source_context.get("schema_version") if isinstance(multi_source_context, dict) else None,
            "sections": [section],
            "not_trading_signal": True,
            "not_recommendation": True,
            "no_raw_payload": True,
            "no_trading_advice": True,
        }

    policy = multi_source_context.get("ai_exposure_policy") or {}
    top_level_safe = bool(policy.get("safe_to_include_in_conversation_context"))
    caveats: list[str] = []
    _extend_unique(caveats, _as_list(multi_source_context.get("cross_source_caveats")))
    projected_instruments = []
    for inst in multi_source_context.get("instrument_contexts", []):
        contexts = [_project_context(dict(ctx, symbol=inst.get("symbol"), market=inst.get("market"), instrument_type=inst.get("instrument_type")), top_level_safe) for ctx in inst.get("contexts", [])]
        projected_instruments.append({
            "symbol": inst.get("symbol"),
            "name": inst.get("name"),
            "market": inst.get("market"),
            "instrument_type": inst.get("instrument_type"),
            "contexts": contexts,
        })
        for ctx in contexts:
            _extend_unique(caveats, ctx.get("caveats", []))

    has_safe_fields = any(ctx.get("safe_fields") for ctx in _iter_projected_contexts(projected_instruments))
    has_metadata = bool(projected_instruments or multi_source_context.get("sources") or caveats)
    if top_level_safe:
        status = "ready_with_caveats" if bool(policy.get("requires_caveats")) or caveats else "ready"
    elif has_metadata:
        status = "metadata_only"
    else:
        status = "blocked"
    if not top_level_safe and not has_safe_fields:
        for ctx in _iter_projected_contexts(projected_instruments):
            ctx["metadata_only"] = True

    markdown = _build_markdown(status, multi_source_context.get("freshness_summary") or {}, multi_source_context.get("sources") or [], projected_instruments, caveats) if include_markdown else None
    if _contains_raw_key(projected_instruments, markdown or ""):
        status = "blocked"
        projected_instruments = []
        _append_unique(caveats, "forbidden raw field detected after projection")
        markdown = "" if include_markdown else None
    elif markdown and _markdown_contains_forbidden_conversation_term(markdown):
        status = "blocked"
        projected_instruments = []
        _append_unique(caveats, "forbidden trading interpretation term detected after projection")
        markdown = "" if include_markdown else None

    section = {
        "section_id": M8_CONVERSATION_SECTION_ID,
        "safe_to_include": status in {"ready", "ready_with_caveats", "metadata_only"},
        "requires_caveats": bool(caveats) or status != "ready",
        "summary": deepcopy(multi_source_context.get("freshness_summary") or {}),
        "sources": deepcopy(multi_source_context.get("sources") or []),
        "instrument_contexts": projected_instruments,
        "caveats": caveats,
        "forbidden_interpretations": deepcopy(policy.get("forbidden_interpretations") or []),
        "markdown": markdown,
    }
    return {
        "schema_version": CONTROLLED_CONVERSATION_CONTEXT_SCHEMA_VERSION,
        "context_status": status,
        "source_context_schema_version": SOURCE_CONTEXT_SCHEMA_VERSION,
        "sections": [section],
        "not_trading_signal": True,
        "not_recommendation": True,
        "no_raw_payload": True,
        "no_trading_advice": True,
    }
