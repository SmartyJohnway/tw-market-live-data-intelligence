"""Count and block external sockets during the bounded R4 offline gate."""
import ipaddress
import os
import socket


def _is_loopback(host):
    if isinstance(host, bytes):
        host = host.decode("ascii", "ignore")
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return str(host).casefold() == "localhost"


def _block_external(host):
    if _is_loopback(host):
        return
    counter = os.environ.get("PHASE_L_A6_R4_NETWORK_ATTEMPTS_FILE")
    if counter:
        with open(counter, "a", encoding="utf-8") as stream:
            stream.write("external\n")
    raise OSError("external network denied by L3-A6-P0-R4 offline gate")


_getaddrinfo = socket.getaddrinfo
_connect = socket.socket.connect
_connect_ex = socket.socket.connect_ex
_create_connection = socket.create_connection


def _guard_getaddrinfo(host, *args, **kwargs):
    _block_external(host)
    return _getaddrinfo(host, *args, **kwargs)


def _guard_connect(self, address):
    _block_external(address[0] if isinstance(address, tuple) and address else address)
    return _connect(self, address)


def _guard_connect_ex(self, address):
    _block_external(address[0] if isinstance(address, tuple) and address else address)
    return _connect_ex(self, address)


def _guard_create_connection(address, *args, **kwargs):
    _block_external(address[0] if isinstance(address, tuple) and address else address)
    return _create_connection(address, *args, **kwargs)


socket.getaddrinfo = _guard_getaddrinfo
socket.socket.connect = _guard_connect
socket.socket.connect_ex = _guard_connect_ex
socket.create_connection = _guard_create_connection
