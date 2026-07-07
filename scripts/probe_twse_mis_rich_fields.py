#!/usr/bin/env python3
"""Manual-only bounded TWSE MIS rich-field evidence probe.

This helper is for M7A evidence collection only. It is not imported by runtime
code, not used by CI, not a scheduler, not a source-health probe, and not a
production observation writer. It writes compact field-presence/shape summaries
only when an operator explicitly invokes it with bounded symbols.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.ssl_policy import resolve_ssl_policy, build_ssl_context
DEFAULT_OUTPUT_DIR = REPO_ROOT / "research/probe_runs/m7a_twse_mis_rich_fields"
DEFAULT_MAX_SYMBOLS = 10
MAX_ALLOWED_SYMBOLS = 10
SOURCE_ID = "TWSE_MIS"
SUMMARY_SCHEMA_VERSION = "m7a_twse_mis_rich_field_probe_summary.v1"

FIELD_CANDIDATE_SEMANTICS = {
    "z": "last_price_or_current_price_like_value",
    "y": "previous_close_candidate_and_reference_fallback",
    "o": "open_price_candidate",
    "h": "high_price_candidate",
    "l": "low_price_candidate",
    "v": "volume_candidate_unit_unverified",
    "tv": "current_or_transaction_volume_candidate_unit_unverified",
    "b": "displayed_bid_price_ladder_candidate",
    "g": "displayed_bid_quantity_ladder_candidate_unit_unverified",
    "a": "displayed_ask_price_ladder_candidate",
    "f": "displayed_ask_quantity_ladder_candidate_unit_unverified",
    "u": "limit_up_price_candidate",
    "w": "limit_down_price_candidate",
    "d": "source_date_candidate",
    "t": "source_time_candidate",
    "tlong": "source_epoch_milliseconds_candidate",
    "%": "snapshot_or_session_time_candidate",
    "ot": "alternate_session_time_candidate",
}

KNOWN_FORENSIC_FIELDS = [
    "@", "tv", "ps", "pid", "pz", "bp", "m%", "^", "key", "a", "b", "c", "#", "d", "%", "ch",
    "tlong", "f", "g", "mt", "h", "i", "ip", "it", "l", "n", "o", "p", "ex", "s", "t", "u",
    "v", "w", "nf", "y", "z", "ts", "q", "r", "oa", "ob", "ot",
]

LADDER_FIELDS = {"a", "b", "f", "g"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_mis_placeholder(raw: object) -> bool:
    if raw is None:
        return True
    if isinstance(raw, str):
        return raw.strip() in {"", "-", "--", "－"}
    return False


def parse_mis_ladder(raw: object) -> list[str]:
    if is_mis_placeholder(raw):
        return []
    text = str(raw)
    if "_" not in text:
        return [text] if text else []
    parts = text.split("_")
    while parts and parts[-1] == "":
        parts.pop()
    return parts


def _is_numeric_string(text: str) -> bool:
    try:
        float(text.replace(",", ""))
        return True
    except ValueError:
        return False


def classify_mis_value_shape(raw: object) -> str:
    if raw is None:
        return "null"
    if isinstance(raw, bool):
        return "unknown"
    if isinstance(raw, int):
        return "integer_string"
    if isinstance(raw, float):
        return "decimal_string"
    if not isinstance(raw, str):
        return "unknown"
    text = raw.strip()
    if text == "":
        return "empty_string"
    if text in {"-", "--", "－"}:
        return "dash_placeholder"
    if "_" in text:
        return "underscore_ladder"
    numeric_text = text.replace(",", "")
    if numeric_text.startswith("-") and _is_numeric_string(numeric_text):
        return "negative_numeric_string"
    if numeric_text.isdigit():
        return "integer_string"
    if _is_numeric_string(numeric_text):
        return "decimal_string" if "." in numeric_text else "numeric_string"
    return "text"


def summarize_field_presence(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    observed_fields = sorted(set(KNOWN_FORENSIC_FIELDS) | {str(k) for row in rows for k in row.keys()})
    summary: dict[str, dict[str, Any]] = {}
    row_count = len(rows)
    for field in observed_fields:
        present_values = [row.get(field) for row in rows if field in row]
        missing_count = row_count - len(present_values)
        shapes = sorted({classify_mis_value_shape(value) for value in present_values})
        placeholders = sorted({str(value) for value in present_values if is_mis_placeholder(value)})
        summary[field] = {
            "present_count": len(present_values),
            "missing_count": missing_count,
            "sample_value_shapes": shapes,
            "placeholder_examples": placeholders[:5],
            "numeric_parse_status": _numeric_parse_status(present_values),
            "empty_string_status": any(isinstance(value, str) and value == "" for value in present_values),
            "dash_status": any(isinstance(value, str) and value.strip() in {"-", "--", "－"} for value in present_values),
            "candidate_semantic": FIELD_CANDIDATE_SEMANTICS.get(field, "unknown_semantics_preserve_raw"),
            "validation_status_update_recommendation": "requires_probe_evidence_review" if present_values else "not_observed_preserve_inventory",
        }
    return summary


def _numeric_parse_status(values: list[Any]) -> str:
    non_placeholder = [value for value in values if not is_mis_placeholder(value)]
    if not non_placeholder:
        return "no_non_placeholder_values"
    numeric = 0
    non_numeric = 0
    for value in non_placeholder:
        if classify_mis_value_shape(value) in {"integer_string", "decimal_string", "numeric_string", "negative_numeric_string"}:
            numeric += 1
        else:
            non_numeric += 1
    if numeric and not non_numeric:
        return "all_observed_non_placeholder_values_numeric"
    if numeric and non_numeric:
        return "mixed_numeric_and_non_numeric"
    return "no_numeric_values_observed"


def summarize_ladder_shapes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_field: dict[str, dict[str, Any]] = {}
    for field in sorted(LADDER_FIELDS):
        lengths = [len(parse_mis_ladder(row.get(field))) for row in rows if field in row]
        per_field[field] = {
            "present_count": len(lengths),
            "lengths_observed": sorted(set(lengths)),
            "placeholder_count": sum(1 for row in rows if field in row and is_mis_placeholder(row.get(field))),
            "underscore_delimited_count": sum(1 for row in rows if field in row and isinstance(row.get(field), str) and "_" in row.get(field, "")),
        }
    mismatch_candidates = []
    for row_index, row in enumerate(rows):
        b_len = len(parse_mis_ladder(row.get("b")))
        g_len = len(parse_mis_ladder(row.get("g")))
        a_len = len(parse_mis_ladder(row.get("a")))
        f_len = len(parse_mis_ladder(row.get("f")))
        if b_len != g_len:
            mismatch_candidates.append({"row_index": row_index, "side": "bid", "price_field": "b", "quantity_field": "g", "price_length": b_len, "quantity_length": g_len})
        if a_len != f_len:
            mismatch_candidates.append({"row_index": row_index, "side": "ask", "price_field": "a", "quantity_field": "f", "price_length": a_len, "quantity_length": f_len})
    return {"per_field": per_field, "mismatch_candidates": mismatch_candidates}


def build_probe_summary(rows: list[dict[str, Any]], failures: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    retrieved_at = metadata.get("retrieved_at_utc") or utc_now()
    field_presence = summarize_field_presence(rows)
    ladder_summary = summarize_ladder_shapes(rows)
    field_shape_summary = {
        field: {
            "sample_value_shapes": details["sample_value_shapes"],
            "numeric_parse_status": details["numeric_parse_status"],
            "candidate_semantic": details["candidate_semantic"],
        }
        for field, details in field_presence.items()
    }
    placeholder_summary = {
        field: {
            "placeholder_examples": details["placeholder_examples"],
            "empty_string_status": details["empty_string_status"],
            "dash_status": details["dash_status"],
        }
        for field, details in field_presence.items()
    }
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "source_id": SOURCE_ID,
        "probe_type": "manual_bounded_probe",
        "runtime_behavior_changed": False,
        "normalization_changed": False,
        "full_market_scan": False,
        "polling": False,
        "scheduler": False,
        "startup_network": False,
        "ci_network_required": False,
        "symbols_requested": list(metadata.get("symbols_requested", [])),
        "symbols_observed": sorted({str(row.get("key") or row.get("ch") or row.get("c")) for row in rows if row.get("key") or row.get("ch") or row.get("c")}),
        "symbols_failed": [failure.get("symbol") for failure in failures if failure.get("symbol")],
        "retrieved_at_utc": retrieved_at,
        "field_presence_summary": field_presence,
        "field_shape_summary": field_shape_summary,
        "placeholder_summary": placeholder_summary,
        "ladder_shape_summary": ladder_summary,
        "field_validation_updates": [
            {
                "raw_field": field,
                "candidate_semantic": details["candidate_semantic"],
                "recommendation": details["validation_status_update_recommendation"],
            }
            for field, details in field_presence.items()
        ],
        "raw_payload_committed": False,
        "notes": list(metadata.get("notes", [])) + [
            "manual_only_bounded_probe_summary",
            "compact_field_shape_evidence_only",
            "no_runtime_integration",
            "no_raw_payload_dump",
            "unit_semantics_remain_unverified_for_volume_and_quantity_candidates",
        ],
        "request_evidence": {
            "method": "GET",
            "endpoint_family": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
            "requires_session": True,
            "headers_committed": False,
            "cookies_committed": False,
            "raw_payload_committed": False,
            "session_tokens_committed": False,
            "raw_response_body_committed": False,
        },
        "session_bootstrap_attempts": metadata.get("session_bootstrap_attempts", []),
        "api_attempts": metadata.get("api_attempts", []),
        "successful_strategy": metadata.get("successful_strategy", "none"),
        "failures": failures,
    }


def validate_symbols(symbols: list[str], max_symbols: int) -> None:
    if not symbols:
        raise ValueError("explicit non-empty --symbols list is required")
    if max_symbols > MAX_ALLOWED_SYMBOLS:
        raise ValueError("--max-symbols must be <= 10 for M7A manual bounded evidence")
    if len(symbols) > max_symbols:
        raise ValueError(f"symbol count {len(symbols)} exceeds max-symbols {max_symbols}")
    for symbol in symbols:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbols must be non-empty strings")
        if "|" in symbol or "," in symbol:
            raise ValueError("symbols must be supplied as separate bounded arguments, not combined routes")


def fetch_twse_mis_rows(symbols: list[str], *, timeout: int = 10, ssl_policy: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Manual network probe. Not called by tests or runtime code."""
    headers = {
        "User-Agent": "Mozilla/5.0 tw-market-m7a-rich-field-manual-probe/1.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
    }
    ssl_context = build_ssl_context(ssl_policy)
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(),
        urllib.request.HTTPSHandler(context=ssl_context)
    )

    bootstrap_candidates = [
        "https://mis.twse.com.tw/stock/fibest.jsp",
        "https://mis.twse.com.tw/stock/index.jsp",
        "https://mis.twse.com.tw/stock/",
        "https://mis.twse.com.tw/stock/index.jsp?lang=zh_tw",
        "https://mis.twse.com.tw/stock/fibest.jsp?lang=zh_tw",
    ]

    session_bootstrap_attempts = []
    bootstrap_succeeded = False

    for candidate in bootstrap_candidates:
        attempt = {
            "url_family": candidate.split("?")[0],
            "status": "failed",
            "error_class": None,
            "http_status": None,
        }
        try:
            req = urllib.request.Request(candidate, headers=headers)
            res = opener.open(req, timeout=timeout)
            status_code = getattr(res, "status", None) or getattr(res, "code", None) or 200
            res.read()
            attempt["status"] = "success"
            attempt["http_status"] = status_code
            session_bootstrap_attempts.append(attempt)
            bootstrap_succeeded = True
            break
        except Exception as exc:
            error_class = exc.__class__.__name__
            http_status = None
            if isinstance(exc, urllib.error.HTTPError):
                http_status = exc.code
            elif hasattr(exc, "code"):
                http_status = getattr(exc, "code")

            attempt["status"] = "failed"
            attempt["error_class"] = error_class
            attempt["http_status"] = http_status
            session_bootstrap_attempts.append(attempt)

    api_attempts = []
    successful_strategy = "none"
    rows = []
    failures = []
    telemetry_status = "session_failed" if not bootstrap_succeeded else "request_failed"
    api_status_code = None
    rtcode = None

    # Attempt the API
    api_strategy = "bootstrap_then_api" if bootstrap_succeeded else "direct_after_bootstrap_failure"
    api_attempt = {
        "strategy": api_strategy,
        "endpoint_family": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
        "status": "failed",
        "http_status": None,
    }
    api_attempts.append(api_attempt)

    query = urllib.parse.urlencode({"ex_ch": "|".join(symbols), "json": "1", "delay": "0", "_": str(int(time.time() * 1000))})
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?{query}"

    try:
        response = opener.open(urllib.request.Request(url, headers=headers), timeout=timeout)
        api_status_code = getattr(response, "status", None) or getattr(response, "code", None) or 200
        api_attempt["http_status"] = api_status_code
        body = response.read().decode("utf-8", "replace")
        data = json.loads(body.strip())

        rows = [row for row in data.get("msgArray", []) if isinstance(row, dict)]
        observed_keys = {str(row.get("key") or row.get("ch") or "") for row in rows}

        for symbol in symbols:
            if symbol not in observed_keys and not any(symbol.endswith(str(row.get("ch") or "")) for row in rows):
                failures.append({"symbol": symbol, "stage": "response", "reason": "missing_from_msgArray"})

        api_attempt["status"] = "success"
        successful_strategy = "bootstrap_then_api" if bootstrap_succeeded else "direct_api_without_session"
        telemetry_status = "ok"
        rtcode = data.get("rtcode") or data.get("rtCode")
    except Exception as exc:
        error_class = exc.__class__.__name__
        http_status = None
        if isinstance(exc, urllib.error.HTTPError):
            http_status = exc.code
        elif hasattr(exc, "code"):
            http_status = getattr(exc, "code")
        api_attempt["http_status"] = http_status
        failures = [{"symbol": symbol, "stage": "request", "reason": f"{error_class}: {str(exc)}"} for symbol in symbols]

    telemetry = {
        "status": telemetry_status,
        "status_code": api_status_code,
        "rtcode": rtcode,
        "row_count": len(rows),
        "raw_payload_committed": False,
        "session_bootstrap_attempts": session_bootstrap_attempts,
        "api_attempts": api_attempts,
        "successful_strategy": successful_strategy,
    }
    return rows, failures, telemetry


def write_summary(summary: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = summary["retrieved_at_utc"].replace(":", "").replace("-", "").replace("Z", "Z")
    path = output_dir / f"m7a_twse_mis_rich_field_probe_summary_{stamp}.json"
    text = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    latest = output_dir / "latest_summary.json"
    latest.write_text(text, encoding="utf-8", newline="\n")
    return path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual-only bounded TWSE MIS rich-field evidence probe; not runtime, not CI, not scheduler.")
    parser.add_argument("--symbols", nargs="+", required=True, help="Explicit bounded TWSE MIS channels such as tse_2330.tw or otc_8069.tw.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Dedicated M7A evidence output directory.")
    parser.add_argument("--max-symbols", type=int, default=DEFAULT_MAX_SYMBOLS, help="Maximum explicit symbols; must be <= 10.")
    parser.add_argument("--timeout", type=int, default=10, help="Manual request timeout in seconds.")
    parser.add_argument("--ssl-policy", type=str, default=None, help="SSL policy: strict, compatibility, unsafe-explicit.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        validate_symbols(args.symbols, args.max_symbols)
    except ValueError as exc:
        print(f"refusing manual probe: {exc}", file=sys.stderr)
        return 2

    resolved_policy = resolve_ssl_policy(args.ssl_policy)
    retrieved_at = utc_now()
    rows, failures, telemetry = fetch_twse_mis_rows(args.symbols, timeout=args.timeout, ssl_policy=resolved_policy)
    summary = build_probe_summary(
        rows,
        failures,
        {
            "symbols_requested": args.symbols,
            "retrieved_at_utc": retrieved_at,
            "notes": ["operator_invoked_manual_bounded_probe", f"telemetry_status={telemetry.get('status')}"],
            "session_bootstrap_attempts": telemetry.get("session_bootstrap_attempts", []),
            "api_attempts": telemetry.get("api_attempts", []),
            "successful_strategy": telemetry.get("successful_strategy", "none"),
        },
    )
    path = write_summary(summary, args.output_dir)
    print(json.dumps({"status": "summary_written", "path": str(path), "rows": len(rows), "failures": len(failures)}, ensure_ascii=False))
    return 0 if rows else 1


if __name__ == "__main__":  # pragma: no cover - manual CLI entrypoint
    raise SystemExit(main())
