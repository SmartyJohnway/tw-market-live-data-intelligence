"""One bounded P0-R3 DGPA semantic re-observation after offline preflight."""
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
from urllib.parse import parse_qs, urlparse

from scripts.phase_i_i3_execution_date import resolve_i3_twse_source_trade_date
from scripts.phase_l_a6_p0_authority import normalized_calendar_sha256, validate_2026_calendar
from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import (
    ARCHIVE_BASE, DAILY_URL, OFFICIAL_HOST, adjudicate_archive_window, build_closure_events,
    R2RequestBudget, daily_candidate_diagnostics, parse_archive_index, parse_daily_status, parse_detail_status, response_sha256,
    validate_official_url,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "l3-a6-p0-r3-20261016T062632Z"
RUN_DIR = ROOT / "docs/governance/phase_l/acceptance_runs" / RUN_ID
P0_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z"
PARENT_HEAD = "3c633c6f36d79bd431eafa568c2ab4c1882b91b3"
BASE_SHA = "7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c"
EVALUATION_TIME = "2026-10-16T11:38:22+08:00"
CALENDAR_SHA = "28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8"
RESOLVER_SHA = "075abdbb9a5cb961cb7054583aeebbe3f8722bb9c570577037396db85dc0f010"
AUTHORITY_ID = "USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_R3_SEMANTIC_CANDIDATE_RECONCILIATION"
LIMITS = {"daily_max": 1, "archive_index_max": 4, "archive_detail_max": 1, "total_max": 6}


def classify_daily_failure(failure: str | None, diagnostics: dict) -> str:
    """Call provider drift only when retained bounded facts prove contradiction."""
    if not failure:
        return "INCOMPLETE_AUTHORITY"
    if "semantic_conflict" in failure or "status_conflict" in failure:
        signals = set(diagnostics.get("page_status_signals", []))
        candidate_dates = {tuple(item.get("bound_date_candidates", [])) for item in diagnostics.get("candidates", [])
                           if item.get("bound_date_candidates")}
        candidate_statuses = {item.get("normalized_status_semantics") or item.get("status_signal")
                              for item in diagnostics.get("candidates", [])
                              if item.get("normalized_status_semantics") not in (None, "UNRESOLVED", "CONFLICTING_PAGE_STATUS")
                              or item.get("status_signal") not in (None, "UNRESOLVED")}
        proven_conflict = (len(signals) > 1 or len(candidate_dates) > 1 or len(candidate_statuses) > 1)
        return "DGPA_SOURCE_DRIFT_OBSERVED" if proven_conflict else "R3_PARSER_CONTRACT_INSUFFICIENT"
    if "semantic_ambiguity" in failure or "subject_ambiguous" in failure:
        return "R3_PARSER_CONTRACT_INSUFFICIENT"
    return "INCOMPLETE_AUTHORITY"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _canonical_sha(value: object) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def _validate_plan(plan: dict, reservation: dict) -> None:
    if plan.get("run_id") != RUN_ID or plan.get("authority_id") != AUTHORITY_ID:
        raise RuntimeError("r3_plan_identity_invalid")
    if plan.get("base_sha") != BASE_SHA or plan.get("parent_p0_head") != PARENT_HEAD:
        raise RuntimeError("r3_plan_lineage_invalid")
    if plan.get("evaluation_time") != EVALUATION_TIME or plan.get("coverage_dates") != ["2026-10-16", "2026-10-15"]:
        raise RuntimeError("r3_plan_window_invalid")
    if plan.get("daily_status_url") != DAILY_URL or plan.get("archive_index_base") != ARCHIVE_BASE:
        raise RuntimeError("r3_plan_endpoint_invalid")
    if plan.get("calendar_path") != "docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z/twse_trading_calendar_2026.json":
        raise RuntimeError("r3_plan_calendar_path_invalid")
    if plan.get("limits") != LIMITS:
        raise RuntimeError("r3_plan_limits_invalid")
    forbidden = ("P01_P18_execution_allowed", "B01_B05_execution_allowed", "TWSE_T86_execution_allowed",
                 "i3_resolver_modification_allowed", "twse_calendar_regeneration_allowed",
                 "a6_market_live_authority_consumption_allowed")
    if any(plan.get(key) is not False for key in forbidden):
        raise RuntimeError("r3_plan_scope_invalid")
    if reservation.get("state") != "RESERVED_NOT_CONSUMED" or reservation.get("authority_consumed") is not False:
        raise RuntimeError("r3_authority_not_reserved")
    if reservation.get("plan_sha256") != sha256((RUN_DIR / "r3_plan.json").read_bytes()).hexdigest():
        raise RuntimeError("r3_plan_hash_mismatch")
    candidate = reservation.get("pre_network_commit_sha")
    if not candidate or candidate != plan.get("pre_network_commit_sha"):
        raise RuntimeError("r3_pre_network_commit_binding_invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", candidate, "HEAD"], cwd=ROOT, capture_output=True).returncode != 0:
        raise RuntimeError("r3_pre_network_commit_not_ancestor")
    if _git("show", "-s", "--format=%T", candidate) != reservation.get("pre_network_tree_sha"):
        raise RuntimeError("r3_pre_network_tree_mismatch")
    if _git("status", "--porcelain=v1"):
        raise RuntimeError("r3_worktree_not_clean")
    if _git("rev-parse", "origin/main") != BASE_SHA:
        raise RuntimeError("r3_base_drift")
    resolver_path = ROOT / "scripts/phase_i_i3_execution_date.py"
    if sha256(resolver_path.read_bytes()).hexdigest() != RESOLVER_SHA:
        raise RuntimeError("R3_I3_RESOLVER_INTEGRITY_VIOLATION")
    parser_hash = sha256((ROOT / "scripts/phase_l_a6_p0_r1_dgpa_closure_authority.py").read_bytes()).hexdigest()
    if parser_hash != plan.get("parser_sha256"):
        raise RuntimeError("r3_parser_binding_mismatch")
    calendar = _json(P0_DIR / "twse_trading_calendar_2026.json")
    validate_2026_calendar(calendar)
    if normalized_calendar_sha256(calendar) != CALENDAR_SHA:
        raise RuntimeError("p0_calendar_hash_mismatch")
    if plan.get("calendar_sha256") != CALENDAR_SHA:
        raise RuntimeError("r3_plan_calendar_binding_invalid")
    if (RUN_DIR / "authority_consumed.json").exists():
        raise RuntimeError("r3_authority_already_consumed")


def preflight_only() -> dict:
    plan, reservation = _json(RUN_DIR / "r3_plan.json"), _json(RUN_DIR / "authority_reservation.json")
    _validate_plan(plan, reservation)
    return {"preflight": "PASS", "run_id": RUN_ID, "external_requests": 0,
            "pre_network_commit_sha": plan["pre_network_commit_sha"], "calendar_sha256": CALENDAR_SHA,
            "resolver_sha256": RESOLVER_SHA, "parser_sha256": plan["parser_sha256"]}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def execute_authorized_r3() -> dict:
    plan, reservation = _json(RUN_DIR / "r3_plan.json"), _json(RUN_DIR / "authority_reservation.json")
    _validate_plan(plan, reservation)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    budget = R2RequestBudget()
    ledger: list[dict] = []
    opener = urllib.request.build_opener(_NoRedirect())

    def get(kind: str, url: str, purpose: str) -> tuple[int, dict[str, str], bytes, str]:
        validate_official_url(url)
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        approved = ((kind == "daily" and parsed.path == "/typh/daily/nds.html" and query.get("uid") == ["31"]) or
                    (kind == "index" and parsed.path == "/informationlist" and query.get("uid") == ["374"] and query.get("page") == [str(budget["archive_index"] + 1)]) or
                    (kind == "detail" and parsed.path == "/information" and query.get("uid") == ["374"] and bool(query.get("pid"))))
        key = {"daily": "daily", "index": "index", "detail": "detail"}.get(kind)
        if not approved or key is None:
            raise RuntimeError("r3_unplanned_request_or_budget_exceeded")
        budget.reserve(key)
        sequence = len(ledger) + 1
        started = _now()
        began = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": "TW-Market bounded DGPA authority materialization"}, method="GET")
        status, headers, body, transport = 0, {}, b"", "transport_failure"
        # Consume only the R3 authority immediately before the first actual dispatch.
        if not ledger:
            _write(RUN_DIR / "authority_consumed.json", {"authority_id": AUTHORITY_ID, "run_id": RUN_ID,
                "state": "CONSUMED", "consumed_at": _now(), "market_authority_consumed": False})
        try:
            with opener.open(req, timeout=10) as response:
                status, headers, body, transport = int(response.status), dict(response.headers.items()), response.read(), "http_response"
        except urllib.error.HTTPError as exc:
            status, headers, body, transport = int(exc.code), dict(exc.headers.items()) if exc.headers else {}, exc.read(), "http_response"
        except Exception as exc:
            transport = type(exc).__name__
        finished = _now()
        entry = {"sequence": sequence, "kind": kind, "purpose": purpose, "requested_url": url,
                 "effective_url": url, "hostname": OFFICIAL_HOST, "started_at": started,
                 "completed_at": finished, "http_status": status or None, "transport_outcome": transport,
                 "content_type": headers.get("Content-Type"), "response_byte_count": len(body),
                 "response_sha256": response_sha256(body) if body else None,
                 "elapsed_ms": int((time.monotonic() - began) * 1000)}
        ledger.append(entry)
        if 300 <= status < 400:
            raise RuntimeError("r3_redirect_not_followed_fail_closed")
        return status, headers, body, finished

    daily_fact = None
    candidate_diagnostics = None
    archive_pages: list[dict] = []
    historical_fact = None
    detail_fact = None
    failure = None
    try:
        status, headers, body, fetched = get("daily", DAILY_URL, "R3_DAILY_SINGLE_OBSERVATION")
        if status != 200:
            failure = "dgpa_daily_http_failure"
        else:
            daily_fact = parse_daily_status(body, content_type=headers.get("Content-Type"), fetched_at=fetched)
            candidate_diagnostics = daily_fact.pop("subject_candidate_diagnostics")
            daily_fact.update({"http_status": status, "endpoint": DAILY_URL, "effective_url": DAILY_URL,
                               "content_type": headers.get("Content-Type"), "response_byte_count": len(body),
                               "response_sha256": response_sha256(body)})
    except (ValueError, RuntimeError) as exc:
        failure = str(exc) or type(exc).__name__
        if ledger and ledger[0].get("http_status") == 200:
            try:
                candidate_diagnostics = getattr(exc, "diagnostics", None) or daily_candidate_diagnostics(body, headers.get("Content-Type"))
            except (ValueError, RuntimeError):
                candidate_diagnostics = {"raw_subject_match_count": 0, "semantic_candidate_count": 0,
                    "canonical_candidate_count": 0, "candidates": [], "diagnostic_error": "candidate_diagnostics_unavailable"}
    if candidate_diagnostics is None:
        candidate_diagnostics = {"raw_subject_match_count": 0, "semantic_candidate_count": 0,
            "canonical_candidate_count": 0, "candidates": [], "diagnostic_error": "daily_response_not_adjudicable"}
    _write(RUN_DIR / "subject_candidate_diagnostics.json", candidate_diagnostics)
    if daily_fact is not None:
        _write(RUN_DIR / "daily_status_2026-10-16.json", daily_fact)
    else:
        daily_attempt = ledger[0] if ledger else None
        _write(RUN_DIR / "daily_status_2026-10-16.json", {"target_date": "2026-10-16",
            "adjudication": "UNRESOLVED", "failure": failure,
            "request": daily_attempt})

    # A failed daily adjudication is a hard stop: there is no refetch and no archive call.
    archive_failure = failure
    if daily_fact is not None:
        for page_number in range(1, 5):
            url = ARCHIVE_BASE + str(page_number)
            try:
                status, headers, body, retrieved = get("index", url, "ARCHIVE_INDEX_WINDOW_DISCOVERY" if page_number == 1 else "ARCHIVE_INDEX_CONTINUATION")
                if status != 200:
                    archive_failure = "dgpa_archive_http_failure"
                    break
                items = parse_archive_index(body, content_type=headers.get("Content-Type"), base_url=url)
                archive_pages.append({"page": page_number, "endpoint": url, "effective_url": url, "http_status": status,
                    "content_type": headers.get("Content-Type"), "retrieved_at": retrieved, "response_byte_count": len(body),
                    "response_sha256": response_sha256(body), "items": items})
                assessment = adjudicate_archive_window(archive_pages, "2026-10-15")
                if assessment["historical_archive_target_entry_present"]:
                    match = assessment["matching_entries"][0]
                    dstatus, dheaders, dbody, dretrieved = get("detail", match["detail_url"], "TARGET_DATE_DETAIL_INSPECTION")
                    if dstatus != 200:
                        archive_failure = "dgpa_archive_detail_http_failure"
                        break
                    detail_fact = parse_detail_status(dbody, content_type=dheaders.get("Content-Type"), target_date="2026-10-15")
                    detail_fact.update({"endpoint": match["detail_url"], "effective_url": match["detail_url"],
                        "http_status": dstatus, "content_type": dheaders.get("Content-Type"), "retrieved_at": dretrieved,
                        "response_byte_count": len(dbody), "response_sha256": response_sha256(dbody)})
                    historical_fact = detail_fact
                    break
                if assessment["historical_negative_evidence"]:
                    historical_fact = {"target_date": "2026-10-15", "taipei_status": "no_archive_entry",
                        "closure_scope": None, "closure_event": None, **assessment}
                    break
            except (ValueError, RuntimeError) as exc:
                archive_failure = str(exc) or type(exc).__name__
                break
    assessment = adjudicate_archive_window(archive_pages, "2026-10-15")
    _write(RUN_DIR / "archive_window.json", {"archive_identity": "歷次天然災害停止上班上課訊息",
        "pages": archive_pages, "assessment": assessment, "archive_error": archive_failure})
    if detail_fact is not None:
        _write(RUN_DIR / "archive_detail.json", detail_fact)

    complete = daily_fact is not None and historical_fact is not None and archive_failure is None
    events = build_closure_events(daily_fact or {}, historical_fact or {})
    binding = None
    if complete:
        calendar = _json(P0_DIR / "twse_trading_calendar_2026.json")
        closure_ref = f"DGPA_R3:{RUN_ID}:complete_for_i3_resolution_window"
        binding = resolve_i3_twse_source_trade_date(evaluation_time=EVALUATION_TIME, official_calendar=calendar,
            closure_events=events, calendar_authority_ref=f"P0:TWSE_CALENDAR:{CALENDAR_SHA}",
            closure_authority_ref=closure_ref, closure_authority_complete=True)
        calendar_days = {item["date"]: item["is_trading_day"] for item in calendar["dates"]}
        if calendar_days.get(binding["resolved_source_trade_date"]) is not True:
            raise RuntimeError("r3_resolver_date_not_calendar_trading_day")
        _write(RUN_DIR / "p17_date_resolution.json", {**binding, "closure_events": events,
            "closure_authority_complete": True, "coverage_dates": ["2026-10-16", "2026-10-15"]})
    if complete:
        disposition = "PASS_CLOSURE_AUTHORITY_COMPLETE"
    elif failure:
        disposition = classify_daily_failure(failure, candidate_diagnostics)
    elif failure or archive_failure:
        disposition = "INCOMPLETE_AUTHORITY"
    else:
        disposition = "INCOMPLETE_AUTHORITY"
    _write(RUN_DIR / "closure_completeness.json", {"coverage_dates": ["2026-10-16", "2026-10-15"],
        "coverage_basis": "complete_for_i3_resolution_window" if complete else "resolver_window_only_incomplete",
        "daily_status_adjudicated": daily_fact is not None, "historical_status_adjudicated": historical_fact is not None,
        "historical_negative_evidence": bool(historical_fact and historical_fact.get("historical_negative_evidence")),
        "events_relevant_to_coverage_dates": events,
        "completeness_reason": "both exact dates adjudicated by official DGPA current page and verified historical archive/detail" if complete else failure or archive_failure or "target window not crossed",
        "closure_authority_complete": complete})
    counts = budget.counts()
    _write(RUN_DIR / "acquisition_ledger.json", {"entries": ledger, "counts": counts,
        "limits": LIMITS, "retry_count": 0})
    result = {"run_id": RUN_ID, "authority_id": AUTHORITY_ID, "disposition": disposition,
        "evaluation_time": EVALUATION_TIME, "closure_authority_complete": complete,
        "p17_trade_date": binding["resolved_source_trade_date"] if binding else None,
        "a6_market_authority_consumed": False, "P01_P18_performed": False,
        "B01_B05_performed": False, "TWSE_T86_performed": False,
        "counts": counts,
        "failure": failure or archive_failure}
    _write(RUN_DIR / "result.json", result)
    retained = sorted(p for p in RUN_DIR.glob("*.json") if p.name != "manifest.json")
    manifest = {"run_id": RUN_ID, "files": [{"path": item.name, "sha256": sha256(item.read_bytes()).hexdigest(),
        "size_bytes": item.stat().st_size} for item in retained]}
    manifest["manifest_sha256"] = _canonical_sha(manifest)
    _write(RUN_DIR / "manifest.json", manifest)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--execute-authorized-r3", action="store_true")
    args = parser.parse_args()
    if args.preflight_only == args.execute_authorized_r3:
        parser.error("select exactly one of --preflight-only or --execute-authorized-r3")
    print(json.dumps(preflight_only() if args.preflight_only else execute_authorized_r3(), ensure_ascii=False, indent=2))
