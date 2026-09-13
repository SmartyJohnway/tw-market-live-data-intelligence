"""Focused M8R-08B test-only outbound socket containment."""
from __future__ import annotations

import ipaddress
import json
import socket
from pathlib import Path

import pytest


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_V1_PREFLIGHT_PATH = (
    _REPOSITORY_ROOT
    / "docs"
    / "reviews"
    / "V1_0_RELEASE_READINESS_AND_PUBLIC_CONTRACT_FREEZE_PREFLIGHT.json"
)
_HISTORICAL_REPLAY_CATEGORIES = frozenset(
    {
        "D_HISTORICAL_FIXTURE_PROVENANCE_DEBT",
        "E_LEGACY_COMPONENT_OUTSIDE_V1_PRODUCT",
        "G_DUPLICATE_OBSOLETE_TEST",
    }
)


def _v1_historical_replay_nodes() -> dict[str, str]:
    """Return only preflight-classified historical replay nodes.

    This is deliberately an exact node-id mapping, rather than a directory
    exclusion or blanket xfail. The original test remains runnable with
    ``-m historical`` and its immutable/provenance failure remains visible.
    """
    review = json.loads(_V1_PREFLIGHT_PATH.read_text(encoding="utf-8"))
    nodes: dict[str, str] = {}
    for family in review["failure_families"]:
        if family["category"] not in _HISTORICAL_REPLAY_CATEGORIES:
            continue
        family_id = family["id"]
        for node_id in family["nodes"]:
            nodes[node_id] = family_id
    return nodes


_V1_HISTORICAL_REPLAY_NODES = _v1_historical_replay_nodes()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Classify preflight-frozen replay fixtures outside active V1 gates."""
    for item in items:
        family = _V1_HISTORICAL_REPLAY_NODES.get(item.nodeid)
        if family is not None:
            item.add_marker(pytest.mark.historical(reason=f"V1 preflight: {family}"))


def _loopback_destination(address: object) -> bool:
    if not isinstance(address, tuple) or not address:
        return False
    host = address[0]
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def _m8r_08b_non_loopback_network_guard(request, monkeypatch):
    """Fail synthetic external socket attempts before any connection is made."""
    if "m8r_08b_mcp" not in request.node.nodeid:
        yield
        return
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def guarded_connect(sock, address):
        if not _loopback_destination(address):
            raise AssertionError("m8r_08b_non_loopback_socket_blocked")
        return original_connect(sock, address)

    def guarded_connect_ex(sock, address):
        if not _loopback_destination(address):
            raise AssertionError("m8r_08b_non_loopback_socket_blocked")
        return original_connect_ex(sock, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    yield
