from __future__ import annotations

import json
import ssl
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

from scripts import manage_security_master
from scripts import ssl_policy

ROOT = Path(__file__).resolve().parents[2]
SKILL_SCRIPTS = ROOT / "skills" / "tw-security-master-classifier" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))
import probe_sources  # noqa: E402


def test_security_master_policy_selection_is_strict_by_default_and_explicit(monkeypatch):
    monkeypatch.setenv(ssl_policy.SSL_POLICY_ENV_VAR, "compatibility")
    assert manage_security_master._select_security_master_ssl_policy() == "strict"
    assert manage_security_master._select_security_master_ssl_policy("strict") == "strict"
    assert manage_security_master._select_security_master_ssl_policy("compatibility") == "compatibility"


@pytest.mark.parametrize("value", ["unknown", "unsafe-explicit"])
def test_invalid_or_unsafe_security_master_policy_is_rejected(value):
    with pytest.raises(ValueError):
        manage_security_master._select_security_master_ssl_policy(value)


def test_compatibility_context_keeps_verification_and_only_clears_strict_flag():
    context = ssl_policy.build_ssl_context(ssl_policy.SSL_POLICY_COMPATIBILITY)
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    if hasattr(ssl, "VERIFY_X509_STRICT") and hasattr(context, "verify_flags"):
        default_flags = ssl.create_default_context().verify_flags
        assert context.verify_flags == default_flags & ~ssl.VERIFY_X509_STRICT


def test_strict_policy_preserves_skill_strict_default():
    assert ssl_policy.build_ssl_context(ssl_policy.SSL_POLICY_STRICT) is None
    context = ssl.create_default_context()
    probe_sources._validate_ssl_context(context)
    assert context.verify_flags == ssl.create_default_context().verify_flags


@pytest.mark.parametrize(
    "failure_mode", ["cert-none", "hostname-disabled"]
)
def test_unverified_or_hostname_disabled_context_rejected_before_dispatch(
    monkeypatch, failure_mode
):
    context = ssl.create_default_context()
    if failure_mode == "cert-none":
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context.check_hostname = False
    budget = probe_sources.BootstrapDispatchBudget(2)

    def unexpected_opener(*_args, **_kwargs):
        pytest.fail("invalid TLS context reached opener construction")

    monkeypatch.setattr(probe_sources.urllib.request, "build_opener", unexpected_opener)
    with pytest.raises(ValueError, match="BOOTSTRAP_SSL_CONTEXT_VERIFICATION_REQUIRED"):
        probe_sources.probe(
            "https://example.test/source",
            ["example.test"],
            dispatch_budget=budget,
            ssl_context=context,
        )
    assert budget.used_dispatches == 0


def test_non_ssl_context_rejected_before_dispatch():
    with pytest.raises(ValueError, match="BOOTSTRAP_SSL_CONTEXT_TYPE_REJECTED"):
        probe_sources.probe(
            "https://example.test/source", ["example.test"], ssl_context=object()
        )


@pytest.mark.parametrize(
    ("reason", "expected_code", "reason_class", "transport_class"),
    [
        (
            ssl.SSLCertVerificationError(1, "Missing Subject Key Identifier"),
            "PYTHON_X509_STRICT_COMPATIBILITY",
            "SSLCertVerificationError",
            "tls_certificate_verification",
        ),
        (TimeoutError("bounded timeout"), "NETWORK_TIMEOUT", "TimeoutError", "timeout"),
        (OSError("C:\\private\\path must not be persisted"), "NETWORK_ERROR", "OSError", "network"),
    ],
)
def test_transport_errors_have_sanitized_classification(
    monkeypatch, reason, expected_code, reason_class, transport_class
):
    captured = {}

    class FailingOpener:
        def open(self, _request, timeout):
            captured["timeout"] = timeout
            raise urllib.error.URLError(reason)

    def fake_build_opener(_redirect_handler, https_handler):
        captured["context"] = https_handler._context
        return FailingOpener()

    monkeypatch.setattr(probe_sources.urllib.request, "build_opener", fake_build_opener)
    context = ssl.create_default_context()
    budget = probe_sources.BootstrapDispatchBudget(2)
    result = probe_sources.probe(
        "https://example.test/source",
        ["example.test"],
        dispatch_budget=budget,
        ssl_context=context,
    )

    assert result["acquisition_status"] == "network_error"
    assert result["error_type"] == "URLError"
    assert result["transport_outer_error_class"] == "URLError"
    assert result["transport_error_class"] == transport_class
    assert result["transport_reason_class"] == reason_class
    assert result["transport_reason_code"] == expected_code
    assert result["dispatch_reservations"] == 1
    assert captured["context"] is context
    assert "private" not in json.dumps(result)
    assert "error" not in result


def test_materializer_parser_rejects_unsafe_policy_before_acquisition():
    with pytest.raises(SystemExit):
        from scripts import m8r_06_01b_materialize_production_inputs as materializer

        materializer.main(["--ssl-policy", "unsafe-explicit"])


def test_manager_cli_rejects_unsafe_policy_before_lifecycle_or_network():
    with pytest.raises(SystemExit):
        manage_security_master.main(["update", "--live", "--ssl-policy", "unsafe-explicit"])


def test_manager_rejects_ssl_policy_outside_live_update():
    with pytest.raises(SystemExit):
        manage_security_master.main(["status", "--ssl-policy", "compatibility"])


@pytest.mark.parametrize("root_present,skill_present", [(True, False), (False, False), (True, True)])
def test_materializer_preserves_caller_owned_sys_path(root_present, skill_present):
    code = r'''
import importlib, json, runpy, sys
from pathlib import Path
root = Path(sys.argv[1])
skill = str(root / "skills/tw-security-master-classifier/scripts")
sentinel = r"C:\twmarket_temp\SENTINEL"
unrelated = r"C:\twmarket_temp\UNRELATED"
root_present, skill_present = json.loads(sys.argv[2])
base = [p for p in sys.path if p and p not in {str(root), skill}]
sys.path[:] = [sentinel, unrelated, *base]
if root_present:
    sys.path.append(str(root))
if skill_present:
    sys.path.append(skill)
caller_paths = list(sys.path)
if root_present:
    module = importlib.import_module("scripts.m8r_06_01b_materialize_production_inputs")
    assert module.ROOT == root
else:
    namespace = runpy.run_path(str(root / "scripts/m8r_06_01b_materialize_production_inputs.py"))
    assert namespace["ROOT"] == root
assert sys.path[:2] == [sentinel, unrelated], sys.path[:2]
assert all(sys.path.count(p) == caller_paths.count(p) for p in caller_paths)
assert [p for p in sys.path if p in caller_paths] == caller_paths
assert sys.path.count(str(root)) == int(root_present)
assert sys.path.count(skill) == int(skill_present)
'''
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code, str(ROOT), json.dumps([root_present, skill_present])],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
