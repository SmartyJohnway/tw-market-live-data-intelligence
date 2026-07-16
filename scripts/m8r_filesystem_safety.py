#!/usr/bin/env python3
from __future__ import annotations
import os, re, tempfile
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

class FilesystemSafetyError(ValueError):
    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or code); self.code = code

@dataclass(frozen=True)
class SafeDestination:
    root: Path
    path: Path
    relative_path: Path

def _looks_windows_absolute(raw: str) -> bool:
    return bool(re.match(r'^[A-Za-z]:[\\/]', raw)) or raw.startswith('\\\\') or raw.startswith('//')

def _looks_drive_relative(raw: str) -> bool:
    return bool(re.match(r'^[A-Za-z]:($|[^\\/])', raw))

def _parts(raw: str) -> tuple[str, ...]:
    return tuple(p for p in re.split(r'[\\/]+', raw) if p not in ('', '.'))

def validate_authorized_root(root: str | os.PathLike[str]) -> Path:
    if root is None or str(root) == '':
        raise FilesystemSafetyError('output_root_missing')
    raw = str(root)
    if '://' in raw:
        raise FilesystemSafetyError('absolute_output_path_forbidden')
    p = Path(root)
    try:
        p.mkdir(parents=True, exist_ok=True)
        resolved = p.resolve(strict=True)
    except PermissionError as exc:
        raise FilesystemSafetyError('filesystem_permission_denied') from exc
    except OSError as exc:
        raise FilesystemSafetyError('output_root_missing') from exc
    if not resolved.is_dir():
        raise FilesystemSafetyError('output_root_missing')
    return resolved

def _reject_unsafe_candidate(candidate: str | os.PathLike[str]) -> str:
    raw = str(candidate)
    if raw == '':
        raise FilesystemSafetyError('path_traversal_forbidden')
    if '://' in raw or Path(raw).is_absolute() or _looks_windows_absolute(raw) or _looks_drive_relative(raw):
        raise FilesystemSafetyError('absolute_output_path_forbidden')
    if '..' in _parts(raw):
        raise FilesystemSafetyError('path_traversal_forbidden')
    if PureWindowsPath(raw).is_reserved():
        raise FilesystemSafetyError('path_traversal_forbidden')
    return raw

def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False

def safe_destination(root: str | os.PathLike[str], candidate: str | os.PathLike[str], *, create_parent: bool = True, allow_destination_symlink: bool = False) -> SafeDestination:
    root_resolved = validate_authorized_root(root)
    raw = _reject_unsafe_candidate(candidate)
    lexical = root_resolved.joinpath(*_parts(raw))
    if not _is_relative_to(lexical, root_resolved):
        raise FilesystemSafetyError('output_path_outside_authorized_root')
    parent = lexical.parent
    existing = parent
    while not existing.exists():
        if existing == root_resolved or existing.parent == existing:
            break
        existing = existing.parent
    try:
        existing_resolved = existing.resolve(strict=True)
    except PermissionError as exc:
        raise FilesystemSafetyError('filesystem_permission_denied') from exc
    if not _is_relative_to(existing_resolved, root_resolved):
        raise FilesystemSafetyError('output_parent_symlink_escape')
    if lexical.exists() or lexical.is_symlink():
        if lexical.is_symlink() and not allow_destination_symlink:
            raise FilesystemSafetyError('output_destination_symlink_forbidden')
        target = lexical.resolve(strict=True)
        if not _is_relative_to(target, root_resolved):
            raise FilesystemSafetyError('output_path_outside_authorized_root')
    if create_parent:
        parent.mkdir(parents=True, exist_ok=True)
    return SafeDestination(root_resolved, lexical, Path(*_parts(raw)))

def atomic_write_text(root: str | os.PathLike[str], candidate: str | os.PathLike[str], text: str, *, encoding: str = 'utf-8', allow_overwrite: bool = True) -> Path:
    dest = safe_destination(root, candidate, create_parent=True)
    if dest.path.exists() and not allow_overwrite:
        raise FilesystemSafetyError('atomic_replace_failed')
    fd = None; tmp_name = None
    try:
        fd, tmp_name = tempfile.mkstemp(prefix=f'.{dest.path.name}.', suffix='.tmp', dir=str(dest.path.parent), text=True)
        tmp = Path(tmp_name)
        if not _is_relative_to(tmp.resolve(strict=True), dest.root):
            raise FilesystemSafetyError('unsafe_temporary_path')
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            fd = None; f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, dest.path)
        return dest.path
    except FilesystemSafetyError:
        raise
    except PermissionError as exc:
        raise FilesystemSafetyError('filesystem_permission_denied') from exc
    except OSError as exc:
        raise FilesystemSafetyError('atomic_replace_failed') from exc
    finally:
        if fd is not None: os.close(fd)
        if tmp_name:
            try:
                tmp = Path(tmp_name)
                if tmp.exists() and _is_relative_to(tmp.resolve(strict=False), dest.root): tmp.unlink()
            except OSError:
                pass
