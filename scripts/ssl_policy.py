from __future__ import annotations

import os
import platform
import ssl
import sys
from typing import Any

SSL_POLICY_ENV_VAR = "TW_MARKET_SSL_POLICY"
SSL_POLICY_STRICT = "strict"
SSL_POLICY_COMPATIBILITY = "compatibility"
SSL_POLICY_UNSAFE = "unsafe-explicit"
VALID_SSL_POLICIES = {SSL_POLICY_STRICT, SSL_POLICY_COMPATIBILITY, SSL_POLICY_UNSAFE}


def validate_ssl_policy(value: str | None) -> str:
    policy = (value or SSL_POLICY_STRICT).strip().lower()
    if policy not in VALID_SSL_POLICIES:
        raise ValueError(f"Invalid ssl policy {value!r}. Expected one of: {', '.join(sorted(VALID_SSL_POLICIES))}.")
    return policy


def resolve_ssl_policy(cli_policy: str | None = None, environ: dict[str, str] | None = None) -> str:
    if cli_policy not in (None, ""):
        return validate_ssl_policy(cli_policy)
    env = os.environ if environ is None else environ
    return validate_ssl_policy(env.get(SSL_POLICY_ENV_VAR))


def build_ssl_context(policy: str | None = None) -> ssl.SSLContext | None:
    selected = validate_ssl_policy(policy)
    if selected == SSL_POLICY_STRICT:
        return None
    if selected == SSL_POLICY_UNSAFE:
        return ssl._create_unverified_context()  # explicit unsafe operator opt-in only
    context = ssl.create_default_context()
    if hasattr(ssl, "VERIFY_X509_STRICT") and hasattr(context, "verify_flags"):
        context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return context


def tls_verification_mode(policy: str | None = None) -> str:
    selected = validate_ssl_policy(policy)
    if selected == SSL_POLICY_STRICT:
        return "default_verified_tls"
    if selected == SSL_POLICY_COMPATIBILITY:
        return "verified_tls_compatibility_context"
    return "unverified_tls_operator_explicit"


def ssl_policy_diagnostics(policy: str | None = None, *, network_calls_may_have_occurred: bool = False) -> dict[str, Any]:
    selected = validate_ssl_policy(policy)
    return {
        "ssl_policy": selected,
        "selected": selected,
        "tls_verification_mode": tls_verification_mode(selected),
        "strict_default": True,
        "compatibility_mode_used": selected == SSL_POLICY_COMPATIBILITY,
        "unsafe_mode_used": selected == SSL_POLICY_UNSAFE,
        "silent_tls_fallback": False,
        "network_calls_may_have_occurred": network_calls_may_have_occurred,
        "warning": ("UNSAFE EXPLICIT TLS POLICY: certificate verification is disabled for this bounded command only." if selected == SSL_POLICY_UNSAFE else None),
    }


def platform_ssl_diagnostics(cli_policy: str | None = None, environ: dict[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    configured = env.get(SSL_POLICY_ENV_VAR)
    try:
        effective = resolve_ssl_policy(cli_policy, env)
        policy_error = None
    except ValueError as exc:
        effective = "invalid"
        policy_error = str(exc)
    paths = ssl.get_default_verify_paths()
    is_windows = platform.system().lower() == "windows"
    is_py313 = sys.version_info[:2] == (3, 13)
    return {
        "os_platform": platform.platform(),
        "python_version": platform.python_version(),
        "python_313_detected": is_py313,
        "windows_detected": is_windows,
        "ssl_default_verify_paths": {
            "cafile": paths.cafile,
            "capath": paths.capath,
            "openssl_cafile_env": paths.openssl_cafile_env,
            "openssl_cafile": paths.openssl_cafile,
            "openssl_capath_env": paths.openssl_capath_env,
            "openssl_capath": paths.openssl_capath,
        },
        "configured_tw_market_ssl_policy": configured,
        "effective_ssl_policy": effective,
        "ssl_policy_error": policy_error,
        "operator_hint": (
            "If TWSE MIS TLS fails on Windows/Python 3.13, retry only the explicit bounded live command with --ssl-policy compatibility. Do not use unsafe-explicit unless you understand TLS verification is disabled."
            if is_windows and is_py313 else
            "Strict TLS remains default. Use --ssl-policy compatibility only for explicit bounded live commands when diagnosing known certificate compatibility failures. Do not use unsafe-explicit unless you understand TLS verification is disabled."
        ),
        "network_calls": False,
    }
