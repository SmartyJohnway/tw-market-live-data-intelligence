from __future__ import annotations

import json
import subprocess
import sys

from tests.unit.m8r_05b_03_test_helpers import EVALUATION_TIMESTAMP, artifacts, registry_metadata


def _write(path, payload):
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def test_cli_outputs_valid_json_and_does_not_write_outputs(tmp_path):
    plan, authorization, binding, state = artifacts()
    output_root = tmp_path / "governed"
    output_root.mkdir()
    args = [
        sys.executable,
        "-m",
        "scripts.m8r_05b_03.cli",
        "--plan-input",
        str(_write(tmp_path / "plan.json", plan)),
        "--authorization-input",
        str(_write(tmp_path / "authorization.json", authorization)),
        "--consumption-binding-input",
        str(_write(tmp_path / "binding.json", binding)),
        "--consumption-state-input",
        str(_write(tmp_path / "state.json", state)),
        "--executor-registry-metadata-input",
        str(_write(tmp_path / "registry.json", registry_metadata(plan))),
        "--output-root",
        str(output_root),
        "--evaluation-timestamp",
        EVALUATION_TIMESTAMP,
    ]
    before = sorted(path.relative_to(output_root).as_posix() for path in output_root.rglob("*"))
    result = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8")
    after = sorted(path.relative_to(output_root).as_posix() for path in output_root.rglob("*"))
    artifact = json.loads(result.stdout)
    assert result.returncode == 0
    assert result.stderr == ""
    assert artifact["schema_version"] == "unified_market_evidence_orchestrator_preflight.v1"
    assert after == before == []


def test_cli_uses_stable_error_code(tmp_path):
    plan, authorization, binding, state = artifacts()
    state["state"] = "consumed"
    output_root = tmp_path / "governed"
    output_root.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.m8r_05b_03.cli",
            "--plan-input",
            str(_write(tmp_path / "plan.json", plan)),
            "--authorization-input",
            str(_write(tmp_path / "authorization.json", authorization)),
            "--consumption-binding-input",
            str(_write(tmp_path / "binding.json", binding)),
            "--consumption-state-input",
            str(_write(tmp_path / "state.json", state)),
            "--executor-registry-metadata-input",
            str(_write(tmp_path / "registry.json", registry_metadata(plan))),
            "--output-root",
            str(output_root),
            "--evaluation-timestamp",
            EVALUATION_TIMESTAMP,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert json.loads(result.stderr)["error_code"] == "authorization_already_consumed"
