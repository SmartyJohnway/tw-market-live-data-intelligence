import asyncio
import json

from fastapi.testclient import TestClient

from server.main import app
from server import mcp_server
from scripts.m5k_common import DEFAULT_WATCHLIST_PATH, build_conversation_context, load_json, validate_watchlist, watchlist_schema, watchlist_summary


def test_m5n_watchlist_schema_and_default_symbols():
    watchlist = load_json(DEFAULT_WATCHLIST_PATH)
    validation = validate_watchlist(watchlist)
    assert validation["valid"] is True
    assert watchlist_schema()["required_item_fields"] == ["id", "symbol", "display_name", "market", "instrument_type", "adapter", "category", "enabled", "display_order", "tags", "notes"]
    assert watchlist_summary(watchlist)["symbols"] == ["0050", "00878", "00919", "00929", "00934", "00939", "00940", "00981A", "1569", "2317", "2324", "2330", "2603", "2609", "3293", "3483", "3543", "TAIEX", "TX"]


def test_conversation_context_omits_raw_payloads():
    context = build_conversation_context(load_json(DEFAULT_WATCHLIST_PATH), {"observations": [], "failures": []})
    assert context["schema_version"] == "m5n_conversation_context.v1"
    assert context["governance"]["raw_endpoint_payload_included"] is False
    assert "raw_payload" not in json.dumps(context)


def test_fastapi_watchlist_endpoints():
    client = TestClient(app)
    for path in ["/api/watchlist", "/api/watchlist/summary", "/api/watchlist/schema", "/api/conversation/context"]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["governance"]["network_calls"] is False


def test_mcp_watchlist_tools_readonly():
    async def run():
        tools = await mcp_server.list_tools()
        names = {tool.name for tool in tools}
        assert {"get_watchlist", "get_watchlist_summary", "validate_watchlist"}.issubset(names)
        for name in ["get_watchlist", "get_watchlist_summary", "validate_watchlist"]:
            payload = json.loads((await mcp_server.call_tool(name, {}))[0].text)
            assert payload["status"] == "ok"
            assert payload["governance"]["network_calls"] is False
    asyncio.run(run())


def test_frontend_watchlist_workspace_static_contract():
    html = (DEFAULT_WATCHLIST_PATH.parents[1] / "frontend/readonly-preview/watchlist-workspace.html").read_text(encoding="utf-8")
    assert "/api/watchlist" in html
    assert "Last observation" in html
    assert "Export JSON" in html
