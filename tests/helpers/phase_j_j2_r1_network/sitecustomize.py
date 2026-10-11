import ipaddress
import socket

_original_getaddrinfo = socket.getaddrinfo
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_original_create_connection = socket.create_connection


def _is_loopback_host(host):
    if isinstance(host, bytes):
        host = host.decode("ascii", "ignore")
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return str(host).casefold() in {"localhost"}


def _guard_getaddrinfo(host, *args, **kwargs):
    if not _is_loopback_host(host):
        raise OSError("external network denied by J2-R1 test guard")
    return _original_getaddrinfo(host, *args, **kwargs)


def _address_host(address):
    return address[0] if isinstance(address, tuple) and address else address


def _guard_connect(self, address):
    if not _is_loopback_host(_address_host(address)):
        raise OSError("external network denied by J2-R1 test guard")
    return _original_connect(self, address)


def _guard_connect_ex(self, address):
    if not _is_loopback_host(_address_host(address)):
        raise OSError("external network denied by J2-R1 test guard")
    return _original_connect_ex(self, address)


def _guard_create_connection(address, *args, **kwargs):
    if not _is_loopback_host(_address_host(address)):
        raise OSError("external network denied by J2-R1 test guard")
    return _original_create_connection(address, *args, **kwargs)


socket.getaddrinfo = _guard_getaddrinfo
socket.socket.connect = _guard_connect
socket.socket.connect_ex = _guard_connect_ex
socket.create_connection = _guard_create_connection
