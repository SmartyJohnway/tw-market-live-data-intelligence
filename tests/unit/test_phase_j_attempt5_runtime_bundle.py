from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts import phase_j_attempt5_runtime_bundle as bundle


def _files():
    return {
        "bin/codex.exe": b"codex-0160",
        "bin/codex-code-mode-host.exe": b"host-0160",
        "codex-resources/codex-command-runner.exe": b"runner-0160",
        "codex-resources/codex-windows-sandbox-setup.exe": b"sandbox-0160",
        "codex-package.json": b'{"version":"0.160.1"}',
        "codex-path/rg.exe": b"rg-0160",
    }


def _fixture(tmp_path, monkeypatch):
    root = tmp_path / "bundle"
    files = _files()
    for relative, data in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    entries = [
        {"path": relative, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for relative, data in sorted(files.items())
    ]
    identities = {p: (e["size"], e["sha256"]) for p, e in ((x["path"], x) for x in entries)}
    monkeypatch.setattr(bundle, "KEY_FILE_IDENTITIES", identities)
    return root, files, entries


def _verify(root, entries, *, expected_root=None, expected_hash=None, count=None, total=None, version="codex-cli 0.160.1"):
    return bundle.verify_bundle(
        root=root,
        expected_root=root if expected_root is None else expected_root,
        expected_entries=entries,
        expected_inventory_sha256=bundle.inventory_sha256(entries) if expected_hash is None else expected_hash,
        expected_file_count=len(entries) if count is None else count,
        expected_total_size=sum(item["size"] for item in entries) if total is None else total,
        expected_version=version,
        version_runner=lambda _path: (0, "codex-cli 0.160.1"),
        required_key_files=bundle.KEY_FILE_IDENTITIES,
        pe_check=lambda _path: True,
    )


def test_exact_bundle_inventory_and_runtime_version_pass(tmp_path, monkeypatch):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    result = _verify(root, entries)
    assert result["file_count"] == 6
    assert result["code_mode_host_relative_path"] == "bin/codex-code-mode-host.exe"
    assert result["executable_observed_version"] == "codex-cli 0.160.1"


def test_codex_executable_alone_is_not_a_runtime_bundle(tmp_path, monkeypatch):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    (root / "bin/codex-code-mode-host.exe").unlink()
    with pytest.raises(ValueError, match="inventory"):
        _verify(root, entries)


@pytest.mark.parametrize("mutation", ["missing", "changed", "wrong_size"])
def test_codex_executable_missing_or_changed_bytes_fail(tmp_path, monkeypatch, mutation):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    executable = root / "bin/codex.exe"
    if mutation == "missing":
        executable.unlink()
    elif mutation == "changed":
        executable.write_bytes(b"substituted codex runtime")
    else:
        executable.write_bytes(executable.read_bytes() + b"x")
    with pytest.raises(ValueError, match="inventory"):
        _verify(root, entries)


@pytest.mark.parametrize("relative", [
    "bin/codex-code-mode-host.exe",
    "codex-resources/codex-command-runner.exe",
    "codex-resources/codex-windows-sandbox-setup.exe",
])
def test_missing_required_runtime_helpers_fail(tmp_path, monkeypatch, relative):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    (root / relative).unlink()
    with pytest.raises(ValueError, match="inventory"):
        _verify(root, entries)


@pytest.mark.parametrize("relative", [
    "bin/codex-code-mode-host.exe",
    "codex-resources/codex-command-runner.exe",
    "codex-resources/codex-windows-sandbox-setup.exe",
])
def test_wrong_helper_bytes_fail_even_when_file_is_present(tmp_path, monkeypatch, relative):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    (root / relative).write_bytes(b"substituted-app-0.162")
    with pytest.raises(ValueError, match="inventory"):
        _verify(root, entries)


def test_app_0162_code_mode_host_is_rejected(tmp_path, monkeypatch):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    (root / "bin/codex-code-mode-host.exe").write_bytes(b"app-0.162-host")
    with pytest.raises(ValueError):
        _verify(root, entries)


@pytest.mark.parametrize("mutation", ["extra", "missing", "aggregate", "wrong_root", "flattened"])
def test_exact_set_layout_and_aggregate_are_mandatory(tmp_path, monkeypatch, mutation):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    expected_root = root
    expected_entries = entries
    expected_hash = bundle.inventory_sha256(entries)
    if mutation == "extra":
        (root / "unexpected.dll").write_bytes(b"extra")
    elif mutation == "missing":
        (root / "codex-package.json").unlink()
    elif mutation == "aggregate":
        expected_hash = "0" * 64
    elif mutation == "wrong_root":
        expected_root = root.parent / "other"
    elif mutation == "flattened":
        for path in list(root.rglob("*")):
            if path.is_file():
                flat = root / path.name
                if flat != path:
                    flat.parent.mkdir(parents=True, exist_ok=True)
                    path.replace(flat)
    with pytest.raises((ValueError, FileNotFoundError)):
        _verify(root, expected_entries, expected_root=expected_root, expected_hash=expected_hash)


def test_source_target_copy_equivalence_checks_every_path_size_and_hash(tmp_path, monkeypatch):
    source = tmp_path / "source"
    target = tmp_path / "target"
    for root in (source, target):
        (root / "bin").mkdir(parents=True)
        (root / "bin/codex.exe").write_bytes(b"same executable")
    entries = bundle.inventory(source)
    monkeypatch.setattr(bundle, "EXPECTED_FILE_COUNT", len(entries))
    monkeypatch.setattr(bundle, "EXPECTED_TOTAL_SIZE", sum(entry["size"] for entry in entries))
    monkeypatch.setattr(bundle, "EXPECTED_BUNDLE_INVENTORY_SHA256", bundle.inventory_sha256(entries))
    assert bundle.verify_source_target_equivalence(source, target)["source_entries"] == entries
    (target / "bin/codex.exe").write_bytes(b"different executable")
    with pytest.raises(ValueError, match="manifests differ"):
        bundle.verify_source_target_equivalence(source, target)


@pytest.mark.parametrize("reported", ["codex-cli 0.162.0-alpha.2", "not-codex"])
def test_wrong_executable_version_fails_closed(tmp_path, monkeypatch, reported):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="version"):
        bundle.verify_bundle(
            root=root, expected_root=root, expected_entries=entries,
            expected_inventory_sha256=bundle.inventory_sha256(entries),
            expected_file_count=len(entries), expected_total_size=sum(e["size"] for e in entries),
            expected_version="codex-cli 0.160.1",
            version_runner=lambda _path: (0, reported), required_key_files=bundle.KEY_FILE_IDENTITIES,
            pe_check=lambda _path: True,
        )


def _valid_launch_contract():
    identity = {
        "bundle_root_absolute_path": str(bundle.BUNDLE_ROOT),
        "bundle_manifest_schema_version": "codex_vendor_runtime_bundle_inventory.v1",
        "file_count": bundle.EXPECTED_FILE_COUNT,
        "total_byte_size": bundle.EXPECTED_TOTAL_SIZE,
        "canonical_inventory_sha256": bundle.EXPECTED_BUNDLE_INVENTORY_SHA256,
        "executable_relative_path": "bin/codex.exe",
        "executable_absolute_path": str(bundle.BUNDLE_ROOT / "bin/codex.exe"),
        "executable_observed_version": bundle.EXPECTED_VERSION,
        "executable_sha256": bundle.KEY_FILE_IDENTITIES["bin/codex.exe"][1],
        "code_mode_host_relative_path": "bin/codex-code-mode-host.exe",
        "code_mode_host_sha256": bundle.KEY_FILE_IDENTITIES["bin/codex-code-mode-host.exe"][1],
        "command_runner_relative_path": "codex-resources/codex-command-runner.exe",
        "command_runner_sha256": bundle.KEY_FILE_IDENTITIES["codex-resources/codex-command-runner.exe"][1],
        "sandbox_setup_relative_path": "codex-resources/codex-windows-sandbox-setup.exe",
        "sandbox_setup_sha256": bundle.KEY_FILE_IDENTITIES["codex-resources/codex-windows-sandbox-setup.exe"][1],
        "package_descriptor_relative_path": "codex-package.json",
        "package_descriptor_sha256": bundle.KEY_FILE_IDENTITIES["codex-package.json"][1],
        "rg_relative_path": "codex-path/rg.exe",
        "rg_sha256": bundle.KEY_FILE_IDENTITIES["codex-path/rg.exe"][1],
    }
    return bundle._launch_contract_from_identity(identity)


@pytest.mark.parametrize("mutation", [
    "wrong_package", "wrong_proxy", "required_false", "wrong_cwd", "path_codex_only", "path_path_codex",
    "host_path", "host_hash", "runner_hash", "sandbox_hash", "executable_hash", "wrong_count", "wrong_bundle_hash",
    "runner_path", "sandbox_path", "descriptor_path", "rg_path",
])
def test_successor_contract_rejects_binding_and_runtime_mutations(mutation):
    contract = _valid_launch_contract()
    identity = contract["codex_runtime_bundle_identity"]
    if mutation == "wrong_package":
        contract["control_package_id"] = "umea-v1-00000000000000000000"
    elif mutation == "wrong_proxy":
        contract["mcp_server_template"]["args"][0] = str(bundle.ROOT / "scripts/other_proxy.py")
    elif mutation == "required_false":
        contract["mcp_server_template"]["required"] = False
    elif mutation == "wrong_cwd":
        contract["mcp_server_template"]["cwd"] = str(bundle.ROOT / "elsewhere")
    elif mutation == "path_codex_only":
        contract["formal_executable_absolute_path"] = str(bundle.RUNTIME_ROOT / "codex-pinned/0.160.1/codex.exe")
    elif mutation == "path_path_codex":
        contract["formal_executable_absolute_path"] = r"C:\Users\weitang\AppData\Roaming\npm\codex.exe"
    elif mutation == "host_path":
        identity["code_mode_host_relative_path"] = "codex-code-mode-host.exe"
    elif mutation == "host_hash":
        identity["code_mode_host_sha256"] = "0" * 64
    elif mutation == "runner_hash":
        identity["command_runner_sha256"] = "0" * 64
    elif mutation == "sandbox_hash":
        identity["sandbox_setup_sha256"] = "0" * 64
    elif mutation == "executable_hash":
        identity["executable_sha256"] = "0" * 64
    elif mutation == "wrong_count":
        identity["file_count"] -= 1
    elif mutation == "wrong_bundle_hash":
        identity["canonical_inventory_sha256"] = "0" * 64
    elif mutation == "runner_path":
        identity["command_runner_relative_path"] = "codex-command-runner.exe"
    elif mutation == "sandbox_path":
        identity["sandbox_setup_relative_path"] = "codex-windows-sandbox-setup.exe"
    elif mutation == "descriptor_path":
        identity["package_descriptor_relative_path"] = "package.json"
    elif mutation == "rg_path":
        identity["rg_relative_path"] = "rg.exe"
    with pytest.raises((ValueError, OSError)):
        bundle.validate_launch_contract(contract)


@pytest.mark.parametrize("slot", [0, 4, True])
def test_slot_number_outside_three_slot_budget_fails(slot):
    with pytest.raises(ValueError, match="between 1 and 3"):
        bundle.slot_paths(slot)


def test_build_contract_does_not_accept_caller_identity_as_authority():
    with pytest.raises(TypeError):
        bundle.build_launch_contract({"canonical_inventory_sha256": bundle.EXPECTED_BUNDLE_INVENTORY_SHA256})


def test_nonzero_version_command_fails_closed(tmp_path, monkeypatch):
    root, _, entries = _fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="version"):
        bundle.verify_bundle(
            root=root, expected_root=root, expected_entries=entries,
            expected_inventory_sha256=bundle.inventory_sha256(entries),
            expected_file_count=len(entries), expected_total_size=sum(e["size"] for e in entries),
            expected_version="codex-cli 0.160.1",
            version_runner=lambda _path: (23, "codex-cli 0.160.1"),
            required_key_files=bundle.KEY_FILE_IDENTITIES,
            pe_check=lambda _path: True,
        )


def test_pre_reservation_gate_remeasures_bundle_and_contract_hash(monkeypatch):
    contract = _valid_launch_contract()
    expected_hash = bundle.canonical_sha256(contract)
    identity = contract["codex_runtime_bundle_identity"]
    calls = []

    def measured():
        calls.append(True)
        return identity, {"inventory_sha256": bundle.EXPECTED_BUNDLE_INVENTORY_SHA256}

    monkeypatch.setattr(bundle, "build_verified_bundle_identity", measured)
    assert bundle.verify_contract_runtime_identity(contract, expected_hash) == identity
    assert len(calls) == 1
    with pytest.raises(ValueError, match="contract hash"):
        bundle.verify_contract_runtime_identity(contract, "0" * 64)


def test_pre_reservation_gate_rejects_runtime_drift(monkeypatch):
    contract = _valid_launch_contract()
    expected_hash = bundle.canonical_sha256(contract)
    actual = dict(contract["codex_runtime_bundle_identity"])
    actual["code_mode_host_sha256"] = "0" * 64
    monkeypatch.setattr(bundle, "build_verified_bundle_identity", lambda: (actual, {}))
    with pytest.raises(ValueError, match="measured complete runtime bundle"):
        bundle.verify_contract_runtime_identity(contract, expected_hash)
