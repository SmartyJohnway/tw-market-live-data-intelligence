"""No-network governance checks for the M8R-08B adapter surface."""
import asyncio

from server.unified_mcp.server import dispatch_safe_tool


class NoNetworkClient:
    def __init__(self):
        self.calls = []

    async def describe_capabilities(self):
        self.calls.append("capabilities")
        return {"service_contract_version": "unified_market_evidence_local_service.v1", "capabilities": []}

    async def validate_request(self, payload):
        self.calls.append(("validate", payload))
        return {"validation_status": "valid"}

    async def preview_request(self, payload):
        self.calls.append(("preview", payload))
        return {"status": "ready_for_confirmation", "execution_authorized": False}

    async def read_result(self, identifier):
        self.calls.append(("read", identifier))
        return {"canonical_result": {"targets": []}, "external_market_network_executed": False}

    async def export_ai_handoff(self, identifier):
        self.calls.append(("handoff", identifier))
        return {
            "canonical_result": {"targets": []}, "ai_ready_markdown": "# governed",
            "citation_references": [], "additional_market_network_executed": False,
        }


def test_safe_surface_never_reaches_authorization_execution_or_raw_evidence():
    client = NoNetworkClient()
    request = {
        "schema_version": "unified_market_evidence_request.v1", "request_id": "safe-surface",
        "execution_mode": "preview", "targets": [{"input": "2330"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }
    identifier = "umea-v1-0123456789abcdef0123"
    async def run():
        for name, arguments in (
            ("market_describe_capabilities", {}),
            ("market_validate_request", {"request": request}),
            ("market_preview_request", {"request": request}),
            ("market_read_result", {"control_package_id": identifier}),
            ("market_export_ai_handoff", {"control_package_id": identifier}),
        ):
            result = await dispatch_safe_tool(name, arguments, client=client)
            assert result.isError is False
            assert "twse_mis_rich_facts" not in str(result.structuredContent)
        for name in ("market_authorize_request", "market_execute_request", "execute_once"):
            result = await dispatch_safe_tool(name, {"confirm_authorization": True, "confirm_execution": True}, client=client)
            assert result.isError is True
    asyncio.run(run())
    assert [call[0] if isinstance(call, tuple) else call for call in client.calls] == [
        "capabilities", "validate", "preview", "read", "handoff",
    ]
