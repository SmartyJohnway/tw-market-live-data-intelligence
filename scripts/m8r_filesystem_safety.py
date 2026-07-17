#!/usr/bin/env python3
from __future__ import annotations
import os, re, tempfile
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

class FilesystemSafetyError(ValueError):
    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or code)
        self.code = code

@dataclass(frozen=True)
class SafeDestination:
    root: Path
    path: Path
    relative_path: Path

@dataclass(frozen=True)
class PathClassification:
    raw: str
    segments: tuple[str, ...]
    normalized_relative: str | None
    path_class: str
    platform_hints: tuple[str, ...]
    safe_relative: bool
    rejection_code: str | None

def _looks_device_namespace(raw: str) -> bool:
    if raw.startswith('\\\\?\\') or raw.startswith('\\\\.\\'):
        return True
    if raw.startswith('//?/') or raw.startswith('//./'):
        return True
    return False

def _looks_unc(raw: str) -> bool:
    if _looks_device_namespace(raw):
        return False
    return raw.startswith('\\\\') or raw.startswith('//')

def _looks_drive_relative(raw: str) -> bool:
    return bool(re.match(r'^[A-Za-z]:($|[^\\/])', raw))

def _looks_windows_absolute(raw: str) -> bool:
    return bool(re.match(r'^[A-Za-z]:[\\/]', raw))

def classify_artifact_relative_path(
    candidate: str | os.PathLike[str],
) -> PathClassification:
    raw = str(candidate)
    
    if any(ord(c) < 32 or ord(c) == 127 for c in raw):
        return PathClassification(
            raw=raw, segments=(), normalized_relative=None,
            path_class='control_character', platform_hints=(),
            safe_relative=False, rejection_code='control_character_forbidden'
        )
    
    if '://' in raw:
        return PathClassification(
            raw=raw, segments=(), normalized_relative=None,
            path_class='scheme', platform_hints=(),
            safe_relative=False, rejection_code='absolute_output_path_forbidden'
        )
        
    if _looks_device_namespace(raw):
        return PathClassification(
            raw=raw, segments=(), normalized_relative=None,
            path_class='device_namespace', platform_hints=(),
            safe_relative=False, rejection_code='device_namespace_path_forbidden'
        )
        
    if _looks_unc(raw):
        return PathClassification(
            raw=raw, segments=(), normalized_relative=None,
            path_class='unc', platform_hints=(),
            safe_relative=False, rejection_code='unc_output_path_forbidden'
        )
        
    if _looks_drive_relative(raw) or _looks_windows_absolute(raw):
        pclass = 'drive_relative' if _looks_drive_relative(raw) else 'absolute'
        rejection = 'drive_relative_output_path_forbidden' if pclass == 'drive_relative' else 'absolute_output_path_forbidden'
        return PathClassification(
            raw=raw, segments=(), normalized_relative=None,
            path_class=pclass, platform_hints=(),
            safe_relative=False, rejection_code=rejection
        )

    if raw.startswith('/') or raw.startswith('\\'):
        return PathClassification(
            raw=raw, segments=(), normalized_relative=None,
            path_class='rooted', platform_hints=(),
            safe_relative=False, rejection_code='rooted_output_path_forbidden'
        )

    normalized = raw.replace('\\', '/')
    raw_segments = normalized.split('/')
    
    segments = tuple(s for s in raw_segments if s not in ('', '.'))
    
    if '..' in segments:
        return PathClassification(
            raw=raw, segments=segments, normalized_relative=None,
            path_class='traversal', platform_hints=(),
            safe_relative=False, rejection_code='path_traversal_forbidden'
        )

    RESERVED_NAMES = {'con', 'prn', 'aux', 'nul'}
    for i in range(1, 10):
        RESERVED_NAMES.add(f'com{i}')
        RESERVED_NAMES.add(f'lpt{i}')
        
    for seg in segments:
        seg_lower = seg.lower()
        base = seg_lower.split('.')[0]
        if base in RESERVED_NAMES:
            return PathClassification(
                raw=raw, segments=segments, normalized_relative=None,
                path_class='reserved_segment', platform_hints=(),
                safe_relative=False, rejection_code='reserved_path_segment_forbidden'
            )

    for seg in segments:
        if ':' in seg:
            return PathClassification(
                raw=raw, segments=segments, normalized_relative=None,
                path_class='alternate_data_stream', platform_hints=(),
                safe_relative=False, rejection_code='alternate_data_stream_forbidden'
            )

    for seg in segments:
        if seg.endswith('.') or seg.endswith(' '):
            return PathClassification(
                raw=raw, segments=segments, normalized_relative=None,
                path_class='invalid_trailing', platform_hints=(),
                safe_relative=False, rejection_code='reserved_path_segment_forbidden'
            )

    if not segments:
        return PathClassification(
            raw=raw, segments=(), normalized_relative=None,
            path_class='empty', platform_hints=(),
            safe_relative=False, rejection_code='empty_relative_path_forbidden'
        )

    norm_rel = '/'.join(segments)
    return PathClassification(
        raw=raw, segments=segments, normalized_relative=norm_rel,
        path_class='safe_relative', platform_hints=(),
        safe_relative=True, rejection_code=None
    )

def validate_relative_artifact_path(
    candidate: str | os.PathLike[str],
) -> tuple[str, ...]:
    cls = classify_artifact_relative_path(candidate)
    if not cls.safe_relative or cls.rejection_code:
        raise FilesystemSafetyError(cls.rejection_code or 'path_traversal_forbidden')
    return cls.segments

def reject_uri_like_root(root: str | os.PathLike[str]) -> None:
    raw = str(root)
    if '://' in raw:
        raise FilesystemSafetyError('absolute_output_path_forbidden', f"URI-like roots are forbidden: {raw}")
    if re.search(r'^[A-Za-z0-9+.-]{2,}:[/\\]', raw):
        raise FilesystemSafetyError('absolute_output_path_forbidden', f"URI-like roots are forbidden: {raw}")

def validate_authorized_root(
    root: str | os.PathLike[str],
) -> Path:
    if root is None or str(root) == '':
        raise FilesystemSafetyError('output_root_missing')
    reject_uri_like_root(root)
    raw = str(root)
    
    if os.name != 'nt':
        if re.match(r'^[A-Za-z]:', raw):
            raise FilesystemSafetyError('windows_drive_root_forbidden_on_posix', f"Windows drive root is forbidden on POSIX: {raw}")
    else:
        if re.match(r'^[A-Za-z]:(?![/\\])', raw):
            raise FilesystemSafetyError('drive_relative_output_path_forbidden', f"Drive-relative root is forbidden: {raw}")
            
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

def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        common = os.path.commonpath([str(parent), str(child)])
        if os.name == 'nt':
            return os.path.normcase(common) == os.path.normcase(str(parent))
        return common == str(parent)
    except ValueError:
        return False

def safe_destination(
    root: str | os.PathLike[str],
    candidate: str | os.PathLike[str],
    *,
    create_parent: bool = False,
    allow_destination_symlink: bool = False,
) -> SafeDestination:
    segments = validate_relative_artifact_path(candidate)
    root_resolved = validate_authorized_root(root)
    lexical = root_resolved.joinpath(*segments)
    
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
        try:
            target = lexical.resolve(strict=True)
            if not _is_relative_to(target, root_resolved):
                raise FilesystemSafetyError('output_path_outside_authorized_root')
        except OSError:
            if not allow_destination_symlink:
                raise FilesystemSafetyError('output_destination_symlink_forbidden')

    if create_parent:
        parent.mkdir(parents=True, exist_ok=True)
        
    return SafeDestination(root_resolved, lexical, Path(*segments))

def atomic_write_bytes(
    root: str | os.PathLike[str],
    candidate: str | os.PathLike[str],
    data: bytes,
    *,
    allow_overwrite: bool = True,
) -> Path:
    dest = safe_destination(root, candidate, create_parent=True)
    if dest.path.exists() and not allow_overwrite:
        raise FilesystemSafetyError('atomic_replace_failed')
    
    fd = None
    tmp_name = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            prefix=f'.{dest.path.name}.',
            suffix='.tmp',
            dir=str(dest.path.parent),
            text=False
        )
        tmp = Path(tmp_name)
        if not _is_relative_to(tmp.resolve(strict=True), dest.root):
            raise FilesystemSafetyError('unsafe_temporary_path')
            
        with os.fdopen(fd, 'wb') as f:
            fd = None
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
            
        os.replace(tmp, dest.path)
        return dest.path
    except FilesystemSafetyError:
        raise
    except PermissionError as exc:
        raise FilesystemSafetyError('filesystem_permission_denied') from exc
    except OSError as exc:
        raise FilesystemSafetyError('atomic_replace_failed') from exc
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if tmp_name:
            try:
                tmp = Path(tmp_name)
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass

def atomic_write_text(
    root: str | os.PathLike[str],
    candidate: str | os.PathLike[str],
    text: str,
    *,
    encoding: str = 'utf-8',
    allow_overwrite: bool = True,
) -> Path:
    return atomic_write_bytes(
        root,
        candidate,
        text.encode(encoding),
        allow_overwrite=allow_overwrite
    )

def atomic_create_text_exclusive(
    root: str | os.PathLike[str],
    candidate: str | os.PathLike[str],
    content: str,
    *,
    encoding: str = 'utf-8',
) -> SafeDestination:
    dest = safe_destination(root, candidate, create_parent=True)
    
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if os.name == 'nt':
        flags |= getattr(os, 'O_BINARY', 0)
        
    try:
        fd = os.open(str(dest.path), flags, 0o600)
    except FileExistsError as exc:
        raise FilesystemSafetyError('already_consumed_or_replayed', f"File already exists: {dest.path}") from exc
    except PermissionError as exc:
        raise FilesystemSafetyError('filesystem_permission_denied') from exc
    except OSError as exc:
        raise FilesystemSafetyError('atomic_replace_failed') from exc
        
    fd_open = None
    try:
        fd_open = os.fdopen(fd, 'w', encoding=encoding)
        fd_open.write(content)
        fd_open.flush()
        os.fsync(fd)
    except Exception as exc:
        if fd_open is not None:
            try:
                fd_open.close()
            except OSError:
                pass
            fd_open = None
        elif fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
            fd = None
            
        try:
            if dest.path.exists():
                os.remove(dest.path)
        except OSError as cleanup_exc:
            raise FilesystemSafetyError(
                'exclusive_create_cleanup_failed',
                f"Failed to remove incomplete file {dest.path}: {cleanup_exc}"
            ) from exc
        raise exc
    finally:
        if fd_open is not None:
            try:
                fd_open.close()
            except OSError:
                pass
        elif fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
                
    return dest
