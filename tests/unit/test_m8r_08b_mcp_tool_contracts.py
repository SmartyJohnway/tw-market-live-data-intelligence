import asyncio
import hashlib
import json

from server.unified_mcp import ADAPTER_VERSION
from server.unified_mcp.local_service_client import LocalServiceClientError
from server.unified_mcp.server import dispatch_safe_tool
from server.unified_mcp.tool_contracts import (
    CONTROL_PACKAGE_PATTERN,
    REQUEST_SCHEMA_PATH,
    TOOL_DESCRIPTIONS,
    build_tool_specs,
    canonical_request_schema_sha256,
)


EXPECTED_NAMES = (
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
)
FORBIDDEN = {
    "market_authorize_request", "market_execute_request", "authorize_market_request",
    "execute_market_request", "run_market_request", "run_market_evidence",
    "fetch_live_market", "refresh_market", "probe_market", "execute_once",
}


class RecordingClient:
    def __init__(self):
        self.calls = []

    async def describe_capabilities(self):
        self.calls.append(("describe", None))
        return {"service_contract_version": "unified_market_evidence_local_service.v1"}

    async def validate_request(self, envelope):
        self.calls.append(("validate", envelope))
        return {"validation_status": "valid"}

    async def preview_request(self, envelope):
        self.calls.append(("preview", envelope))
        return {"status": "ready_for_confirmation"}

    async def read_result(self, identifier):
        self.calls.append(("read", identifier))
        return {"canonical_result": {"status": "success"}}

    async def export_ai_handoff(self, identifier):
        self.calls.append(("export", identifier))
        return {"ai_ready_markdown": "# governed"}


def test_exactly_five_deterministic_safe_tool_contracts():
    first = build_tool_specs()
    second = build_tool_specs()
    assert tuple(tool.name for tool in first) == EXPECTED_NAMES
    assert [tool.model_dump(by_alias=True) for tool in first] == [tool.model_dump(by_alias=True) for tool in second]
    assert not (set(EXPECTED_NAMES) & FORBIDDEN)
    assert ADAPTER_VERSION == "unified_market_evidence_mcp_adapter.v1"
    for tool in first:
        assert tool.description == TOOL_DESCRIPTIONS[tool.name]
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.idempotentHint is True
        assert tool.annotations.openWorldHint is False
    assert all(tool.annotations.readOnlyHint is True for tool in first[:3])
    assert all(tool.annotations.readOnlyHint is False for tool in first[3:])


def test_request_schemas_embed_committed_authority_without_placeholder():
    tools = {tool.name: tool for tool in build_tool_specs()}
    canonical = json.loads(REQUEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(REQUEST_SCHEMA_PATH.read_bytes()).hexdigest()
    assert canonical_request_schema_sha256() == expected_hash
    validate = tools["market_validate_request"].inputSchema
    preview = tools["market_preview_request"].inputSchema
    assert validate == preview
    assert validate["type"] == "object"
    assert validate["required"] == ["request"]
    assert validate["additionalProperties"] is False
    assert validate["properties"]["request"] == canonical
    assert validate["properties"]["request"] != {}
    for name in ("market_read_result", "market_export_ai_handoff"):
        schema = tools[name].inputSchema
        assert schema["additionalProperties"] is False
        assert schema["required"] == ["control_package_id"]
        assert schema["properties"]["control_package_id"]["pattern"] == CONTROL_PACKAGE_PATTERN


def test_tool_contracts_have_no_adapter_privileged_or_endpoint_inputs():
    forbidden_fields = {"url", "path", "source", "executor", "confirm_authorization", "confirm_execution", "confirm_network_execution", "headers", "credentials"}
    for tool in build_tool_specs():
        assert not (set(tool.inputSchema["properties"]) & forbidden_fields)


def test_dispatch_uses_exact_envelopes_and_never_dispatches_actions():
    client = RecordingClient()
    request = {
        "schema_version": "unified_market_evidence_request.v1", "request_id": "mcp-test",
        "execution_mode": "preview", "targets": [{"input": "2330"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }
    identifier = "umea-v1-0123456789abcdef0123"
    async def run():
        assert not (await dispatch_safe_tool("market_describe_capabilities", {}, client=client)).isError
        assert not (await dispatch_safe_tool("market_validate_request", {"request": request}, client=client)).isError
        assert not (await dispatch_safe_tool("market_preview_request", {"request": request}, client=client)).isError
        assert not (await dispatch_safe_tool("market_read_result", {"control_package_id": identifier}, client=client)).isError
        handoff = await dispatch_safe_tool("market_export_ai_handoff", {"control_package_id": identifier}, client=client)
        assert handoff.content[0].text == "# governed"
        for forbidden in FORBIDDEN:
            result = await dispatch_safe_tool(forbidden, {"confirm_execution": True}, client=client)
            assert result.isError is True
    asyncio.run(run())
    assert client.calls == [
        ("describe", None), ("validate", {"request": request}), ("preview", {"request": request}),
        ("read", identifier), ("export", identifier),
    ]


def test_malformed_control_identifier_is_rejected_before_client_dispatch():
    client = RecordingClient()
    result = asyncio.run(dispatch_safe_tool("market_read_result", {"control_package_id": "../umea-v1-bad"}, client=client))
    assert result.isError is True
    assert client.calls == []
