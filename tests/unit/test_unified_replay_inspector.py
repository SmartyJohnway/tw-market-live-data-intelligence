"""Retained-only inspection: deterministic packages, forbidden seams, byte inventory."""
import builtins
import hashlib
import json
import socket
import sqlite3
from pathlib import Path

import pytest

from tests.unit.test_m8r_06_04_mode_c import mode_c_root, PACKAGE_ID, FIXTURES
from server.services import unified_mode_c as mode_c
from server.services.unified_replay_inspector import inspect_finalized_package

pytestmark = [pytest.mark.unit, pytest.mark.offline, pytest.mark.default_ci]


def inventory(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            if p.is_file() else "directory" for p in root.rglob("*")}


@pytest.mark.parametrize("case,state", [
    ("existing", "EXISTING_VERIFIED"),
    ("retained", "REPLAYABLE"),
    ("missing_f3", "REPLAY_UNAVAILABLE_MISSING_ARTIFACT"),
    ("missing_evidence", "REPLAY_UNAVAILABLE_MISSING_ARTIFACT"),
    ("tamper_evidence", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
    ("tamper_control", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
    ("partial", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
    ("multiple", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
    ("duplicate_claim", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
    ("projector", "REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION"),
    ("schema", "REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION"),
    ("new_filename", "REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION"),
    ("nonfinal", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
    ("predecessor_version", "REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION"),
    ("malformed_evidence", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
    ("invalid_id", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
    ("traversal", "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"),
])
def test_inspection_is_read_only(mode_c_root, monkeypatch, case, state):
    package = mode_c_root
    f3 = package / "mode_c/f3_validation.json"
    f3.parent.mkdir()
    f3.write_text(json.dumps(json.loads((FIXTURES / "f3_validation.json").read_text()), ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    if case in {"existing", "partial", "multiple", "projector", "schema"}:
        mode_c.build_mode_c_result_package({"control_package_id": PACKAGE_ID})
    if case == "missing_f3":
        f3.unlink()
    if case in {"missing_evidence", "tamper_evidence", "malformed_evidence"}:
        evidence = next((package / "operations").rglob("*.json"))
        if case == "missing_evidence":
            evidence.unlink()
        else:
            evidence.write_text("{" if case == "malformed_evidence" else "{}", encoding="utf-8")
    if case == "tamper_control":
        (package / "control/request.json").write_text("{}", encoding="utf-8")
    if case == "duplicate_claim":
        path = next((package / "claims").glob("*.json"))
        (path.parent / "duplicate.json").write_bytes(path.read_bytes())
    result_rel, md_rel, audit_rel, _ = mode_c._OUTPUT_PATHS[mode_c.PREFERRED_RESULT_SCHEMA_VERSION]
    if case == "partial":
        (package / md_rel).unlink()
    if case == "multiple":
        for source, target in zip(mode_c._OUTPUT_PATHS[mode_c.PREFERRED_RESULT_SCHEMA_VERSION][:3], mode_c._OUTPUT_PATHS["unified_market_evidence_result.v1"][:3]):
            (package / target).write_bytes((package / source).read_bytes())
    if case in {"projector", "schema"}:
        path = package / (audit_rel if case == "projector" else result_rel)
        obj = json.loads(path.read_text(encoding="utf-8"))
        if case == "projector":
            obj["projector_metadata"]["projector_version"] = "future"
        else:
            obj["schema_version"] = "unified_market_evidence_result.v99"
        path.write_text(json.dumps(obj), encoding="utf-8")
    if case == "new_filename":
        (package / "ai_context").mkdir()
        (package / "ai_context/unified_market_evidence_result.v99.json").write_text("{}")
    if case in {"nonfinal", "predecessor_version"}:
        path = next((package / "claims").glob("*.json"))
        obj = json.loads(path.read_text())
        if case == "nonfinal":
            obj["state"] = "claimed"
        else:
            obj["schema_version"] = "unified_market_evidence_consumption_record.v99"
        path.write_text(json.dumps(obj))
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("forbidden side effect")
    from scripts import m8r_06_03_production_adapter as adapter
    from server.services import unified_mode_b2, unified_mode_a
    for module, names in [(mode_c, ["_f3", "materialize_outputs", "validate_mode_a_request"]),
                          (adapter, ["urlopen", "_fetch_official_payload", "production_operation_adapter", "production_batch_operation_adapter", "build_production_runtime_adapter_registry"]),
                          (unified_mode_b2, ["_write_control_package", "_materialize_execution_ticket"]),
                          (unified_mode_a, ["get_production_mode_a_security_master"])]:
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    original_open = builtins.open
    original_path_open = Path.open
    def checked_open(file, mode="r", *args, **kwargs):
        if any(c in mode for c in "wax+"):
            forbidden()
        return original_open(file, mode, *args, **kwargs)
    def checked_path_open(path, mode="r", *args, **kwargs):
        if any(c in mode for c in "wax+"):
            forbidden()
        return original_path_open(path, mode, *args, **kwargs)
    before = inventory(package.parent)
    with monkeypatch.context() as guard:
        guard.setattr(builtins, "open", checked_open)
        guard.setattr(Path, "open", checked_path_open)
        for name in ["mkdir", "unlink", "rmdir", "rename", "replace", "touch"]:
            guard.setattr(Path, name, forbidden)
        control_id = "bad" if case == "invalid_id" else "umea-v1-../outside" if case == "traversal" else PACKAGE_ID
        result = inspect_finalized_package(control_id, control_root=package.parent)
    assert result["state"] == state, result
    assert inventory(package.parent) == before
    assert calls == []
    assert set(result) == {"control_package_id", "request_schema_version", "result_schema_version", "audit_schema_version", "projector_version", "persisted_output_presence", "state", "reason_code"}
