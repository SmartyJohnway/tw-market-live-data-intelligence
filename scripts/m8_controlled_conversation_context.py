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
    "raw_payload_sample",
    "bid_prices",
    "ask_prices",
    "bid_volumes",
    "ask_volumes",
    "raw_bid_ask_ladder",
    "order_book_truth",
    "source_investigation_notes",
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

TRUSTED_SOURCE_IDS = {
    "TWSE_MIS",
    "TWSE_OPENAPI",
    "TPEX_OPENAPI",
    "TAIFEX_OPENAPI",
    "TAIFEX_MIS",
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
    if freshness == "stale_intraday_snapshot" or ctx.get("taifex_mis_role_detail") == "active_stale":
        _append_unique(caveats, "stale source must not be described as current market")
    elif freshness in {"caveated_intraday_snapshot", "closed_session_reference", "source_specific_currentness_unresolved"}:
        _append_unique(caveats, "caveated TAIFEX MIS source must not be described as current market")
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
    taifex_mis_metadata_values_withheld = source_id == "TAIFEX_MIS" and (ctx.get("withhold_market_values_from_conversation") or not ctx.get("safe_for_ai_context"))
    allow_fields = top_level_safe and not unknown and not credential
    if source_id == "TAIFEX_MIS":
        allow_fields = not unknown and not credential
    safe_fields, omitted = _scrub_safe_fields(ctx.get("safe_fields"))
    safe_fields = _scrub_forbidden_conversation_terms(safe_fields, omitted, caveats)
    if unknown and safe_fields:
        omitted.extend(k for k in safe_fields if k not in omitted)
        safe_fields = {}
    if source_id == "TAIFEX_MIS":
        safe_fields = _project_taifex_mis_safe_fields(safe_fields, withhold_values=taifex_mis_metadata_values_withheld)
    if credential:
        safe_fields = {k: v for k, v in safe_fields.items() if k == "provider_name"}
    if not allow_fields:
        safe_fields = safe_fields if credential and source_id == "CREDENTIAL_GATED_PROVIDER" else {}
    projected = {
        "source_id": source_id,
        "context_type": ctx.get("context_type"),
        "endpoint_contract_id": ctx.get("endpoint_contract_id"),
        "context_group": ctx.get("context_group"),
        "symbol": ctx.get("symbol"),
        "market": ctx.get("market"),
        "instrument_type": ctx.get("instrument_type"),
        "authority_level": ctx.get("authority_level"),
        "timing_class": ctx.get("timing_class"),
        "freshness_assessment": freshness,
        "source_timestamp": ctx.get("source_timestamp"),
        "retrieved_at_utc": ctx.get("retrieved_at_utc"),
        "market_date": ctx.get("market_date"),
        "currentness": ctx.get("currentness"),
        "context_role": ctx.get("context_role"),
        "overall_ai_currentness": ctx.get("overall_ai_currentness"),
        "taifex_mis_role_detail": ctx.get("taifex_mis_role_detail"),
        "safe_for_ai_context": bool(ctx.get("safe_for_ai_context")),
        "trading_date": ctx.get("trading_date"),
        "safe_fields": safe_fields,
        "omitted_fields": sorted(set(_as_list(ctx.get("omitted_fields")) + omitted)),
        "caveats": caveats,
        "primary_context_allowed": bool(ctx.get("primary_context_allowed")) and allow_fields and (source_id != "TAIFEX_MIS" or bool(ctx.get("safe_for_ai_context"))) and freshness != "stale_intraday_snapshot",
        "supporting_context_only": bool(ctx.get("supporting_context_only")) or freshness == "validation_only",
        "metadata_only": bool(ctx.get("metadata_only")) or not allow_fields or (source_id == "TAIFEX_MIS" and not ctx.get("safe_for_ai_context")),
    }
    if freshness in {"stale_intraday_snapshot", "caveated_intraday_snapshot", "closed_session_reference", "source_specific_currentness_unresolved", "manual_snapshot", "validation_only", "credential_gated_metadata_only", "unknown"}:
        projected["primary_context_allowed"] = False
    return projected


def _iter_projected_contexts(instruments: list[dict]) -> list[dict]:
    return [ctx for inst in instruments for ctx in inst.get("contexts", [])]


def _contains_forbidden_raw_structure(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_RAW_KEYS or key_text.isdigit():
                return True
            if _contains_forbidden_raw_structure(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_structure(item) for item in value)
    return False


def _contains_raw_key(projected_instruments: list[dict], markdown: str) -> bool:
    lower_markdown = markdown.lower()
    if any(key.lower() in lower_markdown for key in FORBIDDEN_RAW_KEYS):
        return True
    return _contains_forbidden_raw_structure(projected_instruments)


def _markdown_contains_forbidden_conversation_term(markdown: str) -> bool:
    markdown_without_guardrail = markdown.replace(GUARDRAIL_LINE, "")
    for factual_field in ["top5_buy", "top5_sell", "top10_buy", "top10_sell"]:
        markdown_without_guardrail = markdown_without_guardrail.replace(factual_field, factual_field.replace("_", ""))
    return _contains_forbidden_conversation_term(markdown_without_guardrail)




def _project_taifex_mis_safe_fields(safe_fields: dict, *, withhold_values: bool) -> dict:
    ident = deepcopy(safe_fields.get("contract_identity") or {})
    source_time = deepcopy(safe_fields.get("source_time") or {})
    currentness = deepcopy(safe_fields.get("currentness") or {})
    projected = {
        "contract_identity": ident,
        "source_time": source_time,
        "source_status_code": safe_fields.get("source_status_code"),
        "currentness": currentness,
    }
    if not withhold_values and source_time.get("source_timestamp"):
        projected["price"] = deepcopy(safe_fields.get("price") or {})
        projected["activity"] = deepcopy(safe_fields.get("activity") or {})
        projected["top_of_book"] = deepcopy(safe_fields.get("top_of_book") or {})
        projected["field_provenance"] = deepcopy(safe_fields.get("field_provenance") or {})
    return projected

def _format_taifex_context(ctx: dict) -> list[str]:
    sf = ctx.get("safe_fields") or {}
    payload = sf.get("payload") or {}
    ident = sf.get("contract_identity") or sf.get("aggregate_identity") or {}
    currentness = sf.get("currentness") or {}
    q = sf.get("quotation_unit")
    prefix = "    - TAIFEX official"
    ctype = ctx.get("context_type")
    lines: list[str] = []
    if ctype == "official_derivatives_futures_eod_reference":
        price = payload.get("price") or {}; activity = payload.get("activity") or {}; oi = payload.get("open_interest") or {}
        lines.append(f"{prefix} futures EOD reference: product={ident.get('product_id')}, contract_month={ident.get('contract_month_or_week')}, trade_date={sf.get('trade_date')}, session={sf.get('session')}, last={price.get('last')}, settlement={price.get('settlement')}, volume={activity.get('volume')}, open_interest={oi.get('open_interest')}, currentness={currentness.get('status')}, quotation_unit={q}.")
    elif ctype == "official_derivatives_options_eod_reference":
        price = payload.get("price") or {}; activity = payload.get("activity") or {}; oi = payload.get("open_interest") or {}
        lines.append(f"{prefix} options EOD reference: product={ident.get('product_id')}, month_week={ident.get('contract_month_or_week')}, strike={ident.get('strike_price')}, option_type={ident.get('option_type')}, trade_date={sf.get('trade_date')}, session={sf.get('session')}, close={price.get('close')}, settlement={price.get('settlement')}, volume={activity.get('volume')}, open_interest={oi.get('open_interest')}, currentness={currentness.get('status')}, quotation_unit={q}.")
    elif ctype == "official_derivatives_final_settlement_reference":
        fs = payload.get("final_settlement") or {}
        lines.append(f"{prefix} final settlement reference: product={ident.get('product_id')}, final_settlement_day={ident.get('final_settlement_day')}, delivery_month={ident.get('delivery_month')}, final_settlement_price={fs.get('final_settlement_price')}, currentness={currentness.get('status')}. This is not a current market price.")
    elif ctype == "official_derivatives_large_trader_open_interest_reference":
        oi = payload.get("large_trader_open_interest") or {}
        lines.append(f"{prefix} large-trader open-interest concentration reference: product={ident.get('product_id')}, settlement_month={ident.get('settlement_month')}, option_type={ident.get('option_type')}, top5_buy={oi.get('top5_buy')}, top5_sell={oi.get('top5_sell')}, top10_buy={oi.get('top10_buy')}, top10_sell={oi.get('top10_sell')}, market_open_interest={oi.get('market_open_interest')}, currentness={currentness.get('status')}.")
    elif ctype == "official_derivatives_put_call_ratio_reference":
        pcr = payload.get("put_call_ratio") or {}
        lines.append(f"{prefix} Put/Call Ratio reference: trade_date={sf.get('trade_date')}, volume_ratio_percent={pcr.get('put_call_volume_ratio_percent')}%, open_interest_ratio_percent={pcr.get('put_call_open_interest_ratio_percent')}%, currentness={currentness.get('status')}. Source-reported percentage values are preserved.")
    elif ctype == "official_derivatives_block_trade_reference":
        bt = payload.get("block_trade") or {}
        lines.append(f"{prefix} block-trade reference: product={ident.get('product_id')}, contract_month={ident.get('contract_month_or_week')}, strike={ident.get('strike_price')}, option_type={ident.get('option_type')}, trade_date={sf.get('trade_date')}, session={sf.get('session')}, volume={bt.get('volume')}, highest_price={bt.get('highest_price')}, lowest_price={bt.get('lowest_price')}, currentness={currentness.get('status')}. Factual activity only; no directional interpretation is generated.")
    return lines


def _format_taifex_mis_context(ctx: dict) -> list[str]:
    sf = ctx.get("safe_fields") or {}
    ident = sf.get("contract_identity") or {}
    source_time = sf.get("source_time") or {}
    price = sf.get("price") or {}
    activity = sf.get("activity") or {}
    book = sf.get("top_of_book") or {}
    ctype = ctx.get("context_type")
    if ctype not in {"official_derivatives_options_liveish_snapshot", "official_derivatives_futures_liveish_snapshot"}:
        selector = ident.get("selector") or ident.get("runtime_symbol_id") or ctx.get("symbol")
        return [f"    - TAIFEX MIS metadata-only selector record: selector={selector}, currentness={ctx.get('overall_ai_currentness')}, context_role={ctx.get('context_role')}."]
    kind = "options" if ctype == "official_derivatives_options_liveish_snapshot" else "futures"
    parts = [f"product={ident.get('requested_product_id')}", f"contract={ident.get('contract_month_or_week')}"]
    if kind == "options":
        parts.extend([f"strike={ident.get('strike_price')}", f"option_type={ident.get('option_type')}"])
    parts.extend([f"source_timestamp={source_time.get('source_timestamp')}", f"currentness={ctx.get('overall_ai_currentness')}", f"context_role={ctx.get('context_role')}"])
    if price or activity or book:
        parts.extend([f"last={price.get('last')}", f"reference={price.get('reference')}", f"total_volume={activity.get('total_volume')}", f"best_bid={book.get('best_bid')}", f"best_ask={book.get('best_ask')}", f"book_status={book.get('canonicalization_status')}"])
    return [f"    - TAIFEX MIS bounded {kind} snapshot: " + ", ".join(parts) + "."]

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

                if ctx.get("source_id") == "TAIFEX_MIS":
                    lines.extend(_format_taifex_mis_context(ctx))
                elif ctx.get("source_id") == "TAIFEX_OPENAPI":
                    taifex_lines = _format_taifex_context(ctx)
                    lines.extend(taifex_lines or [f"    - TAIFEX official context: {ctx.get('context_type')}"])
                elif ctx.get('timing_class') == 'official_eod':
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
    raw_detected = _contains_raw_key(projected_instruments, markdown or "")
    if raw_detected:
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
        "no_raw_payload": not raw_detected,
        "no_trading_advice": True,
    }
