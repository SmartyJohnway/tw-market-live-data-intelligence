"""Create PRE1-R1 offline evidence; never reserve or consume live authority."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ENTRY_HEAD = "d9d8001b66e4c82ff7c8015fa2264c4bc8cf8365"
MAIN_SHA = "7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c"
BRANCH = "phase-l/l3-a6-bounded-live-source-drift-recertification"
ORIGINAL_RUN = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-pre1-20261016T075811Z"
ORIGINAL_GOVERNANCE = ROOT / "docs/governance/phase_l/PHASE_L_L3_A6_PRE1_SAFE_LIVE_RUNNER_PREFLIGHT_2026-10-16.md"
A0 = ROOT / "docs/governance/phase_l/PHASE_L_L3_A0_SOURCE_DRIFT_SCOPE_AND_INVENTORY_2026-10-15.md"
A5 = ROOT / "docs/governance/phase_l/PHASE_L_L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_2026-10-15.md"
DEBT_TEST = "test_lifecycle_drift_failure_report_preserves_code_without_retry_authority"
EXPECTED_IDS = [f"P{i:02d}" for i in range(1, 19)] + [f"B{i:02d}" for i in range(1, 6)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def verify_original_run() -> tuple[dict, dict]:
    manifest = json.loads((ORIGINAL_RUN / "manifest.json").read_text(encoding="utf-8"))
    base = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if canonical_sha(base) != manifest.get("manifest_sha256"):
        raise ValueError("pre1_original_manifest_invalid")
    for row in manifest.get("files", []):
        path = ORIGINAL_RUN / row["path"]
        if not path.is_file() or sha(path) != row["sha256"]:
            raise ValueError("pre1_original_evidence_changed")
    result = json.loads((ORIGINAL_RUN / "preflight_result.json").read_text(encoding="utf-8"))
    if result.get("disposition") != "A6_PREFLIGHT_DISPATCH_ACCOUNTING_UNRESOLVED":
        raise ValueError("pre1_original_failure_not_preserved")
    return manifest, result


def validate_plan(plan: dict, matrix: dict) -> None:
    sources = plan.get("sources")
    entries = matrix.get("entries")
    if (not isinstance(sources, list) or len(sources) != 23
            or [item.get("logical_sequence") for item in sources] != list(range(1, 24))
            or [item.get("source_contract_id") for item in sources] != EXPECTED_IDS
            or plan.get("logical_plan_count") != 23
            or plan.get("baseline_physical_dispatches") != 23
            or plan.get("absolute_physical_ceiling") != 27):
        raise ValueError("pre1_source_plan_mismatch")
    if not isinstance(entries, list) or len(entries) != 23:
        raise ValueError("pre1_transport_matrix_count_mismatch")
    by_id = {row.get("source_contract_id"): row for row in entries}
    if len(by_id) != 23 or set(by_id) != set(EXPECTED_IDS):
        raise ValueError("pre1_transport_matrix_ids_mismatch")
    for row in entries:
        if (not isinstance(row.get("timeout_seconds"), (int, float)) or row["timeout_seconds"] <= 0
                or row.get("retry_supported") is not False
                or row.get("a6_retry_allowed") is not False):
            raise ValueError("pre1_transport_timeout_or_retry_contract_invalid")
        expected_cap = 2 if row["source_contract_id"] in {"P04", "P05", "P06", "P07"} else 1
        if row.get("maximum_physical_dispatches") != expected_cap:
            raise ValueError("pre1_transport_source_cap_mismatch")
    if sum(row["maximum_physical_dispatches"] for row in entries) != 27:
        raise ValueError("pre1_transport_physical_ceiling_mismatch")
    if not all(token in by_id["P01"]["persistent_write_behavior"] for token in ("write_latest=False", "allow_individual_fallback=False")):
        raise ValueError("pre1_p01_nonpersistent_or_fallback_contract_missing")
    for source_id in ("B01", "B02", "B03", "B04", "B05"):
        text = by_id[source_id]["production_transport"]
        if any(token not in text for token in ("timeout=20", "max_followed_redirects=0", "save_raw=None")):
            raise ValueError("pre1_bootstrap_redirect_or_persistence_contract_missing")
    if ("month=2026-10" not in next(row for row in sources if row["source_contract_id"] == "P12")["target_or_selector"]
            or "2026-10-15" not in next(row for row in sources if row["source_contract_id"] == "P17")["target_or_selector"]):
        raise ValueError("pre1_p12_or_p17_selector_mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--offline-results", type=Path, required=True)
    args = parser.parse_args()
    if not args.run_id.startswith("l3-a6-pre1-r1-"):
        raise SystemExit("PRE1-R1 run id must start with l3-a6-pre1-r1-")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    main_sha = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    if (head != ENTRY_HEAD or branch != BRANCH or main_sha != MAIN_SHA):
        raise SystemExit("PRE1-R1 entry authority mismatch")

    original_manifest, original_result = verify_original_run()
    plan = json.loads((ORIGINAL_RUN / "a6_source_plan.json").read_text(encoding="utf-8"))
    matrix = json.loads((ORIGINAL_RUN / "transport_contract_matrix.json").read_text(encoding="utf-8"))
    validate_plan(plan, matrix)
    a0_text, a5_text = A0.read_text(encoding="utf-8"), A5.read_text(encoding="utf-8")
    if DEBT_TEST not in a0_text or DEBT_TEST not in a5_text or "2 deselected" not in a5_text:
        raise ValueError("known_test_debt_prior_authority_not_found")

    offline = json.loads(args.offline_results.read_text(encoding="utf-8"))
    required_true = ("focused_tests_pass", "integrated_gate_pass", "validators_pass", "compileall_pass", "diff_check_pass",
                     "plan_matrix_pass", "critical_safety_tests_pass", "hidden_retry_audit_pass", "nonpersistent_audit_pass")
    if any(offline.get(key) is not True for key in required_true) or offline.get("external_socket_attempts") != 0:
        raise ValueError("pre1_r1_offline_acceptance_gate_not_green")
    integrated = offline.get("integrated_test_summary", {})
    if (integrated.get("passed") != 543 or integrated.get("failed") != 0
            or integrated.get("deselected") != 1 or integrated.get("deselected_test") != DEBT_TEST):
        raise ValueError("pre1_r1_integrated_result_not_exact_known_debt_exclusion")

    candidate_paths = [
        ORIGINAL_GOVERNANCE,
        ROOT / "scripts/phase_l_a6_live_dispatch_guard.py",
        ROOT / "scripts/run_phase_l_a6_pre1_prepare.py",
        ROOT / "scripts/run_phase_l_a6_pre1_r1_prepare.py",
        ROOT / "tests/helpers/phase_l_a6_pre1_network/sitecustomize.py",
        ROOT / "tests/unit/test_phase_l_a6_pre1_dispatch_controller.py",
    ] + [ORIGINAL_RUN / row["path"] for row in original_manifest["files"]] + [ORIGINAL_RUN / "manifest.json"]
    candidate_files = [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path)} for path in sorted(candidate_paths)]
    candidate_digest = canonical_sha(candidate_files)
    run_dir = ROOT / "docs/governance/phase_l/acceptance_runs" / args.run_id
    plan["pre1_r1_run_id"] = args.run_id
    plan["pre1_r1_candidate_file_manifest_sha256"] = candidate_digest
    matrix["pre1_r1_run_id"] = args.run_id
    matrix["pre1_r1_candidate_file_manifest_sha256"] = candidate_digest
    write(run_dir / "a6_source_plan.json", plan)
    write(run_dir / "transport_contract_matrix.json", matrix)
    write(run_dir / "known_test_debt.json", {
        "test_id": DEBT_TEST,
        "reason": "rglob first-match may select nested source_probes evidence where bootstrap_failure_code is not top-level",
        "a0_governance_reference": "docs/governance/phase_l/PHASE_L_L3_A0_SOURCE_DRIFT_SCOPE_AND_INVENTORY_2026-10-15.md",
        "a5_governance_reference": "docs/governance/phase_l/PHASE_L_L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_2026-10-15.md",
        "excluded": True,
        "represented_as_passing": False,
        "production_runtime_modified_for_test": False,
        "focused_bootstrap_module_result": offline["bootstrap_module_summary"],
    })
    write(run_dir / "offline_review.json", {
        "entry_head": head, "origin_main": main_sha, "branch": branch,
        "original_pre1_run_id": "l3-a6-pre1-20261016T075811Z",
        "original_pre1_disposition": original_result["disposition"],
        "original_pre1_manifest_sha256": original_manifest["manifest_sha256"],
        "candidate_file_manifest_sha256": candidate_digest,
        "candidate_files": candidate_files,
        "offline_results": offline,
        "known_debt_excluded_not_passing": True,
        "external_socket_attempts": 0,
        "provider_requests": 0,
        "final_live_reservation_created": False,
        "market_authority_consumed": False,
    })
    write(run_dir / "preflight_result.json", {
        "disposition": "PASS_READY_FOR_FINAL_LIVE_RESERVATION",
        "logical_sources": 23, "baseline_physical_dispatches": 23,
        "absolute_physical_ceiling": 27,
        "known_test_debt_deselected": DEBT_TEST,
        "known_test_debt_represented_as_passing": False,
        "external_provider_requests": 0,
        "market_authority_consumed": False,
        "final_live_reservation_created": False,
    })
    files = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        files.append({"path": path.name, "size_bytes": path.stat().st_size, "sha256": sha(path)})
    manifest = {"run_id": args.run_id, "candidate_file_manifest_sha256": candidate_digest, "files": files}
    manifest["manifest_sha256"] = canonical_sha(manifest)
    write(run_dir / "manifest.json", manifest)
    print(json.dumps({"run_id": args.run_id, "disposition": "PASS_READY_FOR_FINAL_LIVE_RESERVATION",
                      "candidate_file_manifest_sha256": candidate_digest, "manifest_sha256": manifest["manifest_sha256"],
                      "evidence_files": files}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
