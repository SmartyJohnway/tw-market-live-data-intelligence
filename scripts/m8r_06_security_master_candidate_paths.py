"""Governed candidate identity and deterministic authority paths for M8R-06."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any


LEGACY_ACCEPTED_CANDIDATE_A = "m8r06-01b-20260807T053540Z"
_CANDIDATE_ID_PATTERN = re.compile(r"^m8r06-01b-\d{8}T\d{6}Z$")


def validate_candidate_id(candidate_id: object) -> str:
    """Return one strictly formatted governed candidate ID or reject it."""
    if not isinstance(candidate_id, str) or not _CANDIDATE_ID_PATTERN.fullmatch(candidate_id):
        raise ValueError("invalid_governed_candidate_id")
    try:
        datetime.strptime(candidate_id.removeprefix("m8r06-01b-"), "%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise ValueError("invalid_governed_candidate_id") from exc
    return candidate_id


def is_legacy_accepted_candidate(candidate_id: object) -> bool:
    return candidate_id == LEGACY_ACCEPTED_CANDIDATE_A


def input_bundle_dir(repo_root: Path, candidate_id: object) -> Path:
    candidate = validate_candidate_id(candidate_id)
    return repo_root / "data" / "security_master" / "input_bundles" / candidate


def runtime_index_dir(
    repo_root: Path,
    candidate_id: object,
    *,
    installation: Any | None = None,
    cache_root: Path | str | None = None,
) -> Path:
    candidate = validate_candidate_id(candidate_id)
    if cache_root is not None:
        return Path(cache_root).resolve() / candidate
    selected = _installation_path(installation, "cache_root")
    if selected is not None:
        return selected / "security-master" / candidate
    return repo_root / "data" / "security_master" / "runtime_identity_indexes" / candidate


def source_immutable_seal_path(repo_root: Path, candidate_id: object) -> Path:
    candidate = validate_candidate_id(candidate_id)
    if is_legacy_accepted_candidate(candidate):
        return repo_root / "docs" / "reviews" / "m8r06-01b-bundle-manifest" / "immutable_manifest.json"
    return (
        repo_root
        / "docs"
        / "reviews"
        / "security_master_candidates"
        / candidate
        / "source_immutable_manifest.json"
    )


def runtime_immutable_seal_path(repo_root: Path, candidate_id: object) -> Path:
    candidate = validate_candidate_id(candidate_id)
    if is_legacy_accepted_candidate(candidate):
        return (
            repo_root
            / "docs"
            / "reviews"
            / "m8r06-01c1b-runtime-index-manifest"
            / "immutable_manifest.json"
        )
    return (
        repo_root
        / "docs"
        / "reviews"
        / "security_master_candidates"
        / candidate
        / "runtime_identity_immutable_manifest.json"
    )


def materialization_report_path(repo_root: Path, candidate_id: object) -> Path:
    """Return the candidate-local 01B materialization report path.

    This intentionally has no legacy-A exception: the historical aggregate
    report is immutable evidence and is never a materializer output path.
    """
    candidate = validate_candidate_id(candidate_id)
    return (
        repo_root
        / "docs"
        / "reviews"
        / "security_master_candidates"
        / candidate
        / "materialization_report.json"
    )


def _installation_path(installation: Any, attribute: str) -> Path | None:
    """Read one path from the shared installation resolver without owning it.

    L6-A2 keeps this module usable by historical callers which only provide a
    repository root.  The resolver is the authority for modern installations;
    these helpers merely project its already-selected physical roots.
    """
    value = getattr(installation, attribute, None) if installation is not None else None
    if value is None:
        return None
    return Path(value).resolve()


def security_master_root(
    repo_root: Path,
    *,
    installation: Any | None = None,
    explicit: Path | str | None = None,
) -> Path:
    """Resolve the governed Security Master root for a selected installation."""
    if explicit is not None:
        return Path(explicit).resolve()
    selected = _installation_path(installation, "security_master_root")
    if selected is not None:
        return selected
    return (Path(repo_root) / "data" / "security_master").resolve()


def cache_security_master_root(
    repo_root: Path,
    *,
    installation: Any | None = None,
    explicit: Path | str | None = None,
) -> Path:
    """Resolve the installation-local derived Security Master cache root."""
    if explicit is not None:
        return Path(explicit).resolve()
    selected = _installation_path(installation, "cache_root")
    if selected is not None:
        return selected / "security-master"
    return (Path(repo_root) / "data" / "security_master").resolve()


def temp_security_master_root(
    repo_root: Path,
    *,
    installation: Any | None = None,
    explicit: Path | str | None = None,
) -> Path:
    """Resolve the installation-local temporary Security Master staging root."""
    if explicit is not None:
        return Path(explicit).resolve()
    selected = _installation_path(installation, "temp_root")
    if selected is not None:
        return selected / "security-master"
    return (Path(repo_root) / "data" / "security_master" / "input_bundles").resolve()


def retained_source_bundle_dir(
    security_master_root_path: Path | str, candidate_id: object
) -> Path:
    """Return the durable retained provenance directory for one candidate."""
    candidate = validate_candidate_id(candidate_id)
    return Path(security_master_root_path).resolve() / "source-bundles" / candidate
