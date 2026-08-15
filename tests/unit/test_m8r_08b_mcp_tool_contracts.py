import asyncio
import hashlib
import importlib
import json

import pytest

from server.unified_mcp import ADAPTER_VERSION
from server.unified_mcp.local_service_client import LocalServiceClientError
from server.unified_mcp.server import dispatch_safe_tool
from server.unified_mcp.tool_contracts import (
    CONTROL_PACKAGE_PATTERN,
    REQUEST_SCHEMA_PATH,
    TOOL_DESCRIPTIONS,
    build_tool_specs,
    build_tool_contract_snapshot,
    canonical_request_schema_sha256,
    ToolContractError,
)
import server.unified_mcp.tool_contracts as tool_contracts

launcher = importlib.import_module("scripts.run_unified_market_evidence_mcp")


EXPECTED_NAMES = (
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
    "market_fetch_evidence",
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

    async def fetch_evidence(self, envelope):
        self.calls.append(("fetch", envelope))
        return {"ai_ready_markdown": "# fetched", "canonical_result": {"status": "success"}}


def test_exactly_six_tool_contracts_with_one_bounded_action():
    first = build_tool_specs()
    second = build_tool_specs()
    assert tuple(tool.name for tool in first) == EXPECTED_NAMES
    assert [tool.model_dump(by_alias=True) for tool in first] == [tool.model_dump(by_alias=True) for tool in second]
    assert not (set(EXPECTED_NAMES) & FORBIDDEN)
    assert ADAPTER_VERSION == "unified_market_evidence_mcp_adapter.v1"
    for tool in first:
        assert tool.description == TOOL_DESCRIPTIONS[tool.name]
        assert tool.annotations.destructiveHint is False
        if tool.name != "market_fetch_evidence":
            assert tool.annotations.idempotentHint is True
            assert tool.annotations.openWorldHint is False
    assert all(tool.annotations.readOnlyHint is True for tool in first[:3])
    assert all(tool.annotations.readOnlyHint is False for tool in first[3:])
    action = first[-1]
    assert action.annotations.readOnlyHint is False
    assert action.annotations.destructiveHint is False
    assert action.annotations.idempotentHint is False
    assert action.annotations.openWorldHint is True


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


def test_dispatch_uses_exact_envelopes_and_rejects_preview_action_before_service():
    client = RecordingClient()
    request = {
        "schema_version": "unified_market_evidence_request.v1", "request_id": "mcp-test",
        "execution_mode": "preview", "targets": [{"input": "2330"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }
    identifier = "umea-v1-0123456789abcdef0123"
    async def run():
        snapshot = build_tool_contract_snapshot()
        assert not (await dispatch_safe_tool("market_describe_capabilities", {}, client=client, tool_contract_snapshot=snapshot)).isError
        assert not (await dispatch_safe_tool("market_validate_request", {"request": request}, client=client, tool_contract_snapshot=snapshot)).isError
        assert not (await dispatch_safe_tool("market_preview_request", {"request": request}, client=client, tool_contract_snapshot=snapshot)).isError
        assert not (await dispatch_safe_tool("market_read_result", {"control_package_id": identifier}, client=client, tool_contract_snapshot=snapshot)).isError
        handoff = await dispatch_safe_tool("market_export_ai_handoff", {"control_package_id": identifier}, client=client, tool_contract_snapshot=snapshot)
        assert handoff.content[0].text == "# governed"
        rejected = await dispatch_safe_tool("market_fetch_evidence", {"request": request}, client=client, tool_contract_snapshot=snapshot)
        assert rejected.isError is True
        execute_request = request | {"execution_mode": "execute"}
        fetched = await dispatch_safe_tool("market_fetch_evidence", {"request": execute_request}, client=client, tool_contract_snapshot=snapshot)
        assert fetched.isError is False and fetched.content[0].text == "# fetched"
        for forbidden in FORBIDDEN:
            result = await dispatch_safe_tool(forbidden, {"confirm_execution": True}, client=client, tool_contract_snapshot=snapshot)
            assert result.isError is True
    asyncio.run(run())
    assert client.calls == [
        ("describe", None), ("validate", {"request": request}), ("preview", {"request": request}),
        ("read", identifier), ("export", identifier), ("fetch", {"request": request | {"execution_mode": "execute"}}),
    ]


def test_malformed_control_identifier_is_rejected_before_client_dispatch():
    client = RecordingClient()
    result = asyncio.run(dispatch_safe_tool("market_read_result", {"control_package_id": "../umea-v1-bad"}, client=client, tool_contract_snapshot=build_tool_contract_snapshot()))
    assert result.isError is True
    assert client.calls == []


@pytest.mark.parametrize(
    ("contents", "error"),
    (
        (None, "canonical_request_schema_unavailable"),
        ("{not json", "canonical_request_schema_malformed"),
        (json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "$id": "wrong", "type": "object"}), "canonical_request_schema_identity_mismatch"),
        (json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "$id": "urn:tw-market-live-data-intelligence:unified_market_evidence_request:v1", "type": 7, "properties": {"schema_version": {"const": "unified_market_evidence_request.v1"}}}), "canonical_request_schema_malformed"),
    ),
)
def test_startup_snapshot_fails_closed_for_unusable_canonical_authority(monkeypatch, contents, error):
    monkeypatch.setattr(tool_contracts, "REQUEST_SCHEMA_PATH", tool_contracts.Path("synthetic-request.schema.json"))
    if contents is None:
        def read_text(_path, **_kwargs):
            raise OSError("synthetic missing authority")
        def read_bytes(_path):
            raise OSError("synthetic missing authority")
    else:
        def read_text(_path, **_kwargs):
            return contents
        def read_bytes(_path):
            return contents.encode("utf-8")
    monkeypatch.setattr(tool_contracts.Path, "read_text", read_text)
    monkeypatch.setattr(tool_contracts.Path, "read_bytes", read_bytes)
    with pytest.raises(ToolContractError, match=error):
        build_tool_contract_snapshot()


def test_one_snapshot_builds_six_tools_and_avoids_per_call_authority_reads(monkeypatch):
    snapshot = build_tool_contract_snapshot()
    monkeypatch.setattr(
        tool_contracts,
        "load_canonical_unified_request_schema",
        lambda: (_ for _ in ()).throw(AssertionError("authority reread")),
    )
    client = RecordingClient()
    request = {
        "schema_version": "unified_market_evidence_request.v1", "request_id": "snapshot-test",
        "execution_mode": "preview", "targets": [{"input": "2330"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }
    asyncio.run(dispatch_safe_tool("market_validate_request", {"request": request}, client=client, tool_contract_snapshot=snapshot))
    asyncio.run(dispatch_safe_tool("market_preview_request", {"request": request}, client=client, tool_contract_snapshot=snapshot))
    assert len(snapshot.tools) == 6


@pytest.mark.parametrize(
    "error",
    (
        "canonical_request_schema_unavailable",
        "canonical_request_schema_malformed",
        "canonical_request_schema_identity_mismatch",
    ),
)
def test_launcher_stops_before_local_service_or_stdio_on_tool_contract_failure(monkeypatch, capsys, error):
    def fail_snapshot():
        raise ToolContractError(error)

    class LocalServiceMustNotStart:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("local service must not be contacted")

    monkeypatch.setattr(launcher, "build_tool_contract_snapshot", fail_snapshot)
    monkeypatch.setattr(launcher, "UnifiedLocalServiceClient", LocalServiceMustNotStart)
    assert asyncio.run(launcher._serve("http://127.0.0.1:8000")) == launcher.EXIT_CONFIGURATION
    stderr = capsys.readouterr().err
    assert error in stderr
    assert "P:\\" not in stderr
