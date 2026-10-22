"""Shared, offline installation identity and state-root resolver."""
from __future__ import annotations

import datetime as _dt
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from scripts.m8r_filesystem_safety import (
    atomic_write_text,
    reject_reparse_components,
    reject_uri_like_root,
    validate_authorized_root,
)


APP_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
_ROOT_ENV = {
    "security_master": "TW_MARKET_SECURITY_MASTER_ROOT",
    "watchlists": "TW_MARKET_WATCHLIST_ROOT",
    "governed": "M8R_06_03_CONTROL_ROOT",
}


class InstallationError(ValueError):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        super().__init__(message or code)


def _absolute(value: str | os.PathLike[str]) -> Path:
    raw = os.fspath(value)
    if not raw:
        raise InstallationError("INVALID_PATH")
    try:
        reject_uri_like_root(raw)
    except ValueError as exc:
        raise InstallationError("INVALID_PATH") from exc
    if raw.startswith(("\\\\?\\", "\\\\.\\", "//?/", "//./", "\\\\", "//")) or re.match(r"^[A-Za-z]:(?![\\/])", raw):
        raise InstallationError("UNSAFE_PATH_NAMESPACE")
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    # Validate the lexical chain before abspath can erase a `..` component.
    try:
        lexical = reject_reparse_components(p)
    except ValueError as exc:
        raise InstallationError(getattr(exc, "code", "PATH_REPARSE_COMPONENT")) from exc
    p = Path(os.path.normpath(os.fspath(lexical)))
    try:
        reject_reparse_components(p)
    except ValueError as exc:
        raise InstallationError(getattr(exc, "code", "PATH_REPARSE_COMPONENT")) from exc
    return p


def _reject_reparse(path: Path) -> None:
    cur = Path(path.anchor) if path.anchor else Path.cwd()
    for part in path.parts[1:] if path.anchor else path.parts:
        cur = cur / part
        try:
            if cur.is_symlink():
                raise InstallationError("PATH_REPARSE_COMPONENT")
            st = cur.lstat()
            if getattr(st, "st_file_attributes", 0) & 0x400:
                raise InstallationError("PATH_REPARSE_COMPONENT")
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise InstallationError("PATH_UNAVAILABLE") from exc


def _same_or_below(child: Path, parent: Path) -> bool:
    try:
        return os.path.commonpath([os.path.normcase(str(child)), os.path.normcase(str(parent))]) == os.path.normcase(str(parent))
    except ValueError:
        return False


def _outside_app(path: Path, app_root: Path) -> None:
    if _same_or_below(path, app_root):
        raise InstallationError("PATH_INSIDE_APP_ROOT")


def _json(path: Path, *, kind: str) -> dict[str, Any]:
    try:
        try:
            reject_reparse_components(path)
        except ValueError as exc:
            raise InstallationError(getattr(exc, "code", "PATH_REPARSE_COMPONENT")) from exc
        if path.is_symlink() or not path.is_file():
            raise InstallationError("INVALID_JSON_FILE")
        with path.open("rb") as fh:
            raw = fh.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise InstallationError("JSON_RESOURCE_LIMIT")
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise InstallationError("DUPLICATE_JSON_KEY")
                result[key] = value
            return result
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(InstallationError("NONFINITE_JSON")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstallationError(f"MALFORMED_{kind.upper()}") from exc
    if not isinstance(data, dict):
        raise InstallationError(f"MALFORMED_{kind.upper()}")
    return data


def _version(data: Mapping[str, Any], kind: str) -> None:
    value = data.get("schema_version" if kind == "settings" else "installation_schema_version")
    if isinstance(value, bool) or not isinstance(value, int) or value != 1:
        raise InstallationError(f"UNSUPPORTED_{kind.upper()}_VERSION")


def _validate_endpoint(host: Any, port: Any) -> tuple[str, int]:
    if not isinstance(host, str) or host not in {"127.0.0.1", "localhost", "::1"}:
        raise InstallationError("INVALID_LOCAL_ENDPOINT")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise InstallationError("INVALID_PORT")
    return host, port


def _settings(path: Path) -> tuple[str, int, dict[str, str]]:
    try:
        reject_reparse_components(path)
    except ValueError as exc:
        raise InstallationError(getattr(exc, "code", "PATH_REPARSE_COMPONENT")) from exc
    if path.is_symlink():
        raise InstallationError("PATH_REPARSE_COMPONENT")
    if not path.exists():
        return DEFAULT_HOST, DEFAULT_PORT, {"host": "product_default", "port": "product_default"}
    data = _json(path, kind="settings")
    _version(data, "settings")
    for key in data:
        if key.lower() in {"home", "state_root", "root", "security_master_root", "watchlist_root", "governed_root", "cache_root", "logs_root"} or key.lower().endswith("_root"):
            raise InstallationError("SETTINGS_ROOT_AUTHORITY_FORBIDDEN")
    service = data.get("service")
    if not isinstance(service, dict):
        raise InstallationError("MALFORMED_SETTINGS")
    if "host" not in service or "port" not in service:
        raise InstallationError("MALFORMED_SETTINGS")
    host, port = _validate_endpoint(service["host"], service["port"])
    return host, port, {"host": "settings", "port": "settings"}


def _metadata(path: Path) -> dict[str, Any] | None:
    try:
        reject_reparse_components(path)
    except ValueError as exc:
        raise InstallationError(getattr(exc, "code", "PATH_REPARSE_COMPONENT")) from exc
    if path.is_symlink():
        raise InstallationError("PATH_REPARSE_COMPONENT")
    if not path.exists():
        return None
    data = _json(path, kind="metadata")
    _version(data, "metadata")
    ident = data.get("installation_id")
    try:
        if not isinstance(ident, str) or uuid.UUID(ident).version != 4 or str(uuid.UUID(ident)) != ident:
            raise ValueError
    except (ValueError, AttributeError, TypeError) as exc:
        raise InstallationError("MALFORMED_INSTALLATION_METADATA") from exc
    if not isinstance(data.get("state_root"), str) or not Path(data["state_root"]).is_absolute() or not isinstance(data.get("created_at"), str) or not data.get("created_at"):
        raise InstallationError("MALFORMED_INSTALLATION_METADATA")
    try:
        _dt.datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise InstallationError("MALFORMED_INSTALLATION_METADATA") from exc
    return data


def _atomic_json(path: Path, data: Mapping[str, Any], *, exclusive: bool = False) -> None:
    try:
        validate_authorized_root(path.parent)
    except ValueError as exc:
        raise InstallationError(getattr(exc, "code", "PATH_UNAVAILABLE")) from exc
    lock = path.with_name(f".{path.name}.init-lock")
    lock_fd = None
    if exclusive:
        try:
            lock_fd = os.open(os.fspath(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            if path.exists():
                return
            raise InstallationError("CONCURRENT_INITIALIZATION") from exc
    content = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    try:
        if exclusive and path.exists():
            return
        from server.resource_boundaries import require_disk_capacity, ResourceDiskAdmissionError
        try:
            require_disk_capacity(path.parent, len(content.encode("utf-8")))
            atomic_write_text(path.parent, path.name, content, allow_overwrite=not exclusive)
        except ResourceDiskAdmissionError as exc:
            raise InstallationError(exc.code) from exc
        except ValueError as exc:
            raise InstallationError(getattr(exc, "code", "ATOMIC_PUBLICATION_FAILED")) from exc
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
            try: os.unlink(lock)
            except FileNotFoundError: pass


@dataclass(frozen=True)
class Installation:
    app_root: Path
    home: Path
    state_root: Path
    installation_metadata_path: Path
    settings_path: Path
    security_master_root: Path
    watchlist_root: Path
    governed_root: Path
    cache_root: Path
    logs_root: Path
    runtime_root: Path | None
    temp_root: Path | None
    installation_id: str | None
    installation_status: str
    effective_service_host: str
    effective_service_port: int
    operational_event_path: Path
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    @property
    def configuration_sources(self) -> Mapping[str, Any]:
        return self.diagnostics.get("settings_origins", MappingProxyType({}))

    def as_dict(self) -> dict[str, Any]:
        return {k: (str(v) if isinstance(v, Path) else dict(v) if isinstance(v, Mapping) else v) for k, v in self.__dict__.items()}

    def require_initialized(self) -> "Installation":
        if self.installation_status != "READY" or not self.installation_id:
            raise InstallationError("INSTALLATION_NOT_INITIALIZED")
        return self


def _resolve_home(home: str | os.PathLike[str] | None, env: Mapping[str, str]) -> tuple[Path, str]:
    raw = home if home is not None else env.get("TW_MARKET_HOME")
    source = "cli" if home is not None else "env" if env.get("TW_MARKET_HOME") else "platform_default"
    if raw is None:
        local = env.get("LOCALAPPDATA")
        if not local:
            raise InstallationError("HOME_UNAVAILABLE")
        raw = Path(local) / "TW-Market"
    return _absolute(raw), source


def resolve_installation(*, home=None, state_root=None, host=None, port=None, app_root=APP_ROOT, environ=None) -> Installation:
    env = dict(os.environ if environ is None else environ)
    app = _absolute(app_root)
    selected_home, home_source = _resolve_home(home, env)
    _outside_app(selected_home, app)
    meta_path = selected_home / "meta" / "installation.json"
    settings_path = selected_home / "config" / "settings.json"
    _outside_app(meta_path, app)
    _outside_app(settings_path, app)
    meta = _metadata(meta_path)
    persisted_state = _absolute(meta["state_root"]) if meta else None
    requested_state_raw = state_root if state_root is not None else env.get("TW_MARKET_STATE_ROOT")
    requested_state = _absolute(requested_state_raw) if requested_state_raw else None
    if persisted_state and requested_state and os.path.normcase(str(persisted_state)) != os.path.normcase(str(requested_state)):
        raise InstallationError("STATE_ROOT_CONFLICT")
    selected_state = persisted_state or requested_state or _absolute(selected_home / "state")
    _outside_app(selected_state, app)
    settings_host, settings_port, origins = _settings(settings_path)
    selected_host = host if host is not None else env.get("TW_MARKET_HOST", settings_host)
    try:
        selected_port = port if port is not None else (int(env["TW_MARKET_PORT"]) if "TW_MARKET_PORT" in env else settings_port)
    except (TypeError, ValueError) as exc:
        raise InstallationError("INVALID_PORT") from exc
    selected_host, selected_port = _validate_endpoint(selected_host, selected_port)
    origins = dict(origins)
    origins["host"] = "cli" if host is not None else "env" if "TW_MARKET_HOST" in env else origins["host"]
    origins["port"] = "cli" if port is not None else "env" if "TW_MARKET_PORT" in env else origins["port"]
    required_layout = (selected_home / "config", selected_home / "meta", selected_home / "cache", selected_home / "logs", selected_state / "security-master", selected_state / "watchlists", selected_state / "governed")
    initialized = bool(meta) and settings_path.exists() and all(path.is_dir() and not path.is_symlink() for path in required_layout)
    ident = meta.get("installation_id") if meta else None
    runtime = temp = None
    if ident:
        temp = _absolute(Path(tempfile.gettempdir()) / "TW-Market" / ident / "temp")
        runtime = _absolute(Path(tempfile.gettempdir()) / "TW-Market" / ident / "runtime")
    diagnostics: dict[str, Any] = {"home_source": home_source, "state_root_source": "metadata" if persisted_state else "cli_or_env_or_default", "settings_origins": origins}
    roots = {}
    for role, canonical in (("security_master", selected_state / "security-master"), ("watchlists", selected_state / "watchlists"), ("governed", selected_state / "governed"), ("cache", selected_home / "cache"), ("logs", selected_home / "logs")):
        override = env.get(_ROOT_ENV.get(role, ""))
        if override:
            roots[role] = _absolute(override)
            if os.path.normcase(str(roots[role])) != os.path.normcase(str(_absolute(canonical))):
                diagnostics.setdefault("NONCANONICAL_ROOT_OVERRIDE", {})[role] = _ROOT_ENV[role]
        else:
            roots[role] = _absolute(canonical)
            _outside_app(roots[role], app)
    event_path = env.get("TW_MARKET_OPERATIONAL_EVENT_PATH")
    operational_event_path = _absolute(event_path) if event_path else _absolute(selected_home / "logs" / "operational-events.jsonl")
    if event_path and not _same_or_below(operational_event_path, selected_home / "logs"):
        diagnostics.setdefault("NONCANONICAL_ROOT_OVERRIDE", {})["operational_events"] = "TW_MARKET_OPERATIONAL_EVENT_PATH"
    status = "READY" if initialized else "INSTALLATION_NOT_INITIALIZED" if not meta else "INSTALLATION_INCOMPLETE"
    return Installation(app, selected_home, selected_state, meta_path, settings_path, roots["security_master"], roots["watchlists"], roots["governed"], roots["cache"], roots["logs"], runtime, temp, ident, status, selected_host, selected_port, operational_event_path, MappingProxyType(diagnostics))


@contextmanager
def _home_init_lock(home: Path, app: Path):
    _outside_app(home, app)
    try:
        validate_authorized_root(home)
    except ValueError as exc:
        raise InstallationError(getattr(exc, "code", "PATH_UNAVAILABLE")) from exc
    lock = home / ".installation-init.lock"
    try:
        fd = os.open(os.fspath(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise InstallationError("INIT_IN_PROGRESS") from exc
    try:
        os.close(fd)
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def _initialize_locked(inst: Installation, *, home=None, state_root=None, host=None, port=None, app_root=APP_ROOT, environ=None) -> Installation:
    fresh = not inst.installation_metadata_path.exists()
    if fresh:
        # Fresh layout creation is not authority to adopt an existing business
        # store. Inspect only the three fixed canonical roles, never discover
        # arbitrary state or follow the explicit legacy override roots.
        for name in ("security-master", "watchlists", "governed"):
            path = inst.state_root / name
            try:
                reject_reparse_components(path)
            except ValueError as exc:
                raise InstallationError(getattr(exc, "code", "PATH_REPARSE_COMPONENT")) from exc
            if path.exists() and (not path.is_dir() or next(path.iterdir(), None) is not None):
                raise InstallationError("EXISTING_STATE_REQUIRES_EXPLICIT_TRANSFER")
    canonical_roots = (inst.home, inst.home / "meta", inst.home / "config", inst.home / "cache", inst.home / "logs", inst.state_root, inst.state_root / "security-master", inst.state_root / "watchlists", inst.state_root / "governed")
    for path in canonical_roots:
        try:
            validate_authorized_root(path)
        except ValueError as exc:
            raise InstallationError(getattr(exc, "code", "PATH_UNAVAILABLE")) from exc
    for path in canonical_roots:
        _verify_writable(path)
    meta = _metadata(inst.installation_metadata_path)
    ident = meta["installation_id"] if meta else str(uuid.uuid4())
    metadata = meta or {"installation_schema_version": 1, "installation_id": ident, "state_root": str(inst.state_root), "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat()}
    if not inst.settings_path.exists():
        # CLI/ENV are transient higher-precedence selection layers, not an
        # implicit settings-write command. Fresh persisted preferences are
        # product defaults; explicit user edits remain durable on rerun.
        _atomic_json(inst.settings_path, {"schema_version": 1, "service": {"host": DEFAULT_HOST, "port": DEFAULT_PORT}}, exclusive=True)
    # Publish identity last, after settings and all canonical directories exist.
    if fresh:
        _atomic_json(inst.installation_metadata_path, metadata, exclusive=True)
    return resolve_installation(home=inst.home, state_root=inst.state_root, host=host, port=port, app_root=app_root, environ=environ)


def _verify_writable(root: Path) -> None:
    """Explicit init-only bounded write/fsync/delete probe; never a doctor action."""
    name = f".tw-market-init-probe-{uuid.uuid4().hex}"
    probe = root / name
    created = False
    try:
        atomic_write_text(root, name, "TW-Market init writable-root probe\n", allow_overwrite=False)
        created = True
    except (OSError, ValueError) as exc:
        raise InstallationError("INSTALLATION_ROOT_NOT_WRITABLE") from exc
    finally:
        if created:
            try:
                reject_reparse_components(probe)
                probe.unlink()
            except (OSError, ValueError) as exc:
                raise InstallationError("INSTALLATION_ROOT_PROBE_CLEANUP_FAILED") from exc


def initialize_installation(*, home=None, state_root=None, host=None, port=None, app_root=APP_ROOT, environ=None) -> Installation:
    env = dict(os.environ if environ is None else environ)
    app = _absolute(app_root)
    selected_home, _ = _resolve_home(home, env)
    with _home_init_lock(selected_home, app):
        inst = resolve_installation(home=home, state_root=state_root, host=host, port=port, app_root=app_root, environ=environ)
        return _initialize_locked(inst, home=home, state_root=state_root, host=host, port=port, app_root=app_root, environ=environ)


def effective_root(role: str, *, explicit=None, installation: Installation | None = None, require_initialized=False) -> Path:
    if role not in {"security_master", "watchlists", "governed", "cache", "logs"}:
        raise InstallationError("UNKNOWN_STATE_ROLE")
    inst = installation or resolve_installation()
    if require_initialized:
        inst.require_initialized()
    if explicit is not None:
        selected = _absolute(explicit)
        return selected
    return getattr(inst, {"watchlists": "watchlist_root", "security_master": "security_master_root"}.get(role, f"{role}_root"))


def enumerate_installation_state(installation: Installation | None = None) -> tuple[dict[str, Any], ...]:
    inst = installation or resolve_installation()
    return tuple({"role": role, "path": str(path) if path is not None else None, "backup": backup, "portable": portable, "l2_binding_required": True, "classifier_bypass": False} for role, path, backup, portable in (("installation_metadata", inst.installation_metadata_path, "PORTABLE_FACTS_ONLY", False), ("settings", inst.settings_path, "CORE", True), ("security_master", inst.security_master_root, "CORE", True), ("watchlists", inst.watchlist_root, "CORE", True), ("governed", inst.governed_root, "FULL_GOVERNED", True), ("cache", inst.cache_root, "EXCLUDED_CORE", False), ("logs", inst.logs_root, "EXCLUDED_CORE_DEFAULT", False), ("runtime", inst.runtime_root, "EXCLUDED", False), ("temp", inst.temp_root, "EXCLUDED", False)))
