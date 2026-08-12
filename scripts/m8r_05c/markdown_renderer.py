"""Markdown renderer for M8R-05C AI-context result.

Renders the unified_market_evidence_result.v1 dict into an AI-ready
Markdown representation for direct use in conversation context.

This module:
- Is a pure function (no I/O, no network, no datetime.now()).
- Never emits authorization secrets, tokens, credentials, or absolute paths.
- Never emits investment recommendations, rankings, or sentiment labels.
- Renders only requested evidence fields that are available.
"""
from __future__ import annotations

_TIMING_CLASS_LABELS: dict[str, str] = {
    "intraday_live": "即時 (Intraday Live)",
    "intraday_delayed": "延遲 (Intraday Delayed)",
    "eod_official": "官方收盤 (Official EOD)",
    "eod_provisional": "暫定收盤 (Provisional EOD)",
    "eod_reference_only": "參考收盤 (EOD Reference Only)",
    "non_trading_day": "非交易日 (Non-trading Day)",
}

_STATUS_LABELS: dict[str, str] = {
    "full_success": "✅ 完整成功",
    "success_with_partial_coverage": "⚠️ 部分覆蓋",
    "partially_failed": "⚠️ 部分失敗",
    "failed": "❌ 失敗",
    "available": "可用",
    "missing": "缺失",
    "failed": "失敗",
    "empty": "空",
    "plan_only_not_executed": "⏸ Plan-only（未執行）",
}

_RESOLUTION_STATUS_LABELS: dict[str, str] = {
    "resolved": "✅ 已解析",
    "ambiguous": "⚠️ 不明確",
    "not_found": "❌ 未找到",
    "market_hint_conflict": "⚠️ 市場衝突",
    "unsupported_market": "❌ 不支援市場",
}


def _section(title: str, level: int = 2) -> str:
    prefix = "#" * level
    return f"{prefix} {title}"


def _fmt_timing(timing_class: str | None) -> str:
    if not timing_class:
        return "未知"
    return _TIMING_CLASS_LABELS.get(timing_class, timing_class)


def _fmt_evidence_envelope(envelope: dict, data_need: str) -> str:
    """Render a single evidence envelope to markdown."""
    lines: list[str] = []
    status = envelope.get("status", "unknown")
    timing = _fmt_timing(envelope.get("timing_class"))

    lines.append(f"- **狀態**: {_STATUS_LABELS.get(status, status)}")
    lines.append(f"- **時效類別**: {timing}")

    observed = envelope.get("observed_fields", {})
    if observed:
        if data_need == "current_observation":
            labels = {"instrument_context": "Instrument Context", "source_context": "Source", "price_snapshot": "Current Market Snapshot", "reference_price_context": "Reference Prices", "displayed_quote_snapshot": "Displayed Quote Snapshot", "extended_displayed_depth_snapshot": "Extended Displayed Depth", "freshness_context": "Freshness / Source", "market_session_context": "Market / Session", "data_quality_context": "Data Quality"}
            for key, value in observed.items():
                lines.append(f"\n**{labels.get(key, key)}**:")
                if isinstance(value, dict):
                    for field, field_value in value.items(): lines.append(f"- `{field}`: {field_value}")
                else: lines.append(f"- `{key}`: {value}")
        else:
            lines.append("\n**觀測欄位**:\n")
            for k, v in sorted(observed.items()): lines.append(f"  - `{k}`: {v}")

    missing = envelope.get("missing_fields", [])
    if missing:
        lines.append(f"\n- **缺失欄位**: {', '.join(f'`{f}`' for f in missing)}")

    currentness = envelope.get("currentness", {})
    if currentness:
        lines.append("\n**時效資訊**:")
        for k, v in sorted(currentness.items()):
            lines.append(f"  - `{k}`: {v}")

    caveats = envelope.get("caveats", [])
    if caveats:
        lines.append("\n> **注意**:")
        for c in caveats:
            lines.append(f"> - {c}")

    fallback = envelope.get("fallback", False)
    fallback_state = envelope.get("fallback_state")
    if fallback:
        fallback_note = f" ({fallback_state})" if fallback_state else ""
        lines.append(f"\n> ⚠️ 使用了備援資料{fallback_note}")

    return "\n".join(lines)


def _fmt_eod_reference(eod: dict, *, legacy: bool = False) -> str:
    """Render official_eod_reference to markdown."""
    lines: list[str] = []
    currentness_status = eod.get("currentness_status", "unknown")
    trade_date = eod.get("trade_date")
    expected = eod.get("expected_latest_completed_trade_date")
    session = eod.get("session_status")
    caveats = eod.get("caveats", [])

    labels = {
        "official_latest_completed_eod": "✅ 最新完整 EOD",
        "official_previous_session_eod_before_close": "⚠️ 前一交易日 EOD（收盤前）",
        "not_yet_published_after_close": "⏳ 收盤後尚未公佈",
        "market_closed_no_session": "🔒 市場休市",
        "unexpected_stale_eod": "⚠️ 異常舊 EOD",
        "calendar_status_unresolved": "❓ 日曆狀態未解析",
        "future_trade_date_invalid": "❌ 交易日期為未來日期",
        "source_trade_date_missing": "❌ 來源交易日期缺失",
        "invalid_trade_date_format": "❌ 交易日期格式無效",
    }
    if legacy:
        lines.append(f"- **EOD 狀態**: {labels.get(currentness_status, currentness_status)}")
    else:
        lines.append(f"- **EOD 狀態**: {_STATUS_LABELS.get(eod.get('status', 'available'), eod.get('status', 'available'))}")
        for key, label in (("source_id", "來源"), ("source_family", "來源家族"), ("authority_level", "權威等級")):
            if eod.get(key): lines.append(f"- **{label}**: {eod[key]}")
    if trade_date:
        lines.append(f"- **交易日期**: {trade_date}")
    if expected:
        lines.append(f"- **預期最新交易日**: {expected}")
    if session:
        lines.append(f"- **交易時段狀態**: {session}")
    if not legacy and eod.get("price"):
        lines.append("\n**Price**:")
        for key, value in eod["price"].items(): lines.append(f"- `{key}`: {value}")
    if not legacy and eod.get("activity"):
        lines.append("\n**Activity**:")
        for key, value in eod["activity"].items(): lines.append(f"- `{key}`: {value}")
    if not legacy: lines.append(f"\n**Currentness**: {labels.get(currentness_status, currentness_status)}")
    if eod.get("fallback_policy_used"):
        lines.append("- ⚠️ 使用了備援政策")
    if eod.get("publication_grace_applied"):
        lines.append("- ⏳ 已套用公佈寬限期")
    if caveats:
        lines.append("\n> **注意**:")
        for c in caveats:
            lines.append(f"> - {c}")
    return "\n".join(lines)


def _data_need_label(need: str) -> str:
    labels = {
        "identity": "身分 (Identity)",
        "current_observation": "即時觀測 (Current Observation)",
        "official_eod_reference": "官方收盤參考 (Official EOD Reference)",
        "recent_performance": "近期表現 (Recent Performance)",
        "session_status": "交易時段狀態 (Session Status)",
        "source_currentness": "資料來源時效 (Source Currentness)",
        "evidence_quality": "資料品質 (Evidence Quality)",
    }
    return labels.get(need, need)


def render_result_markdown(result: dict, *, projector_version: str = "m8r_05c_v1_2") -> str:
    """Render the result dict as AI-ready Markdown.

    Pure function: no I/O, no network, no datetime.now().
    Never emits authorization secrets, tokens, credentials, or absolute paths.
    Never emits investment recommendations or sentiment labels.
    """
    lines: list[str] = []

    status = result.get("status", "unknown")
    result_id = result.get("result_id", "")
    request_id = result.get("request_id", "")
    generated_at = result.get("generated_at", "")

    lines.append("# 市場證據結果 (Market Evidence Result)")
    lines.append("")
    lines.append(f"**整體狀態**: {_STATUS_LABELS.get(status, status)}")
    lines.append(f"**結果 ID**: `{result_id}`")
    lines.append(f"**請求 ID**: `{request_id}`")
    lines.append(f"**生成時間**: {generated_at}")

    # Request summary.
    rs = result.get("request_summary", {})
    if rs:
        lines.append("")
        lines.append(_section("請求摘要", 2))
        lines.append(f"- **執行模式**: {rs.get('execution_mode', '未知')}")
        lines.append(f"- **目標數量**: {rs.get('target_count', 0)}")
        req_needs = rs.get("requested_data_needs", [])
        lines.append(f"- **請求的資料需求**: {', '.join(req_needs) if req_needs else '（無）'}")
        opt_needs = rs.get("optional_data_needs", [])
        if opt_needs:
            lines.append(f"- **選擇性需求**: {', '.join(opt_needs)}")

    # Partial failures.
    pf_list = result.get("partial_failures", [])
    if pf_list:
        lines.append("")
        lines.append(_section("部分失敗", 2))
        for pf in pf_list:
            idx = pf.get("target_index", "?")
            reason = pf.get("reason", "")
            data_need = pf.get("data_need", "")
            need_label = f" [{data_need}]" if data_need else ""
            display_idx = idx if projector_version == "m8r_05c_v1" else (idx + 1 if isinstance(idx, int) else idx)
            lines.append(f"- 目標 #{display_idx}{need_label}: {reason}")

    # Request caveats.
    req_caveats = result.get("request_caveats", [])
    if req_caveats:
        lines.append("")
        lines.append("> **請求層注意事項**:")
        for c in req_caveats:
            lines.append(f"> - {c}")

    # Targets.
    targets = result.get("targets", [])
    for i, target in enumerate(targets, start=1):
        lines.append("")
        lines.append(_section(f"目標 {i}", 2))

        resolution = target.get("resolution", {})
        res_status = resolution.get("status", "unknown")
        canonical_id = resolution.get("canonical_target_id", "")
        market = resolution.get("market", "")
        security_code = resolution.get("security_code", "")
        security_name = resolution.get("security_name", "")
        client_ref = target.get("client_target_reference", "")

        lines.append(f"- **解析狀態**: {_RESOLUTION_STATUS_LABELS.get(res_status, res_status)}")
        if canonical_id:
            lines.append(f"- **規範目標 ID**: `{canonical_id}`")
        if security_code:
            lines.append(f"- **證券代碼**: {security_code}")
        if security_name:
            lines.append(f"- **證券名稱**: {security_name}")
        if market:
            lines.append(f"- **市場**: {market}")
        if client_ref:
            lines.append(f"- **查詢參考**: {client_ref}")

        # Coverage.
        coverage = target.get("coverage", {})
        provided = coverage.get("provided_needs", [])
        missing = coverage.get("missing_needs", [])
        if provided or missing:
            lines.append(f"- **已提供資料需求**: {', '.join(provided) if provided else '（無）'}")
            if missing:
                lines.append(f"- **缺失資料需求**: {', '.join(missing)}")

        # Target caveats.
        target_caveats = target.get("caveats", [])
        if target_caveats:
            lines.append("")
            lines.append("> **目標注意事項**:")
            for c in target_caveats:
                lines.append(f"> - {c}")

        # Evidence.
        evidence = target.get("evidence", {})
        if evidence:
            lines.append("")
            lines.append(_section("證據", 3))

            for need_key in [
                "identity",
                "current_observation",
                "official_eod_reference",
                "recent_performance",
                "session_status",
                "source_currentness",
                "evidence_quality",
            ]:
                ev = evidence.get(need_key)
                if ev is None:
                    continue
                lines.append("")
                lines.append(_section(f"{_data_need_label(need_key)}", 4))
                if need_key == "official_eod_reference":
                    lines.append(_fmt_eod_reference(ev, legacy=projector_version == "m8r_05c_v1"))
                else:
                    lines.append(_fmt_evidence_envelope(ev, need_key if projector_version != "m8r_05c_v1" else "legacy"))

        # Derived metrics.
        derived_metrics = target.get("derived_metrics", [])
        if derived_metrics:
            lines.append("")
            lines.append(_section("衍生指標", 3))
            for dm in derived_metrics:
                metric_name = dm.get("metric_name", dm.get("metric_id", "?"))
                status = dm.get("status", "unknown")
                value = dm.get("value")
                unit = dm.get("unit", "")
                method = dm.get("method", "")
                caveats = dm.get("caveats", [])
                invalid_reason = dm.get("invalid_reason", "")
                lines.append("")
                lines.append(f"**{metric_name}**")
                lines.append(f"- **狀態**: {status}")
                if value is not None:
                    val_str = f"{value} {unit}".strip() if unit else str(value)
                    lines.append(f"- **值**: {val_str}")
                if method:
                    lines.append(f"- **計算方法**: {method}")
                if invalid_reason:
                    lines.append(f"- **無效原因**: {invalid_reason}")
                if caveats:
                    for c in caveats:
                        lines.append(f"- ⚠️ {c}")

        # Citations (brief).
        citations = target.get("citations", [])
        if citations:
            lines.append("")
            lines.append(_section("引用來源", 3))
            for cit in citations:
                cit_id = cit.get("citation_id", "")
                source = cit.get("source_family", "")
                retrieved = cit.get("retrieved_at", "")
                artifact_ref = cit.get("artifact_reference", "")
                lines.append(
                    f"- `{cit_id}` — 來源: {source} | 擷取時間: {retrieved}"
                    + (f" | 參考: `{artifact_ref}`" if artifact_ref else "")
                )

    # Audit reference.
    audit_ref = result.get("audit_reference", {})
    if audit_ref:
        lines.append("")
        lines.append(_section("審計包參考", 2))
        audit_id = audit_ref.get("audit_package_id", "")
        audit_path = audit_ref.get("relative_path", "")
        lines.append(f"- **審計包 ID**: `{audit_id}`")
        if audit_path:
            lines.append(f"- **相對路徑**: `{audit_path}`")
        lines.append(
            "\n> ℹ️ 審計包 (`unified_market_evidence_audit_package.v1`) 包含完整作業系譜、"
            "人工製品清單、引用對應表與重播說明。審計包與 AI 對話結果分開保存。"
        )

    lines.append("")
    lines.append("---")
    lines.append(
        "> ⚠️ 本結果由確定性投影層 (M8R-05C) 生成，不含投資建議、買賣推薦、目標價格或市場展望。"
        " 所有時效語義由來源 evidence artifact 和執行收據決定。"
    )

    return "\n".join(lines)
