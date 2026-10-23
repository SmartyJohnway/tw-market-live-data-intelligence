from __future__ import annotations

import asyncio

import pytest
from starlette.responses import JSONResponse
from scripts.tw_market_docker import default_ipv4_gateway

from server.local_network_boundary import (
    DOCKER_PROFILE,
    ERROR_CODE,
    LocalNetworkBoundaryMiddleware,
    is_docker_local_network_scope,
    is_loopback_network_scope,
)


def test_docker_profile_accepts_only_peers_inside_configured_private_subnet():
    gateway = "172.30.0.1"
    subnet = "172.30.0.0/29"
    assert is_docker_local_network_scope(
        {"client": (gateway, 52344), "server": ("172.30.0.2", 8000)}, gateway, subnet
    )
    assert not is_docker_local_network_scope(
        {"client": ("172.30.0.3", 52344), "server": ("172.30.0.2", 8000)}, gateway, subnet
    )
    assert not is_docker_local_network_scope(
        {"client": ("192.168.1.5", 52344), "server": ("172.30.0.2", 8000)}, gateway, subnet
    )
    assert not is_docker_local_network_scope(
        {"client": (gateway, 52344), "server": ("198.51.100.2", 8000)}, gateway, subnet
    )


def test_docker_profile_is_explicit_and_unknown_profiles_fail_closed(monkeypatch):
    monkeypatch.setenv("TW_MARKET_NETWORK_PROFILE", DOCKER_PROFILE)
    monkeypatch.setenv("TW_MARKET_DOCKER_GATEWAY_IP", "172.30.0.1")
    monkeypatch.setenv("TW_MARKET_DOCKER_SUBNET", "172.30.0.0/29")
    middleware = LocalNetworkBoundaryMiddleware(lambda *_: None)
    assert middleware.docker_gateway == "172.30.0.1"
    assert middleware.docker_subnet == "172.30.0.0/29"
    monkeypatch.setenv("TW_MARKET_NETWORK_PROFILE", "allow-non-loopback")
    with pytest.raises(RuntimeError, match="network_profile_invalid"):
        LocalNetworkBoundaryMiddleware(lambda *_: None)


def test_docker_profile_keeps_native_and_container_loopback_requests():
    assert is_loopback_network_scope(
        {"client": ("127.0.0.1", 50200), "server": ("127.0.0.1", 8000)}
    )
    assert is_docker_local_network_scope(
        {"client": ("172.30.0.1", 50200), "server": ("172.30.0.2", 8000)},
        "172.30.0.1", "172.30.0.0/29",
    )


def test_docker_route_parsers_use_linux_route_table(tmp_path):
    routes = tmp_path / "route"
    routes.write_text(
        "Iface Destination Gateway Flags RefCnt Use Metric Mask\n"
        "eth0 00000000 01001EAC 0003 0 0 0 00000000\n"
        "eth0 00001EAC 00000000 0001 0 0 0 00FFFFFF\n",
        encoding="ascii",
    )
    assert default_ipv4_gateway(routes) == "172.30.0.1"
    from server.local_network_boundary import _default_ipv4_subnet
    assert _default_ipv4_subnet(routes) == "172.30.0.0/24"


def test_missing_docker_subnet_fails_closed(tmp_path):
    from server.local_network_boundary import _default_ipv4_subnet
    with pytest.raises(RuntimeError, match="docker_network_subnet_unavailable"):
        _default_ipv4_subnet(tmp_path / "missing-route")


def test_docker_profile_middleware_rejects_peer_outside_docker_subnet():
    sent = []

    async def downstream(scope, receive, send):
        await JSONResponse({"ok": True})(scope, receive, send)

    async def invoke():
        middleware = LocalNetworkBoundaryMiddleware(
            downstream, network_profile=DOCKER_PROFILE, docker_gateway="172.30.0.1",
            docker_subnet="172.30.0.0/29",
        )

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            sent.append(message)

        await middleware(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/health",
                "headers": [],
                "client": ("172.31.0.3", 50123),
                "server": ("172.30.0.2", 8000),
            },
            receive,
            send,
        )

    asyncio.run(invoke())
    assert sent[0]["status"] == 403
    assert ERROR_CODE.encode() in sent[1]["body"]
