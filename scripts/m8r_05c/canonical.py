"""Canonical JSON and hash utilities for M8R-05C.

Re-uses the single authoritative canonicalization implementation from
scripts/m8r_05b_03/canonical.py.  Do NOT add a second canonicalization
algorithm.
"""
from __future__ import annotations

# Re-export from the single authoritative implementation.
from scripts.m8r_05b_03.canonical import canonical_json, sha256_json  # noqa: F401

_RESULT_ID_PREFIX = "umeresult-v1-"
_AUDIT_PACKAGE_ID_PREFIX = "umeap-v1-"
_HASH_PREFIX_LEN = 20


def build_result_id(request_id: str, receipt_id: str, bundle_id: str) -> str:
    """Deterministic result identity.

    Computed from the three durable artifact identities.  Pure function —
    no network, no clock, no side effects.
    """
    identity_scope = {
        "request_id": request_id,
        "receipt_id": receipt_id,
        "bundle_id": bundle_id,
    }
    digest = sha256_json(identity_scope)
    return _RESULT_ID_PREFIX + digest[:_HASH_PREFIX_LEN]


def build_audit_package_id(result_id: str, bundle_id: str) -> str:
    """Deterministic audit package identity.

    Computed from result_id (which already embeds bundle_id) plus the
    raw bundle_id to keep the scope explicit.  Pure function.
    """
    identity_scope = {
        "result_id": result_id,
        "bundle_id": bundle_id,
    }
    digest = sha256_json(identity_scope)
    return _AUDIT_PACKAGE_ID_PREFIX + digest[:_HASH_PREFIX_LEN]


def hash_body_excluding_key(body: dict, exclude_key: str) -> str:
    """SHA-256 of the canonical body with one key excluded.

    Used to produce result_hash and audit_package_hash without circular
    reference.
    """
    trimmed = {k: v for k, v in body.items() if k != exclude_key}
    return sha256_json(trimmed)
