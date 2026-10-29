from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).parents[2]
PS1 = ROOT / "packaging_native/launchers/tw-market-launcher.ps1"
CMD = ROOT / "packaging_native/launchers/Launch-TW-Market.cmd"
POLICY = ROOT / "packaging_native/resource-policy.json"


def _powershell() -> str:
    if os.name != "nt":
        pytest.skip("P1-A3 launcher is Windows-only")
    return str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe")


def _payload(process: str, alive: bool, *, host: str = "127.0.0.1", identity: str = "NOT_INITIALIZED") -> dict:
    return {
        "status": "SERVICE_ALIVE" if alive else process,
        "installation": {"installation_status": "READY"},
        "service": {"process": process, "alive": alive, "host": host, "port": 8000},
        "identity": {"status": identity},
        "mcp": {"status": "READY" if alive else "SERVICE_UNREACHABLE"},
    }


def _fake_bundle(tmp_path: Path, status: dict) -> Path:
    bundle = tmp_path / "bundle"
    (bundle / "launcher").mkdir(parents=True)
    (bundle / "runtime/venv/Scripts").mkdir(parents=True)
    shutil.copy2(PS1, bundle / "launcher/tw-market-launcher.ps1")
    (bundle / "runtime/venv/Scripts/python.exe").write_bytes(b"stub")
    (bundle / "runtime/runtime-marker.json").write_text("{}", encoding="utf-8")
    (bundle / "test-status.json").write_text(json.dumps(status), encoding="utf-8")
    (bundle / "test-doctor.json").write_text(json.dumps({**status, "status": "WARN", "checks": []}), encoding="utf-8")
    (bundle / "tw-market.cmd").write_text(
        "@echo off\n"
        "if /I \"%1\"==\"status\" (type \"%~dp0test-status.json\" & exit /b 0)\n"
        "if /I \"%1\"==\"doctor\" (type \"%~dp0test-doctor.json\" & exit /b 0)\n"
        "echo {\"status\":\"UNEXPECTED_ACTION\",\"reason_code\":\"UNEXPECTED_ACTION\"}\n"
        "exit /b 1\n",
        encoding="ascii",
    )
    return bundle


def _invoke(bundle: Path, action: str, *extra: str) -> subprocess.CompletedProcess[str]:
    command = [
        _powershell(), "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(bundle / "launcher/tw-market-launcher.ps1"),
        "-Headless", "-Action", action, *extra,
    ]
    return subprocess.run(command, capture_output=True, text=True, timeout=30)


def _run_function_probe(bundle: Path, body: str) -> subprocess.CompletedProcess[str]:
    source = (bundle / "launcher/tw-market-launcher.ps1").read_text(encoding="utf-8")
    marker = "\nif ($Action -ne 'Gui' -or $Headless) {"
    assert marker in source
    probe = bundle / "launcher/function-probe.ps1"
    probe.write_text(source.split(marker, 1)[0] + "\n" + body + "\n", encoding="utf-8")
    return subprocess.run(
        [_powershell(), "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(probe)],
        capture_output=True, text=True, timeout=30,
    )


def test_launcher_sources_are_packaged() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    destinations = {row["destination"] for row in policy["members"]}
    assert "Launch-TW-Market.cmd" in destinations
    assert "launcher/tw-market-launcher.ps1" in destinations
    assert CMD.is_file() and PS1.is_file()


def test_launcher_has_no_hidden_installer_or_polling_surface() -> None:
    text = PS1.read_text(encoding="utf-8").lower()
    forbidden = (
        "invoke-webrequest", "invoke-restmethod", "system.net.webclient",
        "winget ", "choco ", "scoop ", "start-sleep", "forms.timer",
        "register-objectevent", "update --live", "start mcp server",
    )
    assert not any(token in text for token in forbidden)
    assert "tw-market.cmd" in text
    assert "bootstrap\\bootstrap.ps1" in text


def test_launcher_parses_in_windows_powershell() -> None:
    command = (
        "$t=$null;$e=$null;"
        f"[void][System.Management.Automation.Language.Parser]::ParseFile('{PS1}',[ref]$t,[ref]$e);"
        "if($e.Count){$e|%{$_.ToString()};exit 1}"
    )
    result = subprocess.run([_powershell(), "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.parametrize(
    ("process", "alive", "expected"),
    [
        ("NOT_RUNNING", False, "STOPPED"),
        ("START_IN_PROGRESS", False, "STARTING"),
        ("RUNNING", True, "RUNNING_READY"),
        ("RUNNING", False, "RUNNING_UNHEALTHY"),
        ("PORT_OCCUPIED_NOT_OWNED", False, "PORT_CONFLICT"),
        ("STALE_PROCESS_OWNERSHIP", False, "STALE_OWNERSHIP"),
    ],
)
def test_headless_status_projects_canonical_runtime_states(tmp_path: Path, process: str, alive: bool, expected: str) -> None:
    bundle = _fake_bundle(tmp_path, _payload(process, alive))
    result = _invoke(bundle, "Status")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == expected


def test_workbench_uri_is_loopback_only(tmp_path: Path) -> None:
    good = _fake_bundle(tmp_path / "good", _payload("RUNNING", True, host="localhost"))
    result = _invoke(good, "WorkbenchUri")
    assert result.returncode == 0
    assert json.loads(result.stdout)["data"]["uri"] == "http://localhost:8000/workbench/"

    bad = _fake_bundle(tmp_path / "bad", _payload("RUNNING", True, host="example.com"))
    result = _invoke(bad, "WorkbenchUri")
    assert result.returncode == 1
    assert json.loads(result.stdout)["reason_code"] == "WORKBENCH_URI_INVALID"


def test_stale_ownership_start_requires_confirmation(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("STALE_PROCESS_OWNERSHIP", False))
    result = _invoke(bundle, "Start")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "CONFIRMATION_REQUIRED"
    assert payload["reason_code"] == "STALE_PROCESS_OWNERSHIP"


def test_missing_runtime_status_is_read_only_setup_required(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    (bundle / "launcher").mkdir(parents=True)
    shutil.copy2(PS1, bundle / "launcher/tw-market-launcher.ps1")
    result = _invoke(bundle, "Status")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == {"status": "SETUP_REQUIRED", "reason_code": "PACKAGE_RUNTIME_NOT_READY"}
    assert not (bundle / "runtime").exists()


def test_setup_final_verification_fails_closed_for_unexpected_running_state(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("RUNNING", True))
    result = _invoke(bundle, "Setup")
    assert result.returncode == 1, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "SETUP_BLOCKED"
    assert payload["reason_code"] == "SETUP_FINAL_STATE_RUNNING_READY"
    assert payload["data"]["status"] == "RUNNING_READY"


def test_gui_render_guards_optional_snapshot_data_under_strict_mode() -> None:
    text = PS1.read_text(encoding="utf-8")
    assert "$payload = $null" in text
    assert "if ($snapshot.PSObject.Properties.Name -contains 'data') { $payload = $snapshot.data }" in text
    assert "($payload.PSObject.Properties.Name -contains 'installation')" in text
    assert "($payload.PSObject.Properties.Name -contains 'identity')" in text
    assert "($payload.PSObject.Properties.Name -contains 'mcp')" in text


def test_gui_action_render_reuses_post_action_snapshot_and_preserves_details() -> None:
    text = PS1.read_text(encoding="utf-8")
    marker = "& $render -UseCurrentSnapshot -PreserveTechnicalDetails"
    assert text.count(marker) >= 3
    assert "if (-not $PreserveTechnicalDetails)" in text
    assert "$script:CurrentSnapshot = $after" in text
    assert "$script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12)" in text


def test_setup_completion_is_explicit_allowlist_not_fail_open() -> None:
    text = PS1.read_text(encoding="utf-8")
    assert "if ($final.status -eq 'STOPPED')" in text
    assert "return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode $reason -Data $final" in text
    assert text.count("return New-LauncherResult -Status 'SETUP_COMPLETE' -Data $final.data") == 1


def test_setup_failure_status_refresh_preserves_action_technical_details(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("RUNNING", True))
    probe = _run_function_probe(
        bundle,
        r'''
$result = Invoke-Setup
$script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12 -Compress)
$beforeDetails = $script:LastTechnicalDetails
$snapshot = Get-LauncherSnapshot -PreserveTechnicalDetails
[pscustomobject]@{
  result_status = $result.status
  snapshot_status = $snapshot.status
  details_same = ($script:LastTechnicalDetails -eq $beforeDetails)
  details = $script:LastTechnicalDetails
} | ConvertTo-Json -Depth 12 -Compress
''',
    )
    assert probe.returncode == 0, probe.stderr + probe.stdout
    observed = json.loads(probe.stdout)
    assert observed["result_status"] == "SETUP_BLOCKED"
    assert observed["snapshot_status"] == "RUNNING_READY"
    assert observed["details_same"] is True
    assert json.loads(observed["details"])["status"] == "SETUP_BLOCKED"


@pytest.mark.parametrize(
    ("action", "before_status", "after_status", "expected_result", "expected_snapshot"),
    [
        ("Start", _payload("NOT_RUNNING", False), _payload("RUNNING", True), "START_FAILED", "RUNNING_READY"),
        ("Stop", _payload("RUNNING", True), _payload("NOT_RUNNING", False), "STOP_FAILED", "STOPPED"),
    ],
)
def test_start_stop_malformed_response_still_refreshes_actual_state(
    tmp_path: Path,
    action: str,
    before_status: dict,
    after_status: dict,
    expected_result: str,
    expected_snapshot: str,
) -> None:
    bundle = _fake_bundle(tmp_path, before_status)
    before_json = json.dumps(before_status, separators=(",", ":"))
    after_json = json.dumps(after_status, separators=(",", ":"))
    lifecycle_action = action.lower()
    probe = _run_function_probe(
        bundle,
        f'''$script:StatusCalls = 0
$beforePayload = '{before_json}' | ConvertFrom-Json
$afterPayload = '{after_json}' | ConvertFrom-Json
function Invoke-Lifecycle {{
  param([ValidateSet('init','start','status','stop','doctor')][string]$Command)
  if ($Command -eq 'status') {{
    $script:StatusCalls += 1
    $payload = if ($script:StatusCalls -eq 1) {{ $beforePayload }} else {{ $afterPayload }}
    return [pscustomobject]@{{ exit_code = 0; payload = $payload; raw = 'status-json'; error = $null }}
  }}
  if ($Command -eq '{lifecycle_action}') {{
    return [pscustomobject]@{{ exit_code = 1; payload = $null; raw = 'not-json'; error = $null }}
  }}
  throw "unexpected lifecycle command: $Command"
}}
$result = Invoke-{action}Action
[pscustomobject]@{{
  result_status = $result.status
  status_calls = $script:StatusCalls
  current_snapshot = $script:CurrentSnapshot.status
  technical = $script:LastTechnicalDetails
}} | ConvertTo-Json -Compress
''',
    )
    assert probe.returncode == 0, probe.stderr + probe.stdout
    observed = json.loads(probe.stdout)
    assert observed["result_status"] == expected_result
    assert observed["status_calls"] == 2
    assert observed["current_snapshot"] == expected_snapshot
    assert observed["technical"] == "not-json"
