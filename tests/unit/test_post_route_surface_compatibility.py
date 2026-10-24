"""Negative controls outside frozen release-blocking membership."""
import asyncio

from fastapi import APIRouter, FastAPI
import httpx
import pytest
from starlette.staticfiles import StaticFiles

from tests.post_route_surface import schema_post_paths_with_visibility_guard


async def endpoint():
    return {}


def test_nested_included_router_and_prefixes_are_discovered():
    app = FastAPI()
    leaf = APIRouter(prefix="/leaf")
    leaf.add_api_route("/post", endpoint, methods=["POST"])
    middle = APIRouter(prefix="/middle")
    middle.include_router(leaf, prefix="/nested")
    app.include_router(middle, prefix="/api")
    assert schema_post_paths_with_visibility_guard(app) == {"/api/middle/nested/leaf/post"}


@pytest.mark.parametrize("hiding", ["direct", "route", "router", "include", "nested-include"])
def test_hidden_post_is_rejected(hiding):
    app = FastAPI()
    if hiding == "direct":
        app.add_api_route("/hidden", endpoint, methods=["POST"], include_in_schema=False)
    else:
        router = APIRouter(include_in_schema=hiding != "router")
        router.add_api_route("/hidden", endpoint, methods=["POST"], include_in_schema=hiding != "route")
        if hiding == "nested-include":
            middle = APIRouter()
            middle.include_router(router, prefix="/nested", include_in_schema=False)
            router = middle
        app.include_router(router, prefix="/api", include_in_schema=hiding != "include")
    with pytest.raises(AssertionError, match="POST schema visibility mismatch"):
        schema_post_paths_with_visibility_guard(app)


def test_cached_schema_does_not_hide_later_hidden_registration():
    app = FastAPI()
    original = app.openapi()
    app.add_api_route("/hidden", endpoint, methods=["POST"], include_in_schema=False)
    with pytest.raises(AssertionError, match="POST schema visibility mismatch"):
        schema_post_paths_with_visibility_guard(app)
    assert app.openapi_schema is original


def test_duplicate_post_path_is_not_collapsed_to_one_schema_operation():
    app = FastAPI()
    app.add_api_route("/same", endpoint, methods=["POST"])
    router = APIRouter()
    router.add_api_route("/same", endpoint, methods=["POST"])
    app.include_router(router)
    with pytest.raises(AssertionError, match="duplicate effective POST"):
        schema_post_paths_with_visibility_guard(app)


def test_unknown_mounted_asgi_surface_fails_closed():
    app = FastAPI()
    child = FastAPI()
    child.add_api_route("/hidden", endpoint, methods=["POST"])
    app.mount("/child", child)
    with pytest.raises(AssertionError, match="unverified mounted HTTP surface"):
        schema_post_paths_with_visibility_guard(app)


def test_static_mount_exception_cannot_accept_post(tmp_path):
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=tmp_path))
    assert schema_post_paths_with_visibility_guard(app) == set()
    async def post():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1") as client:
            return await client.post("/static/anything")
    assert asyncio.run(post()).status_code == 405
