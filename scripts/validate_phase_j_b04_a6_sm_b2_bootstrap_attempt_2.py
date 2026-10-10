#!/usr/bin/env python3
"""Validate sanitized SM-B2 evidence against installation-local artifacts.

This validator is strictly local and performs no network access.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B2_QUALIFIED_SECURITY_MASTER_BOOTSTRAP_ATTEMPT_2_2026-10-10.json"
AUTH_HEAD = "6d0bed858b58238712df761be9963c8b86dec15d"
AUTH_TREE = "d210546549b9f7b76d567e432674f720e6b0d89e"
AUTH_MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
AUTH_SHA = "76750a5147901b34102120baee47ab5e9f1022bd7a5e9465ad10aee1807f34c4"
RELEASE_ID = "security-master-20261010T112837Z"
BUNDLE_ID = "m8r06-01b-20261010T112548Z"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def strict_json(path: Path) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate JSON key {key!r}")
            out[key] = value
        return out

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except Exception as exc:
        fail(f"invalid strict JSON {path}: {exc}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_hash(path: Path, expected_hash: str, expected_bytes: int | None = None) -> None:
    if not path.is_file():
        fail(f"required local artifact missing: {path}")
    if expected_bytes is not None and path.stat().st_size != expected_bytes:
        fail(f"byte count mismatch: {path}")
    if sha256(path) != expected_hash:
        fail(f"SHA-256 mismatch: {path}")


def main() -> int:
    record = strict_json(RECORD)
    if not isinstance(record, dict):
        fail("governance record root is not an object")

    baseline = record["authorized_baseline"]
    if baseline != {
        "head": AUTH_HEAD,
        "tree": AUTH_TREE,
        "origin_main": AUTH_MAIN,
        "tracked_worktree_clean_preflight": True,
        "pr_326_open_draft_unmerged_preflight": True,
    }:
        fail("authorized baseline differs")
    if record["terminal_disposition"] != "SM_B2_BOOTSTRAP_SUCCESS_ACTIVE_IDENTITY_VERIFIED":
        fail("unexpected terminal disposition")
    if record["owner_authorization"]["statement_sha256"] != AUTH_SHA:
        fail("Owner authorization hash differs")

    run = record["bootstrap_invocation"]
    if (run["exact_command"] != "python scripts/manage_security_master.py update --live"
            or run["invocation_count"] != 1 or run["retry_count"] != 0
            or run["exit_code"] != 0 or run["authorization_consumed"] is not True):
        fail("bootstrap invocation accounting differs")

    transport = record["transport"]
    ids = ["twse_isin_mode2_zh", "twse_isin_mode4_zh", "twse_delisted", "tpex_delisted", "twse_etn_expired"]
    if transport["source_ids_in_order"] != ids or transport["logical_source_probes"] != 5:
        fail("source inventory is not exactly the five governed probes")
    if (transport["GET_dispatches"] != 4 or transport["POST_dispatches"] != 1
            or transport["actual_http_dispatches"] != 5
            or transport["total_dispatch_reservations"] != 5
            or transport["redirects_followed"] != 0
            or transport["automatic_retries"] != 0
            or transport["budget_respected"] is not True):
        fail("transport accounting differs")

    expected = {
        "twse_isin_mode2_zh": ("GET", "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2", 9027968, "9e4bed5cd08f65cb6c181630538925d389ea7e7507e9eb34dc055d4257504753", 37824),
        "twse_isin_mode4_zh": ("GET", "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4", 3018993, "036d7f2b59880aa3df5ea0c8448394a7e0e48e5633ad1ac73cac0235cd757bdd", 12665),
        "twse_delisted": ("GET", "https://www.twse.com.tw/company/suspendListingCsvAndHtml?lang=zh&type=html", 51814, "3ba1395a7549d8ebee35c02350bb5470c9cdde68ddc4339a461b6d19953a9228", 265),
        "tpex_delisted": ("POST", "https://www.tpex.org.tw/www/zh-tw/company/deListed", 71065, "d70bcef49999ffb4c6642ae1e55910e26636d02fd4eb90f8eab84094b98de4a5", 582),
        "twse_etn_expired": ("GET", "https://www.twse.com.tw/rwd/zh/ETN/expireEnd?response=json", 1703, "e049ed302b3bdd7b73bc77a3c8d2d015835da6882db8652f397d4c8514019484", 13),
    }
    source_results = record["source_results"]
    if [item["source_id"] for item in source_results] != ids:
        fail("per-source results are incomplete or reordered")
    for source in source_results:
        method, url, size, digest, count = expected[source["source_id"]]
        if (source["method"] != method or source["url"] != url
                or source["http_status"] != 200 or source["redirect_count"] != 0
                or source["dispatch_reservations"] != 1 or source["actual_dispatches"] != 1
                or source["bytes"] != size or source["sha256"] != digest):
            fail(f"source telemetry mismatch: {source['source_id']}")
        raw_path = ROOT / source["raw_path"]
        verify_hash(raw_path, digest, size)
        if source["source_id"] in ("twse_isin_mode2_zh", "twse_isin_mode4_zh"):
            if source["record_count"] != count:
                fail(f"identity record count mismatch: {source['source_id']}")
        elif source["source_id"] in ("twse_delisted", "twse_etn_expired"):
            if source["event_count"] != count:
                fail(f"lifecycle event count mismatch: {source['source_id']}")

    tpex = source_results[3]
    if (tpex["rows"] != 582 or tpex["totalCount"] != 582 or not tpex["count_reconciled"]
            or tpex["request_body_parameters"] != {
                "code": "", "date": "ALL", "reason": "-1", "response": "json",
                "paging-offset": "0", "paging-size": "1000"}):
        fail("TPEx qualified request/count evidence differs")
    etn = source_results[4]
    if (etn["date_min"] != "2020-04-30" or etn["date_max"] != "2026-05-28"
            or etn["duplicate_identity_count"] != 0):
        fail("ETN bounded lifecycle evidence differs")
    twse_delisted = source_results[2]
    if (twse_delisted["generic_probe_acquisition_status"] != "schema_drift"
            or twse_delisted["generic_probe_schema_valid"] is not False
            or twse_delisted["event_count"] != 265):
        fail("TWSE delisted telemetry discrepancy was not retained")

    pipeline = record["pipeline"]
    if (pipeline["candidate_qualification"] != "PASS"
            or pipeline["release_state"] != "QUALIFIED"
            or pipeline["activation_succeeded"] is not True
            or pipeline["lifecycle_events_qualified"] != 860
            or pipeline["dryrun_snapshot_lifecycle_events_attached"] != 145
            or pipeline["dryrun_snapshot_lifecycle_events_quarantined"] != 715):
        fail("pipeline result or known count discrepancy differs")

    bundle = ROOT / "data/security_master/input_bundles" / BUNDLE_ID
    release = ROOT / "data/security_master/releases" / RELEASE_ID
    candidate = ROOT / "data/security_master/candidates" / RELEASE_ID
    hashes = record["artifact_hashes"]
    for key in ("active_selector", "release_descriptor", "release_manifest", "release_index", "release_qualification", "bundle_source_evidence_manifest", "bundle_immutable_manifest", "bundle_qualification_report", "dryrun_manifest", "materialization_report"):
        item = hashes[key]
        path = ROOT / item["path"]
        verify_hash(path, item["sha256"], item["bytes"])
    verify_hash(candidate / "candidate.json", hashes["candidate_descriptor"]["sha256"], hashes["candidate_descriptor"]["bytes"])
    verify_hash(candidate / "index.json", hashes["candidate_index"]["sha256"], hashes["candidate_index"]["bytes"])
    verify_hash(candidate / "qualification.json", hashes["candidate_qualification"]["sha256"], hashes["candidate_qualification"]["bytes"])

    selector = strict_json(ROOT / "data/security_master/active.json")
    manifest = strict_json(release / "manifest.json")
    qualification = strict_json(release / "qualification.json")
    release_descriptor = strict_json(release / "release.json")
    if selector["release_id"] != RELEASE_ID:
        fail("active selector does not target the expected release")
    if (selector["release_manifest_sha256"] != hashes["release_manifest"]["sha256"]
            or selector["release_index_sha256"] != hashes["release_index"]["sha256"]):
        fail("active selector hashes do not bind the recorded release artifacts")
    if manifest["release_id"] != RELEASE_ID or release_descriptor["state"] != "QUALIFIED":
        fail("release manifest/descriptor binding mismatch")
    if qualification["status"] != "PASS":
        fail("release qualification is not PASS")
    binding = record["active_binding"]
    if (binding["active_release_id"] != RELEASE_ID or binding["atomic_binding_verified"] is not True
            or binding["active_manifest_sha256_matches_file"] is not True
            or binding["active_index_sha256_matches_file"] is not True):
        fail("recorded ACTIVE binding is incomplete")

    identity = record["production_identity"]
    if (identity["fresh_process"] is not True or identity["target"] != "TWSE:2330"
            or identity["identity_resolution_status"] != "resolved"
            or identity["reason"] != "exact_listing_id" or identity["market"] != "TWSE"
            or identity["security_code"] != "2330" or identity["isin"] != "TW0002330008"
            or identity["instrument_family"] != "company_share"
            or identity["instrument_type"] != "common_share"
            or identity["execution_eligibility"] != "allowed" or identity["verified"] is not True):
        fail("production identity predicates do not all pass")
    preflight = strict_json(Path(identity["preflight_output_path"]))
    target_binding = preflight["identity_resolution"]["target_binding"]
    if (preflight["production_identity_verified"] is not True
            or preflight["security_master_release_id"] != RELEASE_ID
            or preflight["security_master_manifest_hash"] != hashes["release_manifest"]["sha256"]
            or target_binding["canonical_target_id"] != "TWSE:2330"
            or target_binding["execution_eligibility"] != "allowed"):
        fail("fresh-process preflight does not verify identity")

    boundaries = record["network_and_execution_boundaries"]
    if (boundaries["source_network_after_bootstrap"] != 0
            or boundaries["H3_live_calls"] != 0 or boundaries["H2_live_calls"] != 0
            or boundaries["A6_integrated_live_execution"] is not False
            or boundaries["H2_activation"] is not False):
        fail("post-bootstrap boundary state differs")
    print("PASS: SM-B2 evidence, source receipts, ACTIVE hashes, and fresh identity are locally bound")
    return 0


if __name__ == "__main__":
    sys.exit(main())
