from __future__ import annotations

import ipaddress
import os
from collections.abc import Sequence
from pathlib import Path
import socket
from typing import Any

from starlette.responses import JSONResponse


ERROR_CODE = "local_service_loopback_required"
NETWORK_PROFILE_ENV = "TW_MARKET_NETWORK_PROFILE"
DOCKER_PROFILE = "docker-local-service"
DOCKER_GATEWAY_ENV = "TW_MARKET_DOCKER_GATEWAY_IP"
DOCKER_SUBNET_ENV = "TW_MARKET_DOCKER_SUBNET"


def _host_from_address(address: Any) -> str | None:
    """Return the host component of an ASGI address tuple when present."""
    if not isinstance(address, Sequence) or isinstance(address, (str, bytes)) or not address:
        return None
    host = address[0]
    return host if isinstance(host, str) else None


def is_loopback_network_scope(scope: dict[str, Any]) -> bool:
    """Allow in-process non-IP scopes and require every known IP endpoint to loop back.

    ASGI transports may use synthetic non-IP identities. Those identities do not
    prove a reachable socket and are treated as in-process. Parseable IP values
    are network evidence, and any non-loopback client or server address fails
    closed. A locally trusted ASGI server can still lie about its scope; this is
    not an authentication boundary against a dishonest local server.
    """
    known_ip_addresses = []
    for key in ("client", "server"):
        host = _host_from_address(scope.get(key))
        if host is None:
            continue
        try:
            known_ip_addresses.append(ipaddress.ip_address(host))
        except ValueError:
            continue
    return all(address.is_loopback for address in known_ip_addresses)


def _default_ipv4_subnet(route_file: Path = Path("/proc/net/route")) -> str:
    try:
        rows = route_file.read_text(encoding="ascii").splitlines()[1:]
        routes = []
        for row in rows:
            fields = row.split()
            if len(fields) < 8 or fields[1] == "00000000" or fields[2] != "00000000":
                continue
            destination = socket.inet_ntoa(bytes.fromhex(fields[1])[::-1])
            mask = socket.inet_ntoa(bytes.fromhex(fields[7])[::-1])
            network = ipaddress.IPv4Network((destination, mask), strict=False)
            if network.prefixlen:
                routes.append(network)
        if routes:
            return str(max(routes, key=lambda item: item.prefixlen))
    except (OSError, ValueError, IndexError):
        pass
    raise RuntimeError("docker_network_subnet_unavailable")


def is_docker_local_network_scope(scope: dict[str, Any], gateway: str, subnet: str) -> bool:
    """Accept only the Docker bridge gateway reaching a container address."""
    client_host = _host_from_address(scope.get("client"))
    server_host = _host_from_address(scope.get("server"))
    if client_host is None or server_host is None:
        return False
    try:
        client = ipaddress.ip_address(client_host)
        server = ipaddress.ip_address(server_host)
        expected_gateway = ipaddress.IPv4Address(gateway)
        expected_subnet = ipaddress.ip_network(subnet, strict=True)
    except ValueError:
        return False
    private_networks = (
        ipaddress.IPv4Network("10.0.0.0/8"),
        ipaddress.IPv4Network("172.16.0.0/12"),
        ipaddress.IPv4Network("192.168.0.0/16"),
    )
    return (
        isinstance(client, ipaddress.IPv4Address)
        and isinstance(server, ipaddress.IPv4Address)
        and isinstance(expected_subnet, ipaddress.IPv4Network)
        and expected_subnet.prefixlen <= 30
        and any(expected_subnet.subnet_of(private) for private in private_networks)
        and client == expected_gateway
        and expected_gateway in expected_subnet
        and server in expected_subnet
    )


class LocalNetworkBoundaryMiddleware:
    """Enforce native loopback or the explicit Docker bridge profile."""

    def __init__(self, app, *, network_profile: str | None = None,
                 docker_gateway: str | None = None, docker_subnet: str | None = None):
        self.app = app
        self.network_profile = network_profile if network_profile is not None else os.environ.get(NETWORK_PROFILE_ENV)
        self.docker_gateway = None
        self.docker_subnet = None
        if self.network_profile == DOCKER_PROFILE:
            self.docker_gateway = docker_gateway or os.environ.get(DOCKER_GATEWAY_ENV) or _default_ipv4_gateway()
            self.docker_subnet = docker_subnet or os.environ.get(DOCKER_SUBNET_ENV) or _default_ipv4_subnet()
            try:
                gateway = ipaddress.IPv4Address(self.docker_gateway)
                subnet = ipaddress.ip_network(self.docker_subnet, strict=True)
            except ValueError as exc:
                raise RuntimeError("docker_network_gateway_invalid") from exc
            private_networks = (ipaddress.IPv4Network("10.0.0.0/8"),
                                ipaddress.IPv4Network("172.16.0.0/12"),
                                ipaddress.IPv4Network("192.168.0.0/16"))
            if (not isinstance(subnet, ipaddress.IPv4Network) or subnet.prefixlen > 30
                    or gateway not in subnet
                    or not any(subnet.subnet_of(private) for private in private_networks)):
                raise RuntimeError("docker_network_gateway_invalid")
        elif self.network_profile not in (None, ""):
            raise RuntimeError("network_profile_invalid")

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        allowed = (
            is_loopback_network_scope(scope)
            or is_docker_local_network_scope(scope, self.docker_gateway, self.docker_subnet)
            if self.docker_gateway is not None and self.docker_subnet is not None
            else is_loopback_network_scope(scope)
        )
        if allowed:
            await self.app(scope, receive, send)
            return
        response = JSONResponse(
            status_code=403,
            content={"error": ERROR_CODE},
            headers={"Cache-Control": "no-store"},
        )
        await response(scope, receive, send)
