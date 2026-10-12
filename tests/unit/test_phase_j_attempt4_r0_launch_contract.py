from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts import phase_j_attempt4_r0_launch_contract as contract


@pytest.fixture
def pinned_test_runtime(tmp_path, monkeypatch):
    binary = tmp_path / "codex.exe"
    binary.write_bytes(b"synthetic-codex-runtime")
    identity = {
        "absolute_executable_path": str(binary.resolve()),
        "observed_version": "codex-cli 0.160.1",
        "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "byte_size": binary.stat().st_size,
    }
    monkeypatch.setattr(contract, "PINNED_IDENTITY", identity)
    monkeypatch.setattr(contract, "PINNED_CODEX", binary)
    monkeypatch.setattr(contract, "_run_version", lambda path: (0, "codex-cli 0.160.1"))
    return binary, identity


def _contract_with_test_runtime(pinned_test_runtime):
    item = contract.build_contract()
    contract.validate_contract(item)
    return item


def test_runtime_identity_measures_exact_path_hash_size_and_version(pinned_test_runtime, monkeypatch):
    binary, expected = pinned_test_runtime
    calls = []

    def runner(path):
        calls.append(path)
        return 0, "codex-cli 0.160.1"

    monkeypatch.setattr(contract, "_run_version", runner)
    measured = contract.verify_codex_runtime_identity(expected)
    assert measured == expected
    assert calls == [str(binary.resolve())]


def test_contract_does_not_accept_caller_supplied_version_as_authority(pinned_test_runtime, monkeypatch):
    with pytest.raises(TypeError):
        contract.build_contract(codex_version="codex-cli 0.160.1")
    monkeypatch.setattr(contract, "_run_version", lambda _: (0, "codex-cli 0.162.0-alpha.2"))
    with pytest.raises(ValueError, match="version output"):
        contract.verify_codex_runtime_identity()


@pytest.mark.parametrize("mutation", ["wrong_path", "app_binary", "wrong_version", "wrong_hash", "wrong_size", "wrong_package", "required_false", "proxy_path", "wrong_cwd", "evidence_root"])
def test_launch_contract_rejects_runtime_and_semantic_mutations(pinned_test_runtime, mutation):
    item = _contract_with_test_runtime(pinned_test_runtime)
    if mutation == "wrong_path":
        item["codex_runtime_identity"]["absolute_executable_path"] = str(Path(item["codex_runtime_identity"]["absolute_executable_path"]).with_name("app_codex.exe"))
    elif mutation == "app_binary":
        item["codex_runtime_identity"]["absolute_executable_path"] = r"C:\Users\weitang\AppData\Local\OpenAI\Codex\bin\9691020b546a15b2\codex.exe"
    elif mutation == "wrong_version":
        item["codex_runtime_identity"]["observed_version"] = "codex-cli 0.162.0-alpha.2"
    elif mutation == "wrong_hash":
        item["codex_runtime_identity"]["sha256"] = "0" * 64
    elif mutation == "wrong_size":
        item["codex_runtime_identity"]["byte_size"] += 1
    elif mutation == "wrong_package":
        item["control_package_id"] = "umea-v1-00000000000000000000"
    elif mutation == "required_false":
        item["mcp_server_template"]["required"] = False
    elif mutation == "proxy_path":
        item["proxy_script_absolute_path"] = str(contract.ROOT / "scripts" / "other.py")
    elif mutation == "wrong_cwd":
        item["repository_cwd"] = str(Path(item["repository_cwd"]) / "other")
    elif mutation == "evidence_root":
        item["attempt_evidence_root"] = str(Path(item["package_root"]) / "attempt4")
    with pytest.raises((ValueError, OSError)):
        contract.validate_contract(item)


def test_missing_executable_and_nonzero_version_fail_closed(pinned_test_runtime):
    binary, identity = pinned_test_runtime
    binary.unlink()
    with pytest.raises((ValueError, OSError)):
        contract.verify_codex_runtime_identity(identity)


def test_nonzero_version_command_fails_closed(pinned_test_runtime, monkeypatch):
    _, identity = pinned_test_runtime
    monkeypatch.setattr(contract, "_run_version", lambda _: (1, "codex-cli 0.160.1"))
    with pytest.raises(ValueError, match="non-zero"):
        contract.verify_codex_runtime_identity(identity)


def test_executable_replacement_after_contract_generation_is_detected(pinned_test_runtime):
    binary, _ = pinned_test_runtime
    item = _contract_with_test_runtime(pinned_test_runtime)
    binary.write_bytes(b"replaced-runtime-with-different-bytes")
    with pytest.raises(ValueError, match="byte size|SHA-256"):
        contract.validate_contract(item)


def test_slot_derivation_is_bounded_and_captures_every_stream(pinned_test_runtime, tmp_path):
    item = _contract_with_test_runtime(pinned_test_runtime)
    first = contract.derive_slot_contract(item, 1, root=tmp_path)
    second = contract.derive_slot_contract(item, 2, root=tmp_path)
    assert Path(first["paths"]["directory"]).parent == tmp_path
    assert Path(first["paths"]["directory"]).parent != contract.PACKAGE_ROOT
    assert first["mcp_server"]["required"] is True
    assert first["mcp_server"]["args"][-1] == contract.CONTROL_ID
    assert first["formal_command"][0] == contract.PINNED_IDENTITY["absolute_executable_path"]
    assert first["formal_command"][1:3] == ["exec", "--ignore-user-config"]
    assert first["stdout_path"].endswith("codex-events.jsonl")
    assert first["stderr_path"].endswith("codex-stderr.txt")
    assert first["formal_command"][first["formal_command"].index("--output-last-message") + 1].endswith("agent-final.txt")
    assert first["mcp_server"]["args"][2].endswith("witness-events.jsonl")
    assert first["paths"]["directory"] != second["paths"]["directory"]
    with pytest.raises(ValueError, match="between 1 and 3"):
        contract.derive_slot_contract(item, 4, root=tmp_path)


def test_existing_slot_log_prevents_derivation(pinned_test_runtime, tmp_path):
    item = _contract_with_test_runtime(pinned_test_runtime)
    paths = contract.slot_paths(1, root=tmp_path)
    Path(paths["directory"]).mkdir()
    Path(paths["witness_events"]).write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        contract.derive_slot_contract(item, 1, root=tmp_path)


def test_slot_reservation_requires_all_preflight_gates(pinned_test_runtime, tmp_path, monkeypatch):
    item = _contract_with_test_runtime(pinned_test_runtime)
    monkeypatch.setattr(contract, "FROZEN_LAUNCH_CONTRACT_SHA256", contract.canonical_sha256(item))
    preflight = {"launch_contract_sha256": contract.canonical_sha256(item)}
    with pytest.raises(ValueError, match="preflight gates"):
        contract.reserve_slot(item, 1, now="2026-10-12T00:00:00Z", preflight=preflight, expected_contract_sha256=contract.canonical_sha256(item))


def test_future_launcher_captures_codex_stdout_stderr_and_prompt_without_launching_in_r0(pinned_test_runtime, tmp_path, monkeypatch):
    item = _contract_with_test_runtime(pinned_test_runtime)
    monkeypatch.setattr(contract, "ATTEMPT_ROOT", tmp_path)
    item["attempt_evidence_root"] = str(tmp_path)
    monkeypatch.setattr(contract, "FROZEN_LAUNCH_CONTRACT_SHA256", contract.canonical_sha256(item))
    gates = {
        "launch_contract_sha256": contract.canonical_sha256(item),
        "git_authority_verified": True, "retained_package_verified": True,
        "codex_runtime_verified": True, "local_service_healthy": True,
        "mcp_configuration_verified": True, "mcp_exact_six_probe_passed": True,
    }
    reservation = contract.reserve_slot(item, 1, now="2026-10-12T00:00:00Z", preflight=gates, expected_contract_sha256=contract.canonical_sha256(item))
    observed = {}

    class Process:
        returncode = 0
        def communicate(self, input):
            observed["input"] = input

    def factory(argv, **kwargs):
        observed["argv"] = argv
        observed["cwd"] = kwargs["cwd"]
        observed["stdout"] = kwargs["stdout"]
        observed["stderr"] = kwargs["stderr"]
        assert kwargs["stdin"] is not None
        return Process()

    prompt = contract.PROMPT_PATH.read_bytes()
    assert contract.run_reserved_slot(item, 1, preflight=gates, authorization_consumed=True, prompt_bytes=prompt, popen_factory=factory) == 0
    assert observed["input"] == prompt
    assert observed["argv"][0] == contract.PINNED_IDENTITY["absolute_executable_path"]
    assert observed["cwd"] == str(contract.ROOT)
    assert observed["stdout"].name.endswith("codex-events.jsonl")
    assert observed["stderr"].name.endswith("codex-stderr.txt")
    assert reservation.exists()


def test_old_app_binary_cannot_pass_with_fake_expected_version(pinned_test_runtime, monkeypatch):
    _, identity = pinned_test_runtime
    fake = dict(identity)
    fake["observed_version"] = "codex-cli 0.160.1"
    monkeypatch.setattr(contract, "_run_version", lambda _: (0, "codex-cli 0.162.0-alpha.2"))
    with pytest.raises(ValueError):
        contract.verify_codex_runtime_identity(fake)


def test_reviewed_contract_rejects_any_canonical_hash_drift(pinned_test_runtime, monkeypatch):
    item = _contract_with_test_runtime(pinned_test_runtime)
    monkeypatch.setattr(contract, "FROZEN_LAUNCH_CONTRACT_SHA256", contract.canonical_sha256(item))
    contract.validate_reviewed_contract(item)
    item["profile_identity"] = "unreviewed-profile"
    with pytest.raises(ValueError, match="exact R0-reviewed canonical hash"):
        contract.validate_reviewed_contract(item)
