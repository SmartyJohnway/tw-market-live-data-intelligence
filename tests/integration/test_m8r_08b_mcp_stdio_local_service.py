import asyncio
import json
import os
from pathlib import Path
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"
LAUNCHER = ROOT / "scripts" / "run_unified_market_evidence_mcp.py"
CONTROL_ID = "umea-v1-0123456789abcdef0123"


class _Handler(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *_args):
        return

    def _json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        type(self).calls.append(("GET", self.path, None))
        if self.path == "/api/unified/capabilities":
            self._json(200, {"service_contract_version": "unified_market_evidence_local_service.v1", "capabilities": []})
        elif self.path == f"/api/unified/result-package/{CONTROL_ID}/handoff":
            self._json(200, {"service_contract_version": "unified_market_evidence_local_service.v1", "ai_ready_markdown": "# AI-ready\n"})
        else:
            self._json(404, {"error": "not_found", "trace_id": "test"})

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(size)
        payload = json.loads(raw)
        type(self).calls.append(("POST", self.path, payload))
        if self.path == "/api/unified/validate-request":
            self._json(200, {"validation_status": "valid", "request_id": payload["request"]["request_id"]})
        elif self.path == "/api/unified/preview-request":
            self._json(200, {"status": "ready_for_confirmation", "request_id": payload["request"]["request_id"]})
        elif self.path == "/api/unified/result-package":
            self._json(200, {"result_status": "success", "canonical_result": {"status": "success"}})
        elif self.path == "/api/unified/fetch-evidence":
            self._json(200, {"execution_outcome": "success", "canonical_result": {"status": "success"}, "ai_ready_markdown": "# fetched\n"})
        else:
            self._json(409, {"error": "bounded_error", "trace_id": "test"})


class LoopbackService:
    def __enter__(self):
        _Handler.calls = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.server.server_port}"

    def __exit__(self, *_args):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()


def _request():
    return {
        "schema_version": "unified_market_evidence_request.v1", "request_id": "stdio-test",
        "execution_mode": "preview", "targets": [{"input": "2330"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }


def test_real_stdio_to_actual_loopback_http_service():
    assert PYTHON.is_file(), "M8R-08B test must use the repository runtime"
    with LoopbackService() as service_url:
        async def run():
            env = {**os.environ, "UNIFIED_MARKET_EVIDENCE_SERVICE_URL": service_url}
            params = StdioServerParameters(command=str(PYTHON), args=[str(LAUNCHER)], env=env, cwd=str(ROOT))
            with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stderr:
                async with stdio_client(params, errlog=stderr) as (read, write):
                    async with ClientSession(read, write) as session:
                        initialized = await session.initialize()
                        assert initialized.protocolVersion
                        tools = await session.list_tools()
                        assert [tool.name for tool in tools.tools] == [
                            "market_describe_capabilities", "market_validate_request", "market_preview_request",
                            "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
                        ]
                        assert tools.tools[0].annotations.readOnlyHint is True
                        assert tools.tools[3].annotations.readOnlyHint is False
                        assert tools.tools[1].inputSchema["properties"]["request"] != {}
                        assert not (await session.call_tool("market_describe_capabilities", {})).isError
                        assert not (await session.call_tool("market_validate_request", {"request": _request()})).isError
                        assert not (await session.call_tool("market_preview_request", {"request": _request()})).isError
                        assert not (await session.call_tool("market_read_result", {"control_package_id": CONTROL_ID})).isError
                        handoff = await session.call_tool("market_export_ai_handoff", {"control_package_id": CONTROL_ID})
                        assert handoff.structuredContent["ai_ready_markdown"] == "# AI-ready\n"
                        assert handoff.content[0].text == "# AI-ready\n"
                        preview_fetch = await session.call_tool("market_fetch_evidence", {"request": _request()})
                        assert preview_fetch.isError
                        fetched = await session.call_tool("market_fetch_evidence", {"request": _request() | {"execution_mode": "execute"}})
                        assert not fetched.isError
                        assert fetched.content[0].text == "# fetched\n"
                        unknown = await session.call_tool("market_execute_request", {"confirm_execution": True})
                        assert unknown.isError is True
                stderr.seek(0)
                assert "Starting unified_market_evidence_mcp_adapter.v1 over stdio" in stderr.read()
        asyncio.run(run())
    assert _Handler.calls == [
        ("GET", "/api/unified/capabilities", None),
        ("GET", "/api/unified/capabilities", None),
        ("POST", "/api/unified/validate-request", {"request": _request()}),
        ("POST", "/api/unified/preview-request", {"request": _request()}),
        ("POST", "/api/unified/result-package", {"control_package_id": CONTROL_ID}),
        ("GET", f"/api/unified/result-package/{CONTROL_ID}/handoff", None),
        ("POST", "/api/unified/fetch-evidence", {"request": _request() | {"execution_mode": "execute"}}),
    ]
