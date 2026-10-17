"""One bounded P0 authority run; never dispatches A6 market/bootstrap sources."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request
import urllib.error

from scripts.phase_l_a6_p0_authority import (
    AcquisitionBudget, CALENDAR_URL, CLOSURE_URL, assess_closure_completeness,
    canonical_sha256, compare_calendar_snapshots, derive_resolver_coverage_dates,
    normalized_calendar_sha256, validate_2026_calendar,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z"
PLAN_PATH = RUN_DIR / "p0_plan.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _validate_reservation(plan: dict, reservation: dict) -> None:
    plan_digest = hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest()
    if reservation.get("plan_sha256") != plan_digest:
        raise RuntimeError("p0_plan_reservation_hash_mismatch")
    candidate = plan.get("candidate_pre_network_sha")
    if candidate != reservation.get("pre_network_commit_sha"):
        raise RuntimeError("p0_candidate_commit_reservation_mismatch")
    tree = subprocess.run(["git", "show", "-s", "--format=%T", candidate], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()
    if tree != reservation.get("pre_network_commit_tree_sha"):
        raise RuntimeError("p0_candidate_tree_reservation_mismatch")
    status = subprocess.run(["git", "status", "--porcelain=v1"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout
    if status.strip():
        raise RuntimeError("p0_worktree_not_clean_before_dispatch")
    subprocess.run(["git", "merge-base", "--is-ancestor", candidate, "HEAD"], cwd=ROOT, check=True,
                   capture_output=True, text=True)


class _CapturedResponse:
    def __init__(self, response, on_read):
        self._response = response
        self._on_read = on_read
        self.status = getattr(response, "status", None)
        self.headers = response.headers

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return self._response.__exit__(*exc)

    def read(self, *args, **kwargs):
        body = self._response.read(*args, **kwargs)
        self._on_read(body)
        return body

    def __getattr__(self, name):
        return getattr(self._response, name)


def execute_p0() -> dict:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if (plan.get("authority_id") != "USER_CHAT_2026-10-16_PHASE_L_L3_A6_P0_CALENDAR_AND_CLOSURE_AUTHORITY_ACQUISITION"
            or plan.get("market_source_recertification_authorized_here") is not False
            or plan.get("P01_P18_execution_allowed") is not False
            or plan.get("B01_B05_execution_allowed") is not False):
        raise RuntimeError("p0_plan_authority_invalid")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    reservation = json.loads((RUN_DIR / "authority_reservation.json").read_text(encoding="utf-8"))
    if reservation.get("state") != "RESERVED" or reservation.get("consumed") is not False:
        raise RuntimeError("p0_authority_not_reserved")
    _validate_reservation(plan, reservation)

    budget = AcquisitionBudget()
    ledger: list[dict] = []
    captures: list[dict] = []
    original_urlopen = urllib.request.urlopen

    def bounded_urlopen(request, *args, **kwargs):
        url = request.full_url if isinstance(request, urllib.request.Request) else str(request)
        method = request.get_method() if isinstance(request, urllib.request.Request) else "GET"
        if method != "GET" or url not in {CALENDAR_URL, CLOSURE_URL}:
            raise RuntimeError("p0_unplanned_external_dispatch_blocked")
        authority = "TWSE_HOLIDAY_SCHEDULE" if url == CALENDAR_URL else "NCDR_DGPA_CLOSURE_CAP"
        budget.check_total()
        sequence = budget.reserve(authority)
        entry = {"attempt_sequence": len(ledger) + 1, "source_authority": authority,
                 "purpose": "INITIAL_AUTHORITY_ACQUISITION", "started_at": _utc_now(),
                 "endpoint_identity": authority, "http_outcome": "pending"}
        if not captures:
            consumed_at = _utc_now()
            consumed = {"authority_id": plan["authority_id"], "state": "CONSUMED",
                        "consumed_at": consumed_at, "first_dispatch_sequence": entry["attempt_sequence"],
                        "p0_pre_network_commit": reservation["pre_network_commit_sha"]}
            reservation.update({"state": "CONSUMED", "consumed": True, "consumed_at": consumed_at,
                                "first_dispatch_sequence": entry["attempt_sequence"]})
            (RUN_DIR / "authority_reservation.json").write_text(json.dumps(reservation, indent=2, sort_keys=True)+"\n", encoding="utf-8")
            (RUN_DIR / "authority_consumed.json").write_text(json.dumps(consumed, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        ledger.append(entry)
        started = time.monotonic()
        try:
            response = original_urlopen(request, *args, **kwargs)
            def got_body(body):
                captures.append({"endpoint_identity": authority, "body": body,
                                 "http_status": getattr(response, "status", None),
                                 "content_type": response.headers.get("Content-Type", ""),
                                 "response_bytes": len(body), "response_sha256": hashlib.sha256(body).hexdigest(),
                                 "elapsed_ms": round((time.monotonic()-started)*1000)})
            wrapped = _CapturedResponse(response, got_body)
            wrapped._attempt_entry = entry
            wrapped._started = started
            return wrapped
        except Exception as exc:
            failure_facts = {"http_outcome": "transport_or_http_exception", "failure_class": type(exc).__name__}
            if isinstance(exc, urllib.error.HTTPError):
                body = exc.read()
                failure_facts.update({"http_status": exc.code,
                                      "content_type": exc.headers.get("Content-Type", ""),
                                      "response_bytes": len(body),
                                      "response_sha256": hashlib.sha256(body).hexdigest()})
            entry.update({**failure_facts, "completed_at": _utc_now(),
                          "elapsed_ms": round((time.monotonic()-started)*1000)})
            raise

    # Reuse the current acquisition seams. Only cache writes in the temporary
    # isolated calendar root are suppressed; the caller's installation is never touched.
    import scripts.m8r_03d_watchlist_controlled_executor as calendar_executor
    import scripts.m8a_ncdr_dgpa_closure_cap as closure_source
    original_atomic_write = calendar_executor.atomic_write_text
    urllib.request.urlopen = bounded_urlopen
    calendar_executor.atomic_write_text = lambda *_a, **_k: None
    try:
        evaluation = datetime.fromisoformat(plan["evaluation_time"])
        with tempfile.TemporaryDirectory(prefix="tw-market-a6-p0-calendar-") as temp_root:
            calendar, origin = calendar_executor._load_production_calendar(evaluation, Path(temp_root))
        if calendar is None or origin != "network_fetch":
            (RUN_DIR / "acquisition_ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
            result = {"run_id": plan["run_id"], "p0_disposition": "INCOMPLETE_AUTHORITY",
                      "calendar_validation": None, "resolver_candidate_dates": [],
                      "closure_authority_complete": False, "p17_trade_date": None,
                      "reason": "TWSE calendar acquisition or normalization did not produce a valid artifact",
                      "a6_market_live_authority_consumed": False, "p01_p18_executed": False,
                      "b01_b05_executed": False,
                      "acquisition_counts": {"calendar": budget.calendar_count, "closure": budget.closure_count, "total": budget.total}}
            (RUN_DIR / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
            _write_manifest()
            return result
        calendar_stats = validate_2026_calendar(calendar)
        calendar_sha = normalized_calendar_sha256(calendar)
        coverage_dates = derive_resolver_coverage_dates(evaluation, calendar)
        calendar_capture = next(x for x in captures if x["endpoint_identity"] == "TWSE_HOLIDAY_SCHEDULE")
        calendar_entry = next(x for x in ledger if x["source_authority"] == "TWSE_HOLIDAY_SCHEDULE")
        calendar_entry.update({"completed_at": _utc_now(), "http_status": calendar_capture["http_status"],
                               "retrieved_at": _utc_now(), "content_type": calendar_capture["content_type"],
                               "http_outcome": "success", "response_sha256": calendar_capture["response_sha256"],
                               "response_bytes": calendar_capture["response_bytes"],
                               "normalized_sha256": calendar_sha,
                               "elapsed_ms": calendar_capture["elapsed_ms"],
                               "decision_after_attempt": "calendar_validated_and_resolver_window_derived"})
        (RUN_DIR / "twse_trading_calendar_2026.json").write_text(json.dumps(calendar, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")

        try:
            parsed = closure_source.fetch_and_parse_closure_feed(target_date=None, timeout=10)
        except Exception as exc:
            parsed = {"source_id": "NCDR_DGPA_CLOSURE_CAP", "parse_status": "transport_or_http_failure",
                      "closure_query_succeeded": False, "events": [], "failure_class": type(exc).__name__}
        closure_capture = next((x for x in captures if x["endpoint_identity"] == "NCDR_DGPA_CLOSURE_CAP"), None)
        closure_entry = next(x for x in ledger if x["source_authority"] == "NCDR_DGPA_CLOSURE_CAP")
        if closure_capture is not None:
            closure_entry.update({"completed_at": _utc_now(), "retrieved_at": _utc_now(),
                                  "http_status": closure_capture["http_status"],
                                  "content_type": closure_capture["content_type"], "http_outcome": "success",
                                  "response_sha256": closure_capture["response_sha256"],
                                  "response_bytes": closure_capture["response_bytes"],
                                  "normalized_sha256": canonical_sha256(parsed),
                                  "decision_after_attempt": "parsed_feed_does_not_attest_historical_window_completeness"})
        parsed.pop("provenance", None)
        closure_assessment = assess_closure_completeness(parsed, coverage_dates)
        relevant_events = closure_assessment["events_relevant_to_coverage_dates"]
        taipei_summary = [{"target_date": e.get("target_date"), "decision_status": e.get("decision_status"),
                           "work_status": e.get("work_status"), "closure_scope": e.get("closure_scope"),
                           "status": e.get("status"), "published_at": e.get("published_at")} for e in relevant_events]
        closure_snapshot = {"schema_version": "a6_p0_closure_authority_snapshot.v1",
                            "source_id": parsed.get("source_id"), "source_url": CLOSURE_URL,
                            "http_status": closure_capture["http_status"] if closure_capture else closure_entry.get("http_status"),
                            "content_type": closure_capture["content_type"] if closure_capture else closure_entry.get("content_type"),
                            "retrieved_at": closure_entry.get("retrieved_at"), "response_bytes": closure_capture["response_bytes"] if closure_capture else closure_entry.get("response_bytes"),
                            "response_sha256": closure_capture["response_sha256"] if closure_capture else closure_entry.get("response_sha256"),
                            "parse_status": parsed.get("parse_status"),
                            "closure_query_succeeded": parsed.get("closure_query_succeeded"),
                            "event_count": len(parsed.get("events", [])),
                            "taipei_municipality_event_summary": taipei_summary,
                            "events_relevant_to_coverage_dates": relevant_events, **closure_assessment}
        (RUN_DIR / "closure_authority_snapshot.json").write_text(json.dumps(closure_snapshot, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        (RUN_DIR / "acquisition_ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")

        result = {"run_id": plan["run_id"], "p0_disposition": "INCOMPLETE_AUTHORITY",
                  "calendar_validation": calendar_stats, "normalized_calendar_sha256": calendar_sha,
                  "resolver_candidate_dates": coverage_dates,
                  "closure_authority_complete": False,
                  "closure_completeness_reason": closure_assessment["completeness_reason"],
                  "p17_trade_date": None, "a6_market_live_authority_consumed": False,
                  "p01_p18_executed": False, "b01_b05_executed": False,
                  "acquisition_counts": {"calendar": budget.calendar_count, "closure": budget.closure_count, "total": budget.total}}
        (RUN_DIR / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        _write_manifest()
        return result
    finally:
        urllib.request.urlopen = original_urlopen
        calendar_executor.atomic_write_text = original_atomic_write


def _write_manifest() -> None:
    files = [p for p in RUN_DIR.iterdir() if p.is_file() and p.name != "manifest.json"]
    manifest = {"schema_version": "a6_p0_manifest.v1", "run_id": RUN_DIR.name.removeprefix("l3-a6-p0-"),
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
    (RUN_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-authorized-p0", action="store_true")
    args = parser.parse_args()
    if not args.execute_authorized_p0:
        raise SystemExit("network is disabled; pass --execute-authorized-p0 only after committed offline preflight")
    print(json.dumps(execute_p0(), ensure_ascii=False, indent=2, sort_keys=True))
