from __future__ import annotations

import socket
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import operator_workbench
from scripts import verify_dependency_supply_chain as verifier
from scripts.verify_environment import SUPPORTED

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_DOCS = (
    "README.md",
    "README.zh-TW.md",
    "docs/operator/QUICK_START.md",
    "docs/operator/LOCAL_WORKBENCH.md",
    "docs/operator/TROUBLESHOOTING.md",
    "docs/runbooks/DEVELOPER_ONBOARDING_LOCAL_FIRST.md",
)
ACTIVE_EXECUTION_FILES = (
    "server/services/unified_mode_b2_execution.py",
    "scripts/tw_market_lifecycle.py",
    "scripts/operator_workbench.py",
    "scripts/run_unified_market_evidence_mcp.py",
    "scripts/run_unified_workbench.py",
    "scripts/verify_environment.py",
)


def _write_manifests(root: Path, *, direct: str = "requests>=2.31\nmcp==1.29.0\n", lock: str = "requests==2.34.2\nmcp==1.29.0\n", browser: str = "-r requirements-lock.txt\nplaywright==1.55.0\n") -> None:
    (root / "requirements.txt").write_text(direct, encoding="utf-8")
    (root / "requirements-lock.txt").write_text(lock, encoding="utf-8")
    (root / "requirements-browser-e2e.txt").write_text(browser, encoding="utf-8")


def test_checked_in_dependency_authorities_pass_offline() -> None:
    assert verifier.validate(ROOT)["status"] == "PASS"


def test_direct_policy_members_are_all_locked() -> None:
    report = verifier.validate(ROOT)
    assert report["direct_count"] == 11
    assert not any(error.startswith("direct_requirement_missing_from_lock:") for error in report["errors"])


def test_locked_exact_versions_satisfy_direct_specifiers() -> None:
    assert not any(error.startswith("locked_version_outside_direct_policy:") for error in verifier.validate(ROOT)["errors"])


def test_duplicate_lock_package_is_rejected(tmp_path: Path) -> None:
    _write_manifests(tmp_path, lock="requests==2.34.2\nRequests==2.34.2\nmcp==1.29.0\n")
    assert "duplicate_lock_package:requests" in verifier.validate(tmp_path)["errors"]


def test_missing_lock_pin_fails_closed_without_exception(tmp_path: Path) -> None:
    _write_manifests(tmp_path, lock="requests\nmcp==1.29.0\n")
    report = verifier.validate(tmp_path)
    assert report["status"] == "FAIL"
    assert "lock_not_exact_pin:requests" in report["errors"]


def test_invalid_pep508_lock_marker_is_rejected(tmp_path: Path) -> None:
    _write_manifests(tmp_path, lock="requests==2.34.2; python_version ==\nmcp==1.29.0\n")
    report = verifier.validate(tmp_path)
    assert report["status"] == "FAIL"
    assert any(error.startswith("requirements-lock.txt:") and error.endswith(":invalid_requirement") for error in report["errors"])


@pytest.mark.parametrize("bad_line", ["requests @ https://example.invalid/a.whl", "git+https://example.invalid/repo.git", "-e ./local-package", "--extra-index-url https://example.invalid/simple"])
def test_urls_vcs_editables_and_custom_indexes_are_rejected(tmp_path: Path, bad_line: str) -> None:
    _write_manifests(tmp_path, direct=f"{bad_line}\nmcp==1.29.0\n")
    assert verifier.validate(tmp_path)["status"] == "FAIL"


def test_mcp_exact_pin_is_preserved_in_direct_and_lock_authorities() -> None:
    assert "mcp==1.29.0" in (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "mcp==1.29.0" in (ROOT / "requirements-lock.txt").read_text(encoding="utf-8")


def test_browser_extra_inherits_core_lock() -> None:
    lines = (ROOT / "requirements-browser-e2e.txt").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "-r requirements-lock.txt"
    assert "-r requirements.txt" not in lines


def test_playwright_remains_exactly_pinned() -> None:
    assert "playwright==1.55.0" in (ROOT / "requirements-browser-e2e.txt").read_text(encoding="utf-8")


def test_active_install_guidance_allowlist_uses_locked_core() -> None:
    for relative in ACTIVE_DOCS:
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert "pip install -r requirements.txt" not in content, relative
    for relative in ("README.md", "README.zh-TW.md", "docs/operator/QUICK_START.md", "docs/operator/TROUBLESHOOTING.md", "docs/runbooks/DEVELOPER_ONBOARDING_LOCAL_FIRST.md"):
        assert "requirements-lock.txt" in (ROOT / relative).read_text(encoding="utf-8")


def test_operator_remediation_uses_lock_authority() -> None:
    suggestions = [check.suggestion for check in operator_workbench.environment_checks()]
    assert any("requirements-lock.txt" in value for value in suggestions)
    assert not any("requirements.txt" in value for value in suggestions)


def test_operator_workbench_reports_current_unified_mcp_entrypoint() -> None:
    assert operator_workbench.status_report()["mcp_command"] == "python scripts/run_unified_market_evidence_mcp.py --startup-check"


def test_operator_python_support_matches_canonical_environment_verifier() -> None:
    assert SUPPORTED == {(3, 11), (3, 13)}
    check = next(item for item in operator_workbench.environment_checks() if item.name == "Python version")
    assert "CPython 3.11 or CPython 3.13" in check.suggestion


@pytest.mark.parametrize("relative", ACTIVE_EXECUTION_FILES)
def test_internal_python_child_processes_are_fixed(relative: str) -> None:
    content = (ROOT / relative).read_text(encoding="utf-8")
    if relative in {"server/services/unified_mode_b2_execution.py", "scripts/tw_market_lifecycle.py"}:
        assert "sys.executable" in content
    assert "shell=True" not in content


def test_mode_b2_uses_fixed_repo_local_execute_once_wrapper() -> None:
    from server.services import unified_mode_b2_execution as mode_b2

    assert mode_b2.WRAPPER == ROOT / "scripts" / "m8r_06_03_execute_once.py"
    source = (ROOT / "server/services/unified_mode_b2_execution.py").read_text(encoding="utf-8")
    assert "sys.executable, str(WRAPPER)" in source


@pytest.mark.parametrize("field", ["executable", "script", "module", "shell", "command", "cmd"])
def test_mode_b2_caller_cannot_select_executable_or_entrypoint(field: str) -> None:
    from server.services.unified_mode_b2 import ModeB2Error
    from server.services.unified_mode_b2_execution import execute_mode_b2_once

    with pytest.raises(ModeB2Error, match="privileged_field_forbidden"):
        execute_mode_b2_once({field: "attacker-choice"})


def test_lifecycle_child_targets_are_repo_owned_and_timeout_bounded() -> None:
    source = (ROOT / "scripts/tw_market_lifecycle.py").read_text(encoding="utf-8")
    assert "sys.executable, str(ROOT / \"scripts\" / \"manage_security_master.py\")" in source
    assert "sys.executable, str(ROOT / \"scripts\" / \"run_unified_workbench.py\")" in source
    assert "sys.executable, str(ROOT / \"scripts\" / \"verify_environment.py\")" in source
    assert "sys.executable, str(ROOT / \"scripts\" / \"run_unified_market_evidence_mcp.py\")" in source
    assert "sys.executable, \"-m\", \"scripts.tw_market_lifecycle\"" in source
    assert "timeout=" in source


@pytest.mark.parametrize("args", [["branch", "--show-current"], ["rev-parse", "--short", "HEAD"]])
def test_operator_git_metadata_uses_only_fixed_read_only_calls(args: list[str]) -> None:
    with patch.object(operator_workbench.subprocess, "check_output", return_value="ok\n") as call:
        assert operator_workbench.git_value(args) == "ok"
    command = call.call_args.args[0]
    assert command == ["git", *args]
    assert call.call_args.kwargs["timeout"] > 0
    assert "--show-toplevel" not in command


def test_operator_git_helper_rejects_arbitrary_arguments_before_process_launch() -> None:
    with patch.object(operator_workbench.subprocess, "check_output") as call:
        assert operator_workbench.git_value(["config", "--global", "user.name"]) == "unknown"
    call.assert_not_called()


def test_current_unified_path_has_no_generic_user_selected_plugin_loader() -> None:
    source = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in ACTIVE_EXECUTION_FILES if path != "scripts/verify_environment.py")
    assert "import_module(" not in source
    assert "__import__(" not in source
    assert "plugin_path" not in source


def test_active_runtime_has_no_package_manager_or_browser_installer_invocation() -> None:
    for relative in ACTIVE_EXECUTION_FILES:
        content = (ROOT / relative).read_text(encoding="utf-8").lower()
        assert "subprocess.run([\"pip\"" not in content, relative
        assert "subprocess.popen([\"pip\"" not in content, relative
        assert "subprocess.run([\"playwright\"" not in content, relative


def test_supply_chain_validator_is_read_only_and_declares_no_network() -> None:
    source = (ROOT / "scripts/verify_dependency_supply_chain.py").read_text(encoding="utf-8")
    with patch.object(socket, "socket", side_effect=AssertionError("socket use forbidden")):
        assert verifier.validate(ROOT)["status"] == "PASS"
    assert "requests." not in source
    assert "urllib.request" not in source


def test_lock_provenance_metadata_is_preserved() -> None:
    header = "\n".join((ROOT / "requirements-lock.txt").read_text(encoding="utf-8").splitlines()[:2])
    assert "CPython 3.11.15" in header
    assert "Windows 11 x86_64" in header
    assert "pip 26.2.1" in header
