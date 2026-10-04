"""Single-use, bounded A0 Attempt 2 acquisition and offline analysis surface.

This runner is deliberately separate from the disarmed Attempt 1/P0 runner.
It writes a durable reservation and consumed latch before its first HTTP call.
Raw response bodies remain process-memory only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.message import Message
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_phase_i_i3_a0_preflight as p0
from scripts.m8r_filesystem_safety import atomic_write_bytes, atomic_create_text_exclusive

AUTHORITY = "USER_CHAT_2026-10-01_PHASE_I_I3_A0_FRESH_ATTEMPT_2_SOURCE_TIMING_SYMMETRY_REPROBE"
STARTING_MAIN = "dafa5999c63d34d55a4665c6534aa77477448d79"
STARTING_HEAD = "3a8429b61b42fb030933bfae6b7913287378a7a7"
STARTING_TREE = "6838e1e0f0e4529ed57efea5f742597f559552f6"
ATTEMPT_DIR = "docs/governance/phase_i/acceptance_runs"
RESERVATION_REL = f"{ATTEMPT_DIR}/i3-a0-attempt2-authority-reservation.json"
CONSUMED_REL = f"{ATTEMPT_DIR}/i3-a0-attempt2-authority-consumed.json"
RESULT_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-01.json"
SM_DIR = ROOT / "data/security_master/candidates/security-master-20260926T151841Z"
SM_RELEASE = "security-master-20260926T151841Z"
SM_INDEX_SHA = "665d69e53588fa6cd723e434902946a43ac4f712920b0c4ec2adf91b556f4c10"
SM_QUALIFICATION_SHA = "481355bf0b3b79bda1c12cb5dc8a2c0be92642a139b5827335adfaa23c0e6e66"
URLS = {
    "TWSE": "https://www.twse.com.tw/rwd/zh/fund/T86?date=20260930&selectType=ALLBUT0999&response=json",
    "TPEX": "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading",
}
MAX_BYTES = 4 * 1024 * 1024
TIMEOUT_SECONDS = 30
MARKET_BUDGET = {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other_market_data": 0}


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def verify_starting_git_state() -> None:
    if git_value("branch", "--show-current") != p0.BRANCH:
        raise ValueError("branch_guard_failed")
    if git_value("rev-parse", "HEAD") != STARTING_HEAD:
        raise ValueError("head_guard_failed")
    if git_value("rev-parse", "HEAD^{tree}") != STARTING_TREE:
        raise ValueError("tree_guard_failed")
    if git_value("rev-parse", "origin/main") != STARTING_MAIN:
        raise ValueError("main_guard_failed")
    if git_value("rev-parse", "origin/" + p0.BRANCH) != STARTING_HEAD:
        raise ValueError("remote_branch_guard_failed")


def resolve_security_master() -> dict:
    index_path = SM_DIR / "index.json"
    candidate_path = SM_DIR / "candidate.json"
    qualification_path = SM_DIR / "qualification.json"
    index_bytes = index_path.read_bytes()
    candidate_bytes = candidate_path.read_bytes()
    qualification_bytes = qualification_path.read_bytes()
    index_hash = hashlib.sha256(index_bytes).hexdigest()
    qualification_hash = hashlib.sha256(qualification_bytes).hexdigest()
    index = json.loads(index_bytes)
    candidate = json.loads(candidate_bytes)
    qualification = json.loads(qualification_bytes)
    if index_hash != SM_INDEX_SHA or qualification_hash != SM_QUALIFICATION_SHA:
        raise ValueError("security_master_hash_mismatch")
    if (candidate.get("release_id") != SM_RELEASE or candidate.get("index_sha256") != index_hash
            or qualification.get("release_id") != SM_RELEASE or qualification.get("status") != "PASS"):
        raise ValueError("security_master_release_not_qualified")
    selected = {}
    for target in ("TWSE:1101", "TPEX:5347"):
        matches = [r for r in index.get("records", []) if r.get("canonical_target_id") == target]
        if len(matches) != 1:
            raise ValueError(f"security_master_binding:{target}")
        record = matches[0]
        market, code = target.split(":", 1)
        if (record.get("classification", {}).get("market") != market
                or record.get("classification", {}).get("instrument_family") != "company_share"
                or record.get("classification", {}).get("instrument_type") != "common_share"
                or record.get("execution_eligibility", {}).get("status") != "allowed"
                or record.get("identity", {}).get("security_code") != code):
            raise ValueError(f"security_master_eligibility:{target}")
        selected[target] = {
            "canonical_target_id": target,
            "isin": record["identity"].get("isin"),
            "market": market,
            "security_code": code,
            "instrument_family": "company_share",
            "instrument_type": "common_share",
            "execution_eligibility": "allowed",
            "record_id": record.get("record_id"),
            "record_hash": record.get("record_hash"),
        }
    return {
        "release_id": SM_RELEASE,
        "index_path": index_path.relative_to(ROOT).as_posix(),
        "index_sha256": index_hash,
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "qualification_path": qualification_path.relative_to(ROOT).as_posix(),
        "qualification_sha256": qualification_hash,
        "qualification_status": qualification.get("status"),
        "targets": selected,
    }


def base_mime(content_type: str | None) -> str | None:
    if not content_type:
        return None
    message = Message()
    message["content-type"] = content_type
    return message.get_content_type().lower()


def acquire_once(market: str, transport: Callable | None = None) -> tuple[dict, bytes | None]:
    """Make one fixed-URL GET (or invoke one injected fake delegate)."""
    if market not in URLS:
        raise ValueError("unapproved_market")
    if transport is None:
        request = Request(URLS[market], headers={"Accept": "application/json", "User-Agent": "tw-market-i3-a0-attempt2/1.0"}, method="GET")
        opener = build_opener(RejectRedirects())
        try:
            response = opener.open(request, timeout=TIMEOUT_SECONDS)
        except HTTPError as response:
            # HTTPError is a readable response; redirects remain un-followed.
            pass
        except Exception as error:
            return ({"market": market, "endpoint": URLS[market], "method": "GET", "timeout_seconds": TIMEOUT_SECONDS,
                     "retry_count": 0, "redirect_policy": "reject", "http_status": None, "content_type": None,
                     "base_mime": None, "retrieved_at": utc_now(), "response_byte_count": 0,
                     "response_sha256": None, "error_code": type(error).__name__}, None)
        try:
            status = getattr(response, "status", None) or response.getcode()
            content_type = response.headers.get("Content-Type")
            body = response.read(MAX_BYTES + 1)
            response.close()
        except Exception as error:
            return ({"market": market, "endpoint": URLS[market], "method": "GET", "timeout_seconds": TIMEOUT_SECONDS,
                     "retry_count": 0, "redirect_policy": "reject", "http_status": locals().get("status"),
                     "content_type": locals().get("content_type"), "base_mime": base_mime(locals().get("content_type")),
                     "retrieved_at": utc_now(), "response_byte_count": 0, "response_sha256": None,
                     "error_code": type(error).__name__}, None)
    else:
        # Test-only delegate contract receives the exact URL and bounds.
        try:
            response = transport(URLS[market], timeout=TIMEOUT_SECONDS, max_bytes=MAX_BYTES + 1,
                                 follow_redirects=False, method="GET")
            status = response.get("http_status")
            content_type = response.get("content_type")
            body = response.get("body", b"")
        except Exception as error:
            return ({"market": market, "endpoint": URLS[market], "method": "GET", "timeout_seconds": TIMEOUT_SECONDS,
                     "retry_count": 0, "redirect_policy": "reject", "http_status": None, "content_type": None,
                     "base_mime": None, "retrieved_at": utc_now(), "response_byte_count": 0,
                     "response_sha256": None, "error_code": type(error).__name__}, None)
    if not isinstance(body, bytes) or len(body) > MAX_BYTES + 1:
        telemetry = {"market": market, "endpoint": URLS[market], "method": "GET", "timeout_seconds": TIMEOUT_SECONDS,
                     "retry_count": 0, "redirect_policy": "reject", "http_status": status,
                     "content_type": content_type, "base_mime": base_mime(content_type), "retrieved_at": utc_now(),
                     "response_byte_count": min(len(body), MAX_BYTES + 1) if isinstance(body, bytes) else 0,
                     "response_sha256": hashlib.sha256(body[:MAX_BYTES + 1]).hexdigest() if isinstance(body, bytes) else None,
                     "error_code": "response_read_bound_violation"}
        return telemetry, None
    telemetry = {
        "market": market, "endpoint": URLS[market], "method": "GET", "timeout_seconds": TIMEOUT_SECONDS,
        "retry_count": 0, "redirect_policy": "reject", "http_status": status, "content_type": content_type,
        "base_mime": base_mime(content_type), "retrieved_at": utc_now(),
        "response_byte_count": len(body), "response_sha256": hashlib.sha256(body).hexdigest(),
        "error_code": None,
    }
    if len(body) > MAX_BYTES:
        telemetry["error_code"] = "response_byte_limit_exceeded"
        return telemetry, None
    if status != 200:
        telemetry["error_code"] = "http_status_not_200"
        return telemetry, None
    if telemetry["base_mime"] != "application/json":
        telemetry["error_code"] = "unsupported_content_type"
        return telemetry, None
    return telemetry, body


def _unpack_telemetry(market: str, body: bytes) -> dict:
    payload = p0.decode_payload(body)
    fields, rows = p0.unpack(market, payload)
    if market == "TWSE":
        raw_dates = [payload.get("date")] if payload.get("date") is not None else []
        top_keys = sorted(payload.keys())
    else:
        raw_dates = sorted({row.get("Date") for row in rows if row.get("Date") is not None})
        top_keys = None
    normalized_dates = []
    date_parse_errors = []
    for raw_date in raw_dates:
        try:
            normalized_dates.append(p0.official_date(raw_date, "Gregorian_YYYYMMDD" if market == "TWSE" else "ROC_YYYMMDD"))
        except Exception as error:
            date_parse_errors.append({"raw_value": str(raw_date)[:32], "error_code": type(error).__name__})
    dates = sorted(set(normalized_dates))
    return {"root_type": "object" if market == "TWSE" else "array", "top_level_keys": top_keys,
            "field_count": len(fields), "fields": fields, "row_count": len(rows),
            "raw_unique_official_dates": raw_dates, "normalized_official_dates": dates,
            "date_parse_errors": date_parse_errors,
            "source_date": dates[0] if len(dates) == 1 else None}


def _decision(telemetry: dict, analysis: dict | None, preflight_error: str | None) -> str:
    if preflight_error or set(telemetry) != {"TWSE", "TPEX"}:
        return "HOLD"
    if any(t.get("error_code") or t.get("http_status") != 200 or t.get("response_byte_count", MAX_BYTES + 1) > MAX_BYTES
           for t in telemetry.values()):
        return "HOLD"
    if analysis is None or analysis.get("status") != "PASS" or analysis.get("accepted_pure_analyzer_status") != "PASS":
        return "HOLD"
    adjudication = analysis.get("dealer_sell_adjudication") or {}
    if adjudication.get("selection_status") != "RESOLVED":
        return "HOLD"
    for source in analysis.get("sources", {}).values():
        if source.get("exact_matches") != 1 or source.get("status") != "PASS" or not source.get("normalized_trade_dates") or not source.get("selected_observation"):
            return "HOLD"
        if any(item.get("status") not in {"PASS", p0.NOT_APPLICABLE} or item.get("rows_failed") != 0
               for item in source.get("arithmetic", {}).values()):
            return "HOLD"
    return "GO_PASS"


def _diagnose_market(market: str, body: bytes, mapping: dict) -> dict:
    """Retain per-invariant failures rather than losing diagnostics on one bad row."""
    payload = p0.decode_payload(body)
    fields, rows = p0.unpack(market, payload)
    identity_field = mapping["code_field"]
    matches = [row for row in rows if row.get(identity_field) == p0.TARGETS[market]]
    date_error = None
    try:
        raw_dates = ([payload[mapping["date_field"]]] if mapping["date_source"] == "top_level"
                     else [row[mapping["date_field"]] for row in rows])
        normalized_dates = sorted({p0.official_date(value, mapping["date_encoding"]) for value in raw_dates})
        if mapping["single_date_required"] and len(normalized_dates) != 1:
            date_error = "unexpected_multiple_source_dates"
    except Exception as error:
        normalized_dates = []
        date_error = f"{type(error).__name__}:{str(error)[:100]}"
    arithmetic = p0.arithmetic(rows, mapping)
    observation = None
    observation_error = None
    if len(matches) == 1:
        try:
            observation = {"market": market, "security_code": p0.TARGETS[market],
                           "trade_date": normalized_dates[0], "unit": mapping["unit"],
                           **p0.normalized(matches[0], mapping)}
        except Exception as error:
            observation_error = f"{type(error).__name__}:{str(error)[:100]}"
    status = "PASS"
    if len(matches) != 1 or date_error or observation is None:
        status = "FAIL"
    if any(check["status"] not in {"PASS", p0.NOT_APPLICABLE} or check["rows_failed"] for check in arithmetic.values()):
        status = "FAIL"
    return {"market": market, "exact_matches": len(matches), "row_count": len(rows), "field_count": len(fields),
            "normalized_trade_dates": normalized_dates, "date_error": date_error,
            "selected_observation": observation, "observation_error": observation_error,
            "arithmetic": arithmetic, "status": status}


def analyze_payloads_detailed(twse_body: bytes, tpex_body: bytes, mapping: dict,
                              adjudication_authority: dict, adjudication: dict) -> dict:
    """Use accepted P0/P1 pure functions and retain useful HOLD diagnostics."""
    effective = mapping
    if adjudication["selection_status"] == "RESOLVED":
        import copy
        effective = copy.deepcopy(mapping)
        tpex_map = effective["markets"]["TPEX"]
        tpex_map["required_common_core"]["dealer_total"]["sell_shares"] = [adjudication["selected_candidate"]]
        tpex_map["mapping_status"] = "RESOLVED_BY_P1_WHOLE_DATASET_ARITHMETIC"
        tpex_map.pop("unresolved_fields", None)
        effective["mapping_status"] = "RESOLVED_EPHEMERAL"
        p0.validate_mapping(effective, require_resolved=True)
    sources = {"TWSE": _diagnose_market("TWSE", twse_body, effective["markets"]["TWSE"])}
    if adjudication["selection_status"] == "RESOLVED":
        sources["TPEX"] = _diagnose_market("TPEX", tpex_body, effective["markets"]["TPEX"])
    else:
        payload = p0.decode_payload(tpex_body)
        fields, rows = p0.unpack("TPEX", payload)
        matches = [row for row in rows if row.get(effective["markets"]["TPEX"]["code_field"]) == p0.TARGETS["TPEX"]]
        try:
            dates = sorted({p0.official_date(row["Date"], "ROC_YYYMMDD") for row in rows})
            date_error = None if len(dates) == 1 else "unexpected_multiple_source_dates"
        except Exception as error:
            dates, date_error = [], f"{type(error).__name__}:{str(error)[:100]}"
        sources["TPEX"] = {"market": "TPEX", "exact_matches": len(matches), "row_count": len(rows),
                            "field_count": len(fields), "normalized_trade_dates": dates,
                            "date_error": date_error, "selected_observation": None,
                            "observation_error": "dealer_sell_mapping_unresolved",
                            "arithmetic": {"candidate_invariant": adjudication["candidate_statistics"],
                                           "institutional_total_invariant": adjudication["institutional_total_invariant"],
                                           "dealer_component_split": p0.NOT_APPLICABLE},
                            "status": "FAIL"}
    dates_twse = sources["TWSE"]["normalized_trade_dates"]
    dates_tpex = sources["TPEX"]["normalized_trade_dates"]
    date_symmetry = "same" if dates_twse and dates_twse == dates_tpex else "different" if dates_twse and dates_tpex else "NOT_EVALUATED"
    return {"sources": sources, "status": "PASS" if adjudication["selection_status"] == "RESOLVED"
            and all(source["status"] == "PASS" for source in sources.values()) else "HOLD",
            "trade_date_symmetry": date_symmetry, "dealer_sell_adjudication": adjudication}


def build_record(*, security_master: dict, execution_reference_at: str, telemetry: dict,
                 payload_meta: dict, adjudication: dict | None, analysis: dict | None,
                 actual_counts: dict, preflight_error: str | None = None, reservation_path: str | None = None,
                 consumed_path: str | None = None, accepted_analyzer_status: str = "NOT_RUN") -> dict:
    decision = _decision(telemetry, analysis, preflight_error)
    symmetry = {
        "identity_symmetry": "PASS_MARKET_AND_CODE_BOUND_EXACTLY",
        "trade_date_symmetry": ("same_trade_date" if analysis and analysis.get("trade_date_symmetry") == "same"
                                else "different_trade_date_not_same_observation_date" if analysis and analysis.get("trade_date_symmetry") == "different"
                                else "NOT_PROVEN"),
        "unit_symmetry": "PASS_SHARE" if analysis and all(s["selected_observation"]["unit"] == "share" for s in analysis.get("sources", {}).values()) else "NOT_PROVEN",
        "participant_semantic_symmetry": "PASS_COMMON_CORE" if analysis and analysis.get("status") == "PASS" else "NOT_PROVEN",
        "field_grain_symmetry": "security_code_by_trade_date" if analysis and analysis.get("sources") else "NOT_PROVEN",
        "publication_timing_symmetry": "ASYMMETRIC_TPEX_FINALITY_UNRESOLVED",
        "transport_symmetry": "NOT_REQUIRED_SEMANTIC_NORMALIZATION_REQUIRED",
    }
    return {
        "schema_version": "phase_i_i3_a0_attempt_2_source_timing_symmetry_reprobe.v1",
        "owner_authority": AUTHORITY,
        "baseline_main": STARTING_MAIN,
        "starting_branch": p0.BRANCH,
        "starting_branch_head": STARTING_HEAD,
        "starting_tree": STARTING_TREE,
        "execution_reference_at": execution_reference_at,
        "security_master": security_master,
        "historical_authorities": {
            "attempt_1": {"status": "HOLD", "sha256": p0.HISTORICAL_SHA, "TWSE_gets": 1, "TPEx_gets": 1, "retry": 0},
            "p0_mapping": {"sha256": p0.MAPPING_SHA, "status": "UNRESOLVED"},
            "p0_record": {"sha256": "8d58c1eb22941099f28e72e884c4686ddab1a66de752dfd343892e959fca118a", "status": "HOLD"},
            "p1_authority": {"sha256": p0.ADJUDICATION_AUTHORITY_SHA, "selection_status": "UNRESOLVED_UNTIL_FRESH_SOURCE"},
            "p1_record": {"sha256": "541b62d45d248d28e114d04628aac379dbd2f5b6d66d6ad07ae8cd4ee661a70c", "status": "OFFLINE_ADJUDICATION_HARNESS_READY"},
        },
        "reservation": {"path": reservation_path, "reserved": True, "consumed": True,
                         "consumed_record_path": consumed_path},
        "network_budget": {"TWSE_max_gets": 1, "TPEx_max_gets": 1, "total_max_gets": 2,
                           "TAIFEX_gets": 0, "other_market_gets": 0, "retry_count": 0},
        "actual_network_counts": actual_counts,
        "source_telemetry": telemetry,
        "source_payload_metadata": payload_meta,
        "tpex_dealer_sell_adjudication": adjudication,
        "whole_dataset_arithmetic": {market: summary.get("arithmetic") for market, summary in (analysis or {}).get("sources", {}).items()},
        "normalized_target_observations": {
            market: source["selected_observation"]
            for market, source in (analysis or {}).get("sources", {}).items()
        },
        "cross_market_symmetry": symmetry,
        "publication_timing": {
            "TWSE_official_daily_product": {"18:00": "preliminary excluding block trades", "20:00": "daily product including block trades",
                                             "publication_phase_in_payload": "absent" if "TWSE" in payload_meta and not any("publish" in f.lower() or "update" in f.lower() for f in payload_meta["TWSE"].get("fields", [])) else "not_proven"},
            "TPEx": {"timestamp_fields": [f for f in payload_meta.get("TPEX", {}).get("fields", []) if "time" in f.lower() or "update" in f.lower() or "publish" in f.lower()],
                     "same_day_finality": "UNRESOLVED"},
        },
        "same_source_batching": {"per_target_network_request_required": False if payload_meta else None,
                                 "whole_market_acquisition_per_market": True if payload_meta else None,
                                 "mixed_market_max_unique_acquisitions": 2 if payload_meta else None},
        "raw_persistence": {"result": "NONE", "raw_bodies_written": False, "temporary_raw_files_written": False,
                            "source_payload_references_released_after_analysis": True},
        "analysis_status": analysis.get("status") if analysis else "NOT_COMPLETED",
        "accepted_pure_analyzer_status": accepted_analyzer_status,
        "preflight_error": preflight_error,
        "final_decision": decision,
        "A1_authorized": False,
        "implementation_authorized": False,
        "production_activation_authorized": False,
        "merge_authorized": False,
    }


def _write_record(record: dict) -> None:
    atomic_write_bytes(ROOT, RESULT_REL, json_bytes(record), allow_overwrite=False)


def preflight() -> dict:
    verify_starting_git_state()
    if (ROOT / RESERVATION_REL).exists() or (ROOT / CONSUMED_REL).exists() or (ROOT / RESULT_REL).exists():
        raise ValueError("attempt2_one_shot_latch_already_exists")
    if (ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-01.json").exists():
        raise ValueError("attempt2_record_already_exists")
    # Verify immutable historical artifacts and the accepted offline authorities before reserving.
    history_paths = {
        p0.RECORD: p0.HISTORICAL_SHA,
        "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_PROBE_MAPPING_V1.json": p0.MAPPING_SHA,
        "docs/governance/phase_i/PHASE_I_I3_A0_P0_OFFLINE_PROBE_HARNESS_CLOSURE_2026-10-01.json": "8d58c1eb22941099f28e72e884c4686ddab1a66de752dfd343892e959fca118a",
        p0.ADJUDICATION_AUTHORITY_PATH.relative_to(p0.ROOT).as_posix(): p0.ADJUDICATION_AUTHORITY_SHA,
        "docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json": "541b62d45d248d28e114d04628aac379dbd2f5b6d66d6ad07ae8cd4ee661a70c",
    }
    for path, digest in history_paths.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"immutable_authority_hash_mismatch:{path}")
    p0.load_mapping()
    p0.validate_adjudication_authority(p0.load_adjudication_authority())
    security_master = resolve_security_master()
    return {"security_master": security_master, "historical_hashes": history_paths}


def run_attempt2(*, transport: Callable | None = None, now: Callable[[], str] = utc_now) -> dict:
    preflight_result = preflight()
    security_master = preflight_result["security_master"]
    history_paths = preflight_result["historical_hashes"]
    execution_reference_at = now()
    reservation = {
        "schema_version": "phase_i_i3_a0_attempt2_authority_reservation.v1", "owner_authority": AUTHORITY,
        "reserved": True, "consumed": False, "reserved_at": execution_reference_at,
        "starting_main": STARTING_MAIN, "starting_branch": p0.BRANCH, "starting_branch_head": STARTING_HEAD,
        "starting_tree": STARTING_TREE, "historical_attempt_1_sha256": p0.HISTORICAL_SHA,
        "p0_mapping_sha256": p0.MAPPING_SHA,
        "p0_record_sha256": history_paths[p0.RECORD],
        "p1_authority_sha256": p0.ADJUDICATION_AUTHORITY_SHA,
        "p1_record_sha256": history_paths["docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json"],
        "network_budget": MARKET_BUDGET, "retry_count": 0,
        "security_master_release": security_master["release_id"],
        "targets": list(security_master["targets"]),
    }
    atomic_create_text_exclusive(ROOT, RESERVATION_REL, json_bytes(reservation).decode("utf-8"))
    consumed = dict(reservation, consumed=True, consumed_at=now(), consumed_before_first_http_attempt=True)
    atomic_create_text_exclusive(ROOT, CONSUMED_REL, json_bytes(consumed).decode("utf-8"))

    telemetry: dict[str, dict] = {}
    payload_meta: dict[str, dict] = {}
    counts = {"TWSE": 0, "TPEx": 0, "TAIFEX": 0, "other_market_data": 0}
    bodies: dict[str, bytes] = {}
    analysis = None
    adjudication = None
    accepted_analyzer_status = "NOT_RUN"
    preflight_error = None
    for market in ("TWSE", "TPEX"):
        counts["TWSE" if market == "TWSE" else "TPEx"] += 1
        info, body = acquire_once(market, transport)
        telemetry[market] = info
        if body is None:
            break
        bodies[market] = body
        try:
            payload_meta[market] = _unpack_telemetry(market, body)
        except Exception as error:
            info["error_code"] = f"payload_invalid:{type(error).__name__}"
            break

    if len(bodies) == 2:
        try:
            mapping = p0.load_mapping()
            adjudication_authority = p0.load_adjudication_authority()
            tpex_payload = p0.decode_payload(bodies["TPEX"])
            _, tpex_rows = p0.unpack("TPEX", tpex_payload)
            adjudication = p0.adjudicate_tpex_dealer_sell(tpex_rows, adjudication_authority)
            # Run the accepted pure analyzer as the semantic authority. Keep the
            # detailed per-invariant result even when it returns a governed HOLD.
            try:
                accepted_analysis = p0.analyze_acquired_payloads(
                    bodies["TWSE"], bodies["TPEX"], mapping, adjudication_authority)
                accepted_analyzer_status = accepted_analysis.get("status", "UNKNOWN")
            except Exception as error:
                accepted_analyzer_status = f"ERROR:{type(error).__name__}:{str(error)[:100]}"
            analysis = analyze_payloads_detailed(bodies["TWSE"], bodies["TPEX"], mapping,
                                                 adjudication_authority, adjudication)
            analysis["accepted_pure_analyzer_status"] = accepted_analyzer_status
        except Exception as error:
            preflight_error = f"analysis_failed:{type(error).__name__}:{str(error)[:120]}"
    else:
        preflight_error = "source_acquisition_or_payload_validation_failed"
    record = build_record(security_master=security_master, execution_reference_at=execution_reference_at,
                          telemetry=telemetry, payload_meta=payload_meta, adjudication=adjudication,
                          analysis=analysis, actual_counts=counts, preflight_error=preflight_error,
                          reservation_path=RESERVATION_REL, consumed_path=CONSUMED_REL,
                          accepted_analyzer_status=accepted_analyzer_status)
    _write_record(record)
    # Drop local raw payload references after telemetry, analysis and record creation.
    for key in list(bodies):
        bodies[key] = b""
    del bodies
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-shot I3-A0 Attempt 2; fixed endpoints only")
    parser.add_argument("--owner-authorization-reference", required=True)
    args = parser.parse_args(argv)
    if args.owner_authorization_reference != AUTHORITY:
        raise SystemExit("authority_reference_mismatch; no request made")
    result = run_attempt2()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["final_decision"] == "GO_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
