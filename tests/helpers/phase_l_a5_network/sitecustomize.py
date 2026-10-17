"""Block and count non-loopback socket attempts during the A5 offline gate."""
from __future__ import annotations

import ipaddress
import json
import os
import socket
from pathlib import Path

_counter = Path(os.environ["A5_NETWORK_COUNTER_FILE"])
_count = 0


def _is_loopback(address: object) -> bool:
    if not isinstance(address, tuple) or not address:
        return False
    try:
        return ipaddress.ip_address(address[0]).is_loopback
    except ValueError:
        return address[0] == "localhost"


def _deny(address: object) -> None:
    global _count
    if _is_loopback(address):
        return
    _count += 1
    _counter.write_text(json.dumps({"external_socket_attempts": _count}), encoding="utf-8")
    raise OSError("A5_EXTERNAL_NETWORK_BLOCKED")


_connect = socket.socket.connect
_connect_ex = socket.socket.connect_ex
_create_connection = socket.create_connection


def _guard_connect(self, address):
    _deny(address)
    return _connect(self, address)


def _guard_connect_ex(self, address):
    _deny(address)
    return _connect_ex(self, address)


def _guard_create_connection(address, *args, **kwargs):
    _deny(address)
    return _create_connection(address, *args, **kwargs)


socket.socket.connect = _guard_connect
socket.socket.connect_ex = _guard_connect_ex
socket.create_connection = _guard_create_connection
