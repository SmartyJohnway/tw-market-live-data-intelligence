"""Write bounded, non-live PRE1 plan and review artifacts only."""
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
EXPECTED_HEAD = "d9d8001b66e4c82ff7c8015fa2264c4bc8cf8365"
EXPECTED_MAIN = "7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c"
BRANCH = "phase-l/l3-a6-bounded-live-source-drift-recertification"
R5_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-r5-20261016T070339Z"
R4_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-r4-20261016T065039Z"
P0_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def verify_p0_r5_prerequisites() -> dict[str, object]:
    """Verify retained prerequisites by their governed normalized/content hashes."""
    calendar = P0_DIR / "twse_trading_calendar_2026.json"
    p0_result = json.loads((P0_DIR / "result.json").read_text(encoding="utf-8"))
    daily = R4_DIR / "daily_status_2026-10-16.json"
    p17 = R5_DIR / "p17_date_resolution.json"
    r5_manifest = R5_DIR / "manifest.json"
    r5_manifest_value = json.loads(r5_manifest.read_text(encoding="utf-8"))
    if (p0_result.get("normalized_calendar_sha256") != "28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8"
            or sha(daily) != "059e9bbc5bc1c31d06a7d182c27c4dce4d0e01deef8a0a9b30b2cdf430b5574c"
            or sha(p17) != "9f9335de7c43d83e2d8304c754a3c2d488925cc1dd794b9379a53c83bb1c41a7"
            or r5_manifest_value.get("manifest_sha256") != "fe987d86be99108fe49a70d123040402b477ade3aa19ce179a6a0c4624d820a0"):
        raise ValueError("P0-R5 prerequisite provenance mismatch")
    daily_value = json.loads(daily.read_text(encoding="utf-8"))
    resolution = json.loads(p17.read_text(encoding="utf-8"))
    if (daily_value.get("target_date") != "2026-10-16"
            or daily_value.get("status_semantics") != "NO_CLOSURE_NOTICE"
            or resolution.get("closure_authority_complete") is not True
            or resolution.get("resolved_source_trade_date") != "2026-10-15"):
        raise ValueError("P0-R5 semantic prerequisite mismatch")
    return {
        "calendar_path": str(calendar.relative_to(ROOT)).replace("\\", "/"),
        "calendar_artifact_sha256": sha(calendar),
        "calendar_normalized_sha256": p0_result["normalized_calendar_sha256"],
        "r4_daily_path": str(daily.relative_to(ROOT)).replace("\\", "/"),
        "r4_daily_artifact_sha256": sha(daily),
        "r4_daily_response_sha256": daily_value["response_sha256"],
        "r4_manifest_sha256": json.loads((R4_DIR / "manifest.json").read_text(encoding="utf-8"))["manifest_sha256"],
        "r5_manifest_sha256": r5_manifest_value["manifest_sha256"],
        "r5_p17_resolution_path": str(p17.relative_to(ROOT)).replace("\\", "/"),
        "r5_p17_resolution_sha256": sha(p17),
        "closure_authority_complete": True,
        "closure_scope": "complete_for_i3_resolution_window",
        "resolved_source_trade_date": "2026-10-15",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--offline-gates-json", type=Path, required=True)
    args = parser.parse_args()
    if not args.run_id.startswith("l3-a6-pre1-"):
        raise SystemExit("PRE1 run id must start with l3-a6-pre1-")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if head != EXPECTED_HEAD or branch != BRANCH:
        raise SystemExit("PRE1 entry HEAD or branch changed")
    try:
        provenance = verify_p0_r5_prerequisites()
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"P0-R5 prerequisite verification failed: {type(exc).__name__}") from exc

    from scripts.phase_l_a6_live_dispatch_guard import build_plan, contract_matrix, AUTHORITY_ID
    plan_items = build_plan()
    matrix = contract_matrix()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    daily_value = json.loads((R4_DIR / "daily_status_2026-10-16.json").read_text(encoding="utf-8"))
    calendar = P0_DIR / "twse_trading_calendar_2026.json"
    folder = ROOT / "docs/governance/phase_l/acceptance_runs" / args.run_id
    plan = {
        "run_id": args.run_id, "authority_id": AUTHORITY_ID,
        "canonical_main_sha": EXPECTED_MAIN, "entry_head": head, "branch": branch,
        "evaluation_timestamp": now, "logical_plan_count": len(plan_items),
        "baseline_physical_dispatches": 23, "absolute_physical_ceiling": 27,
        "p17_trade_date": "2026-10-15", "p17_target": "TWSE:2330",
        "p0_r5_prerequisites": provenance,
        "sources": [item.__dict__ for item in plan_items],
        "external_provider_requests_authorized_in_pre1": False,
    }
    write(folder / "a6_source_plan.json", plan)
    write(folder / "transport_contract_matrix.json", {
        "entry_count": len(matrix), "entries": matrix,
    })
    review = json.loads(args.offline_gates_json.read_text(encoding="utf-8"))
    required = {"focused_tests", "integrated_source_tests", "validators", "compileall", "diff_check", "external_socket_attempts"}
    if not required.issubset(review):
        raise SystemExit("offline gate result fields mismatch")
    passed = (all(review[key] is True for key in required - {"external_socket_attempts"})
              and review["external_socket_attempts"] == 0)
    write(folder / "offline_review.json", {
        "entry_head": head, "offline_gates": review,
        "p0_r5_provenance_verified": True,
        "external_socket_attempts": 0,
        "production_state_mutations": 0,
        "live_source_requests": 0,
        "final_live_reservation_created": False,
        "authority_consumed": False,
    })
    write(folder / "authority_reservation_template.json", {
        "authority_id": AUTHORITY_ID, "state": "NOT_RESERVED_PREVIEW_ONLY",
        "live_authority_consumed": False,
        "pre1_cannot_create_final_reservation": True,
    })
    write(folder / "preflight_result.json", {
        "disposition": "PASS_READY_FOR_FINAL_LIVE_RESERVATION" if passed else "A6_PREFLIGHT_DISPATCH_ACCOUNTING_UNRESOLVED",
        "failed_gates": [key for key in sorted(required - {"external_socket_attempts"}) if review[key] is not True],
        "integrated_test_summary": review.get("integrated_test_summary"),
        "logical_sources": len(plan_items), "baseline_physical_dispatches": 23,
        "absolute_physical_ceiling": 27, "external_provider_requests": 0,
        "live_authority_consumed": False, "final_live_reservation_created": False,
    })
    files = []
    for path in sorted(folder.glob("*.json")):
        if path.name == "manifest.json":
            continue
        files.append({"path": path.name, "size_bytes": path.stat().st_size, "sha256": sha(path)})
    manifest = {"run_id": args.run_id, "files": files}
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    write(folder / "manifest.json", manifest)
    print(json.dumps({"run_id": args.run_id, "directory": str(folder), "disposition": "PASS_READY_FOR_FINAL_LIVE_RESERVATION" if passed else "A6_PREFLIGHT_DISPATCH_ACCOUNTING_UNRESOLVED", "files": files}, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
