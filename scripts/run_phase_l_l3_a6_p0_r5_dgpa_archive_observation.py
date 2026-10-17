"""One-shot, archive-only P0-R5 DGPA observation; never fetches the daily page."""
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
    ARCHIVE_BASE, OFFICIAL_HOST, R5RequestBudget, adjudicate_archive_window,
    archive_window_needs_cross_page_confirmation, build_closure_events,
    parse_archive_index_with_diagnostics, parse_detail_status,
    response_sha256, validate_official_url,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "l3-a6-p0-r5-20261016T070339Z"
RUN_DIR = ROOT / "docs/governance/phase_l/acceptance_runs" / RUN_ID
R4_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-r4-20261016T065039Z"
P0_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z"
BASE_SHA = "7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c"
ENTRY_SHA = "3adaafb866967f0f146858ccc8a995e97e31866d"
EVALUATION_TIME = "2026-10-16T11:38:22+08:00"
CALENDAR_SHA = "28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8"
RESOLVER_SHA = "075abdbb9a5cb961cb7054583aeebbe3f8722bb9c570577037396db85dc0f010"
R4_DAILY_SHA = "059e9bbc5bc1c31d06a7d182c27c4dce4d0e01deef8a0a9b30b2cdf430b5574c"
R4_RESPONSE_SHA = "b1bdcdee51ae9513a094c5de4107c05f9fff2025cdd82a4052a7fbfd9c0c156e"
R4_MANIFEST_SHA = "f46287dbe950e0af0575569862e3dffa8d416d13dc67e4e394ba2a8f8e643e13"
AUTHORITY_ID = "USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_R5_DGPA_ARCHIVE_LIST_ITEM_GRAMMAR_AUTHORIZATION"
LIMITS = {"daily_max": 0, "archive_index_max": 4, "archive_detail_max": 1, "total_max": 5}


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


def _verify_r4_daily() -> dict:
    daily_path = R4_DIR / "daily_status_2026-10-16.json"
    manifest_path = R4_DIR / "manifest.json"
    daily_raw = daily_path.read_bytes()
    manifest = _json(manifest_path)
    manifest_body = dict(manifest)
    recorded_manifest_sha = manifest_body.pop("manifest_sha256", None)
    entry = next((item for item in manifest.get("files", []) if item.get("path") == daily_path.name), None)
    if (sha256(daily_raw).hexdigest() != R4_DAILY_SHA or not entry
            or entry.get("sha256") != R4_DAILY_SHA or recorded_manifest_sha != R4_MANIFEST_SHA
            or _canonical_sha(manifest_body) != R4_MANIFEST_SHA):
        raise RuntimeError("r4_daily_or_manifest_integrity_mismatch")
    daily = json.loads(daily_raw)
    if (daily.get("target_date") != "2026-10-16" or daily.get("status_semantics") != "NO_CLOSURE_NOTICE"
            or daily.get("response_sha256") != R4_RESPONSE_SHA or daily.get("http_status") != 200):
        raise RuntimeError("r4_daily_authority_semantics_invalid")
    return daily


def _validate_plan(plan: dict, reservation: dict) -> None:
    if plan.get("run_id") != RUN_ID or plan.get("authority_id") != AUTHORITY_ID:
        raise RuntimeError("r5_plan_identity_invalid")
    if plan.get("entry_head") != ENTRY_SHA or plan.get("base_sha") != BASE_SHA:
        raise RuntimeError("r5_plan_lineage_invalid")
    if plan.get("evaluation_time") != EVALUATION_TIME or plan.get("coverage_dates") != ["2026-10-16", "2026-10-15"]:
        raise RuntimeError("r5_plan_window_invalid")
    if plan.get("limits") != LIMITS or plan.get("daily_get_allowed") is not False:
        raise RuntimeError("r5_plan_limits_invalid")
    if plan.get("archive_index_base") != ARCHIVE_BASE:
        raise RuntimeError("r5_plan_endpoint_invalid")
    for key in ("P01_P18_execution_allowed", "B01_B05_execution_allowed", "TWSE_T86_execution_allowed",
                "daily_refetch_allowed", "i3_resolver_modification_allowed", "twse_calendar_refetch_allowed",
                "a6_market_live_authority_consumption_allowed", "retry_allowed", "sleep_backoff_allowed",
                "polling_scheduler_allowed", "production_state_mutation_allowed"):
        if plan.get(key) is not False:
            raise RuntimeError("r5_plan_scope_invalid")
    offline_path = RUN_DIR / "offline_review.json"
    if sha256(offline_path.read_bytes()).hexdigest() != plan.get("offline_review_sha256"):
        raise RuntimeError("r5_offline_review_hash_mismatch")
    offline = _json(offline_path)
    if (offline.get("all_gates_pass") is not True or offline.get("external_socket_attempts") != 0
            or offline.get("resolver_sha256") != RESOLVER_SHA or offline.get("calendar_sha256") != CALENDAR_SHA):
        raise RuntimeError("r5_offline_review_invalid")
    plan_path = RUN_DIR / "r5_plan.json"
    if reservation.get("state") != "RESERVED_NOT_CONSUMED" or reservation.get("authority_consumed") is not False:
        raise RuntimeError("r5_authority_not_reserved")
    if reservation.get("plan_sha256") != sha256(plan_path.read_bytes()).hexdigest():
        raise RuntimeError("r5_plan_hash_mismatch")
    if reservation.get("pre_network_sha") != plan.get("pre_network_sha"):
        raise RuntimeError("r5_pre_network_commit_binding_invalid")
    commit = plan.get("pre_network_sha")
    if not commit or subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, capture_output=True).returncode:
        raise RuntimeError("r5_pre_network_commit_not_ancestor")
    if _git("show", "-s", "--format=%T", commit) != reservation.get("tree_sha"):
        raise RuntimeError("r5_pre_network_tree_mismatch")
    if _git("status", "--porcelain=v1"):
        raise RuntimeError("r5_worktree_not_clean")
    if _git("rev-parse", "origin/main") != BASE_SHA:
        raise RuntimeError("r5_base_drift")
    if _git("branch", "--show-current") != "phase-l/l3-a6-bounded-live-source-drift-recertification":
        raise RuntimeError("r5_branch_invalid")
    if sha256((ROOT / "scripts/phase_i_i3_execution_date.py").read_bytes()).hexdigest() != RESOLVER_SHA:
        raise RuntimeError("R5_I3_RESOLVER_INTEGRITY_VIOLATION")
    if sha256((ROOT / "scripts/phase_l_a6_p0_r1_dgpa_closure_authority.py").read_bytes()).hexdigest() != plan.get("archive_parser_sha256"):
        raise RuntimeError("r5_archive_parser_integrity_mismatch")
    calendar = _json(P0_DIR / "twse_trading_calendar_2026.json")
    validate_2026_calendar(calendar)
    if normalized_calendar_sha256(calendar) != CALENDAR_SHA:
        raise RuntimeError("r5_p0_calendar_integrity_mismatch")
    if sha256((R4_DIR / "daily_status_2026-10-16.json").read_bytes()).hexdigest() != R4_DAILY_SHA:
        raise RuntimeError("r4_daily_mutated")
    _verify_r4_daily()
    if (RUN_DIR / "authority_consumed.json").exists():
        raise RuntimeError("r5_authority_already_consumed")


def preflight_only() -> dict:
    _validate_plan(_json(RUN_DIR / "r5_plan.json"), _json(RUN_DIR / "authority_reservation.json"))
    return {"preflight": "PASS", "run_id": RUN_ID, "external_requests": 0,
            "daily_gets_allowed": 0, "calendar_sha256": CALENDAR_SHA, "resolver_sha256": RESOLVER_SHA,
            "r4_daily_sha256": R4_DAILY_SHA}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def execute_authorized_r5() -> dict:
    plan = _json(RUN_DIR / "r5_plan.json")
    _validate_plan(plan, _json(RUN_DIR / "authority_reservation.json"))
    daily_fact = _verify_r4_daily()
    budget = R5RequestBudget()
    ledger: list[dict] = []
    pages: list[dict] = []
    diagnostics: list[dict] = []
    historical_fact = None
    detail_fact = None
    failure = None
    opener = urllib.request.build_opener(_NoRedirect())

    def get(kind: str, url: str, purpose: str) -> tuple[int, dict[str, str], bytes, str]:
        if kind == "daily":
            raise RuntimeError("r5_daily_get_forbidden")
        validate_official_url(url)
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        expected_page = budget.index + 1
        if (kind == "index" and (parsed.path != "/informationlist" or query.get("uid") != ["374"]
                                  or query.get("page") != [str(expected_page)])):
            raise RuntimeError("r5_unplanned_archive_page")
        if kind == "detail" and (parsed.path != "/information" or query.get("uid") != ["374"] or not query.get("pid")):
            raise RuntimeError("r5_unplanned_detail")
        budget.reserve(kind)
        sequence = len(ledger) + 1
        started, began = _now(), time.monotonic()
        request = urllib.request.Request(url, headers={"User-Agent": "TW-Market bounded DGPA archive authority"}, method="GET")
        if not ledger:
            _write(RUN_DIR / "authority_consumed.json", {"authority_id": AUTHORITY_ID, "run_id": RUN_ID,
                "state": "CONSUMED", "consumed_at": started, "a6_market_authority_consumed": False})
        status, headers, body, transport = 0, {}, b"", "transport_failure"
        try:
            with opener.open(request, timeout=10) as response:
                status, headers, body, transport = int(response.status), dict(response.headers.items()), response.read(), "http_response"
        except urllib.error.HTTPError as exc:
            status, headers, body, transport = int(exc.code), dict(exc.headers.items()) if exc.headers else {}, exc.read(), "http_response"
        except Exception as exc:
            transport = type(exc).__name__
        finished = _now()
        entry = {"sequence": sequence, "kind": kind, "purpose": purpose, "requested_url": url,
            "effective_url": url, "hostname": OFFICIAL_HOST, "started_at": started, "completed_at": finished,
            "http_status": status or None, "transport_outcome": transport, "content_type": headers.get("Content-Type"),
            "response_byte_count": len(body), "response_sha256": response_sha256(body) if body else None,
            "elapsed_ms": int((time.monotonic() - began) * 1000), "retry_count": 0}
        ledger.append(entry)
        _write(RUN_DIR / "acquisition_ledger.json", {"entries": ledger, "counts": budget.counts(),
            "limits": LIMITS, "retry_count": 0})
        if 300 <= status < 400:
            raise RuntimeError("r5_cross_domain_or_redirect_fail_closed")
        return status, headers, body, finished

    for page_number in range(1, 5):
        url = ARCHIVE_BASE + str(page_number)
        try:
            status, headers, body, retrieved = get("index", url,
                "ARCHIVE_INDEX_WINDOW_DISCOVERY" if page_number == 1 else "CROSS_PAGE_ORDER_CONFIRMATION" if page_number == 2 else "ARCHIVE_INDEX_CONTINUATION")
            if status != 200:
                failure = "dgpa_archive_http_failure"
                pages.append({"page": page_number, "endpoint": url, "http_status": status,
                    "response_sha256": response_sha256(body) if body else None, "items": []})
                break
            try:
                items, page_diag = parse_archive_index_with_diagnostics(body, content_type=headers.get("Content-Type"), base_url=url)
                diagnostics.extend(page_diag["items"])
            except ValueError as exc:
                error_diag = getattr(exc, "diagnostics", {"requested_page": page_number, "page_number": None,
                    "page_identity": None, "items": []})
                diagnostics.extend(error_diag.get("items", []))
                pages.append({"page": page_number, "endpoint": url, "effective_url": url,
                    "http_status": status, "retrieved_at": retrieved, "content_type": headers.get("Content-Type"),
                    "response_byte_count": len(body), "response_sha256": response_sha256(body), "items": [],
                    "parse_failure": str(exc), "page_diagnostics": error_diag,
                    "item_diagnostics": error_diag.get("items", [])})
                failure = str(exc) or "r5_archive_parser_contract_insufficient"
                break
            pages.append({"page": page_number, "endpoint": url, "effective_url": url, "http_status": status,
                "retrieved_at": retrieved, "content_type": headers.get("Content-Type"),
                "response_byte_count": len(body), "response_sha256": response_sha256(body),
                "page_identity": page_diag["page_identity"], "page_number_marker": page_diag["page_number"],
                "items": items, "item_diagnostics": page_diag["items"]})
            assessment = adjudicate_archive_window(pages, "2026-10-15")
            if assessment["historical_archive_target_entry_present"]:
                match = assessment["matching_entries"][0]
                dstatus, dheaders, dbody, dretrieved = get("detail", match["detail_url"], "TARGET_DATE_DETAIL_INSPECTION")
                if dstatus != 200:
                    failure = "dgpa_archive_detail_http_failure"
                    break
                try:
                    detail_fact = parse_detail_status(dbody, content_type=dheaders.get("Content-Type"), target_date="2026-10-15")
                    detail_fact.update({"endpoint": match["detail_url"], "effective_url": match["detail_url"],
                        "http_status": dstatus, "content_type": dheaders.get("Content-Type"), "retrieved_at": dretrieved,
                        "response_byte_count": len(dbody), "response_sha256": response_sha256(dbody)})
                    historical_fact = detail_fact
                except ValueError:
                    failure = "ARCHIVE_TARGET_DETAIL_REQUIRES_ADDITIONAL_AUTHORIZED_SURFACE"
                break
            if assessment["historical_negative_evidence"]:
                if archive_window_needs_cross_page_confirmation(pages, "2026-10-15"):
                    continue
                historical_fact = {"target_date": "2026-10-15", "taipei_status": "no_archive_entry",
                    "closure_scope": None, "closure_event": None, **assessment}
                break
        except (ValueError, RuntimeError) as exc:
            failure = str(exc) or type(exc).__name__
            break

    try:
        assessment = adjudicate_archive_window(pages, "2026-10-15")
    except ValueError as exc:
        failure = failure or str(exc)
        assessment = {"historical_archive_target_entry_present": False, "historical_negative_evidence": False,
            "reason": str(exc), "coverage_dates": []}
    complete = (daily_fact.get("status_semantics") == "NO_CLOSURE_NOTICE" and
                daily_fact.get("target_date") == "2026-10-16" and historical_fact is not None and failure is None)
    events = build_closure_events(daily_fact, historical_fact or {})
    binding = None
    if complete:
        calendar = _json(P0_DIR / "twse_trading_calendar_2026.json")
        binding = resolve_i3_twse_source_trade_date(evaluation_time=EVALUATION_TIME, official_calendar=calendar,
            closure_events=events, calendar_authority_ref=f"P0:TWSE_CALENDAR:{CALENDAR_SHA}",
            closure_authority_ref=f"DGPA_R5:{RUN_ID}:complete_for_i3_resolution_window",
            closure_authority_complete=True)
        calendar_days = {entry["date"]: entry["is_trading_day"] for entry in calendar["dates"]}
        if calendar_days.get(binding["resolved_source_trade_date"]) is not True:
            raise RuntimeError("r5_resolver_date_not_calendar_trading_day")
        _write(RUN_DIR / "p17_date_resolution.json", {**binding, "closure_events": events,
            "closure_authority_complete": True, "coverage_dates": ["2026-10-16", "2026-10-15"]})
    if complete:
        disposition = "PASS_CLOSURE_AUTHORITY_COMPLETE"
    elif failure and any(token in failure for token in ("order_unresolved", "page_identity_mismatch", "semantic_identity_missing")):
        disposition = "DGPA_ARCHIVE_CONTRACT_DRIFT_OBSERVED"
    elif failure:
        disposition = "R5_ARCHIVE_PARSER_CONTRACT_INSUFFICIENT" if "publication_date" in failure or "event_date" in failure or "items_missing" in failure else "INCOMPLETE_AUTHORITY"
    else:
        disposition = "INCOMPLETE_AUTHORITY"
    _write(RUN_DIR / "reused_r4_daily_authority.json", {"source_artifact": str(R4_DIR.name + "/daily_status_2026-10-16.json"),
        "artifact_sha256": R4_DAILY_SHA, "response_sha256": R4_RESPONSE_SHA, "manifest_sha256": R4_MANIFEST_SHA,
        "target_date": daily_fact["target_date"], "status_semantics": daily_fact["status_semantics"]})
    _write(RUN_DIR / "archive_index_diagnostics.json", {"pages": [{"page": page["page"],
        "item_count": len(page.get("items", [])), "page_number_marker": page.get("page_number_marker"),
        "items": page.get("item_diagnostics", [])}
        for page in pages], "items": diagnostics, "failure": failure})
    _write(RUN_DIR / "archive_window.json", {"archive_identity": "歷次天然災害停止上班上課訊息",
        "pages": pages, "assessment": assessment, "archive_error": failure})
    if detail_fact is not None:
        _write(RUN_DIR / "archive_detail.json", detail_fact)
    _write(RUN_DIR / "closure_completeness.json", {"coverage_dates": ["2026-10-16", "2026-10-15"],
        "coverage_basis": "complete_for_i3_resolution_window" if complete else "resolver_window_only_incomplete",
        "daily_status_adjudicated_from_r4": True, "historical_status_adjudicated": historical_fact is not None,
        "historical_negative_evidence": bool(historical_fact and historical_fact.get("historical_negative_evidence")),
        "events_relevant_to_coverage_dates": events,
        "completeness_reason": "R4 daily authority plus R5 verified archive/detail" if complete else failure or assessment.get("reason"),
        "closure_authority_complete": complete})
    counts = budget.counts()
    _write(RUN_DIR / "acquisition_ledger.json", {"entries": ledger, "counts": counts, "limits": LIMITS, "retry_count": 0})
    result = {"run_id": RUN_ID, "authority_id": AUTHORITY_ID, "disposition": disposition,
        "evaluation_time": EVALUATION_TIME, "closure_authority_complete": complete,
        "p17_trade_date": binding["resolved_source_trade_date"] if binding else None,
        "a6_market_authority_consumed": False, "P01_P18_performed": False,
        "B01_B05_performed": False, "TWSE_T86_performed": False,
        "daily_gets": 0, "counts": counts, "failure": failure}
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
    parser.add_argument("--execute-authorized-r5", action="store_true")
    args = parser.parse_args()
    if args.preflight_only == args.execute_authorized_r5:
        parser.error("select exactly one of --preflight-only or --execute-authorized-r5")
    print(json.dumps(preflight_only() if args.preflight_only else execute_authorized_r5(), ensure_ascii=False, indent=2))
