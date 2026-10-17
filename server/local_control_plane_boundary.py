"""Browser-origin boundary for Local Service control-plane POST routes."""
from __future__ import annotations

import ipaddress
import re
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlsplit

from starlette.responses import JSONResponse


READ_OR_OFFLINE_PROJECTION = "READ_OR_OFFLINE_PROJECTION"
LOCAL_STATE_MUTATION = "LOCAL_STATE_MUTATION"
NETWORK_EXECUTION = "NETWORK_EXECUTION"
LEGACY_DISABLED = "LEGACY_DISABLED"

# Keep this map explicit: adding a POST route requires a reviewed control-plane
# classification and a corresponding test assertion.
POST_ROUTE_CLASSIFICATIONS = {
    "/api/unified/validate-request": READ_OR_OFFLINE_PROJECTION,
    "/api/unified/preview-request": READ_OR_OFFLINE_PROJECTION,
    "/api/unified/authorizations": LOCAL_STATE_MUTATION,
    "/api/unified/executions": NETWORK_EXECUTION,
    "/api/unified/fetch-evidence": NETWORK_EXECUTION,
    "/api/unified/result-package": LOCAL_STATE_MUTATION,
    "/api/watchlists/{watchlist_id}/evidence-request-preview": READ_OR_OFFLINE_PROJECTION,
    "/api/evidence-request-previews": READ_OR_OFFLINE_PROJECTION,
    "/api/watchlist-mutations/preview": LOCAL_STATE_MUTATION,
    "/api/watchlist-mutations/commit": LOCAL_STATE_MUTATION,
    "/api/m5k/watchlist/validate": READ_OR_OFFLINE_PROJECTION,
    "/api/m5k/conversation/handoff": READ_OR_OFFLINE_PROJECTION,
    "/api/m5k/live-observation/plan": READ_OR_OFFLINE_PROJECTION,
    "/api/m5k/live-observation/execute": LEGACY_DISABLED,
    "/api/m7g/controlled-refresh/execute": LEGACY_DISABLED,
}

_PATH_MATCHERS = tuple(
    (re.compile("^" + re.sub(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", r"[^/]+", path) + "$"), classification)
    for path, classification in POST_ROUTE_CLASSIFICATIONS.items()
)
PRIVILEGED_CLASSES = frozenset({LOCAL_STATE_MUTATION, NETWORK_EXECUTION})
CONTROL_PLANE_ERROR = "local_control_plane_same_origin_required"
CONTENT_TYPE_ERROR = "privileged_json_required"


def classify_post_path(path: str) -> str | None:
    for matcher, classification in _PATH_MATCHERS:
        if matcher.fullmatch(path):
            return classification
    return None


def _host_port(value: str, scheme: str) -> tuple[str, int] | None:
    try:
        parsed = urlsplit("//" + value)
        if parsed.username is not None or parsed.password is not None or parsed.path or parsed.query or parsed.fragment:
            return None
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        return None
    if not host:
        return None
    if port is None:
        port = 443 if scheme == "https" else 80
    return host.rstrip(".").lower(), port


def _is_local_host(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def is_same_local_service_origin(scope: dict[str, Any], origin: str) -> bool:
    """Compare Origin to the request's actual scheme/Host and listener port.

    Host is used only to identify the URL the browser addressed; it must also
    be a loopback literal or localhost and match the actual ASGI listener port.
    Forwarded headers are deliberately ignored.
    """
    try:
        parsed_origin = urlsplit(origin)
        if parsed_origin.scheme not in {"http", "https"} or parsed_origin.path or parsed_origin.query or parsed_origin.fragment:
            return False
        origin_port = parsed_origin.port
    except ValueError:
        return False
    if parsed_origin.hostname is None:
        return False
    scheme = str(scope.get("scheme") or "").lower()
    if parsed_origin.scheme.lower() != scheme:
        return False
    server = scope.get("server")
    if not isinstance(server, Sequence) or isinstance(server, (str, bytes)) or len(server) < 2:
        return False
    try:
        server_port = int(server[1])
    except (TypeError, ValueError):
        return False
    origin_host = parsed_origin.hostname.rstrip(".").lower()
    if origin_port is None:
        origin_port = 443 if scheme == "https" else 80
    host_header = None
    for name, value in scope.get("headers", []):
        if name.lower() == b"host":
            try:
                host_header = value.decode("latin-1")
            except (AttributeError, UnicodeDecodeError):
                return False
            break
    if not host_header:
        return False
    request_host = _host_port(host_header, scheme)
    if request_host is None:
        return False
    return (
        _is_local_host(origin_host)
        and request_host[0] == origin_host
        and request_host[1] == server_port
        and origin_port == server_port
    )


def _header(scope: dict[str, Any], name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            try:
                return value.decode("latin-1").strip()
            except (AttributeError, UnicodeDecodeError):
                return "\x00"
    return None


def control_plane_rejection(scope: dict[str, Any]) -> tuple[int, str] | None:
    if scope.get("type") != "http" or scope.get("method", "").upper() != "POST":
        return None
    classification = classify_post_path(str(scope.get("path") or ""))
    if classification not in PRIVILEGED_CLASSES:
        return None
    content_type = _header(scope, b"content-type")
    if content_type is None or content_type.split(";", 1)[0].strip().lower() != "application/json":
        return 415, CONTENT_TYPE_ERROR
    origin = _header(scope, b"origin")
    fetch_site = _header(scope, b"sec-fetch-site")
    if origin is None:
        # Native local integrations do not send browser-origin metadata.
        if fetch_site is None:
            return None
        return 403, CONTROL_PLANE_ERROR
    if origin.lower() == "null" or not is_same_local_service_origin(scope, origin):
        return 403, CONTROL_PLANE_ERROR
    if fetch_site is not None and fetch_site.lower() != "same-origin":
        return 403, CONTROL_PLANE_ERROR
    return None


class LocalControlPlaneBoundaryMiddleware:
    """Protect state-changing and acquisition routes from cross-origin browsers."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        rejection = control_plane_rejection(scope)
        if rejection is None:
            await self.app(scope, receive, send)
            return
        status, code = rejection
        response = JSONResponse(
            status_code=status,
            content={"error": code},
            headers={"Cache-Control": "no-store"},
        )
        await response(scope, receive, send)
