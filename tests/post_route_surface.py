"""Test-only POST inventory: public schema plus independent visibility guard.

Newer FastAPI supplies the non-underscore routing iterator used by its own
OpenAPI generator. Older versions expose flat Starlette routes. Never inspect
private router classes, include contexts, or underscore-prefixed attributes.
An unsupported opaque surface fails closed instead of being silently omitted.
"""
from collections import Counter

from fastapi import routing
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles


def effective_post_paths(application):
    iterator = getattr(routing, "iter_route_contexts", None)
    surfaces = iterator(application.routes) if callable(iterator) else application.routes
    paths = []
    for surface in surfaces:
        route = surface.route if callable(iterator) else surface
        if isinstance(route, Mount):
            # StaticFiles accepts GET/HEAD only. Arbitrary ASGI mounts could
            # hide POST endpoints and must receive explicit future coverage.
            assert type(route.app) is StaticFiles, "unverified mounted HTTP surface"
            continue
        if isinstance(route, WebSocketRoute):
            continue
        assert isinstance(route, Route), "unverified opaque HTTP route surface"
        methods = surface.methods
        assert methods is not None, "HTTP route has no inspectable methods"
        if "POST" in methods:
            path = surface.path_format
            assert isinstance(path, str) and path.startswith("/"), "POST path unavailable"
            paths.append(path)
    duplicates = sorted(path for path, count in Counter(paths).items() if count != 1)
    assert not duplicates, f"duplicate effective POST operations: {duplicates}"
    return set(paths)


def schema_post_paths_with_visibility_guard(application):
    # Do not let a stale cached schema conceal a route added after generation.
    cached = application.openapi_schema
    try:
        application.openapi_schema = None
        paths = {
            path for path, operations in application.openapi()["paths"].items()
            if "post" in operations
        }
    finally:
        application.openapi_schema = cached
    effective = effective_post_paths(application)
    assert effective == paths, (
        f"POST schema visibility mismatch: hidden={sorted(effective - paths)}, "
        f"schema_only={sorted(paths - effective)}"
    )
    return paths
