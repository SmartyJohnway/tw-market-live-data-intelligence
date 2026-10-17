"""Create a reservation bound to the committed A6 PRE2 candidate.

This utility performs no network access. It is deliberately separate from the
live runner; the live runner consumes the resulting one-shot reservation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from scripts.phase_l_a6_live_dispatch_guard import AUTHORITY_ID, contract_matrix, plan_json


def _git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _validate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    base = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("manifest_sha256") != _canonical_sha(base):
        raise ValueError("a6_pre2_manifest_digest_invalid")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("a6_pre2_manifest_invalid")
    for row in files:
        artifact = (path.parent / row["path"]).resolve()
        if path.parent.resolve() not in artifact.parents or not artifact.is_file() or _sha(artifact) != row.get("sha256"):
            raise ValueError("a6_pre2_manifest_invalid")
    return manifest


def create_reservation(*, repo: Path, plan_path: Path, matrix_path: Path,
                       pre2_manifest_path: Path, output_path: Path,
                       planned_run_id: str) -> dict[str, Any]:
    """Bind a reservation to actual Git state and reviewed PRE2 files."""
    head = _git("rev-parse", "HEAD", cwd=repo)
    tree = _git("rev-parse", "HEAD^{tree}", cwd=repo)
    if _git("status", "--porcelain", cwd=repo):
        raise ValueError("a6_reservation_worktree_not_clean")
    manifest = _validate_manifest(pre2_manifest_path.resolve())
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    sources = plan.get("sources")
    expected_ids = [f"P{i:02d}" for i in range(1, 19)] + [f"B{i:02d}" for i in range(1, 6)]
    entries = matrix.get("entries")
    if (not isinstance(sources, list) or len(sources) != 23
            or [row.get("source_contract_id") for row in sources] != expected_ids
            or [row.get("logical_sequence", row.get("sequence")) for row in sources] != list(range(1, 24))
            or plan.get("logical_count", plan.get("logical_plan_count")) != 23
            or plan.get("physical_ceiling", plan.get("absolute_physical_ceiling")) != 27
            or not isinstance(entries, list) or len(entries) != 23
            or {row.get("source_contract_id") for row in entries} != set(expected_ids)
            or _canonical_sha(sources) != _canonical_sha(plan_json())
            or _canonical_sha(entries) != _canonical_sha(contract_matrix())
            or plan.get("P17_trade_date", plan.get("p17_trade_date")) != "2026-10-15"):
        raise ValueError("a6_source_plan_invalid")
    listed = {row.get("path"): row.get("sha256") for row in manifest["files"]}
    for artifact in (plan_path.resolve(), matrix_path.resolve()):
        try:
            relative = artifact.relative_to(pre2_manifest_path.parent.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError("a6_pre2_artifact_outside_manifest_root") from exc
        if listed.get(relative) != _sha(artifact):
            raise ValueError("a6_pre2_plan_or_matrix_not_manifest_bound")
    if output_path.exists():
        raise ValueError("a6_reservation_output_already_exists")
    value = {
        "authority_id": AUTHORITY_ID,
        "state": "RESERVED_NOT_CONSUMED",
        "pre_network_head": head,
        "pre_network_tree": tree,
        "source_plan_path": str(plan_path.resolve()),
        "source_plan_sha256": _sha(plan_path),
        "transport_matrix_path": str(matrix_path.resolve()),
        "transport_matrix_sha256": _sha(matrix_path),
        "pre2_manifest_path": str(pre2_manifest_path.resolve()),
        "pre2_manifest_sha256": _sha(pre2_manifest_path.resolve()),
        "pre2_manifest_canonical_sha256": manifest["manifest_sha256"],
        "planned_run_id": planned_run_id,
        "logical_count": 23,
        "physical_ceiling": 27,
        "P17_trade_date": "2026-10-15",
        "live_authority_consumed": False,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--pre2-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--planned-run-id", required=True)
    args = parser.parse_args()
    create_reservation(repo=args.repo.resolve(), plan_path=args.plan.resolve(), matrix_path=args.matrix.resolve(),
                       pre2_manifest_path=args.pre2_manifest.resolve(), output_path=args.output.resolve(),
                       planned_run_id=args.planned_run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
