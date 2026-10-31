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
    (bundle / "app").mkdir(parents=True)
    shutil.copy2(PS1, bundle / "launcher/tw-market-launcher.ps1")
    (bundle / "runtime/venv/Scripts/python.exe").write_bytes(b"stub")
    (bundle / "runtime/runtime-marker.json").write_text("{}", encoding="utf-8")
    (bundle / "app/VERSION").write_text("1.5.0\n", encoding="ascii")
    status = json.loads(json.dumps(status))
    status.setdefault("installation", {})["temp_root"] = str(bundle / "test-temp")
    (bundle / "test-status.json").write_text(json.dumps(status), encoding="utf-8")
    (bundle / "test-doctor.json").write_text(json.dumps({**status, "status": "WARN", "checks": []}), encoding="utf-8")
    (bundle / "test-security-status.json").write_text(json.dumps({"status": "NOT_INITIALIZED"}), encoding="utf-8")
    (bundle / "test-security-update.json").write_text(json.dumps({"status": "ACTIVE", "release_id": "test-release", "qualification": "PASS", "restart_required": True}), encoding="utf-8")
    (bundle / "test-security-strict-failure.json").write_text(json.dumps({"status": "REJECTED", "reason_code": "official_acquisition_or_qualification_failed"}), encoding="utf-8")
    (bundle / "test-security-strict-evidence.json").write_text(json.dumps({
        "principal_decision": "BLOCKED_BY_OFFICIAL_SOURCE_PROBE_FAILURE",
        "source_probes": [
            {"transport_success": False, "transport_reason_code": "PYTHON_X509_STRICT_COMPATIBILITY"},
            {"transport_success": False, "transport_reason_code": "PYTHON_X509_STRICT_COMPATIBILITY"},
        ],
    }), encoding="utf-8")
    (bundle / "tw-market.cmd").write_text(
        "@echo off\n"
        "if /I \"%1\"==\"status\" (type \"%~dp0test-status.json\" & exit /b 0)\n"
        "if /I \"%1\"==\"doctor\" (type \"%~dp0test-doctor.json\" & exit /b 0)\n"
        "echo {\"status\":\"UNEXPECTED_ACTION\",\"reason_code\":\"UNEXPECTED_ACTION\"}\n"
        "exit /b 1\n",
        encoding="ascii",
    )
    (bundle / "tw-market-security-master.cmd").write_text(
        "@echo off\n"
        "if /I \"%1\"==\"status\" (type \"%~dp0test-security-status.json\" & exit /b 0)\n"
        "if /I \"%1\"==\"update\" (\n"
        "  if /I not \"%2\"==\"--live\" exit /b 9\n"
        "  echo %*>\"%~dp0security-update-args.txt\"\n"
        "  echo called>\"%~dp0security-update-called.txt\"\n"
        "  if exist \"%~dp0strict-x509-fail.flag\" if /I not \"%4\"==\"compatibility\" (\n"
        "    if not exist \"%~dp0test-temp\\security-master\\invocation-current\\m8r06-01b-current\" mkdir \"%~dp0test-temp\\security-master\\invocation-current\\m8r06-01b-current\"\n"
        "    copy /Y \"%~dp0test-security-strict-evidence.json\" \"%~dp0test-temp\\security-master\\invocation-current\\m8r06-01b-current\\source_evidence_manifest.json\" >nul\n"
        "    echo diagnostic-prefix\n"
        "    type \"%~dp0test-security-strict-failure.json\"\n"
        "    exit /b 1\n"
        "  )\n"
        "  echo diagnostic-prefix\n"
        "  type \"%~dp0test-security-update.json\"\n"
        "  exit /b 0\n"
        ")\n"
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


def test_source_tree_cmd_fails_fast_with_actionable_package_message() -> None:
    if os.name != "nt":
        pytest.skip("P1-A3 launcher is Windows-only")
    result = subprocess.run(
        [str(CMD), "--no-pause"], capture_output=True, text=True, timeout=20, shell=False
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 2
    assert "Native package source template" in combined
    assert "root of a built or extracted TW-Market Native bundle" in combined
    assert "launcher\\tw-market-launcher.ps1" in combined


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


def test_launcher_v2_daily_surface_is_host_neutral() -> None:
    text = PS1.read_text(encoding="ascii")
    for required in (
        "Local Runtime", "Workbench", "Security Master", "Local MCP",
        "Ready for MCP clients", "tw-market-security-master.cmd",
        "Advanced / Technical Details",
    ):
        assert required in text
    for forbidden in (
        "D:\\MCP-Tunnel", "Local AI Tools Supervisor", "OpenAI Secure MCP Tunnel", "ChatGPT connector",
    ):
        assert forbidden not in text
    assert "Start MCP Server" not in text
    assert "Stop MCP Server" not in text


def test_product_version_is_read_from_packaged_metadata(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("NOT_RUNNING", False))
    probe = _run_function_probe(bundle, "Get-ProductVersion")
    assert probe.returncode == 0, probe.stderr + probe.stdout
    assert probe.stdout.strip() == "1.5.0"


def test_security_master_first_install_requires_explicit_confirmation(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("NOT_RUNNING", False))
    marker = bundle / "security-update-called.txt"
    status = _invoke(bundle, "SecurityStatus")
    assert status.returncode == 0, status.stderr + status.stdout
    assert json.loads(status.stdout)["status"] == "NOT_INITIALIZED"
    assert not marker.exists()

    blocked = _invoke(bundle, "SecurityUpdate")
    assert blocked.returncode == 1, blocked.stderr + blocked.stdout
    payload = json.loads(blocked.stdout)
    assert payload["status"] == "CONFIRMATION_REQUIRED"
    assert payload["reason_code"] == "SECURITY_MASTER_EXTERNAL_ACQUISITION"
    assert not marker.exists()

    accepted = _invoke(bundle, "SecurityUpdate", "-ConfirmSecurityNetwork")
    assert accepted.returncode == 0, accepted.stderr + accepted.stdout
    payload = json.loads(accepted.stdout)
    assert payload["status"] == "SECURITY_MASTER_UPDATE_COMPLETE"
    assert payload["data"]["mode"] == "INSTALL"
    assert payload["data"]["restart_required"] is True
    assert marker.read_text(encoding="ascii").strip() == "called"


def test_security_master_active_state_projects_update_mode(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("RUNNING", True, identity="ACTIVE"))
    (bundle / "test-security-status.json").write_text(
        json.dumps({"status": "ACTIVE", "release": {"release_id": "old-release"}}), encoding="utf-8"
    )
    result = _invoke(bundle, "SecurityUpdate", "-ConfirmSecurityNetwork")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "SECURITY_MASTER_UPDATE_COMPLETE"
    assert payload["data"]["mode"] == "UPDATE"
    assert payload["data"]["runtime_state"] == "RUNNING_READY"


def test_security_master_update_is_blocked_during_unstable_runtime_state(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("START_IN_PROGRESS", False))
    marker = bundle / "security-update-called.txt"
    result = _invoke(bundle, "SecurityUpdate", "-ConfirmSecurityNetwork")
    assert result.returncode == 1, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ACTION_BLOCKED"
    assert payload["reason_code"] == "SECURITY_MASTER_REQUIRES_STABLE_RUNTIME_STATE_STARTING"
    assert not marker.exists()


def test_security_update_parser_accepts_trailing_json_after_diagnostics(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("NOT_RUNNING", False))
    result = _invoke(bundle, "SecurityUpdate", "-ConfirmSecurityNetwork")
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout)["data"]["security_master"]["release_id"] == "test-release"


def test_security_master_strict_x509_failure_requires_explicit_compatibility_retry(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("NOT_RUNNING", False))
    (bundle / "strict-x509-fail.flag").write_text("1", encoding="ascii")

    strict = _invoke(bundle, "SecurityUpdate", "-ConfirmSecurityNetwork")
    assert strict.returncode == 1, strict.stderr + strict.stdout
    payload = json.loads(strict.stdout)
    assert payload["status"] == "SECURITY_MASTER_TLS_COMPATIBILITY_RETRY_AVAILABLE"
    assert payload["reason_code"] == "PYTHON_X509_STRICT_COMPATIBILITY"
    assert payload["data"]["compatibility"]["tls_verification"] == "enabled"
    assert payload["data"]["compatibility"]["hostname_verification"] == "enabled"
    assert "--ssl-policy" not in (bundle / "security-update-args.txt").read_text(encoding="ascii")

    unconfirmed = _invoke(bundle, "SecurityUpdate", "-ConfirmSecurityNetwork", "-ConfirmSecurityCompatibility")
    assert unconfirmed.returncode == 0, unconfirmed.stderr + unconfirmed.stdout
    accepted = json.loads(unconfirmed.stdout)
    assert accepted["status"] == "SECURITY_MASTER_UPDATE_COMPLETE"
    assert accepted["data"]["ssl_policy"] == "compatibility"
    assert "--ssl-policy compatibility" in (bundle / "security-update-args.txt").read_text(encoding="ascii")


def test_security_master_compatibility_policy_requires_second_confirmation(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("NOT_RUNNING", False))
    probe = _run_function_probe(
        bundle,
        r'''$result = Invoke-SecurityMasterUpdateAction -Confirmed -SslPolicy 'compatibility'
$result | ConvertTo-Json -Depth 12 -Compress
''',
    )
    assert probe.returncode == 0, probe.stderr + probe.stdout
    payload = json.loads(probe.stdout)
    assert payload["status"] == "CONFIRMATION_REQUIRED"
    assert payload["reason_code"] == "SECURITY_MASTER_TLS_COMPATIBILITY_RETRY"
    assert not (bundle / "security-update-called.txt").exists()


def test_non_x509_acquisition_failure_does_not_offer_tls_compatibility_retry(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("NOT_RUNNING", False))
    (bundle / "strict-x509-fail.flag").write_text("1", encoding="ascii")
    evidence = json.loads((bundle / "test-security-strict-evidence.json").read_text(encoding="utf-8"))
    evidence["source_probes"][1]["transport_reason_code"] = "NETWORK_TIMEOUT"
    (bundle / "test-security-strict-evidence.json").write_text(json.dumps(evidence), encoding="utf-8")

    result = _invoke(bundle, "SecurityUpdate", "-ConfirmSecurityNetwork")
    assert result.returncode == 1, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "SECURITY_MASTER_UPDATE_FAILED"
    assert payload["reason_code"] == "official_acquisition_or_qualification_failed"


def test_launcher_tls_retry_copy_is_explicit_verified_and_never_unsafe() -> None:
    text = PS1.read_text(encoding="ascii")
    assert "Retry with compatibility mode now?" in text
    assert "Certificate and hostname verification remain enabled" in text
    assert "-SslPolicy 'compatibility' -CompatibilityConfirmed" in text
    assert "unsafe-explicit" not in text

def test_restart_action_is_explicit_stop_then_start(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("RUNNING", True))
    probe = _run_function_probe(
        bundle,
        r'''
$script:Sequence = @()
function Get-LauncherSnapshot { return [pscustomobject]@{ status='RUNNING_READY'; data=$null } }
function Invoke-StopAction {
  $script:Sequence += 'stop'
  $script:CurrentSnapshot = [pscustomobject]@{ status='STOPPED'; data=$null }
  return New-LauncherResult -Status 'STOP_COMPLETE'
}
function Invoke-StartAction {
  $script:Sequence += 'start'
  $script:CurrentSnapshot = [pscustomobject]@{ status='RUNNING_READY'; data=$null }
  return New-LauncherResult -Status 'START_COMPLETE' -Data ([pscustomobject]@{ok=$true})
}
$result = Invoke-RestartAction
[pscustomobject]@{status=$result.status; sequence=$script:Sequence} | ConvertTo-Json -Compress
''',
    )
    assert probe.returncode == 0, probe.stderr + probe.stdout
    observed = json.loads(probe.stdout)
    assert observed == {"status": "RESTART_COMPLETE", "sequence": ["stop", "start"]}


def test_restart_action_fail_closes_before_start_when_stop_fails(tmp_path: Path) -> None:
    bundle = _fake_bundle(tmp_path, _payload("RUNNING", True))
    probe = _run_function_probe(
        bundle,
        r'''
$script:StartCalled = $false
function Get-LauncherSnapshot { return [pscustomobject]@{ status='RUNNING_READY'; data=$null } }
function Invoke-StopAction { return New-LauncherResult -Status 'STOP_FAILED' -ReasonCode 'synthetic' }
function Invoke-StartAction { $script:StartCalled = $true; return New-LauncherResult -Status 'START_COMPLETE' }
$result = Invoke-RestartAction
[pscustomobject]@{status=$result.status; reason=$result.reason_code; start_called=$script:StartCalled} | ConvertTo-Json -Compress
''',
    )
    assert probe.returncode == 0, probe.stderr + probe.stdout
    observed = json.loads(probe.stdout)
    assert observed["status"] == "RESTART_FAILED"
    assert observed["reason"] == "RESTART_STOP_FAILED"
    assert observed["start_called"] is False


def test_launcher_v2_incomplete_installation_does_not_offer_automatic_setup_repair() -> None:
    text = PS1.read_text(encoding="ascii")
    assert "$snapshot.status -in @('SETUP_REQUIRED','INSTALLATION_INCOMPLETE')" in text
    assert "$snapshot.status -eq 'SETUP_REQUIRED' -and $snapshot.reason_code" in text
    assert "Automatic repair is not performed" in text
    assert "$setupDoctorButton.Enabled = ($presence -eq 'PRESENT')" in text


def test_launcher_v2_security_update_notice_distinguishes_stopped_runtime() -> None:
    text = PS1.read_text(encoding="ascii")
    assert "elseif ($result.data.runtime_state -eq 'STOPPED')" in text
    assert "The new release will be used the next time TW-Market starts." in text
    assert "Restart TW-Market to use the new release." in text


def test_security_master_mutation_renders_updating_state_before_network_action() -> None:
    text = PS1.read_text(encoding="ascii")
    assert "& $setCardState $securityCard 'Updating...' 'info'" in text
    assert "$securityActionButton.Enabled = $false" in text
    assert "[System.Windows.Forms.Application]::DoEvents()" in text
