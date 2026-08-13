"""Focused M8R-08B test-only outbound socket containment."""
from __future__ import annotations

import ipaddress
import socket

import pytest


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
