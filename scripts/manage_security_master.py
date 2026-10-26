#!/usr/bin/env python3
"""Explicit local Security Master lifecycle management; never runs at startup."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.m8r_08g_security_master_releases import (
    REPO_ROOT,
    LocalSecurityMasterError,
    activate_qualified_release,
    build_candidate_release,
    qualify_candidate_release,
    list_releases,
    load_active_identity_service,
    release_id_for_now,
    resolve_default_security_master_root,
)
from scripts.m8r_06_security_master_candidate_paths import (
    retained_source_bundle_dir,
    temp_security_master_root,
    validate_candidate_id,
)
from scripts.m8r_filesystem_safety import (
    FilesystemSafetyError,
    is_reparse_or_symlink,
    reject_reparse_components,
    validate_authorized_root,
)
from scripts.ssl_policy import (
    SSL_POLICY_COMPATIBILITY,
    SSL_POLICY_STRICT,
    SSL_POLICY_UNSAFE,
    resolve_ssl_policy,
)
from server.resource_boundaries import ResourceDiskAdmissionError, require_disk_capacity


def _installation_context(args, *, require_initialized: bool = False):
    """Resolve modern installation roots while preserving explicit test roots."""
    from scripts.tw_market_installation import (
        InstallationError,
        effective_root,
        resolve_installation,
    )

    try:
        installation = resolve_installation(
            home=args.home,
            state_root=args.state_root,
        )
        selected = effective_root(
            "security_master", explicit=args.root, installation=installation
        )
        if require_initialized:
            installation.require_initialized()
    except InstallationError as exc:
        raise LocalSecurityMasterError(str(exc)) from exc
    # Explicit roots remain usable for read-only and historical/test
    # injection.  Mutating canonical operations, including live acquisition,
    # must nevertheless be bound to an initialized installation so staging
    # cannot fall back to the replaceable checkout tree.
    return Path(selected).resolve(), installation


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _select_security_master_ssl_policy(value: str | None = None) -> str:
    """Select an explicit verified TLS policy for Security Master acquisition."""
    selected = resolve_ssl_policy(value, environ={})
    if selected == SSL_POLICY_UNSAFE:
        raise ValueError("SECURITY_MASTER_UNSAFE_TLS_POLICY_REJECTED")
    return selected


def _validate_staged_candidate(bundle_dir: Path, staging_base: Path) -> str:
    """Validate one generated bundle before it can become retained provenance."""
    try:
        reject_reparse_components(staging_base)
        reject_reparse_components(bundle_dir)
    except FilesystemSafetyError as exc:
        raise LocalSecurityMasterError("staged_candidate_reparse_point") from exc
    candidate_id = validate_candidate_id(bundle_dir.name)
    staging_root = staging_base.resolve()
    candidate_root = bundle_dir.resolve()
    if bundle_dir.is_symlink() or candidate_root.parent != staging_root:
        raise LocalSecurityMasterError("staged_candidate_outside_temp_root")
    if not bundle_dir.is_dir():
        raise LocalSecurityMasterError("staged_candidate_not_directory")
    for child in bundle_dir.rglob("*"):
        if is_reparse_or_symlink(child):
            raise LocalSecurityMasterError("staged_candidate_reparse_point")
        try:
            child.resolve().relative_to(candidate_root)
        except ValueError as exc:
            raise LocalSecurityMasterError("staged_candidate_outside_temp_root") from exc
    return candidate_id


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _retain_or_verify_bundle(bundle_dir: Path, retained_bundle: Path) -> None:
    """Retain one qualified bundle, rejecting collisions without overwrite."""
    try:
        reject_reparse_components(bundle_dir)
        validate_authorized_root(retained_bundle.parent)
    except FilesystemSafetyError as exc:
        raise LocalSecurityMasterError("retained_bundle_reparse_point") from exc
    if any(is_reparse_or_symlink(path) for path in bundle_dir.rglob("*")):
        raise LocalSecurityMasterError("staged_candidate_reparse_point")
    total_bytes = sum(path.stat().st_size for path in bundle_dir.rglob("*") if path.is_file())
    try:
        require_disk_capacity(retained_bundle.parent, total_bytes)
    except ResourceDiskAdmissionError as exc:
        raise LocalSecurityMasterError("retained_bundle_disk_admission_failed") from exc
    if retained_bundle.exists() or retained_bundle.is_symlink():
        if is_reparse_or_symlink(retained_bundle) or not retained_bundle.is_dir():
            raise LocalSecurityMasterError("retained_bundle_collision")
        if any(is_reparse_or_symlink(path) for path in retained_bundle.rglob("*")):
            raise LocalSecurityMasterError("retained_bundle_reparse_point")
        source_files = sorted(
            path.relative_to(bundle_dir)
            for path in bundle_dir.rglob("*")
            if path.is_file()
        )
        retained_files = sorted(
            path.relative_to(retained_bundle)
            for path in retained_bundle.rglob("*")
            if path.is_file()
        )
        if source_files != retained_files or any(
            _file_hash(bundle_dir / relative) != _file_hash(retained_bundle / relative)
            for relative in source_files
        ):
            raise LocalSecurityMasterError("retained_bundle_collision")
        return
    retained_bundle.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{retained_bundle.name}.staging-", dir=retained_bundle.parent)
    )
    try:
        shutil.rmtree(temporary)
        shutil.copytree(bundle_dir, temporary, symlinks=False)
        if any(is_reparse_or_symlink(path) for path in temporary.rglob("*")):
            raise LocalSecurityMasterError("retained_bundle_copy_failed")
        source_files = sorted(
            path.relative_to(bundle_dir) for path in bundle_dir.rglob("*") if path.is_file()
        )
        retained_files = sorted(
            path.relative_to(temporary) for path in temporary.rglob("*") if path.is_file()
        )
        if source_files != retained_files or any(
            _file_hash(bundle_dir / relative) != _file_hash(temporary / relative)
            for relative in source_files
        ):
            raise LocalSecurityMasterError("retained_bundle_copy_verification_failed")
        try:
            temporary.rename(retained_bundle)
        except FileExistsError as exc:
            raise LocalSecurityMasterError("retained_bundle_collision") from exc
        except OSError as exc:
            raise LocalSecurityMasterError("retained_bundle_promotion_failed") from exc
        # Re-open the promoted directory through the same guarded verifier.
        # A promotion failure must never be hidden by a partial final tree.
        _retain_or_verify_bundle(bundle_dir, retained_bundle)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("status", "update", "history", "rollback", "migrate-legacy-active"),
    )
    parser.add_argument("release_id", nargs="?")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--home", type=Path, default=None)
    parser.add_argument("--state-root", type=Path, default=None)
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
    parser.add_argument(
        "--ssl-policy",
        type=_select_security_master_ssl_policy,
        choices=(SSL_POLICY_STRICT, SSL_POLICY_COMPATIBILITY),
        default=None,
        help="verified TLS policy for update --live (default: strict)",
    )
    # Keep the documented command form portable across supported Python
    # versions when optional flags appear between the two positional values.
    args = parser.parse_intermixed_args(argv)
    if args.ssl_policy is not None and not (args.command == "update" and args.live):
        parser.error("--ssl-policy is only valid with update --live")
    try:
        requires_init = args.command in {"rollback", "migrate-legacy-active"} or (
            args.command == "update" and args.live
        )
        selected_root, installation = _installation_context(
            args, require_initialized=requires_init
        )
        installation_diagnostics = dict(getattr(installation, "diagnostics", {}))
        if args.root is not None:
            installation_diagnostics.setdefault("NONCANONICAL_ROOT_OVERRIDE", {})[
                "security_master"
            ] = "--root"
            installation_diagnostics["effective_security_master_root"] = str(
                selected_root
            )
        if args.command == "status":
            try:
                _, pointer, release, manifest = load_active_identity_service(
                    root=selected_root
                )
                _print(
                    {
                        "status": "ACTIVE",
                        "pointer": pointer,
                        "release": release,
                        "manifest": manifest,
                        "installation_diagnostics": installation_diagnostics,
                    }
                )
            except LocalSecurityMasterError as exc:
                if exc.code == "NOT_INITIALIZED":
                    _print(
                        {
                            "status": "NOT_INITIALIZED",
                            "installation_diagnostics": installation_diagnostics,
                        }
                    )
                    return 0
                raise
        elif args.command == "history":
            _print({"releases": list_releases(root=selected_root)})
        elif args.command == "rollback":
            if not args.release_id:
                parser.error("rollback requires release_id")
            _print(
                {
                    "active_pointer": activate_qualified_release(
                        root=selected_root, release_id=args.release_id
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
                root=selected_root,
                release_id=release_id,
                records=records,
                source_provenance=source_provenance,
            )
            qualified, diagnostic = qualify_candidate_release(
                root=selected_root, release_id=release_id
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
                        root=selected_root, release_id=release_id
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
                try:
                    ssl_policy = _select_security_master_ssl_policy(args.ssl_policy)
                except ValueError as exc:
                    parser.error(str(exc))
                # The existing governed materializer is the only acquisition
                # path.  It is explicit here and never reachable from startup.
                staging_base = (
                    temp_security_master_root(REPO_ROOT, installation=installation)
                    / f"invocation-{uuid.uuid4().hex}"
                )
                staging_base = validate_authorized_root(staging_base)
                command = [
                    sys.executable,
                    str(
                        REPO_ROOT
                        / "scripts"
                        / "m8r_06_01b_materialize_production_inputs.py"
                    ),
                    "--ssl-policy",
                    ssl_policy,
                ]
                if installation is not None:
                    command.extend(
                        [
                            "--bundle-root",
                            str(staging_base),
                            "--report-root",
                            str(staging_base),
                        ]
                    )
                child_env = os.environ.copy()
                child_env["TW_MARKET_HOME"] = str(installation.home)
                child_env["TW_MARKET_STATE_ROOT"] = str(installation.state_root)
                completed = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    check=False,
                    env=child_env,
                )
                if completed.returncode != 0:
                    raise LocalSecurityMasterError(
                        "official_acquisition_or_qualification_failed"
                    )
                bundles = sorted(
                    staging_base.glob("m8r06-01b-*") if staging_base.exists() else [],
                    key=lambda path: path.stat().st_mtime,
                )
                if len(bundles) != 1:
                    raise LocalSecurityMasterError(
                        "official_acquisition_output_ambiguous"
                    )
                bundle_dir = bundles[-1]
                _validate_staged_candidate(bundle_dir, staging_base)
                source_path = bundle_dir / "dryrun_snapshot.json"
                retained_bundle = retained_source_bundle_dir(selected_root, bundle_dir.name)
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
                "local_diagnostic_path_role": "NONCANONICAL_TEMP_DIAGNOSTIC",
                "retained_artifact_path": (
                    f"source-bundles/{bundle_dir.name}/dryrun_snapshot.json"
                ),
                "source_content_hashes": {
                    "input_snapshot": _file_hash(source_path)
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
                root=selected_root,
                release_id=release_id,
                records=records,
                source_provenance=provenance,
            )
            qualified, report_or_rejected = qualify_candidate_release(
                root=selected_root, release_id=release_id
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
            if args.live:
                # Retain provenance only after release qualification succeeds;
                # rejected candidates remain confined to temporary staging.
                _retain_or_verify_bundle(bundle_dir, retained_bundle)
            pointer = activate_qualified_release(root=selected_root, release_id=release_id)
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
