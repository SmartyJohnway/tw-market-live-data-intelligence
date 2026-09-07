#!/usr/bin/env python3
"""Explicit local Security Master lifecycle management; never runs at startup."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.m8r_08g_security_master_releases import (
    REPO_ROOT,
    SECURITY_MASTER_ROOT,
    LocalSecurityMasterError,
    activate_qualified_release,
    build_candidate_release,
    qualify_candidate_release,
    list_releases,
    load_active_identity_service,
    release_id_for_now,
)


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("status", "update", "history", "rollback", "migrate-legacy-active"),
    )
    parser.add_argument("release_id", nargs="?")
    parser.add_argument("--root", type=Path, default=SECURITY_MASTER_ROOT)
    parser.add_argument(
        "--records", type=Path, help="non-production diagnostic import; cannot activate"
    )
    parser.add_argument(
        "--legacy-pointer",
        type=Path,
        help="one-time strict historical Mode A pointer import",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="perform one explicit bounded official acquisition",
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            try:
                _, pointer, release, manifest = load_active_identity_service(
                    root=args.root
                )
                _print(
                    {
                        "status": "ACTIVE",
                        "pointer": pointer,
                        "release": release,
                        "manifest": manifest,
                    }
                )
            except LocalSecurityMasterError as exc:
                if exc.code == "NOT_INITIALIZED":
                    _print({"status": "NOT_INITIALIZED"})
                    return 0
                raise
        elif args.command == "history":
            _print({"releases": list_releases(root=args.root)})
        elif args.command == "rollback":
            if not args.release_id:
                parser.error("rollback requires release_id")
            _print(
                {
                    "active_pointer": activate_qualified_release(
                        root=args.root, release_id=args.release_id
                    ),
                    "restart_required": True,
                }
            )
        elif args.command == "migrate-legacy-active":
            if not args.legacy_pointer:
                parser.error("migrate-legacy-active requires --legacy-pointer")
            # An arbitrary JSON file is not Candidate authority.  The legacy
            # loader validates pointer, immutable seal, index, manifest, and
            # their lineage before this one-time import can proceed.
            from scripts.m8r_06_01c2_mode_a_security_master_loader import (
                load_mode_a_security_master,
            )

            legacy = load_mode_a_security_master(args.legacy_pointer)
            records = legacy.index.get("records")
            if not isinstance(records, list):
                raise LocalSecurityMasterError("legacy_index_invalid")
            release_id = args.release_id or release_id_for_now()
            source_provenance = {
                "source_type": "validated_legacy_candidate_import",
                "snapshot_id": legacy.pointer["source_snapshot_id"],
                "source_content_hashes": {
                    "legacy_compact_index": legacy.pointer["compact_index_sha256"],
                    "legacy_compact_manifest": legacy.pointer[
                        "compact_manifest_sha256"
                    ],
                    "legacy_source_snapshot": legacy.pointer["source_snapshot_sha256"],
                },
                "producer_skill": {
                    "name": "tw-security-master-classifier",
                    "skill_version": "historical",
                    "skill_contract_hash": legacy.pointer["source_skill_contract_hash"],
                },
            }
            build_candidate_release(
                root=args.root,
                release_id=release_id,
                records=records,
                source_provenance=source_provenance,
            )
            qualified, diagnostic = qualify_candidate_release(
                root=args.root, release_id=release_id
            )
            if qualified is None:
                _print(
                    {
                        "status": "REJECTED",
                        "release_id": release_id,
                        "qualification": "FAIL",
                        "diagnostic_directory": str(diagnostic),
                    }
                )
                return 1
            _print(
                {
                    "status": "ACTIVE",
                    "release_id": release_id,
                    "qualification": "PASS",
                    "active_pointer": activate_qualified_release(
                        root=args.root, release_id=release_id
                    ),
                    "migration": "validated_legacy_import",
                    "restart_required": True,
                }
            )
        else:
            # Update is deliberately explicit.  It never runs on service startup;
            # callers must supply the locally qualified acquisition projection.
            if args.live and args.records:
                parser.error("update accepts either --live or --records, not both")
            if args.live:
                # The existing governed materializer is the only acquisition
                # path.  It is explicit here and never reachable from startup.
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(
                            REPO_ROOT
                            / "scripts"
                            / "m8r_06_01b_materialize_production_inputs.py"
                        ),
                    ],
                    cwd=REPO_ROOT,
                    check=False,
                )
                if completed.returncode != 0:
                    raise LocalSecurityMasterError(
                        "official_acquisition_or_qualification_failed"
                    )
                bundles = sorted(
                    (REPO_ROOT / "data" / "security_master" / "input_bundles").glob(
                        "m8r06-01b-*"
                    ),
                    key=lambda path: path.stat().st_mtime,
                )
                if not bundles:
                    raise LocalSecurityMasterError(
                        "official_acquisition_output_missing"
                    )
                source_path = bundles[-1] / "dryrun_snapshot.json"
            else:
                if not args.records:
                    parser.error(
                        "update requires --live or --records from an explicit qualified acquisition"
                    )
                _print(
                    {
                        "status": "REJECTED",
                        "reason_code": "records_import_non_production",
                    }
                )
                return 1
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            records = payload.get("records") if isinstance(payload, dict) else payload
            if not isinstance(records, list):
                raise LocalSecurityMasterError("records_input_invalid")
            release_id = args.release_id or release_id_for_now()
            source_skill = (
                payload.get("source_skill") if isinstance(payload, dict) else None
            )
            provenance = {
                "source_type": "explicit_official_acquisition"
                if args.live
                else "explicit_qualified_acquisition",
                "local_diagnostic_path": str(source_path),
                "source_content_hashes": {
                    "input_snapshot": hashlib.sha256(
                        source_path.read_bytes()
                    ).hexdigest()
                },
                "snapshot_id": payload.get("snapshot_id")
                if isinstance(payload, dict)
                else None,
            }
            if isinstance(source_skill, dict):
                provenance["producer_skill"] = {
                    "name": source_skill.get("name"),
                    "skill_version": source_skill.get("skill_version"),
                    "skill_contract_hash": source_skill.get("skill_contract_hash"),
                }
            directory = build_candidate_release(
                root=args.root,
                release_id=release_id,
                records=records,
                source_provenance=provenance,
            )
            qualified, report_or_rejected = qualify_candidate_release(
                root=args.root, release_id=release_id
            )
            if qualified is None:
                _print(
                    {
                        "status": "REJECTED",
                        "release_id": release_id,
                        "qualification": "FAIL",
                        "diagnostic_directory": str(report_or_rejected),
                    }
                )
                return 1
            pointer = activate_qualified_release(root=args.root, release_id=release_id)
            _print(
                {
                    "status": "ACTIVE",
                    "release_id": release_id,
                    "release_directory": str(directory),
                    "qualification": "PASS",
                    "active_pointer": pointer,
                    "restart_required": True,
                }
            )
    except LocalSecurityMasterError as exc:
        _print({"status": "REJECTED", "reason_code": exc.code})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
