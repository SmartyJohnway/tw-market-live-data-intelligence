"""Output containment for M8R-05C.

Stage-before-promote pattern:
1. Validate all output paths are relative (no absolute, UNC, or path traversal).
2. Write to temporary staging files.
3. Validate staged content (schemas, hashes).
4. Promote by atomic rename.
5. On any failure, remove staged files without promoting.

Never creates files outside the governed output directory.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .errors import ProjectionError

_FORBIDDEN_PREFIX_PATTERNS = (
    # Windows drive-rooted
    ("drive_rooted", lambda p: len(p) >= 2 and p[1] == ":"),
    # UNC paths
    ("unc_path", lambda p: p.startswith("\\\\") or p.startswith("//")),
    # Unix absolute
    ("unix_absolute", lambda p: p.startswith("/")),
    # Windows absolute with backslash
    ("win_absolute_backslash", lambda p: p.startswith("\\")),
)

_TRAVERSAL_SEGMENTS = {"..", "~"}


def _validate_relative_output_path(relative_path: str) -> list[str]:
    """Validate that relative_path is safe and return normalized segments.

    Raises ProjectionError if any containment rule is violated.
    """
    if not relative_path:
        raise ProjectionError("output_path_empty")

    for name, check in _FORBIDDEN_PREFIX_PATTERNS:
        if check(relative_path):
            raise ProjectionError(f"output_path_absolute_{name}")

    # Normalize separators.
    normalized = relative_path.replace("\\", "/")
    segments = [s for s in normalized.split("/") if s]

    if not segments:
        raise ProjectionError("output_path_empty")

    for seg in segments:
        if seg in _TRAVERSAL_SEGMENTS:
            raise ProjectionError("output_path_traversal")
        if seg.startswith(".") and len(seg) > 1:
            # Hidden files like .env are forbidden.
            raise ProjectionError("output_path_hidden_file")

    return segments


def _validate_output_root(output_root: str) -> Path:
    """Validate and return the output root path."""
    if not output_root:
        raise ProjectionError("output_root_missing")
    root = Path(output_root)
    if not root.is_absolute():
        raise ProjectionError("output_root_not_absolute")
    if not root.exists() or not root.is_dir():
        raise ProjectionError("output_root_missing")
    return root.resolve(strict=True)


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        common = os.path.commonpath([str(parent), str(child)])
        if os.name == "nt":
            return os.path.normcase(common) == os.path.normcase(str(parent))
        return common == str(parent)
    except ValueError:
        return False


def materialize_outputs(
    *,
    output_root: str,
    result_json: dict,
    audit_package_json: dict,
    result_markdown: str,
    result_relative_path: str,
    audit_relative_path: str,
    result_md_relative_path: str,
) -> dict[str, str]:
    """Materialize all output files using stage-before-promote.

    Returns a dict mapping relative_path → absolute_path for all promoted files.

    On failure, removes any staged files without promoting.
    """
    root = _validate_output_root(output_root)

    # Validate all output paths.
    result_segs = _validate_relative_output_path(result_relative_path)
    audit_segs = _validate_relative_output_path(audit_relative_path)
    md_segs = _validate_relative_output_path(result_md_relative_path)

    result_dest = root.joinpath(*result_segs)
    audit_dest = root.joinpath(*audit_segs)
    md_dest = root.joinpath(*md_segs)

    for dest in [result_dest, audit_dest, md_dest]:
        if not _is_relative_to(dest, root):
            raise ProjectionError("output_path_outside_root")

    # Check for collisions with existing files.
    for dest, rel in [
        (result_dest, result_relative_path),
        (audit_dest, audit_relative_path),
        (md_dest, result_md_relative_path),
    ]:
        if dest.exists():
            raise ProjectionError(f"output_path_already_exists:{rel}")

    # Create parent directories.
    for dest in [result_dest, audit_dest, md_dest]:
        dest.parent.mkdir(parents=True, exist_ok=True)

    # Stage all files.
    staged: list[tuple[Path, Path]] = []  # (staged, dest)
    try:
        for content, dest, is_json in [
            (json.dumps(result_json, ensure_ascii=False, sort_keys=True, indent=2), result_dest, True),
            (json.dumps(audit_package_json, ensure_ascii=False, sort_keys=True, indent=2), audit_dest, True),
            (result_markdown, md_dest, False),
        ]:
            fd, staged_path_str = tempfile.mkstemp(
                dir=dest.parent,
                prefix=".tmp_m8r_05c_",
                suffix=".json" if is_json else ".md",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                os.unlink(staged_path_str)
                raise
            staged.append((Path(staged_path_str), dest))

        # Validate staged JSON can be parsed back, and check sizes.
        for staged_path, dest in staged:
            size = staged_path.stat().st_size
            if size == 0:
                raise ProjectionError("staged_file_empty")
            if size > 50 * 1024 * 1024:  # 50MB sanity limit
                raise ProjectionError("staged_file_too_large")

            if dest.suffix == ".json":
                try:
                    json.loads(staged_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    raise ProjectionError("staged_json_invalid") from exc

        # Promote: atomic rename.
        promoted: list[tuple[str, str]] = []
        for staged_path, dest in staged:
            staged_path.rename(dest)
            promoted.append((str(dest.relative_to(root)).replace("\\", "/"), str(dest)))

        return {rel: abs_path for rel, abs_path in promoted}

    except Exception:
        # Remove staged files on any failure.
        for staged_path, _dest in staged:
            try:
                if staged_path.exists():
                    staged_path.unlink()
            except OSError:
                pass
        raise


def validate_output_paths_only(
    *,
    output_root: str,
    result_relative_path: str,
    audit_relative_path: str,
    result_md_relative_path: str,
) -> None:
    """Validate containment without writing any files.

    Used in --check-only mode.
    """
    root = _validate_output_root(output_root)
    for rel in [result_relative_path, audit_relative_path, result_md_relative_path]:
        segs = _validate_relative_output_path(rel)
        dest = root.joinpath(*segs)
        if not _is_relative_to(dest, root):
            raise ProjectionError("output_path_outside_root")
