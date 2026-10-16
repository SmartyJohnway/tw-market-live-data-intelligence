"""Execute the separately authorized, bounded DGPA P0-R1 authority run."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlencode, urlparse

from scripts.phase_i_i3_execution_date import resolve_i3_twse_source_trade_date
from scripts.phase_l_a6_p0_authority import normalized_calendar_sha256, validate_2026_calendar
from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import (
    ARCHIVE_BASE, DAILY_URL, MAX_DETAIL, MAX_INDEX, MAX_TOTAL, OFFICIAL_HOST,
    RequestBudget, adjudicate_archive_window, build_closure_events, parse_archive_index,
    parse_daily_status, parse_detail_status, response_sha256, resolve_only_with_complete_authority,
    validate_official_url,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "l3-a6-p0-r1-20261016T042447Z"
RUN_DIR = ROOT / "docs/governance/phase_l/acceptance_runs" / RUN_ID
P0_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z"
EVALUATION_TIME = "2026-10-16T11:38:22+08:00"
EXPECTED_CALENDAR_SHA = "28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8"
AUTHORITY_ID = "USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_R1_DGPA_HISTORICAL_CLOSURE_COMPLETENESS_AUTHORIZATION"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _canonical_sha(value: object) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def _validate_preflight(plan: dict, reservation: dict) -> None:
    if plan.get("authority_id") != AUTHORITY_ID or plan.get("run_id") != RUN_ID:
        raise RuntimeError("r1_plan_identity_invalid")
    if plan.get("base_sha") != "7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c" or plan.get("parent_p0_head") != "4f840f424e45b7836b78ab6e8c09f79282df78dd":
        raise RuntimeError("r1_plan_lineage_invalid")
    if plan.get("evaluation_time") != EVALUATION_TIME or plan.get("coverage_dates") != ["2026-10-16", "2026-10-15"]:
        raise RuntimeError("r1_plan_window_invalid")
    if plan.get("limits") != {"daily_max": 2, "archive_index_max": 6, "archive_detail_max": 2, "total_max": 10}:
        raise RuntimeError("r1_plan_limits_invalid")
    if any(plan.get(k) is not False for k in ("P01_P18_execution_allowed", "B01_B05_execution_allowed", "TWSE_T86_execution_allowed", "i3_resolver_modification_allowed", "a6_market_live_authority_consumption_allowed")):
        raise RuntimeError("r1_plan_scope_invalid")
    if reservation.get("state") != "RESERVED_NOT_CONSUMED" or reservation.get("authority_consumed") is not False:
        raise RuntimeError("r1_authority_not_reserved")
    if reservation.get("plan_sha256") != sha256((RUN_DIR / "r1_plan.json").read_bytes()).hexdigest():
        raise RuntimeError("r1_plan_hash_mismatch")
    candidate = reservation.get("pre_network_commit_sha")
    if not candidate or plan.get("candidate_pre_network_sha") != candidate:
        raise RuntimeError("r1_pre_network_commit_binding_invalid")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", candidate, "HEAD"], cwd=ROOT, capture_output=True)
    if ancestor.returncode != 0:
        raise RuntimeError("r1_pre_network_commit_not_ancestor")
    if _git("show", "-s", "--format=%T", candidate) != reservation.get("pre_network_commit_tree_sha"):
        raise RuntimeError("r1_pre_network_tree_mismatch")
    if _git("status", "--porcelain=v1"):
        raise RuntimeError("r1_worktree_not_clean")
    if _git("rev-parse", "origin/main") != plan["base_sha"]:
        raise RuntimeError("r1_base_drift")
    calendar = json.loads((P0_DIR / "twse_trading_calendar_2026.json").read_text(encoding="utf-8"))
    validate_2026_calendar(calendar)
    if normalized_calendar_sha256(calendar) != EXPECTED_CALENDAR_SHA:
        raise RuntimeError("p0_calendar_hash_mismatch")


def preflight_only() -> dict:
    plan = json.loads((RUN_DIR / "r1_plan.json").read_text(encoding="utf-8"))
    reservation = json.loads((RUN_DIR / "authority_reservation.json").read_text(encoding="utf-8"))
    _validate_preflight(plan, reservation)
    return {"preflight": "PASS", "run_id": RUN_ID, "base_sha": plan["base_sha"],
            "candidate_pre_network_sha": plan["candidate_pre_network_sha"],
            "calendar_sha256": EXPECTED_CALENDAR_SHA, "external_requests": 0}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def execute_authorized_r1() -> dict:
    plan = json.loads((RUN_DIR / "r1_plan.json").read_text(encoding="utf-8"))
    reservation = json.loads((RUN_DIR / "authority_reservation.json").read_text(encoding="utf-8"))
    _validate_preflight(plan, reservation)
    budget = RequestBudget()
    ledger: list[dict] = []
    pages: list[dict] = []
    daily_fact = None
    historical_fact = None
    details: list[dict] = []
    fatal_error = None
    opener = urllib.request.build_opener(_NoRedirect())

    def get(kind: str, url: str, purpose: str) -> tuple[int, dict[str, str], bytes, str]:
        validate_official_url(url)
        # Enforce source-specific URL families before reserving and dispatching.
        parsed = urlparse(url)
        if kind == "daily" and not (parsed.path == "/typh/daily/nds.html" and parse_qs(parsed.query).get("uid") == ["31"]):
            raise RuntimeError("r1_unplanned_daily_url")
        if kind == "index" and not (parsed.path == "/informationlist" and parse_qs(parsed.query).get("uid") == ["374"]):
            raise RuntimeError("r1_unplanned_archive_url")
        if kind == "detail" and not (parsed.path == "/information" and parse_qs(parsed.query).get("uid") == ["374"] and parse_qs(parsed.query).get("pid")):
            raise RuntimeError("r1_unplanned_detail_url")
        seq = budget.reserve(kind)
        started = _now()
        began = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": "TW-Market bounded authority materialization"}, method="GET")
        status, headers, body = 0, {}, b""
        outcome = "transport_failure"
        try:
            if not ledger:
                _write_json(RUN_DIR / "authority_consumed.json", {"authority_id": AUTHORITY_ID, "run_id": RUN_ID,
                    "state": "CONSUMED", "consumed_at": _now(), "market_authority_consumed": False})
            with opener.open(req, timeout=10) as response:
                status = int(response.status)
                headers = dict(response.headers.items())
                body = response.read()
                outcome = "http_response"
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            headers = dict(exc.headers.items()) if exc.headers else {}
            body = exc.read()
            outcome = "http_response"
        except Exception as exc:
            outcome = type(exc).__name__
        finished = _now()
        elapsed_ms = int((time.monotonic() - began) * 1000)
        effective = url
        entry = {"attempt_sequence": len(ledger) + 1, "kind": kind, "purpose": purpose,
                 "endpoint": url, "effective_url": effective, "hostname": OFFICIAL_HOST,
                 "started_at": started, "completed_at": finished, "http_status": status or None,
                 "http_outcome": outcome, "content_type": headers.get("Content-Type"),
                 "response_byte_count": len(body), "response_sha256": response_sha256(body) if body else None,
                 "elapsed_ms": elapsed_ms}
        ledger.append(entry)
        if 300 <= status < 400:
            raise RuntimeError("dgpa_redirect_not_followed_fail_closed")
        return status, headers, body, finished

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    # Daily current-state authority.
    try:
        status, headers, body, fetched = get("daily", DAILY_URL, "INITIAL_DAILY_STATUS")
        if status != 200:
            fatal_error = "dgpa_daily_http_failure"
        else:
            daily_fact = parse_daily_status(body, content_type=headers.get("Content-Type"), fetched_at=fetched)
            daily_fact.update({"http_status": status, "endpoint": DAILY_URL, "effective_url": DAILY_URL,
                               "content_type": headers.get("Content-Type"), "response_byte_count": len(body),
                               "response_sha256": response_sha256(body)})
    except (ValueError, RuntimeError) as exc:
        fatal_error = str(exc) or type(exc).__name__
    if daily_fact is not None:
        _write_json(RUN_DIR / "daily_status_2026-10-16.json", daily_fact)

    # Historical archive: strictly monotonic page numbers from page 1.
    archive_error = fatal_error
    for page_number in range(1, 7) if fatal_error is None else ():
        url = ARCHIVE_BASE + str(page_number)
        try:
            status, headers, body, fetched = get("index", url, "ARCHIVE_INDEX_WINDOW_DISCOVERY" if page_number == 1 else "ARCHIVE_INDEX_CONTINUATION")
            if status != 200:
                archive_error = "dgpa_archive_http_failure"
                break
            items = parse_archive_index(body, content_type=headers.get("Content-Type"), base_url=url)
            pages.append({"page": page_number, "endpoint": url, "effective_url": url, "http_status": status,
                          "content_type": headers.get("Content-Type"), "retrieved_at": fetched,
                          "response_byte_count": len(body), "response_sha256": response_sha256(body), "items": items})
            assessment = adjudicate_archive_window(pages, "2026-10-15")
            if assessment["historical_archive_target_entry_present"]:
                match = assessment["matching_entries"][0]
                detail_status, detail_headers, detail_body, detail_fetched = get("detail", match["detail_url"], "TARGET_DATE_DETAIL_INSPECTION")
                if detail_status != 200:
                    archive_error = "dgpa_archive_detail_http_failure"
                    break
                historical_fact = parse_detail_status(detail_body, content_type=detail_headers.get("Content-Type"), target_date="2026-10-15")
                historical_fact.update({"endpoint": match["detail_url"], "effective_url": match["detail_url"],
                    "http_status": detail_status, "content_type": detail_headers.get("Content-Type"),
                    "retrieved_at": detail_fetched, "response_byte_count": len(detail_body), "response_sha256": response_sha256(detail_body)})
                details.append(historical_fact)
                break
            if assessment["historical_negative_evidence"]:
                historical_fact = {"target_date": "2026-10-15", "taipei_status": "no_archive_entry",
                                   "closure_scope": None, "closure_event": None, **assessment}
                break
        except (ValueError, RuntimeError) as exc:
            archive_error = str(exc) or type(exc).__name__
            break
    if not pages and archive_error is None:
        archive_error = archive_error or "dgpa_archive_window_missing"
    if pages:
        assessment = adjudicate_archive_window(pages, "2026-10-15")
        _write_json(RUN_DIR / "archive_window.json", {"archive_identity": "歷次天然災害停止上班上課訊息",
            "pages": pages, "assessment": assessment, "archive_error": archive_error})
    if details:
        _write_json(RUN_DIR / "archive_detail_2026-10-15.json", details[0])

    complete = daily_fact is not None and historical_fact is not None and archive_error is None
    if complete:
        events = build_closure_events(daily_fact, historical_fact)
        closure_ref = f"DGPA_R1:{RUN_ID}:complete_for_i3_resolution_window"
        calendar = json.loads((P0_DIR / "twse_trading_calendar_2026.json").read_text(encoding="utf-8"))
        binding = resolve_only_with_complete_authority(complete, resolve_i3_twse_source_trade_date,
            evaluation_time=EVALUATION_TIME, official_calendar=calendar,
            closure_events=events, calendar_authority_ref=f"P0:{RUN_ID}:TWSE_CALENDAR:{EXPECTED_CALENDAR_SHA}",
            closure_authority_ref=closure_ref, closure_authority_complete=True)
        calendar_days = {item["date"]: item["is_trading_day"] for item in calendar["dates"]}
        resolved = binding["resolved_source_trade_date"]
        if calendar_days.get(resolved) is not True:
            raise RuntimeError("r1_resolver_date_not_calendar_trading_day")
        _write_json(RUN_DIR / "p17_date_resolution.json", {**binding, "closure_events": events,
            "closure_authority_complete": True, "coverage_dates": ["2026-10-16", "2026-10-15"]})
        disposition = "PASS_CLOSURE_AUTHORITY_COMPLETE"
    else:
        disposition = "DGPA_SOURCE_DRIFT_OBSERVED" if fatal_error or (archive_error and archive_error.startswith("dgpa_")) else "INCOMPLETE_AUTHORITY"
    completeness = {"coverage_dates": ["2026-10-16", "2026-10-15"],
        "coverage_basis": "complete_for_i3_resolution_window" if complete else "resolver_window_only_incomplete",
        "daily_status_adjudicated": daily_fact is not None, "historical_status_adjudicated": historical_fact is not None,
        "historical_negative_evidence": bool(historical_fact and historical_fact.get("historical_negative_evidence")),
        "events_relevant_to_coverage_dates": build_closure_events(daily_fact or {}, historical_fact or {}),
        "completeness_reason": "both exact dates adjudicated by official DGPA current page and verified historical archive/detail" if complete else archive_error or "one or more exact dates remain unadjudicated",
        "closure_authority_complete": complete}
    _write_json(RUN_DIR / "closure_completeness.json", completeness)
    _write_json(RUN_DIR / "acquisition_ledger.json", {"entries": ledger, "daily_get_count": budget.daily,
        "archive_index_get_count": budget.index, "archive_detail_get_count": budget.detail, "total_get_count": budget.total,
        "limits": {"daily_max": 2, "archive_index_max": 6, "archive_detail_max": 2, "total_max": 10}})
    result = {"run_id": RUN_ID, "authority_id": AUTHORITY_ID, "disposition": disposition,
        "evaluation_time": EVALUATION_TIME, "closure_authority_complete": complete,
        "p17_trade_date": binding["resolved_source_trade_date"] if complete else None,
        "a6_market_authority_consumed": False, "P01_P18_performed": False, "B01_B05_performed": False,
        "TWSE_T86_performed": False, "counts": {"daily": budget.daily, "archive_index": budget.index,
        "archive_detail": budget.detail, "total": budget.total}}
    _write_json(RUN_DIR / "result.json", result)
    files = sorted(p for p in RUN_DIR.glob("*.json") if p.name != "manifest.json")
    manifest = {"run_id": RUN_ID, "files": [{"path": p.name, "sha256": sha256(p.read_bytes()).hexdigest(), "size_bytes": p.stat().st_size} for p in files]}
    manifest["manifest_sha256"] = _canonical_sha(manifest)
    _write_json(RUN_DIR / "manifest.json", manifest)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--execute-authorized-r1", action="store_true")
    args = parser.parse_args()
    if args.preflight_only == args.execute_authorized_r1:
        parser.error("select exactly one of --preflight-only or --execute-authorized-r1")
    result = preflight_only() if args.preflight_only else execute_authorized_r1()
    print(json.dumps(result, ensure_ascii=False, indent=2))
