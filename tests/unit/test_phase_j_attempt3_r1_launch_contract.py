from __future__ import annotations

from pathlib import Path

import pytest

from scripts.phase_j_attempt3_r1_launch_contract import (
    CONTROL_ID, SERVER_NAME, build_contract, canonical_bytes, sha256_bytes,
    validate_contract,
)


def contract(tmp_path: Path):
    root = tmp_path.resolve()
    return build_contract(
        codex_executable=str(root / "codex.exe"), codex_version="codex-cli 0.160.1",
        python_executable=str(root / "python.exe"), repository_cwd=str(root),
        runtime_root=str(root / "runtime"), service_url="http://127.0.0.1:18264",
        prompt_path=str(root / "prompt.txt"), witness_log_path=str(root / "runtime" / "witness.jsonl"),
        codex_events_path=str(root / "runtime" / "events.jsonl"),
        stderr_path=str(root / "runtime" / "stderr.txt"), final_output_path=str(root / "runtime" / "final.txt"),
    )


def test_contract_canonical_hash_and_exact_server_command_are_deterministic(tmp_path):
    first = contract(tmp_path)
    second = contract(tmp_path)
    validate_contract(first)
    assert sha256_bytes(canonical_bytes(first)) == sha256_bytes(canonical_bytes(second))
    assert first["mcp_server"]["name"] == SERVER_NAME
    assert first["mcp_server"]["required"] is True
    assert first["mcp_server"]["args"][-1] == CONTROL_ID
    assert first["codex"]["ignore_user_config"] is True


@pytest.mark.parametrize("mutation", ["required", "package", "cwd", "args", "proxy_path", "log_exists"])
def test_contract_rejects_broken_or_mismatched_witness_configuration(tmp_path, mutation):
    item = contract(tmp_path)
    if mutation == "required":
        item["mcp_server"]["required"] = False
    elif mutation == "package":
        item["control_package_id"] = "umea-v1-00000000000000000000"
    elif mutation == "cwd":
        item["mcp_server"]["cwd"] = str(tmp_path / "elsewhere")
    elif mutation == "args":
        item["mcp_server"]["args"][0] = str(tmp_path / "missing-proxy.py")
    elif mutation == "proxy_path":
        missing = str(tmp_path / "missing-proxy.py")
        item["proxy"]["script_absolute_path"] = missing
        item["proxy"]["argv"][0] = missing
        item["mcp_server"]["args"][0] = missing
    elif mutation == "log_exists":
        Path(item["mcp_server"]["env"]["PHASEJ_WITNESS_PROXY_LOG"]).parent.mkdir(parents=True)
        Path(item["mcp_server"]["env"]["PHASEJ_WITNESS_PROXY_LOG"]).write_text("", encoding="utf-8")
    with pytest.raises((ValueError, OSError)):
        validate_contract(item)
