"""Local governance guard for repository paths that must never receive generated writes."""
from __future__ import annotations
from pathlib import Path, PurePosixPath

FORBIDDEN_DIRS = {"credentials", "cookies", "tokens", "broker", "production", "prod", "current_market_state"}
FORBIDDEN_PREFIXES = {("frontend", "public"), ("research", "generated")}
FORBIDDEN_FILES = {".env"}


def _parts(path: str | Path) -> tuple[str, ...]:
    raw = str(path).replace("\\", "/")
    return tuple(p.lower() for p in PurePosixPath(raw).parts if p not in ("", "."))


def is_forbidden_repo_write_path(path: str | Path) -> str | None:
    parts = _parts(path)
    if not parts:
        return None
    if parts[-1] in FORBIDDEN_FILES or any(p in FORBIDDEN_FILES for p in parts):
        return "credential/env path is forbidden"
    for a, b in FORBIDDEN_PREFIXES:
        for i in range(len(parts) - 1):
            if parts[i : i + 2] == (a, b):
                return f"writes under {a}/{b}/ are forbidden"
    for p in parts:
        if p in FORBIDDEN_DIRS:
            return f"writes under {p}/ are forbidden"
    return None


def assert_not_forbidden_repo_write_path(path: str | Path) -> None:
    reason = is_forbidden_repo_write_path(path)
    if reason:
        raise ValueError(reason)


def frontend_public_changed_files(changed_files: list[str]) -> list[str]:
    """Return changed files under frontend/public without consulting git remotes."""
    return [path for path in changed_files if _parts(path)[:2] == ("frontend", "public")]


def has_frontend_public_changed_file(changed_files: list[str]) -> bool:
    """Pure check used by unit tests and check-only tooling."""
    return bool(frontend_public_changed_files(changed_files))
