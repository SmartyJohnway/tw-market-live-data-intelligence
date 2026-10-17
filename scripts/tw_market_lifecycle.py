"""Small, local-only lifecycle surface for the existing Workbench service."""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.operational_diagnostics import (
    EVENT_PATH_ENV,
    build_event,
    disk_free_bytes,
    emit_jsonl,
    new_trace_id,
    process_memory_bytes,
)
from scripts.m8r_filesystem_safety import (
    FilesystemSafetyError,
    atomic_create_text_exclusive,
    atomic_write_text,
    is_reparse_or_symlink,
    reject_reparse_components,
    validate_authorized_root,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
_INSTANCE = "TW_MARKET_LIFECYCLE_INSTANCE"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


_LOCAL_HTTP = urllib.request.build_opener(_NoRedirect)


def _kernel32():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    from ctypes import wintypes
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong)]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.TerminateProcess.restype = wintypes.BOOL
    kernel.GenerateConsoleCtrlEvent.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.GenerateConsoleCtrlEvent.restype = wintypes.BOOL
    return kernel


def _effective(cli_host: str | None, cli_port: int | None) -> tuple[str, int, dict[str, str]]:
    host = cli_host or os.environ.get("TW_MARKET_HOST") or DEFAULT_HOST
    port = cli_port if cli_port is not None else int(os.environ.get("TW_MARKET_PORT", DEFAULT_PORT))
    if host not in {"127.0.0.1", "localhost", "::1"} or not 1 <= port <= 65535:
        raise ValueError("INVALID_LOCAL_ENDPOINT")
    return host, port, {"host": "cli" if cli_host else "env" if os.environ.get("TW_MARKET_HOST") else "product_default",
                        "port": "cli" if cli_port is not None else "env" if os.environ.get("TW_MARKET_PORT") else "product_default"}


def _owner_path(port: int) -> Path:
    install = hashlib.sha256(str(ROOT.resolve()).encode("utf-8")).hexdigest()[:20]
    return Path(tempfile.gettempdir()) / "tw-market-runtime" / install / f"service-{port}.json"


def _event_path(port: int) -> Path:
    return _owner_path(port).parent / "operational-events.jsonl"


def _process_start_token(pid: int) -> str | None:
    if os.name == "nt":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        api = _kernel32()
        handle = api.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return None
        creation, exit_time, kernel_time, user = (ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong())
        try:
            if not api.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel_time), ctypes.byref(user)):
                return None
            return str(creation.value)
        finally:
            api.CloseHandle(handle)
    try:
        # Linux start ticks distinguish PID reuse; macOS fallback uses a live PID plus executable.
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        return stat.rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        try:
            os.kill(pid, 0)
            return "alive"
        except OSError:
            return None


def _process_executable(pid: int) -> str | None:
    try:
        if os.name == "nt":
            from ctypes import wintypes
            api = _kernel32()
            api.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
            api.QueryFullProcessImageNameW.restype = wintypes.BOOL
            handle = api.OpenProcess(0x1000, False, pid)
            if not handle:
                return None
            try:
                capacity = wintypes.DWORD(32768)
                buffer = ctypes.create_unicode_buffer(capacity.value)
                if not api.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(capacity)):
                    return None
                return str(Path(buffer.value).resolve())
            finally:
                api.CloseHandle(handle)
        return str(Path(f"/proc/{pid}/exe").resolve(strict=True))
    except (OSError, ValueError):
        if pid == os.getpid():
            return str(Path(sys.executable).resolve())
        return None


def _identity_matches(pid: object, token: object, executable: object) -> bool:
    if not isinstance(pid, int) or not isinstance(token, str) or not isinstance(executable, str):
        return False
    actual_token = _process_start_token(pid)
    actual_executable = _process_executable(pid)
    if actual_token is None or actual_executable is None:
        return False
    expected_executable = str(Path(executable).resolve())
    if os.name == "nt":
        return actual_token == token and actual_executable.casefold() == expected_executable.casefold()
    return actual_token == token and actual_executable == expected_executable


def _process_matches(record: dict) -> bool:
    return _identity_matches(record.get("pid"), record.get("process_start_token"), record.get("executable"))


def _starting_creator_matches(record: dict) -> bool:
    return record.get("state") == "starting" and _identity_matches(
        record.get("creator_pid"), record.get("creator_start_token"), record.get("creator_executable")
    )


def _owner_state(record: dict | None, error: str | None) -> str:
    if error:
        return "STALE_PROCESS_OWNERSHIP"
    if record is None:
        return "NOT_RUNNING"
    if record.get("state") == "starting":
        return "START_IN_PROGRESS" if _starting_creator_matches(record) else "STALE_PROCESS_OWNERSHIP"
    return "RUNNING" if _process_matches(record) else "STALE_PROCESS_OWNERSHIP"


def _port_open(host: str, port: int) -> bool:
    family = socket.AF_INET6 if host == "::1" else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def _health(host: str, port: int) -> tuple[bool, dict | None]:
    url_host = "[::1]" if host == "::1" else "127.0.0.1"
    try:
        with _LOCAL_HTTP.open(f"http://{url_host}:{port}/api/health", timeout=1.0) as response:
            body = json.loads(response.read(4096).decode("utf-8"))
            return response.status == 200, body if isinstance(body, dict) else None
    except (OSError, ValueError, urllib.error.URLError):
        return False, None


def _capability_projection(host: str, port: int) -> dict | None:
    url_host = "[::1]" if host == "::1" else "127.0.0.1"
    try:
        with _LOCAL_HTTP.open(f"http://{url_host}:{port}/api/unified/capabilities", timeout=2.0) as response:
            payload = json.loads(response.read(65537).decode("utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("capabilities"), list):
            return None
        capabilities = payload["capabilities"]
        return {"capability_count": len(capabilities), "projection": "READY"}
    except (OSError, ValueError, urllib.error.URLError):
        return None


def _read_owner(path: Path) -> tuple[dict | None, str | None]:
    try:
        reject_reparse_components(path.parent)
        if not path.parent.exists():
            return None, None
        if is_reparse_or_symlink(path) or not path.is_file():
            if not path.exists() and not is_reparse_or_symlink(path):
                return None, None
            return None, "STALE_PROCESS_OWNERSHIP"
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("root") != str(ROOT.resolve()):
            return None, "STALE_PROCESS_OWNERSHIP"
        return value, None
    except FileNotFoundError:
        return None, None
    except (OSError, ValueError):
        return None, "STALE_PROCESS_OWNERSHIP"


def _safe_unlink(path: Path) -> bool:
    try:
        reject_reparse_components(path.parent)
        if is_reparse_or_symlink(path) or not path.is_file():
            return False
        path.unlink()
        return True
    except OSError:
        return False


def _sm_status() -> dict:
    root = Path(os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT", ROOT / "data" / "security_master")).expanduser().resolve()
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "manage_security_master.py"), "status", "--root", str(root)], cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
    try: payload = json.loads(result.stdout)
    except ValueError: payload = {}
    state = payload.get("status")
    if result.returncode == 0 and state == "NOT_INITIALIZED":
        return {"status": "NOT_INITIALIZED", "root": str(root)}
    if result.returncode == 0 and state == "ACTIVE":
        release = payload.get("release")
        release_id = release.get("release_id") if isinstance(release, dict) else release if isinstance(release, str) else None
        return {"status": "ACTIVE", "root": str(root), "release_id": release_id}
    return {"status": "UNAVAILABLE", "root": str(root), "reason_code": payload.get("reason_code", "SECURITY_MASTER_STATE_UNREADABLE")}


def _safe_service_url_for_diagnostics(value: str) -> str:
    """Return only a validated loopback URL; never echo arbitrary env/CLI text."""
    try:
        from server.unified_mcp.local_service_client import validate_loopback_service_url
        return validate_loopback_service_url(value)
    except Exception:
        return "UNAVAILABLE"


def _base(host: str, port: int, sources: dict[str, str], service_url: str | None = None) -> dict:
    path = _owner_path(port)
    owner, owner_error = _read_owner(path)
    owner_state = _owner_state(owner, owner_error)
    opened = _port_open(host, port)
    alive, health = _health(host, port) if opened else (False, None)
    capability_projection = _capability_projection(host, port) if alive else None
    process = owner_state if owner_state != "NOT_RUNNING" else ("PORT_OCCUPIED_NOT_OWNED" if opened else "NOT_RUNNING")
    sm = _sm_status()
    preload_run = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_unified_workbench.py"), "--startup-check"], cwd=ROOT, capture_output=True, text=True, timeout=15, check=False)
    try: preload = json.loads(preload_run.stdout)
    except ValueError: preload = {}
    try:
        import importlib.metadata as metadata
        mcp_ok = metadata.version("mcp") == "1.29.0"
    except Exception: mcp_ok = False
    service_memory = None
    if owner_state == "RUNNING" and isinstance(owner, dict) and isinstance(owner.get("pid"), int):
        service_memory = process_memory_bytes(owner["pid"])
    resources = {
        "managed_service_process_memory_bytes": service_memory,
        "application_root_disk_free_bytes": disk_free_bytes(ROOT),
        "runtime_root_disk_free_bytes": disk_free_bytes(_owner_path(port).parent),
    }
    selected_service_url = service_url or os.environ.get("UNIFIED_MARKET_EVIDENCE_SERVICE_URL", f"http://{host}:{port}")
    return {
        "status": "SERVICE_ALIVE" if alive and sm["status"] == "ACTIVE" else "SERVICE_ALIVE / IDENTITY_NOT_INITIALIZED" if alive else process,
        "service": {"process": process, "alive": alive, "health": health, "host": host, "port": port,
                    "url": f"http://{host}:{port}"},
        "identity": sm,
        "readiness": {"preload": "READY" if preload_run.returncode == 0 else "BLOCKED",
                      "schema_catalog": "READY" if preload.get("canonical_schema_loaded") and preload.get("capability_catalog_loaded") else "BLOCKED",
                      "routes": capability_projection or ({"projection": "UNKNOWN_SERVICE_UNAVAILABLE"} if not alive else {"projection": "BLOCKED", "reason_code": "CAPABILITY_PROJECTION_UNAVAILABLE"})},
        "mcp": {"status": "SERVICE_UNREACHABLE" if not alive else "READY" if mcp_ok else "MCP_RUNTIME_MISMATCH", "service_url": _safe_service_url_for_diagnostics(selected_service_url),
                "sdk_compatible": mcp_ok, "local_service_reachable": alive},
        "paths": {"security_master_root": sm["root"],
                  "watchlist_root": str(Path(os.environ.get("TW_MARKET_WATCHLIST_ROOT", ROOT / "data" / "watchlists")).expanduser().resolve()),
                  "control_root": str(Path(os.environ.get("M8R_06_03_CONTROL_ROOT", ROOT / "artifacts" / "m8r_06_03_workbench")).expanduser().resolve()),
                  "ownership_file": str(path),
                  "operational_event_path": str(_event_path(port))},
        "configuration": {"host": host, "port": port, "sources": sources},
        "resources": resources,
        "checks": [],
    }


def _doctor(host: str, port: int, sources: dict[str, str], service_url: str | None = None) -> dict:
    report = _base(host, port, sources, service_url)
    checks = report["checks"]
    def check(name: str, status: str, reason: str | None = None, detail: dict | None = None) -> None:
        item = {"name": name, "status": status}
        if reason: item["reason_code"] = reason
        if detail: item["detail"] = detail
        checks.append(item)
    try:
        import importlib.metadata as metadata
        check("python", "PASS", detail={"version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"})
        check("dependencies", "PASS" if metadata.version("mcp") == "1.29.0" else "FAIL", None if metadata.version("mcp") == "1.29.0" else "MCP_RUNTIME_MISMATCH")
    except Exception:
        check("dependencies", "FAIL", "DEPENDENCY_CHECK_FAILED")
    environment = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_environment.py")], cwd=ROOT, capture_output=True, text=True, timeout=15, check=False)
    check("environment_verification", "PASS" if environment.returncode == 0 else "FAIL", None if environment.returncode == 0 else "ENVIRONMENT_VERIFICATION_FAILED")
    for label, value in (("security_master_root", report["paths"]["security_master_root"]), ("watchlist_root", report["paths"]["watchlist_root"]), ("control_root", report["paths"]["control_root"])):
        p = Path(value)
        check(label, "PASS" if p.exists() and os.access(p, os.R_OK) else "WARN", None if p.exists() else "PATH_NOT_PRESENT", {"exists": p.exists(), "readable": bool(p.exists() and os.access(p, os.R_OK))})
    event_path = Path(report["paths"]["operational_event_path"])
    event_parent_ready = event_path.parent.is_dir() and os.access(event_path.parent, os.W_OK)
    check(
        "operational_event_sink",
        "PASS" if event_parent_ready else "WARN",
        None if event_parent_ready else "EVENT_SINK_PARENT_NOT_READY",
        {"event_file_exists": event_path.is_file(), "parent_ready": event_parent_ready},
    )
    resources = report["resources"]
    disks_ready = all(
        isinstance(resources.get(key), int) and resources[key] >= 0
        for key in ("application_root_disk_free_bytes", "runtime_root_disk_free_bytes")
    )
    process_state = report["service"]["process"]
    memory_ready = process_state != "RUNNING" or (
        isinstance(resources.get("managed_service_process_memory_bytes"), int)
        and resources["managed_service_process_memory_bytes"] > 0
    )
    resource_ready = disks_ready and memory_ready
    check(
        "resource_snapshot",
        "PASS" if resource_ready else "WARN",
        None if resource_ready else "RESOURCE_SNAPSHOT_PARTIAL",
        dict(resources),
    )
    identity_status = report["identity"]["status"]
    identity_severity = "PASS" if identity_status == "ACTIVE" else "WARN" if identity_status == "NOT_INITIALIZED" else "FAIL"
    identity_reason = "SECURITY_MASTER_NOT_INITIALIZED" if identity_status == "NOT_INITIALIZED" else report["identity"].get("reason_code")
    check("security_master", identity_severity, identity_reason)
    process_state = report["service"]["process"]
    check("process_ownership", "WARN" if process_state in {"STALE_PROCESS_OWNERSHIP", "START_IN_PROGRESS", "PORT_OCCUPIED_NOT_OWNED"} else "PASS",
          process_state if process_state in {"STALE_PROCESS_OWNERSHIP", "START_IN_PROGRESS", "PORT_OCCUPIED_NOT_OWNED"} else None)
    startup = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_unified_workbench.py"), "--startup-check"], cwd=ROOT, capture_output=True, text=True, timeout=15, check=False)
    try: preload = json.loads(startup.stdout)
    except ValueError: preload = {}
    check("workbench_preload", "PASS" if startup.returncode == 0 else "FAIL", None if startup.returncode == 0 else "PRELOAD_FAILED", {"status": preload.get("status"), "security_master_status": preload.get("security_master_status")})
    check("local_service", "PASS" if report["service"]["alive"] else "WARN", None if report["service"]["alive"] else "SERVICE_UNREACHABLE")
    route_state = report["readiness"]["routes"]["projection"]
    check("route_capability_projection", "PASS" if route_state == "READY" else "WARN" if route_state == "UNKNOWN_SERVICE_UNAVAILABLE" else "FAIL", None if route_state == "READY" else report["readiness"]["routes"].get("reason_code", "SERVICE_UNREACHABLE"))
    try:
        from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
        snapshot = build_tool_contract_snapshot()
        names = [tool.name for tool in snapshot.tools]
        exact = len(names) == 6 and len(set(names)) == 6
        check("mcp_tool_contract", "PASS" if exact else "FAIL", None if exact else "MCP_TOOL_SURFACE_MISMATCH", {"tool_count": len(names)})
    except Exception:
        check("mcp_tool_contract", "FAIL", "MCP_TOOL_CONTRACT_UNAVAILABLE")
    effective_service_url = report["mcp"]["service_url"]
    mcp_run = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_unified_market_evidence_mcp.py"), "--service-url", effective_service_url, "--startup-check"], cwd=ROOT, capture_output=True, text=True, timeout=15, check=False)
    mcp_code = "READY" if mcp_run.returncode == 0 else "SERVICE_UNREACHABLE" if not report["service"]["alive"] else "MCP_STARTUP_CHECK_FAILED"
    check("mcp_startup_check", "PASS" if mcp_run.returncode == 0 else "WARN" if not report["service"]["alive"] else "FAIL", None if mcp_run.returncode == 0 else mcp_code)
    report["mcp"]["status"] = mcp_code
    report["mcp"]["local_service_reachable"] = report["service"]["alive"]
    report["status"] = _aggregate_doctor_status(checks)
    return report


def _aggregate_doctor_status(checks: list[dict]) -> str:
    states = {check.get("status") for check in checks}
    if "FAIL" in states:
        return "FAIL"
    if "WARN" in states:
        return "WARN"
    return "PASS"


def _exit_code(status: str) -> int:
    return 1 if status in {"FAIL", "START_FAILED", "START_TIMEOUT", "STOP_FAILED", "PORT_OCCUPIED_NOT_OWNED", "STALE_PROCESS_OWNERSHIP"} else 0


def _start(host: str, port: int) -> dict:
    owner_file = _owner_path(port)
    try:
        reject_reparse_components(owner_file.parent)
    except FilesystemSafetyError:
        return {"status": "START_FAILED", "reason_code": "RUNTIME_PATH_UNSAFE"}
    owner, err = _read_owner(owner_file)
    owner_state = _owner_state(owner, err)
    if owner_state == "RUNNING":
        return {"status": "ALREADY_RUNNING", "reason_code": "ALREADY_RUNNING", "service": {"host": host, "port": port}}
    if owner_state == "START_IN_PROGRESS":
        return {"status": "START_IN_PROGRESS", "reason_code": "START_IN_PROGRESS"}
    if owner_state == "STALE_PROCESS_OWNERSHIP":
        if not _safe_unlink(owner_file):
            return {"status": "STALE_PROCESS_OWNERSHIP", "reason_code": "STALE_PROCESS_OWNERSHIP"}
    if _port_open(host, port):
        return {"status": "PORT_OCCUPIED_NOT_OWNED", "reason_code": "PORT_OCCUPIED_NOT_OWNED"}
    try:
        validate_authorized_root(owner_file.parent)
        reject_reparse_components(owner_file.parent)
    except FilesystemSafetyError:
        return {"status": "START_FAILED", "reason_code": "RUNTIME_PATH_UNSAFE"}
    instance = str(uuid.uuid4())
    creator_pid = os.getpid()
    creator_start_token = _process_start_token(creator_pid)
    creator_executable = _process_executable(creator_pid)
    if not creator_start_token or not creator_executable:
        return {"status": "START_FAILED", "reason_code": "CREATOR_PROCESS_IDENTITY_UNAVAILABLE"}
    reservation = {"schema": 1, "state": "starting", "instance_id": instance, "root": str(ROOT.resolve()),
                   "host": host, "port": port, "creator_pid": creator_pid,
                   "creator_start_token": creator_start_token, "creator_executable": creator_executable,
                   "created_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        reject_reparse_components(owner_file.parent)
        atomic_create_text_exclusive(owner_file.parent, owner_file.name, json.dumps(reservation, sort_keys=True))
    except FilesystemSafetyError as exc:
        if exc.code == "already_consumed_or_replayed":
            return {"status": "START_IN_PROGRESS", "reason_code": "START_IN_PROGRESS"}
        return {"status": "START_FAILED", "reason_code": "RUNTIME_PATH_UNSAFE"}
    env = os.environ.copy(); env[_INSTANCE] = instance
    env[EVENT_PATH_ENV] = str(_event_path(port))
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    args = [sys.executable, "-m", "scripts.tw_market_lifecycle", "_serve", "--host", host, "--port", str(port)]
    try:
        process = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags, start_new_session=(os.name != "nt"))
    except OSError:
        _safe_unlink(owner_file)
        return {"status": "START_FAILED", "reason_code": "PROCESS_LAUNCH_FAILED"}
    token = None
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        token = _process_start_token(process.pid)
        if token: break
        if process.poll() is not None: break
        time.sleep(.05)
    if token is None:
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=2)
            except subprocess.TimeoutExpired: process.kill()
        _safe_unlink(owner_file)
        return {"status": "START_FAILED", "reason_code": "PROCESS_IDENTITY_UNAVAILABLE"}
    record = {"schema": 1, "root": str(ROOT.resolve()), "pid": process.pid, "process_start_token": token,
              "executable": str(Path(sys.executable).resolve()), "instance_id": instance,
              "host": host, "port": port, "started_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        reject_reparse_components(owner_file.parent)
        atomic_write_text(owner_file.parent, owner_file.name, json.dumps(record, sort_keys=True))
    except FilesystemSafetyError:
        _safe_unlink(owner_file)
        return {"status": "START_FAILED", "reason_code": "RUNTIME_PATH_UNSAFE"}
    while time.monotonic() < deadline:
        if process.poll() is not None:
            _safe_unlink(owner_file)
            return {"status": "START_FAILED", "reason_code": "SERVICE_EXITED_DURING_START"}
        if _health(host, port)[0]:
            return {"status": "STARTED", "service": {"host": host, "port": port, "url": f"http://{host}:{port}"}, "pid": process.pid}
        time.sleep(.1)
    cleanup = _cleanup_start_timeout(process, record, owner_file)
    return {"status": "START_TIMEOUT", "reason_code": "SERVICE_START_TIMEOUT", "pid": process.pid,
            "cleanup_status": cleanup.get("status", "CLEANUP_FAILED"),
            "child_terminated": cleanup.get("status") == "STOPPED"}


def _cleanup_start_timeout(process: subprocess.Popen, record: dict, owner_file: Path) -> dict:
    if process.poll() is not None:
        _safe_unlink(owner_file)
        return {"status": "STOPPED", "reason_code": "CHILD_ALREADY_EXITED"}
    cleanup = _terminate_owned(record, owner_file)
    if cleanup.get("status") == "STOPPED" or process.poll() is not None:
        _safe_unlink(owner_file)
        return {"status": "STOPPED", "reason_code": cleanup.get("reason_code", "CHILD_ALREADY_EXITED")}
    # Keep the fallback tied to the Popen handle and revalidate its identity;
    # never use the listening port or an unverified PID for timeout cleanup.
    if _process_matches(record):
        try:
            process.terminate()
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                return {"status": "STOP_FAILED", "reason_code": "OWNED_PROCESS_TERMINATION_FAILED"}
        if process.poll() is not None:
            _safe_unlink(owner_file)
            return {"status": "STOPPED", "reason_code": "OWNED_PROCESS_TERMINATED"}
    return cleanup


def _terminate_owned(record: dict, path: Path) -> dict:
    pid = record["pid"]
    if not _process_matches(record):
        return {"status": "STALE_PROCESS_OWNERSHIP", "reason_code": "STALE_PROCESS_OWNERSHIP", "metadata_cleaned": _safe_unlink(path)}
    if os.name == "nt":
        api = _kernel32()
        handle = api.OpenProcess(0x0001 | 0x00100000 | 0x1000, False, pid)
        if not handle:
            return {"status": "STALE_PROCESS_OWNERSHIP", "reason_code": "STALE_PROCESS_OWNERSHIP", "metadata_cleaned": _safe_unlink(path)}
        try:
            creation, exit_time, kernel_time, user = (ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong())
            if not api.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel_time), ctypes.byref(user)) or str(creation.value) != record["process_start_token"]:
                return {"status": "STALE_PROCESS_OWNERSHIP", "reason_code": "STALE_PROCESS_OWNERSHIP"}
            api.GenerateConsoleCtrlEvent(1, pid)  # CTRL_BREAK_EVENT to owned process group
            if api.WaitForSingleObject(handle, 3000) == 0x102:
                if not api.TerminateProcess(handle, 1) or api.WaitForSingleObject(handle, 3000) != 0:
                    return {"status": "STOP_FAILED", "reason_code": "OWNED_PROCESS_TERMINATION_FAILED"}
        finally: api.CloseHandle(handle)
    else:
        if hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"):
            fd = os.pidfd_open(pid)
            try:
                signal.pidfd_send_signal(fd, signal.SIGTERM)
                exited = bool(select.select([fd], [], [], 3)[0])
                if not exited:
                    signal.pidfd_send_signal(fd, signal.SIGKILL)
                    exited = bool(select.select([fd], [], [], 2)[0])
                if not exited:
                    return {"status": "STOP_FAILED", "reason_code": "OWNED_PROCESS_TERMINATION_FAILED"}
            except ProcessLookupError:
                pass
            finally:
                os.close(fd)
        else:
            try: os.kill(pid, signal.SIGTERM)
            except ProcessLookupError: pass
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and _process_start_token(pid) == record["process_start_token"]: time.sleep(.05)
            if _process_start_token(pid) == record["process_start_token"]:
                os.kill(pid, signal.SIGKILL)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline and _process_start_token(pid) == record["process_start_token"]: time.sleep(.05)
                if _process_start_token(pid) == record["process_start_token"]:
                    return {"status": "STOP_FAILED", "reason_code": "OWNED_PROCESS_TERMINATION_FAILED"}
    _safe_unlink(path)
    return {"status": "STOPPED", "reason_code": "STOPPED"}


def _stop(host: str, port: int) -> dict:
    path = _owner_path(port)
    owner, err = _read_owner(path)
    if err:
        return {"status": err, "reason_code": err}
    if owner and owner.get("state") == "starting":
        if _starting_creator_matches(owner):
            return {"status": "START_IN_PROGRESS", "reason_code": "START_IN_PROGRESS"}
        cleaned = _safe_unlink(path)
        return {"status": "STALE_PROCESS_OWNERSHIP_CLEANED" if cleaned else "STALE_PROCESS_OWNERSHIP",
                "reason_code": "STALE_PROCESS_OWNERSHIP", "metadata_cleaned": cleaned}
    if owner is None:
        return {"status": "PORT_OCCUPIED_NOT_OWNED", "reason_code": "PORT_OCCUPIED_NOT_OWNED"} if _port_open(host, port) else {"status": "NOT_RUNNING", "reason_code": "NOT_RUNNING"}
    if not _process_matches(owner):
        result = {"status": "STALE_PROCESS_OWNERSHIP", "reason_code": "STALE_PROCESS_OWNERSHIP", "metadata_cleaned": _safe_unlink(path)}
        if _port_open(host, port): result["port_status"] = "PORT_OCCUPIED_NOT_OWNED"
        return result
    return _terminate_owned(owner, path)


def _serve(host: str, port: int) -> int:
    if not os.environ.get(_INSTANCE): return 2
    from scripts.run_unified_workbench import main as workbench_main
    sys.argv = [str(ROOT / "scripts" / "run_unified_workbench.py"), "--host", host, "--port", str(port)]
    workbench_main()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TW-Market local runtime lifecycle")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "status", "stop", "doctor"):
        p = sub.add_parser(name); p.add_argument("--host"); p.add_argument("--port", type=int); p.add_argument("--service-url"); p.add_argument("--json", action="store_true")
    sub.add_parser("_serve").add_argument("--host", default=DEFAULT_HOST)
    sub.choices["_serve"].add_argument("--port", type=int, required=True)
    args = parser.parse_args(argv)
    if args.command == "_serve": return _serve(args.host, args.port)
    started = time.monotonic(); operation_id = str(uuid.uuid4()); trace_id = new_trace_id(); timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    port_for_event: int | None = None
    try:
        host, port, sources = _effective(args.host, args.port)
        port_for_event = port
        service_url = args.service_url or (f"http://{host}:{port}" if args.host is not None or args.port is not None else os.environ.get("UNIFIED_MARKET_EVIDENCE_SERVICE_URL"))
        if args.command == "start": result = _start(host, port)
        elif args.command == "stop": result = _stop(host, port)
        elif args.command == "status": result = _base(host, port, sources, service_url)
        else: result = _doctor(host, port, sources, service_url)
    except (ValueError, subprocess.TimeoutExpired) as exc:
        result = {"status": "FAIL", "reason_code": str(exc) if isinstance(exc, ValueError) else "CHECK_TIMEOUT"}
    duration_ms = round((time.monotonic() - started) * 1000, 2)
    result.update({"operation_id": operation_id, "trace_id": trace_id, "started_at": timestamp, "duration_ms": duration_ms})
    if args.command in {"start", "stop"} and port_for_event is not None:
        emit_jsonl(build_event(
            component="lifecycle", event_code=f"lifecycle.{args.command}.completed",
            status="ok" if _exit_code(result["status"]) == 0 else "error",
            trace_id=trace_id, reason_code=result.get("reason_code"),
            references={"lifecycle_operation_id": operation_id},
            metrics={"duration_ms": duration_ms},
        ), _event_path(port_for_event))
    if args.json: print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"{result['status']}" + (f" ({result.get('reason_code')})" if result.get("reason_code") else ""))
        if args.command in {"status", "doctor"}:
            print(f"Service: {result.get('service', {}).get('url')} | alive={result.get('service', {}).get('alive')}")
            print(f"Security Master: {result.get('identity', {}).get('status')} | {result.get('identity', {}).get('root')}")
            for item in result.get("checks", []): print(f"{item['status']} {item['name']}" + (f" [{item['reason_code']}]" if item.get("reason_code") else ""))
    return _exit_code(result["status"])


if __name__ == "__main__": raise SystemExit(main())
