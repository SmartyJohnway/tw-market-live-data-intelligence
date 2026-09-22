"""Canonical JSON and hash utilities for M8R-05C.

Re-uses the single authoritative canonicalization implementation from
scripts/m8r_05b_03/canonical.py.  Do NOT add a second canonicalization
algorithm.
"""
from __future__ import annotations

# Re-export from the single authoritative implementation.
from scripts.m8r_05b_03.canonical import canonical_json, sha256_json  # noqa: F401

_RESULT_ID_PREFIX = "umeresult-v1-"
_RESULT_V2_ID_PREFIX = "umeresult-v2-"
_RESULT_V3_ID_PREFIX = "umeresult-v3-"
_AUDIT_PACKAGE_ID_PREFIX = "umeap-v1-"
_AUDIT_V2_ID_PREFIX = "umeap-v2-"
_AUDIT_V3_ID_PREFIX = "umeap-v3-"
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


def build_result_id_v1(request_id: str, receipt_id: str, bundle_id: str) -> str:
    return build_result_id(request_id, receipt_id, bundle_id)


def build_result_id_v2(request_id: str, receipt_id: str, bundle_id: str) -> str:
    identity_scope = {"request_id": request_id, "receipt_id": receipt_id, "bundle_id": bundle_id}
    return _RESULT_V2_ID_PREFIX + sha256_json(identity_scope)[:_HASH_PREFIX_LEN]


def build_result_id_v3(request_id: str, receipt_id: str, bundle_id: str) -> str:
    """Build the explicit V3 identity from the established result scope."""
    identity_scope = {"request_id": request_id, "receipt_id": receipt_id, "bundle_id": bundle_id}
    return _RESULT_V3_ID_PREFIX + sha256_json(identity_scope)[:_HASH_PREFIX_LEN]


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


def build_audit_package_id_v1(result_id: str, bundle_id: str) -> str:
    return build_audit_package_id(result_id, bundle_id)


def build_audit_package_id_v2(result_id: str, bundle_id: str) -> str:
    identity_scope = {"result_id": result_id, "bundle_id": bundle_id}
    return _AUDIT_V2_ID_PREFIX + sha256_json(identity_scope)[:_HASH_PREFIX_LEN]


def build_audit_package_id_v3(result_id: str, bundle_id: str) -> str:
    """Build the explicit V3 audit identity from the established audit scope."""
    identity_scope = {"result_id": result_id, "bundle_id": bundle_id}
    return _AUDIT_V3_ID_PREFIX + sha256_json(identity_scope)[:_HASH_PREFIX_LEN]


def hash_body_excluding_key(body: dict, exclude_key: str) -> str:
    """SHA-256 of the canonical body with one key excluded.

    Used to produce result_hash and audit_package_hash without circular
    reference.
    """
    trimmed = {k: v for k, v in body.items() if k != exclude_key}
    return sha256_json(trimmed)
