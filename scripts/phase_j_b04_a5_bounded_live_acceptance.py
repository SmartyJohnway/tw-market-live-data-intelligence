"""Acceptance-only J-B04-A5 runner. No implicit or repeatable live access."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STARTING_MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
ENDPOINT = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
TARGET_ID = "TWSE:2330"
EXECUTOR_ID = "phase_h_h2_twse_exright_pre_executor"
SOURCE_ID = "H2-TWSE-EXRIGHT-PRE-OPENAPI"
CONTRACT = "TWT48U_ALL"
MAX_BYTES = 4 * 1024 * 1024
TIMEOUT = 15
PREFLIGHT_JSON = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_BOUNDED_LIVE_PREFLIGHT_2026-10-09.json"
EXECUTION_ENVIRONMENTS = {"installation_bound", "cloud_clean_source_acceptance"}
PREDECLARED_SOURCE_TARGET = {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}
PREDECLARED_SOURCE_TARGET_SHA256 = "d80f5c697d333f043df922a099a0f472780051c1d2abf79866954026b63aaa40"
STAGE_WITNESS_POLICY = "prefer normalizable TWSE:2330; otherwise lexicographically smallest (Code, Date, canonical raw-row SHA-256) among normalizable rows"
ACCEPTANCE_RUNS = ROOT / "docs/governance/phase_j/acceptance_runs"
FORBIDDEN_RAW_KEYS = {"raw_bytes", "rows", "rows_in_memory", "raw_payload", "raw_body", "source_rows", "full_payload"}
LEASE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXECUTION_LEASE_MIN_BYTES = 32


class A5Error(RuntimeError):
    pass


@dataclass
class EphemeralLiveCapture:
    """Source bytes and decoded rows retained only in process memory."""
    raw_bytes: bytes
    rows: list[dict[str, Any]] | None
    retrieved_at: str
    telemetry: dict[str, Any]
    root_type: str | None
    parse_error: str | None = None

    def release(self) -> None:
        self.raw_bytes = b""
        self.rows = None


@dataclass(frozen=True)
class PredeclaredSourceTargetAuthority:
    canonical_json: str
    sha256: str

    def descriptor(self) -> dict[str, str]:
        raw = self.canonical_json.encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != self.sha256 or self.sha256 != PREDECLARED_SOURCE_TARGET_SHA256:
            raise A5Error("predeclared_source_target_authority_corrupt")
        value = json.loads(self.canonical_json)
        if value != {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}:
            raise A5Error("predeclared_source_target_authority_corrupt")
        return value

    def bind(self, candidate: Mapping[str, Any]) -> dict[str, str]:
        expected = self.descriptor()
        selected = {key: candidate.get(key) for key in expected}
        if selected != expected:
            raise A5Error("predeclared_source_target_mutated")
        return expected


class SingleUseAuthority:
    """A chat authorization must be recorded against the exact current commit."""
    def __init__(self, record: Mapping[str, Any], *, head: str, tree: str | None = None,
                 execution_environment: str = "cloud_clean_source_acceptance"):
        if record.get("gate") != "J-B04-A5":
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
        if record.get("authorized_head_sha") != head:
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_STALE_HEAD")
        if tree is not None and record.get("authorized_tree_sha") != tree:
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_STALE_TREE")
        if record.get("execution_environment_class") != execution_environment:
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
        expected_keys = {"gate", "authorized_head_sha", "authorized_tree_sha", "execution_environment_class",
                         "execution_instance_lease_sha256", "statement", "statement_sha256", "consumed"}
        if set(record) != expected_keys:
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
        statement = record.get("statement")
        statement_hash = record.get("statement_sha256")
        lease_hash = record.get("execution_instance_lease_sha256")
        if (not isinstance(statement, str) or not isinstance(statement_hash, str)
                or not isinstance(lease_hash, str) or not LEASE_SHA256_RE.fullmatch(lease_hash)
                or not LEASE_SHA256_RE.fullmatch(statement_hash)):
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
        expected = expected_owner_statement(head, lease_hash)
        if statement != expected or statement_hash != hashlib.sha256(statement.encode("utf-8")).hexdigest():
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
        if record.get("consumed") is not False:
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
        self.consumed = False

    def consume(self) -> None:
        if self.consumed:
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_ALREADY_CONSUMED")
        self.consumed = True


def current_git_state() -> tuple[str, str, str]:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    return git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"), git("rev-parse", "origin/main")


def _canonical_target_bytes(target: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(target), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def predeclared_source_target() -> tuple[dict[str, str], str]:
    authority = PredeclaredSourceTargetAuthority(
        canonical_json=_canonical_target_bytes(PREDECLARED_SOURCE_TARGET).decode("utf-8"),
        sha256=PREDECLARED_SOURCE_TARGET_SHA256)
    target = authority.descriptor()
    return target, authority.sha256


def resolve_predeclared_target() -> dict[str, Any]:
    """Resolve through the process-lifetime production Mode A identity service."""
    from scripts.m8r_06_01c2_mode_a_security_master_loader import (
        ModeASecurityMasterUnavailable,
        get_production_mode_a_security_master,
    )

    root_selected_by_env = bool(os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT"))
    try:
        runtime = get_production_mode_a_security_master()
    except ModeASecurityMasterUnavailable as exc:
        code = getattr(exc, "reason_code", "")
        disposition = ("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_NOT_INITIALIZED"
                      if code == "NOT_INITIALIZED"
                      else "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID")
        raise A5Error(disposition) from exc
    except Exception as exc:
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID") from exc

    service = getattr(runtime, "identity_service", None)
    if service is None or not callable(getattr(service, "resolve", None)):
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID")
    try:
        resolution = service.resolve(TARGET_ID, market_hint="TWSE")
    except Exception as exc:
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID") from exc
    selected = getattr(resolution, "selected", None) or {}
    identity = selected.get("identity") or {}
    classification = selected.get("classification") or {}
    eligibility = selected.get("execution_eligibility") or {}
    if (getattr(resolution, "status", None), list(getattr(resolution, "reason_codes", []))) != (
            "resolved", ["exact_listing_id"]):
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_TARGET_IDENTITY_SCOPE_INVALID")
    if (selected.get("canonical_target_id"), identity.get("security_code"), classification.get("market"),
            classification.get("instrument_family"), classification.get("instrument_type"), eligibility.get("status")) != (
            TARGET_ID, "2330", "TWSE", "company_share", "common_share", "allowed"):
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_TARGET_IDENTITY_SCOPE_INVALID")

    pointer = runtime.pointer
    release_id = pointer.get("release_id")
    manifest_hash = pointer.get("release_manifest_sha256")
    index_hash = pointer.get("release_index_sha256")
    if not all(isinstance(value, str) and value for value in (release_id, manifest_hash, index_hash)):
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID")
    return {
        "canonical_target_id": TARGET_ID,
        "market": "TWSE",
        "security_code": "2330",
        "isin": identity.get("isin"),
        "instrument_family": "company_share",
        "instrument_type": "common_share",
        "execution_eligibility": "allowed",
        "resolution_reason": "exact_listing_id",
        "security_master_release_id": release_id,
        "security_master_manifest_hash": manifest_hash,
        "security_master_release_index_sha256": index_hash,
        "canonical_identity_authority": "installation_local_security_master_release",
        "selected_root_class": "environment_selected_installation_local" if root_selected_by_env else "canonical_installation_local_default",
        "environment_root_selected": root_selected_by_env,
    }


def resolve_execution_target(execution_environment: str) -> dict[str, Any]:
    """Apply explicit environment semantics without weakening production identity checks."""
    if execution_environment not in EXECUTION_ENVIRONMENTS:
        raise A5Error("execution_environment_class_required_or_invalid")
    try:
        identity = resolve_predeclared_target()
        return {
            "preflight_status": "J_B04_A5_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW",
            "security_master_status": "ACTIVE",
            "identity_assurance_level": "production_identity_verified",
            "production_identity_verified": True,
            "A6_identity_reverification_required": False,
            "target_binding": {key: identity[key] for key in ("canonical_target_id", "market", "security_code", "isin",
                "instrument_family", "instrument_type", "execution_eligibility", "resolution_reason")},
            "security_master_release_id": identity["security_master_release_id"],
            "security_master_manifest_hash": identity["security_master_manifest_hash"],
            "security_master_release_index_sha256": identity["security_master_release_index_sha256"],
            "selected_root_class": identity["selected_root_class"],
        }
    except A5Error as exc:
        if str(exc) == "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_NOT_INITIALIZED":
            if execution_environment == "installation_bound":
                return {"preflight_status": str(exc), "security_master_status": "NOT_INITIALIZED",
                    "identity_assurance_level": None, "production_identity_verified": False,
                    "A6_identity_reverification_required": True, "target_binding": None,
                    "security_master_release_id": None, "security_master_manifest_hash": None,
                    "security_master_release_index_sha256": None, "selected_root_class": None}
            target, digest = predeclared_source_target()
            return {"preflight_status": "J_B04_A5_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW",
                "security_master_status": "NOT_INITIALIZED",
                "identity_assurance_level": "acceptance_only_predeclared_source_target",
                "production_identity_verified": False, "A6_identity_reverification_required": True,
                "target_binding": target, "predeclared_source_target": target,
                "predeclared_source_target_sha256": digest,
                "source_target_binding_scope": "A5 exact TWT48U Code-field binding only",
                "security_master_release_id": None, "security_master_manifest_hash": None,
                "security_master_release_index_sha256": None,
                "selected_root_class": "environment_selected_installation_local" if os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT") else "canonical_installation_local_default"}
        return {"preflight_status": str(exc), "security_master_status": "INVALID" if "CANONICAL_SECURITY_MASTER_INVALID" in str(exc) else "TARGET_SCOPE_INVALID",
            "identity_assurance_level": None, "production_identity_verified": False,
            "A6_identity_reverification_required": True, "target_binding": None,
            "security_master_release_id": None, "security_master_manifest_hash": None,
            "security_master_release_index_sha256": None, "selected_root_class": None}


def select_offline_stage_witness(rows: object, *, observed_at: str, citation_prefix: str = "a5-offline-stage") -> dict[str, Any] | None:
    """Select a deterministic normalizable live row without claiming product identity."""
    from server.services.phase_h_corporate_action_adapters import H2NormalizationError, normalize_twse_twt48u_all
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return None
    candidates = []
    for row in rows:
        code = row.get("Code")
        date = row.get("Date")
        if not isinstance(code, str) or not code or not code.isascii() or not code.isdigit():
            continue
        if not isinstance(date, str) or not date:
            continue
        digest = hashlib.sha256(_canonical_target_bytes(row)).hexdigest()
        candidates.append((code, date, digest, row))
    for code, date, digest, row in sorted(candidates, key=lambda item: (item[0] != "2330", item[0], item[1], item[2])):
        target = {"canonical_target_id": f"TWSE:{code}", "market": "TWSE", "security_code": code}
        try:
            normalized = normalize_twse_twt48u_all(rows, target, observed_at=observed_at,
                citation_id=f"{citation_prefix}-{digest[:16]}")
        except (H2NormalizationError, ValueError, TypeError):
            continue
        if normalized.get("status") != "available" or len(normalized.get("events", [])) != 1:
            continue
        return {"source_target": target, "source_row_hash": digest, "source_date": date,
            "normalized_evidence": normalized, "product_scope_identity_verified": False,
            "source_stage_witness_only": True,
            "selection_rule": STAGE_WITNESS_POLICY}
    return None


def acceptance_h3_fixture(target: Mapping[str, str]) -> dict[str, Any]:
    """A deterministic date-window fixture, explicitly not live H3 evidence."""
    from server.services.phase_h_recent_performance import build_recent_performance_evidence
    schema = json.loads((ROOT / "schemas/recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8"))
    start, end = "2026-10-05", "2026-10-06"
    def row(day: str, close: int) -> dict[str, Any]:
        return {**target, "trade_date": day, "close": close, "volume": 1000,
                "source_family": "TEST_ACCEPTANCE_ONLY_NOT_LIVE_H3",
                "source_contract_id": "J-B04-A5 deterministic window fixture",
                "retrieved_at": "2026-10-09T00:00:00Z", "citation_ids": [f"a5-fixture-{day}"]}
    evidence = build_recent_performance_evidence(target=target, observations=[row(start, 100)],
        governed_end_observation=row(end, 101), requested_observations=1, baseline_lookbacks=[1],
        current_volume_basis="completed_session", schema=schema)
    return evidence


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def expected_owner_statement(head: str, lease_sha256: str) -> str:
    return (
        f"AUTHORIZE J-B04-A5 LIVE ON HEAD {head}\n"
        f"WITH EXECUTION LEASE {lease_sha256}:\nexactly 1 GET to\n{ENDPOINT},\n"
        "retry 0,\nno redirects,\ntarget TWSE:2330,\nno H3 live calls,\n"
        "no TWT49U/TPEx/browser fallback,\nno raw payload persistence,\n"
        "no H2 activation,\nno J-B04 closure,\nno Phase J start."
    )


def _external_lease_path(path: Path) -> Path:
    try:
        resolved = path.expanduser().resolve(strict=False)
        if resolved.is_relative_to(ROOT.resolve()):
            raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID")
        return resolved
    except A5Error:
        raise
    except Exception as exc:
        raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID") from exc


def prepare_execution_lease(path: Path, execution_environment: str) -> dict[str, Any]:
    """Create a random external secret once; disclose only its public SHA-256."""
    if execution_environment not in EXECUTION_ENVIRONMENTS:
        raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID")
    target = _external_lease_path(Path(path))
    if not target.parent.is_dir():
        raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID")
    secret = secrets.token_bytes(EXECUTION_LEASE_MIN_BYTES)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = None
    permission_hardening = False
    try:
        fd = os.open(target, flags, 0o600)
        try:
            os.fchmod(fd, 0o600)
            permission_hardening = True
        except (AttributeError, OSError):
            permission_hardening = False
        with os.fdopen(fd, "wb", closefd=True) as stream:
            fd = None
            stream.write(secret)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID") from exc
    except Exception as exc:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID") from exc
    finally:
        if fd is not None:
            os.close(fd)
    lease_hash = hashlib.sha256(secret).hexdigest()
    del secret
    return {"gate": "J-B04-A5", "execution_environment_class": execution_environment,
        "execution_instance_lease_sha256": lease_hash, "lease_file_created": True,
        "permission_hardening_applied": permission_hardening, "secret_disclosed": False,
        "market_GET": 0, "market_HEAD": 0, "market_POST": 0}


def load_execution_lease(path: Path, expected_sha256: str) -> bytes:
    """Load a pre-existing external secret. Live mode never creates/replaces it."""
    if not isinstance(expected_sha256, str) or not LEASE_SHA256_RE.fullmatch(expected_sha256):
        raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
    target = _external_lease_path(Path(path))
    if not target.exists():
        raise A5Error("J_B04_A5_EXECUTION_LEASE_MISSING")
    try:
        mode = target.stat().st_mode
        if not stat.S_ISREG(mode):
            raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID")
        secret = target.read_bytes()
    except A5Error:
        raise
    except FileNotFoundError as exc:
        raise A5Error("J_B04_A5_EXECUTION_LEASE_MISSING") from exc
    except Exception as exc:
        raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID") from exc
    if len(secret) < EXECUTION_LEASE_MIN_BYTES:
        raise A5Error("J_B04_A5_EXECUTION_LEASE_INVALID")
    if hashlib.sha256(secret).hexdigest() != expected_sha256:
        raise A5Error("J_B04_A5_EXECUTION_LEASE_HASH_MISMATCH")
    return secret


def _safe_capture_response(response: Mapping[str, Any]) -> EphemeralLiveCapture:
    raw = response.get("raw_bytes")
    if not isinstance(raw, bytes):
        raise A5Error("response_bytes_invalid")
    content_type = str(response.get("content_type", ""))
    effective_url = response.get("effective_url")
    retrieved_at = response.get("retrieved_at") if isinstance(response.get("retrieved_at"), str) else _utc_now()
    parsed: Any = None
    parse_error = None
    root_type = None
    try:
        if len(raw) > MAX_BYTES:
            parse_error = "response_ceiling_exceeded"
        elif effective_url != ENDPOINT:
            parse_error = "effective_url_mismatch_or_redirect"
        elif isinstance(response.get("status"), int) and 300 <= response["status"] < 400:
            parse_error = "redirect_response_rejected"
        elif response.get("status") != 200:
            parse_error = "http_status_not_200"
        elif "json" not in content_type.casefold():
            parse_error = "content_type_not_json"
        else:
            parsed = json.loads(raw.decode("utf-8", errors="strict"))
            root_type = "array" if isinstance(parsed, list) else type(parsed).__name__
            if not isinstance(parsed, list):
                parse_error = "json_root_not_array"
    except (UnicodeDecodeError, json.JSONDecodeError):
        parse_error = "json_invalid"
    telemetry = {"http_status": response.get("status"), "content_type": content_type,
        "effective_url": effective_url,
        "response_byte_count": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
        "json_root_type": root_type, "root_row_count": len(parsed) if isinstance(parsed, list) else None,
        "retrieved_at": retrieved_at}
    return EphemeralLiveCapture(raw, parsed if isinstance(parsed, list) else None, retrieved_at,
                                telemetry, root_type, parse_error)


def response_telemetry(response: Mapping[str, Any]) -> dict[str, Any]:
    """Return only persistable transport metadata; decoded rows never escape."""
    return _safe_capture_response(response).telemetry


@contextmanager
def count_actual_dispatches(counter: dict[str, int]):
    """Count the production urllib opener dispatch without editing production code."""
    import urllib.request
    original = urllib.request.OpenerDirector.open
    def counted(opener, *args, **kwargs):
        if counter["http_dispatch_attempts"] >= 1:
            raise A5Error("http_dispatch_limit_exceeded")
        counter["http_dispatch_attempts"] += 1
        return original(opener, *args, **kwargs)
    urllib.request.OpenerDirector.open = counted
    try:
        yield
    finally:
        urllib.request.OpenerDirector.open = original


def _strict_auth_json(path: Path) -> dict[str, Any]:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
            result[key] = value
        return result
    try:
        if path.resolve(strict=True).is_relative_to(ROOT.resolve()):
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except A5Error:
        raise
    except Exception as exc:
        raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID") from exc
    if not isinstance(value, dict):
        raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
    return value


def _canonical_runtime_state() -> dict[str, Any]:
    def read(path: str) -> dict[str, Any]:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    descriptor = read("config/phase_h_h2_dormant_source_descriptors.json")
    source = next(item for item in descriptor["sources"] if item["source_id"] == SOURCE_ID)
    routes = read("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    route = next(item for item in routes["routes"] if item["capability_id"] == "corporate_action_context")
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    return {"H2_source_runtime_executable": source["runtime_executable"],
        "corporate_action_context_routing": route["routing_status"],
        "selected_executor_id": route["selected_executor_id"],
        "H2_runtime": "INACTIVE", "J-B04": "BLOCKING", "Phase J": "NOT_STARTED",
        "MCP": len(build_tool_contract_snapshot().tools)}


def validate_live_runtime_invariants(preflight: Mapping[str, Any]) -> None:
    if preflight.get("preflight_status") != "J_B04_A5_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW":
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED")
    state = _canonical_runtime_state()
    if state != {"H2_source_runtime_executable": False, "corporate_action_context_routing": "plan_only",
        "selected_executor_id": None, "H2_runtime": "INACTIVE", "J-B04": "BLOCKING",
        "Phase J": "NOT_STARTED", "MCP": 6}:
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED")
    if preflight.get("security_master_status") not in {"NOT_INITIALIZED", "ACTIVE"}:
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED")
    if preflight.get("security_master_status") == "NOT_INITIALIZED" and (
        preflight.get("identity_assurance_level") != "acceptance_only_predeclared_source_target"
        or preflight.get("production_identity_verified") is not False
        or preflight.get("A6_identity_reverification_required") is not True
    ):
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED")
    try:
        from scripts.validate_phase_j_b04_a5_bounded_live_acceptance import validate_repository
        validate_repository()
    except Exception as exc:
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED") from exc


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def _write_sanitized_json(run_root: Path, relative_path: str, value: Mapping[str, Any], *, overwrite: bool = True) -> Path:
    if _contains_forbidden_raw_key(value):
        raise A5Error("J_B04_A5_RAW_FIELD_PERSISTENCE_BLOCKED")
    from scripts.m8r_filesystem_safety import atomic_write_bytes
    content = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    return atomic_write_bytes(str(run_root), relative_path, content, allow_overwrite=overwrite)


def _verify_sanitized_package(run_root: Path, *, raw_bytes: bytes | None = None,
                              _summary_finalized: bool = False) -> tuple[dict[str, Any], bool]:
    files = sorted(path for path in run_root.rglob("*") if path.is_file())
    manifest_path = run_root / "artifact_manifest.json"
    entries = []
    for path in files:
        if path == manifest_path:
            continue
        if path.suffix.lower() != ".json" or any(token in path.name.casefold() for token in ("raw", "payload", "body")):
            raise A5Error("J_B04_A5_RAW_BODY_FILE_PERSISTENCE_BLOCKED")
        data = path.read_bytes()
        if raw_bytes and (data == raw_bytes or (len(raw_bytes) >= 16 and raw_bytes in data)):
            raise A5Error("J_B04_A5_RAW_BODY_PERSISTENCE_DETECTED")
        if path.suffix.lower() == ".json":
            try:
                parsed = json.loads(data.decode("utf-8"))
            except Exception as exc:
                raise A5Error("J_B04_A5_SANITIZED_PACKAGE_INVALID") from exc
            if _contains_forbidden_raw_key(parsed):
                raise A5Error("J_B04_A5_RAW_FIELD_PERSISTENCE_BLOCKED")
        entries.append({"relative_path": path.relative_to(run_root).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(), "byte_size": len(data),
            "artifact_role": path.stem})
    manifest = {"schema_version": "j_b04_a5_acceptance_artifact_manifest.v1",
        "artifacts": entries, "manifest_excludes_self": True}
    _write_sanitized_json(run_root, "artifact_manifest.json", manifest)
    listed = {item["relative_path"] for item in entries}
    actual = {path.relative_to(run_root).as_posix() for path in run_root.rglob("*") if path.is_file()}
    if actual != listed | {"artifact_manifest.json"}:
        raise A5Error("J_B04_A5_SANITIZED_PACKAGE_UNLISTED_ARTIFACT")
    for item in entries:
        path = run_root / item["relative_path"]
        data = path.read_bytes()
        if len(data) != item["byte_size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise A5Error("J_B04_A5_ARTIFACT_MANIFEST_INTEGRITY_FAILED")
    manifest_bytes = manifest_path.read_bytes()
    manifest_value = json.loads(manifest_bytes.decode("utf-8"))
    if _contains_forbidden_raw_key(manifest_value) or (raw_bytes and (manifest_bytes == raw_bytes
            or (len(raw_bytes) >= 16 and raw_bytes in manifest_bytes))):
        raise A5Error("J_B04_A5_SANITIZED_PACKAGE_INVALID")
    summary_path = run_root / "acceptance_summary.json"
    if summary_path.exists() and not _summary_finalized:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["raw_body_absence_verified"] = True
        _write_sanitized_json(run_root, "acceptance_summary.json", summary)
        return _verify_sanitized_package(run_root, raw_bytes=raw_bytes, _summary_finalized=True)
    return manifest, True


def _persist_live_result(run_root: Path, *, preflight: Mapping[str, Any], counts: Mapping[str, int],
                         attempt: dict[str, Any], capture: EphemeralLiveCapture | None,
                         h2_run: Mapping[str, Any] | None, stage_witness: Mapping[str, Any] | None,
                         h4_artifacts: list[dict[str, Any]], primary_summary: Mapping[str, Any],
                         disposition: str) -> tuple[dict[str, Any], bool]:
    attempt["actual_http_dispatch_attempts"] = counts["http_dispatch_attempts"]
    attempt["completed_at"] = _utc_now()
    _write_sanitized_json(run_root, "transport_attempt.json", attempt)
    if capture is not None:
        telemetry = dict(capture.telemetry)
        if isinstance(telemetry.get("http_status"), int) and 300 <= telemetry["http_status"] < 400:
            redirect_result = "rejected_status_3xx"
        elif telemetry.get("effective_url") != ENDPOINT:
            redirect_result = "rejected_effective_url_mismatch"
        else:
            redirect_result = "none"
        telemetry.update({"logical_get_attempts": counts["logical_get_attempts"],
            "http_dispatch_attempts": counts["http_dispatch_attempts"], "retry_count": 0,
            "redirect_result": redirect_result})
        _write_sanitized_json(run_root, "source_telemetry.json", telemetry)
    if h2_run is not None:
        _write_sanitized_json(run_root, "primary_target_summary.json", primary_summary)
        _write_sanitized_json(run_root, "h3_acceptance_fixture_summary.json", {
            "artifact_path": h2_run["h3_fixture_path"],
            "label": h2_run["h3_fixture_label"],
            "requested_window": h2_run["h3_fixture_window"],
            "live_h3_calls": 0, "historical_source_completeness_authority": False})
    if stage_witness is not None:
        evidence = stage_witness["normalized_evidence"]
        _write_sanitized_json(run_root, "stage_witness_summary.json", {
            "canonical_target_id": stage_witness["source_target"]["canonical_target_id"],
            "security_code": stage_witness["source_target"]["security_code"],
            "source_row_hash": stage_witness["source_row_hash"], "selection_rule": STAGE_WITNESS_POLICY,
            "product_scope_identity_verified": False, "source_stage_witness_only": True,
            "source_evidence_stage": evidence["events"][0]["source_evidence_stage"],
            "event_lifecycle": evidence["events"][0]["event_lifecycle"]})
        _write_sanitized_json(run_root, "stage_witness_normalized_evidence.json", evidence)
    h4 = None
    if h4_artifacts:
        h4 = json.loads((run_root / h4_artifacts[0]["relative_path"]).read_text(encoding="utf-8"))
        _write_sanitized_json(run_root, "h4_acceptance_replay.json", {
            "artifacts": h4_artifacts, "state": h4["state"],
            "ordinary_return_interpretation": h4["ordinary_return_interpretation"]})
    summary = {"disposition": disposition,
        "source_transport_accepted": bool(capture and capture.telemetry.get("http_status") == 200
            and capture.telemetry.get("effective_url") == ENDPOINT and capture.parse_error is None),
        "source_contract_accepted": bool(capture and capture.parse_error is None),
        "primary_target": primary_summary, "stage_witness_available": stage_witness is not None,
        "stage_witness_selection_rule": STAGE_WITNESS_POLICY, "h4_artifact_count": len(h4_artifacts),
        "h4_state": h4["state"] if h4 else None,
        "ordinary_return_interpretation": h4["ordinary_return_interpretation"] if h4 else None,
        "identity_assurance_level": preflight["identity_assurance_level"],
        "production_identity_verified": preflight["production_identity_verified"],
        "A6_identity_reverification_required": preflight["A6_identity_reverification_required"],
        "raw_payload_persistence": "NONE", "transport_attempted": attempt["transport_attempted"],
        "canonical_h2_runtime": "INACTIVE", "selected_executor_id": None,
        "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6}
    _write_sanitized_json(run_root, "acceptance_summary.json", summary)
    return _verify_sanitized_package(run_root, raw_bytes=capture.raw_bytes if capture is not None else None)


def _is_transient_transport_exception(exc: Exception) -> bool:
    if isinstance(exc, (OSError, TimeoutError, ConnectionError)):
        return True
    try:
        from server.services.phase_h_h2_twse_exright_executor import H2SourceAttemptError
        return isinstance(exc, H2SourceAttemptError) and str(exc) == "source_failed:transport_unavailable"
    except Exception:
        return False


def _safe_h2_error_code(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if value.startswith("source_failed"):
        return "source_failed"
    if value.startswith("binding_failed"):
        return "binding_failed"
    return None


def run_live_acceptance(owner_authorization_path: Path, execution_environment: str,
                        execution_lease_file: Path, *,
                        get_once=None, git_state_provider=None, dirty_check=None,
                        preflight_fn=None, runtime_invariant_fn=None, now_fn=None,
                        acceptance_runs_root: Path | None = None) -> dict[str, Any]:
    """Execute the explicitly authorized one-shot path; tests inject only fake transport."""
    if execution_environment not in EXECUTION_ENVIRONMENTS:
        raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_INVALID")
    record = _strict_auth_json(owner_authorization_path)
    state_provider = current_git_state if git_state_provider is None else git_state_provider
    head, tree, main = state_provider()
    authority = SingleUseAuthority(record, head=head, tree=tree, execution_environment=execution_environment)
    if main != STARTING_MAIN:
        raise A5Error("J_B04_A5_LIVE_MAIN_DRIFT_REQUIRES_REVIEW")
    is_dirty = ((subprocess.run(["git", "diff", "--quiet"], cwd=ROOT, check=False).returncode != 0
                or subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, check=False).returncode != 0)
                if dirty_check is None else dirty_check())
    if is_dirty:
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED")
    preflight = (run_p0_preflight if preflight_fn is None else preflight_fn)(execution_environment)
    (validate_live_runtime_invariants if runtime_invariant_fn is None else runtime_invariant_fn)(preflight)
    statement_hash = record["statement_sha256"]
    runs_root = ACCEPTANCE_RUNS if acceptance_runs_root is None else Path(acceptance_runs_root)
    run_root = runs_root / f"j-b04-a5-authority-{statement_hash[:16]}"
    if run_root.exists():
        raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_ALREADY_CONSUMED")
    # Construct/check the output path before consuming; utility validates root containment.
    from scripts.m8r_filesystem_safety import FilesystemSafetyError, atomic_create_text_exclusive, safe_destination
    try:
        safe_destination(str(runs_root), str(Path(run_root.name) / "owner_authorization_consumed.json"), create_parent=False)
    except FilesystemSafetyError as exc:
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED") from exc
    # A missing lease after workspace loss cannot be regenerated by live mode.
    lease_secret = load_execution_lease(Path(execution_lease_file), record["execution_instance_lease_sha256"])
    del lease_secret
    # Recheck the lease after all preflight work and immediately before consuming it.
    final_head, final_tree, final_main = state_provider()
    if final_head != record["authorized_head_sha"]:
        raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_STALE_HEAD")
    if final_tree != record["authorized_tree_sha"]:
        raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_STALE_TREE")
    if final_main != STARTING_MAIN:
        raise A5Error("J_B04_A5_LIVE_MAIN_DRIFT_REQUIRES_REVIEW")
    final_dirty = ((subprocess.run(["git", "diff", "--quiet"], cwd=ROOT, check=False).returncode != 0
                   or subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, check=False).returncode != 0)
                   if dirty_check is None else dirty_check())
    if final_dirty:
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED")
    consumed_at = (now_fn or _utc_now)()
    receipt = {"gate": "J-B04-A5", "authorized_head_sha": head, "authorized_tree_sha": tree,
        "statement_sha256": statement_hash, "execution_environment_class": execution_environment,
        "execution_instance_lease_sha256": record["execution_instance_lease_sha256"],
        "consumed_at_utc": consumed_at, "consumption_state": "CONSUMED_BEFORE_TRANSPORT"}
    try:
        atomic_create_text_exclusive(str(runs_root), str(Path(run_root.name) / "owner_authorization_consumed.json"),
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
    except FilesystemSafetyError as exc:
        if getattr(exc, "reason_code", "") == "already_consumed_or_replayed":
            raise A5Error("J_B04_A5_LIVE_AUTHORIZATION_ALREADY_CONSUMED") from exc
        raise A5Error("J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED") from exc
    authority.consume()
    counts = {"logical_get_attempts": 0, "http_dispatch_attempts": 0}
    attempt = {"transport_attempted": False, "logical_get_attempts": 0,
        "actual_http_dispatch_attempts": 0, "retry_count": 0, "redirect_follow_count": 0,
        "started_at": None, "completed_at": None, "outcome": "in_progress", "failure_class": None}
    response = None
    capture = None
    h2_run = None
    disposition = None
    h4_artifacts: list[dict[str, Any]] = []
    stage_witness = None
    primary_summary: dict[str, Any] = {"outcome": "unavailable"}
    exact_rows: list[dict[str, Any]] | None = None
    noncanonical_code_match = False
    try:
        attempt["started_at"] = (now_fn or _utc_now)()
        _write_sanitized_json(run_root, "owner_authorization.json", {
            "authorization_source": "external_owner_authorization_file", "authorized_head_sha": head,
            "authorized_tree_sha": tree, "statement_sha256": statement_hash,
            "execution_environment_class": execution_environment,
            "execution_instance_lease_sha256": record["execution_instance_lease_sha256"],
            "consumed_at_utc": consumed_at})
        _write_sanitized_json(run_root, "transport_attempt.json", attempt, overwrite=False)
        transport = get_once
        if transport is None:
            from server.services.phase_h_h2_twse_exright_executor import official_get_once
            transport = official_get_once
        counts["logical_get_attempts"] = 1
        attempt["transport_attempted"] = True
        attempt["logical_get_attempts"] = 1
        _write_sanitized_json(run_root, "transport_attempt.json", attempt)
        try:
            with count_actual_dispatches(counts):
                response = transport(timeout_seconds=TIMEOUT)
        except Exception as transport_exc:
            if not _is_transient_transport_exception(transport_exc):
                raise
            attempt["failure_class"] = "transport_failure"
            h2_run = execute_primary_target(None, PREDECLARED_SOURCE_TARGET, run_root, transport_error=True)
            h2_result = h2_run["operation_result"]
            h2_primary = next((item for item in h2_result.get("evidence_artifacts", [])
                if item.get("artifact_role") == "primary_evidence"
                and item.get("evidence_contract") == "corporate_action_context_evidence.v1"), None)
            h2_evidence = json.loads((run_root / h2_primary["relative_path"]).read_text(encoding="utf-8")) if h2_primary else None
            primary_summary = {"outcome": "not_observed_transport_failure",
                "h2_evidence_status": h2_evidence.get("status") if h2_evidence else None,
                "operation_result_status": h2_result.get("status"),
                "operation_error_code": _safe_h2_error_code(h2_result.get("error_code")),
                "historical_absence_asserted": False}
            h4_artifacts = derive_a5_h4_replay(h2_run, output_root=run_root)
            disposition = "J_B04_A5_INCONCLUSIVE_TRANSIENT_SOURCE_FAILURE_NO_ACTIVATION"
            attempt["outcome"] = disposition
        if response is not None:
            attempt["actual_http_dispatch_attempts"] = counts["http_dispatch_attempts"]
            attempt["outcome"] = "response_received"
            capture = _safe_capture_response(response)
            # Production H2 receives this exact response object and performs its normal decode/binding path.
            h2_run = execute_primary_target(response, PREDECLARED_SOURCE_TARGET, run_root)
            h2_result = h2_run["operation_result"]
            h2_artifacts = h2_result.get("evidence_artifacts", [])
            h2_primary = next((item for item in h2_artifacts if item.get("artifact_role") == "primary_evidence"
                               and item.get("evidence_contract") == "corporate_action_context_evidence.v1"), None)
            h2_evidence = None
            if h2_primary is not None:
                h2_evidence = json.loads((run_root / h2_primary["relative_path"]).read_text(encoding="utf-8"))
            exact_rows = [row for row in (capture.rows or []) if row.get("Code") == "2330"]
            noncanonical_code_match = any(str(row.get("Code")) == "2330" and row.get("Code") != "2330"
                for row in (capture.rows or []))
            if noncanonical_code_match:
                primary_summary = {"outcome": "noncanonical_exact_code_type",
                    "semantic": "source_contract_binding_rejected; Code must be the exact string 2330",
                    "historical_absence_asserted": False, "h2_evidence_status": h2_evidence.get("status") if h2_evidence else None}
            elif len(exact_rows) == 0:
                primary_summary = {"outcome": "zero_exact_code_matches", "semantic": "no_evidence_in_retrieved_current_source_slice",
                    "historical_absence_asserted": False, "h2_evidence_status": h2_evidence.get("status") if h2_evidence else None}
            elif len(exact_rows) == 1:
                primary_summary = {"outcome": "one_exact_code_match", "semantic": "normalized_by_production_h2_path",
                    "h2_evidence_status": h2_evidence.get("status") if h2_evidence else None}
            else:
                primary_summary = {"outcome": "multiple_exact_code_matches", "semantic": "binding_failed_no_row_selected",
                    "h2_evidence_status": h2_evidence.get("status") if h2_evidence else None}
            primary_summary["operation_result_status"] = h2_result.get("status")
            primary_summary["operation_error_code"] = _safe_h2_error_code(h2_result.get("error_code"))
            if capture.rows is not None:
                stage_witness = select_offline_stage_witness(capture.rows, observed_at=capture.retrieved_at)
            h4_artifacts = derive_a5_h4_replay(h2_run, output_root=run_root)
            h4_evidence = (json.loads((run_root / h4_artifacts[0]["relative_path"]).read_text(encoding="utf-8"))
                           if h4_artifacts else None)
            if noncanonical_code_match:
                disposition = "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED"
            elif h2_primary is not None and (len(h4_artifacts) != 1 or h4_evidence is None
                    or h4_evidence.get("state") != "coverage_incomplete"
                    or h4_evidence.get("ordinary_return_interpretation") != "blocked"):
                disposition = "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED"
            elif capture.parse_error == "http_status_not_200":
                disposition = "J_B04_A5_INCONCLUSIVE_TRANSIENT_SOURCE_FAILURE_NO_ACTIVATION"
            elif capture.parse_error is not None:
                disposition = "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED"
            elif stage_witness is None:
                disposition = "J_B04_A5_INCONCLUSIVE_LIVE_STAGE_SAMPLE_UNAVAILABLE"
            else:
                disposition = "J_B04_A5_BOUNDED_LIVE_SOURCE_ACCEPTANCE_PASS_AWAITING_INDEPENDENT_REVIEW"
            attempt["outcome"] = disposition
    except Exception as exc:
        # Never serialize exception text; HTTP/adapter errors may contain source content.
        transport_failure = _is_transient_transport_exception(exc)
        attempt["failure_class"] = "transport_failure" if transport_failure else "runner_or_source_failure"
        attempt["outcome"] = "failure_after_authority_consumption"
        disposition = ("J_B04_A5_INCONCLUSIVE_TRANSIENT_SOURCE_FAILURE_NO_ACTIVATION"
            if transport_failure
            else "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED")
    finally:
        try:
            manifest, raw_absence = _persist_live_result(run_root, preflight=preflight, counts=counts,
                attempt=attempt, capture=capture, h2_run=h2_run, stage_witness=stage_witness,
                h4_artifacts=h4_artifacts, primary_summary=primary_summary,
                disposition=disposition or "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED")
        except Exception:
            disposition = "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED"
            attempt["failure_class"] = "evidence_finalization_failure"
            attempt["outcome"] = disposition
            attempt["completed_at"] = _utc_now()
            try:
                _write_sanitized_json(run_root, "transport_attempt.json", attempt)
                _write_sanitized_json(run_root, "acceptance_summary.json", {
                    "disposition": disposition, "transport_attempted": attempt["transport_attempted"],
                    "identity_assurance_level": preflight["identity_assurance_level"],
                    "production_identity_verified": preflight["production_identity_verified"],
                    "A6_identity_reverification_required": preflight["A6_identity_reverification_required"],
                    "raw_payload_persistence": "NONE", "canonical_h2_runtime": "INACTIVE",
                    "selected_executor_id": None, "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6})
                manifest, raw_absence = _verify_sanitized_package(run_root, raw_bytes=capture.raw_bytes if capture is not None else None)
            except Exception:
                manifest, raw_absence = {"artifacts": []}, False
        finally:
            response = None
            if capture is not None:
                capture.release()
                capture = None
            if exact_rows is not None:
                exact_rows.clear()
    return {"disposition": disposition, "run_directory": run_root.name,
        "logical_get_attempts": counts["logical_get_attempts"], "http_dispatch_attempts": counts["http_dispatch_attempts"],
        "raw_body_absence_verified": raw_absence, "artifact_count": len(manifest["artifacts"]),
        "market_GET": counts["logical_get_attempts"], "market_HEAD": 0, "market_POST": 0}


def execute_primary_target(response: Mapping[str, Any] | None, target: Mapping[str, str], output_root: Path,
                           *, transport_error: bool = False) -> dict[str, Any]:
    """Replay the captured in-memory response through the unchanged H2 executor."""
    from scripts.m8r_05b_03.canonical import canonical_json
    from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
    from scripts.m8r_filesystem_safety import atomic_write_bytes
    from server.services.phase_h_h2_twse_exright_executor import execute_h2_twse_exright_pre
    target_authority = PredeclaredSourceTargetAuthority(
        canonical_json=_canonical_target_bytes(PREDECLARED_SOURCE_TARGET).decode("utf-8"),
        sha256=PREDECLARED_SOURCE_TARGET_SHA256)
    target = target_authority.bind(target)
    h3 = acceptance_h3_fixture(target)
    h3_path = "evidence/phase_h/h3/a5-acceptance-only-h3-fixture.json"
    h3_bytes = (canonical_json(h3) + "\n").encode("utf-8")
    atomic_write_bytes(str(output_root), h3_path, h3_bytes)
    h3_ref = {"relative_path": h3_path, "sha256": hashlib.sha256(h3_bytes).hexdigest(),
        "byte_size": len(h3_bytes), "schema_version": "recent_performance_evidence.v1",
        "evidence_contract": "recent_performance_evidence.v1", "artifact_role": "primary_evidence"}
    h3_op = {"operation_id": "a5-acceptance-only-h3-fixture", "capability_id": "recent_performance",
        "executor_id": "phase_h_h3_twse_recent_performance_executor", "market": "TWSE",
        "canonical_target_ids": [target["canonical_target_id"]], "dependency_operation_ids": [],
        "operation_status": "executable_pending_approval", "executor_invocation_eligible": True}
    dependency = {"operation_id": h3_op["operation_id"], "operation": h3_op, "result": {
        "operation_id": h3_op["operation_id"], "status": "succeeded", "capability_id": "recent_performance",
        "executor_id": h3_op["executor_id"], "evidence_contract": "recent_performance_evidence.v1",
        "evidence_artifacts": [h3_ref]}}
    request = {"schema_version": "unified_market_evidence_execution_request.v1",
        "operation_id": "a5-twse-2330-corporate-action", "execution_request_id": "a5-acceptance-only-request",
        "execution_request_hash": hashlib.sha256(b"J-B04-A5 acceptance-only request").hexdigest(),
        "executor_id": EXECUTOR_ID, "capability_id": "corporate_action_context", "market": "TWSE",
        "approved_security_identifiers": [target["canonical_target_id"]], "timeout_seconds": TIMEOUT}
    def fetch_response(**kwargs):
        if transport_error:
            from server.services.phase_h_h2_twse_exright_executor import H2SourceAttemptError
            raise H2SourceAttemptError("source_failed:transport_unavailable")
        if response is None:
            raise RuntimeError("a captured transport response is required")
        return dict(response)
    result = execute_h2_twse_exright_pre(request, DispatchRuntimeContext(str(output_root), "A5 acceptance-only", {"dependencies": [dependency]}),
        fetch_response=fetch_response)
    h2_op = {"operation_id": request["operation_id"], "capability_id": "corporate_action_context",
        "executor_id": EXECUTOR_ID, "market": "TWSE", "canonical_target_ids": [target["canonical_target_id"]],
        "dependency_operation_ids": [h3_op["operation_id"]], "operation_status": "executable_pending_approval",
        "executor_invocation_eligible": True}
    h3_result = {"operation_id": h3_op["operation_id"], "status": "succeeded",
        "capability_id": "recent_performance", "executor_id": h3_op["executor_id"],
        "evidence_contract": "recent_performance_evidence.v1", "evidence_artifacts": [h3_ref]}
    return {"operation_result": result, "h3_fixture_path": h3_path,
        "h3_fixture_label": "TEST / ACCEPTANCE-ONLY; NOT LIVE H3 EVIDENCE; NOT SOURCE COMPLETENESS AUTHORITY",
        "h3_fixture_window": {"start": h3["baselines"][0]["start_observation_date"],
            "end": h3["baselines"][0]["end_observation_date"]},
        "h2_operation": h2_op, "h3_operation": h3_op, "h3_result": h3_result}


def derive_a5_h4_replay(h2_run: Mapping[str, Any], *, output_root: Path) -> list[dict[str, Any]]:
    """Use the frozen production H4 derivation path over A5 H2/H3 artifacts."""
    from server.services.phase_h_h2_twse_exright_executor import derive_h4_for_completed_plan
    h2_result = h2_run["operation_result"]
    plan = {"operations": [h2_run["h3_operation"], h2_run["h2_operation"]]}
    return derive_h4_for_completed_plan(plan, [h2_run["h3_result"], h2_result], output_root=str(output_root))


def run_p0_preflight(execution_environment: str) -> dict[str, Any]:
    head, tree, main = current_git_state()
    target_state = resolve_execution_target(execution_environment)
    identity_status = target_state["preflight_status"]
    identity = target_state.get("target_binding")
    root_selected = bool(os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT"))
    if target_state["production_identity_verified"]:
        identity_resolution = {
            "target": TARGET_ID, "authority": "installation-local Taiwan Market Identity Service",
            "result": "resolved", "resolution_status": "resolved", "resolution_reason": "exact_listing_id",
            "reason_code": None, "selected_root_class": target_state["selected_root_class"],
            "TW_MARKET_SECURITY_MASTER_ROOT_selected": root_selected,
            "security_master_release_id": target_state["security_master_release_id"],
            "security_master_manifest_hash": target_state["security_master_manifest_hash"],
            "security_master_release_index_sha256": target_state["security_master_release_index_sha256"],
            "target_binding": identity,
            "product_scope_identity_verified": True,
            "legacy_candidate_fallback": False, "fixture_identity_fallback": False,
            "company_name_fallback": False, "live_security_master_bootstrap_performed": False,
        }
    elif target_state["identity_assurance_level"] == "acceptance_only_predeclared_source_target":
        identity_resolution = {
            "target": TARGET_ID, "authority": "predeclared A5 source-binding descriptor",
            "result": "predeclared_source_target_only", "resolution_status": None,
            "resolution_reason": "fixed_descriptor; no identity lookup performed",
            "reason_code": "NOT_INITIALIZED", "selected_root_class": target_state["selected_root_class"],
            "TW_MARKET_SECURITY_MASTER_ROOT_selected": root_selected,
            "security_master_release_id": None, "security_master_manifest_hash": None,
            "security_master_release_index_sha256": None,
            "target_binding": identity,
            "product_scope_identity_verified": False,
            "legacy_candidate_fallback": False, "fixture_identity_fallback": False,
            "company_name_fallback": False, "live_security_master_bootstrap_performed": False,
        }
    else:
        identity_resolution = {
            "target": TARGET_ID, "authority": "installation-local Taiwan Market Identity Service",
            "result": "not_resolved", "resolution_status": None,
            "resolution_reason": "production_identity_required_for_installation_bound_execution",
            "reason_code": "NOT_INITIALIZED" if target_state["security_master_status"] == "NOT_INITIALIZED" else identity_status,
            "selected_root_class": target_state["selected_root_class"],
            "TW_MARKET_SECURITY_MASTER_ROOT_selected": root_selected,
            "security_master_release_id": None, "security_master_manifest_hash": None,
            "security_master_release_index_sha256": None, "target_binding": None,
            "product_scope_identity_verified": False,
            "legacy_candidate_fallback": False, "fixture_identity_fallback": False,
            "company_name_fallback": False, "live_security_master_bootstrap_performed": False,
        }
    target_descriptor, descriptor_hash = predeclared_source_target()
    descriptor_json = _canonical_target_bytes(target_descriptor).decode("utf-8")
    return {"gate": "J-B04-A5", "preflight_status": identity_status,
        "execution_environment_class": execution_environment,
        "starting_main": STARTING_MAIN, "observed_origin_main": main,
        "branch_head_sha": head, "tree_sha": tree, "target": TARGET_ID,
        "target_identity": identity, "identity_resolution": identity_resolution,
        "security_master_status": target_state["security_master_status"],
        "identity_assurance_level": target_state["identity_assurance_level"],
        "production_identity_verified": target_state["production_identity_verified"],
        "A6_identity_reverification_required": target_state["A6_identity_reverification_required"],
        "A6_requires_canonical_security_master": True,
        "predeclared_source_target": target_descriptor,
        "predeclared_source_target_canonical_json": descriptor_json,
        "predeclared_source_target_sha256": descriptor_hash,
        "source_target_binding_scope": target_state.get("source_target_binding_scope", "A5 exact TWT48U Code-field binding only"),
        "secondary_stage_witness_policy": STAGE_WITNESS_POLICY,
        "identity_error_code": None if target_state["production_identity_verified"] or target_state["identity_assurance_level"] == "acceptance_only_predeclared_source_target" else identity_status,
        "canonical_identity_authority": "installation_local_security_master_release",
        "selected_root_class": target_state["selected_root_class"],
        "security_master_release_id": target_state["security_master_release_id"],
        "security_master_manifest_hash": target_state["security_master_manifest_hash"],
        "security_master_release_index_sha256": target_state["security_master_release_index_sha256"],
        "legacy_candidate_fallback": False, "fixture_identity_fallback": False,
        "company_name_fallback": False, "live_security_master_bootstrap_performed": False,
        "security_master_bootstrap": {"performed": False, "live_update_performed": False,
            "legacy_migration_performed": False, "records_imported": False,
            "candidate_b_reconstructed": False, "fixture_security_master_used": False},
        "secondary_stage_witness_product_scope_identity_verified": False,
        "secondary_stage_witness_only": True,
        "TW_MARKET_SECURITY_MASTER_ROOT_selected": root_selected,
        "endpoint": ENDPOINT, "method": "GET",
        "logical_get_maximum": 1, "http_dispatch_maximum": 1, "retry": 0,
        "redirect_policy": "reject", "timeout_seconds_maximum": TIMEOUT,
        "response_ceiling_bytes": MAX_BYTES, "H3_live_GETs": 0, "TPEx_GETs": 0,
        "TWT49U_GETs": 0, "browser_fallback": "prohibited",
        "raw_payload_persistence": "NONE", "H2_activation": "NOT_AUTHORIZED",
        "J-B04_closure": "NOT_AUTHORIZED", "Phase_J_start": "NOT_AUTHORIZED",
        "live_authorization": ("NOT PRESENT; not requested because P0 is blocked" if identity is None
                               else "NOT PRESENT; P0-R2 is for independent review only; A5-L1 is not authorized"),
        "network_calls_so_far": {"market_GET": 0, "market_HEAD": 0, "market_POST": 0,
            "security_master_live_acquisition": 0}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true", help="run network-free A5 authority preflight")
    parser.add_argument("--execution-environment", choices=sorted(EXECUTION_ENVIRONMENTS), required=True,
        help="explicit installation identity assurance class; never inferred")
    parser.add_argument("--live-acceptance", action="store_true", help="run one exact-head Owner-authorized bounded-live acceptance")
    parser.add_argument("--prepare-execution-lease", action="store_true",
        help="create a random external execution-instance lease; does not authorize live execution")
    parser.add_argument("--owner-authorization-json", type=Path)
    parser.add_argument("--execution-lease-file", type=Path)
    args = parser.parse_args(argv)
    modes = sum((args.preflight, args.prepare_execution_lease, args.live_acceptance))
    if modes != 1:
        parser.error("choose exactly one of --preflight, --prepare-execution-lease, or --live-acceptance")
    if args.prepare_execution_lease:
        if args.execution_lease_file is None or args.owner_authorization_json is not None:
            parser.error("--prepare-execution-lease requires --execution-lease-file and prohibits --owner-authorization-json")
        try:
            print(json.dumps(prepare_execution_lease(args.execution_lease_file, args.execution_environment),
                ensure_ascii=False, sort_keys=True))
            return 0
        except A5Error as exc:
            print(json.dumps({"disposition": str(exc), "lease_file_created": False,
                "market_GET": 0, "market_HEAD": 0, "market_POST": 0}, sort_keys=True))
            return 3
    if args.live_acceptance:
        if args.owner_authorization_json is None or args.execution_lease_file is None:
            parser.error("--live-acceptance requires --owner-authorization-json and --execution-lease-file")
        try:
            result = run_live_acceptance(args.owner_authorization_json, args.execution_environment,
                args.execution_lease_file)
        except A5Error as exc:
            disposition = str(exc) if str(exc).startswith("J_B04_A5_") else "J_B04_A5_LIVE_AUTHORIZATION_INVALID"
            print(json.dumps({"disposition": disposition, "transport_attempted": False,
                "market_GET": 0, "market_HEAD": 0, "market_POST": 0}, sort_keys=True))
            return 3
        except Exception:
            print(json.dumps({"disposition": "J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED",
                "transport_attempted": False, "market_GET": 0, "market_HEAD": 0, "market_POST": 0}, sort_keys=True))
            return 3
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["disposition"] == "J_B04_A5_BOUNDED_LIVE_SOURCE_ACCEPTANCE_PASS_AWAITING_INDEPENDENT_REVIEW" else 2
    if args.owner_authorization_json is not None or args.execution_lease_file is not None:
        parser.error("authorization and lease paths are valid only in their explicit modes")
    print(json.dumps(run_p0_preflight(args.execution_environment), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
