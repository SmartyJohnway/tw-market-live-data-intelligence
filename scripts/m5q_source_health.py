from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from scripts.m5k_common import (
    DEFAULT_WATCHLIST_PATH, REPO_ROOT, dump_json, execute_live_observation,
    governance as m5k_governance, iter_instruments, load_json, load_source_adapter_matrix,
    plan_live_observation, utc_now, validate_source_adapter_matrix, validate_watchlist,
)

SCHEMA_VERSION = "m5q_source_health_report.v1"
SOURCE_HEALTH_DIR = REPO_ROOT / "research/live_observation_runs/source_health"
REPORT_JSON = SOURCE_HEALTH_DIR / "source_health_report.json"
REPORT_MD = SOURCE_HEALTH_DIR / "source_health_report.md"
LATEST_JSON = SOURCE_HEALTH_DIR / "latest_source_health_report.json"
LATEST_MD = SOURCE_HEALTH_DIR / "latest_source_health_report.md"
HEALTH_TARGET_SYMBOLS = ["2330", "0050", "3483", "TAIEX", "TX"]
REQUIRED_SOURCE_FAMILIES = [
    "TWSE_MIS listed stock route",
    "TWSE_MIS listed ETF route",
    "TWSE_MIS TPEx / OTC route",
    "TWSE_MIS TAIEX route",
    "TAIFEX TX route",
]


def selected_health_watchlist(watchlist: dict[str, Any] | None = None) -> dict[str, Any]:
    watchlist = watchlist or load_json(DEFAULT_WATCHLIST_PATH)
    selected = [i for i in iter_instruments(watchlist, include_disabled=False) if i.get("symbol") in set(HEALTH_TARGET_SYMBOLS)]
    by_symbol = {i.get("symbol"): i for i in selected}
    missing = [s for s in HEALTH_TARGET_SYMBOLS if s not in by_symbol]
    if missing:
        raise ValueError(f"default watchlist missing required health targets: {missing}")
    return {
        "schema_version": "m5n_watchlist.v1",
        "watchlist_id": "m5q_source_health_bounded_targets",
        "name": "M5Q bounded source-health targets",
        "description": "Manual bounded source-health regression target set; not a full-market scan.",
        "governance": (watchlist.get("governance") or {}) | {"bounded_observation_only": True, "trading_signal": False},
        "items": [by_symbol[s] for s in HEALTH_TARGET_SYMBOLS],
    }


def classify_observation(obs: dict[str, Any] | None, failure: dict[str, Any] | None = None, *, planned_supported: bool = True) -> str:
    if not planned_supported:
        return "unsupported"
    if failure is not None and obs is None:
        status = failure.get("status")
        reason = str(failure.get("reason") or "")
        return "unsupported" if status == "unsupported" or "unsupported" in reason else ("degraded" if reason in {"reference_value_only", "value_unavailable", "missing_value"} else "failed")
    if not obs:
        return "failed"
    if obs.get("status") == "ok" and (obs.get("value") is not None or obs.get("price_like_value") is not None) and obs.get("reference_only") is not True and obs.get("freshness_assessment") != "stale_or_closed_session":
        return "healthy"
    return "degraded"


def _obs_status(obs: dict[str, Any] | None, failure: dict[str, Any] | None, status: str) -> str:
    if obs:
        s = obs.get("status") or "value_unavailable"
        return "failed" if s == "missing_value" else s
    if status == "unsupported":
        return "unsupported"
    return "reference_value_only" if failure and failure.get("reason") == "reference_value_only" else ("value_unavailable" if failure and failure.get("reason") in {"value_unavailable", "missing_value"} else ("failed" if failure else "value_unavailable"))


def _embedded_failure_observation(failure: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(failure, dict):
        return None
    summary = failure.get("investigation_summary")
    if not isinstance(summary, dict):
        return None
    embedded = summary.get("observation")
    return embedded if isinstance(embedded, dict) else None


def _check_from_plan(plan: dict[str, Any], obs: dict[str, Any] | None, failure: dict[str, Any] | None, retrieved_at: str) -> dict[str, Any]:
    planned_supported = plan.get("status") not in {"unsupported_market", "unsupported_in_m5k_initial"}
    obs_detail = obs or _embedded_failure_observation(failure)
    status = classify_observation(obs_detail, failure, planned_supported=planned_supported)
    value = None if not obs_detail else (obs_detail.get("value") if obs_detail.get("value") is not None else obs_detail.get("price_like_value"))
    return {
        "target": plan.get("symbol"),
        "instrument_type": plan.get("instrument_type"),
        "market": plan.get("market"),
        "source_family": "TAIFEX TX route" if plan.get("source") == "TAIFEX" else ("TWSE_MIS TAIEX route" if plan.get("symbol") == "TAIEX" else ("TWSE_MIS TPEx / OTC route" if plan.get("market") in {"tpex", "otc"} else ("TWSE_MIS listed ETF route" if plan.get("instrument_type") == "listed_etf" else "TWSE_MIS listed stock route"))),
        "adapter_id": plan.get("adapter_id"),
        "route": plan.get("route") or plan.get("ex_ch") or plan.get("url"),
        "status": status,
        "observation_status": _obs_status(obs_detail, failure, status),
        "value_present": value is not None,
        "reference_only": bool(obs_detail and obs_detail.get("reference_only") is True),
        "source_timestamp": None if not obs_detail else obs_detail.get("source_timestamp"),
        "retrieved_at_utc": (obs_detail or {}).get("retrieved_at_utc") or retrieved_at,
        "freshness_assessment": (obs_detail or {}).get("freshness_assessment") or ("route unsupported" if status == "unsupported" else "source request failed or value unavailable"),
        "delay_seconds": None if not obs_detail else obs_detail.get("delay_seconds"),
        "failure_reason": None if not failure else failure.get("reason"),
        "recommended_next_step": (failure or {}).get("recommended_next_step") or ("Review caveats and rerun manually later if market/session freshness is important." if status != "healthy" else "Source route usable for bounded observation; continue to display caveats and avoid realtime claims."),
        "raw_endpoint_payload_included": False,
        "caveats": sorted(set((obs_detail or {}).get("caveats", []) + (failure or {}).get("caveats", []))),
    }


def build_report(*, execution_mode: str, live_result: dict[str, Any] | None = None) -> dict[str, Any]:
    watchlist = selected_health_watchlist()
    validation = validate_watchlist(watchlist, max_targets=len(HEALTH_TARGET_SYMBOLS))
    matrix_validation = validate_source_adapter_matrix(load_source_adapter_matrix())
    plan = plan_live_observation(watchlist)
    retrieved_at = utc_now()
    obs_by_symbol = {o.get("symbol"): o for o in (live_result or {}).get("observations", []) if isinstance(o, dict)}
    failure_by_symbol = {f.get("symbol"): f for f in (live_result or {}).get("failures", []) if isinstance(f, dict)}
    checks = [_check_from_plan(p, obs_by_symbol.get(p.get("symbol")), failure_by_symbol.get(p.get("symbol")), retrieved_at) for p in plan.get("planned_routes", [])]
    summary = {k: sum(1 for c in checks if c["status"] == k) for k in ["healthy", "degraded", "failed", "unsupported"]}
    network = execution_mode == "explicit_health_probe"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": retrieved_at,
        "execution_mode": execution_mode,
        "bounded": True,
        "full_market_scan": False,
        "polling": False,
        "scheduler": False,
        "network_calls_may_have_occurred": network,
        "targets": HEALTH_TARGET_SYMBOLS,
        "source_families": REQUIRED_SOURCE_FAMILIES,
        "summary": summary,
        "checks": checks,
        "governance": m5k_governance() | {"m5q_source_health": True, "writes_m5f": False, "writes_frontend_public": False, "writes_research_generated": False, "raw_endpoint_payload_included": False, "validation": validation, "adapter_matrix_validation": matrix_validation},
        "caveats": ["manual_bounded_regression_probe", "not_realtime_guaranteed", "not_live_scanner", "no_polling_or_scheduler", "raw_endpoint_payload_excluded"],
    }


def report_markdown(report: dict[str, Any]) -> str:
    lines = ["# M5Q Source Health Report", "", f"- Schema: `{report['schema_version']}`", f"- Generated at UTC: {report['generated_at_utc']}", f"- Execution mode: {report['execution_mode']}", f"- Network calls may have occurred: {report['network_calls_may_have_occurred']}", f"- Bounded targets: {', '.join(report['targets'])}", "", "## Summary", ""]
    for k, v in report["summary"].items(): lines.append(f"- {k}: {v}")
    lines += ["", "## Checks", "", "| Target | Source family | Adapter | Status | Observation status | Freshness | Delay | Caveats | Next step |", "|---|---|---|---|---|---|---|---|---|"]
    for c in report["checks"]:
        lines.append(f"| {c['target']} | {c['source_family']} | {c['adapter_id']} | {c['status']} | {c['observation_status']} | {c['freshness_assessment']} | {c['delay_seconds']} | {'; '.join(c['caveats'])} | {c['recommended_next_step']} |")
    lines += ["", "## Boundaries", "", "No M5F mutation, frontend/public write, research/generated write, polling, scheduler, full-market scan, trading logic, or raw endpoint payload is included."]
    return "\n".join(lines) + "\n"


def execute_health_probe() -> dict[str, Any]:
    watchlist = selected_health_watchlist()
    live = execute_live_observation(watchlist, write_latest=False)
    report = build_report(execution_mode="explicit_health_probe", live_result=live)
    SOURCE_HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(dump_json(report), encoding="utf-8", newline="\n")
    REPORT_MD.write_text(report_markdown(report), encoding="utf-8", newline="\n")
    shutil.copyfile(REPORT_JSON, LATEST_JSON)
    shutil.copyfile(REPORT_MD, LATEST_MD)
    return report


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_latest_source_health() -> dict[str, Any]:
    if not LATEST_JSON.exists():
        return {"status": "not_available", "source_path": _display_path(LATEST_JSON), "schema_version": SCHEMA_VERSION, "governance": {"network_calls": False, "writes": False}}
    return {"status": "ok", "source_path": _display_path(LATEST_JSON), "content": load_json(LATEST_JSON), "governance": {"network_calls": False, "writes": False, "raw_endpoint_payload_included": False}}


def source_health_schema() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "required_top_level": ["schema_version", "generated_at_utc", "execution_mode", "bounded", "full_market_scan", "polling", "scheduler", "network_calls_may_have_occurred", "targets", "source_families", "summary", "checks", "governance", "caveats"], "check_statuses": ["healthy", "degraded", "failed", "unsupported"], "observation_statuses": ["ok", "reference_value_only", "value_unavailable", "failed", "unsupported"], "raw_endpoint_payload_included": False}
