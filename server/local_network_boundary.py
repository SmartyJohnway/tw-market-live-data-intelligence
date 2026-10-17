from __future__ import annotations

import ipaddress
from collections.abc import Sequence
from typing import Any

from starlette.responses import JSONResponse


ERROR_CODE = "local_service_loopback_required"


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


class LocalNetworkBoundaryMiddleware:
    """Reject requests whose ASGI socket addresses demonstrate non-loopback use."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or is_loopback_network_scope(scope):
            await self.app(scope, receive, send)
            return
        response = JSONResponse(
            status_code=403,
            content={"error": ERROR_CODE},
            headers={"Cache-Control": "no-store"},
        )
        await response(scope, receive, send)
