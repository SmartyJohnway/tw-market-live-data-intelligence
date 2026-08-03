"""Output containment preflight. It validates only; it never creates files."""
from __future__ import annotations

import os
from pathlib import Path

from scripts.m8r_filesystem_safety import FilesystemSafetyError, validate_relative_artifact_path

from .errors import OrchestrationError


FORBIDDEN_ROOT_PARTS = {
    ("frontend", "public"),
    ("frontend", "static"),
    ("docs", "data_capabilities"),
    ("docs", "protocol"),
    ("schemas",),
    ("scripts",),
    ("tests",),
}


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        common = os.path.commonpath([str(parent), str(child)])
        if os.name == "nt":
            return os.path.normcase(common) == os.path.normcase(str(parent))
        return common == str(parent)
    except ValueError:
        return False


def validate_governed_output_root(output_root: str | os.PathLike[str]) -> Path:
    if output_root is None or str(output_root) == "":
        raise OrchestrationError("output_root_missing")
    root = Path(output_root)
    if not root.is_absolute():
        raise OrchestrationError("output_root_not_absolute")
    if not root.exists() or not root.is_dir():
        raise OrchestrationError("output_root_missing")
    resolved = root.resolve(strict=True)
    normalized_parts = tuple(part.lower() for part in resolved.parts)
    for forbidden in FORBIDDEN_ROOT_PARTS:
        for index in range(0, len(normalized_parts) - len(forbidden) + 1):
            if normalized_parts[index : index + len(forbidden)] == forbidden:
                raise OrchestrationError("governed_output_root_forbidden")
    return resolved


def validate_contained_relative_paths(output_root: str | os.PathLike[str], relative_paths: list[str]) -> list[str]:
    root = validate_governed_output_root(output_root)
    normalized: list[str] = []
    seen: set[str] = set()
    for candidate in relative_paths:
        try:
            segments = validate_relative_artifact_path(candidate)
        except FilesystemSafetyError as exc:
            raise OrchestrationError(exc.code) from exc
        lexical = root.joinpath(*segments)
        if not _is_relative_to(lexical, root):
            raise OrchestrationError("output_path_outside_authorized_root")
        existing = lexical.parent
        while not existing.exists() and existing != root and existing.parent != existing:
            existing = existing.parent
        if not _is_relative_to(existing.resolve(strict=True), root):
            raise OrchestrationError("output_parent_symlink_escape")
        rel = "/".join(segments)
        if rel in seen:
            raise OrchestrationError("contained_output_path_collision")
        if lexical.exists() or lexical.is_symlink():
            raise OrchestrationError("contained_output_path_collision")
        seen.add(rel)
        normalized.append(rel)
    return normalized
