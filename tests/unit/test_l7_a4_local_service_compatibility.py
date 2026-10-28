"""Published-client bytes exercise the real HTTP backend without client patches."""
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys
import threading
import time

import httpx
import pytest
import uvicorn

from server.main import app
from server.services.unified_local_service import describe_capabilities
from server.unified_mcp.local_service_client import UnifiedLocalServiceClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/l7_a4_published_v1_client"
SOURCE = FIXTURE / "server/unified_mcp"
HEADER = "X-TW-Market-Service-Contract"
V1 = "unified_market_evidence_local_service.v1"
V2 = "unified_market_evidence_local_service.v2"


def test_v1_5_current_state_is_stable_published(tmp_path):
    from scripts.validate_v1_public_contracts import readme_current_product_truth_failures as check
    readme = tmp_path / "README.md"
    text = ("Persistent Watchlists are supported. ProductVersion = `1.5.0`. "
            "TW-Market `v1.5.0` is the current stable GitHub release. "
            "History: v1.0.0, v1.0.0-rc.1 and v0.1.0.")
    readme.write_text(text, encoding="utf-8")
    assert check(readme, current_product_version="1.5.0") == []
    readme.write_text(text + " Selected `v1.5.0` is unpublished.", encoding="utf-8")
    assert "readme_stale_v1_5_unpublished_status" in check(
        readme, current_product_version="1.5.0"
    )


def test_front_door_validates_published_v1_5_state(tmp_path, monkeypatch):
    from scripts import validate_v1_front_door as front
    assert front.required_release_patterns()
    assert front.validate() == []
    readme = tmp_path / "README.md"
    text = front.README.read_text(encoding="utf-8")
    readme.write_text(text + "\nSelected `v1.5.0` is unpublished.\n", encoding="utf-8")
    monkeypatch.setattr(front, "README", readme)
    assert "front_door:readme_stale_v1_5_unpublished_status" in front.validate()


def published_module(name):
    package = "published_v1_acceptance"
    if package not in sys.modules:
        spec = importlib.util.spec_from_file_location(package, SOURCE / "__init__.py",
                                                     submodule_search_locations=[str(SOURCE)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module
        spec.loader.exec_module(module)
    return __import__(package + "." + name, fromlist=[name])


@pytest.fixture(scope="module")
def backend_url():
    # A real TCP server: historical httpx transport and framing are unmodified.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(.01)
        assert server.started
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        sock.close()
        assert not thread.is_alive()


def test_exact_published_source_identity():
    identity = json.loads((FIXTURE / "identity.json").read_text(encoding="utf-8"))
    assert identity["commit"] == "e02bcb125999f542308a75f349c212f0ff3fee83"
    for row in identity["files"]:
        data = (FIXTURE / row["path"]).read_bytes()
        assert len(data) == row["bytes"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"]


def test_exact_historical_client_and_current_client_handshake(backend_url):
    historical = published_module("local_service_client").UnifiedLocalServiceClient(backend_url)
    current = UnifiedLocalServiceClient(backend_url)
    old = asyncio.run(historical.verify_service_contract())
    new = asyncio.run(current.verify_service_contract())
    assert old["service_contract_version"] == V1
    assert old == describe_capabilities(V1)
    assert new == describe_capabilities(V2)
    before = json.loads((FIXTURE / "current_v2_capabilities_before.json").read_text(encoding="utf-8"))
    assert new == before
    assert set(old) == {"service_contract_version", "capability_catalog_schema_version",
                        "routing_matrix_schema_version", "capabilities"}
    assert {c["capability_id"] for c in old["capabilities"]} == {
        "identity", "current_observation", "official_eod_reference", "session_status",
        "recent_performance", "source_currentness", "evidence_quality",
    }
    assert len(new["capabilities"]) > len(old["capabilities"])
    expected_fields = {
        "capability_id", "description", "semantic_support_status", "target_required",
        "allowed_parameters", "approval_required", "network_required", "routing_disposition",
        "selected_executor_id", "batching_scope", "supported_security_types",
        "possible_timing_classes", "known_limitations", "blocking_reasons", "markets",
    }
    assert all(set(capability) == expected_fields for capability in old["capabilities"])


@pytest.mark.parametrize("version", ["", "unified_market_evidence_local_service.v3", V2 + "-extra"])
@pytest.mark.parametrize("route", ["capabilities", "fetch-evidence", "authorizations", "executions"])
def test_unknown_contract_fails_before_operation(backend_url, version, route):
    with httpx.Client(trust_env=False) as client:
        response = client.request("GET" if route == "capabilities" else "POST",
                                  backend_url + "/api/unified/" + route,
                                  headers={HEADER: version, "Content-Type": "application/json"},
                                  content=b"invalid-json")
    assert response.status_code == 409
    assert response.json() == {"detail": "local_service_contract_incompatible"}


def test_historical_client_deterministic_errors_and_fetch_boundary(backend_url):
    module = published_module("local_service_client")
    client = module.UnifiedLocalServiceClient(backend_url)
    request = {"request": {"schema_version": "unified_market_evidence_request.v1",
                            "execution_mode": "preview"}}
    operations = [(client.validate_request, {}), (client.preview_request, {}),
                  (client.read_result, "umea-v1-" + "a" * 20),
                  (client.export_ai_handoff, "umea-v1-" + "a" * 20),
                  (client.fetch_evidence, request)]
    for operation, argument in operations:
        with pytest.raises(module.LocalServiceClientError) as caught:
            asyncio.run(operation(argument))
        assert caught.value.code == "local_service_http_error"
        mapped = published_module("error_mapping").map_local_service_error(caught.value)
        assert mapped.isError is True
        assert isinstance(mapped.structuredContent, dict)
    assert caught.value.payload["error"] == "market_fetch_requires_execute_mode"


def test_historical_client_validates_and_previews_synthetic_identity(backend_url, tmp_path, monkeypatch):
    from scripts.m8r_06_01c2_mode_a_security_master_loader import reset_production_mode_a_security_master_for_tests
    from scripts.m8r_08g_security_master_releases import activate_qualified_release
    from tests.unit.test_m8r_08g_identity_service_and_releases import qualify, rec

    root = tmp_path / "synthetic-security-master"
    release = "security-master-20261025T000000Z"
    _, report = qualify(root, release, [rec()])
    assert report["status"] == "PASS"
    activate_qualified_release(root=root, release_id=release)
    monkeypatch.setenv("TW_MARKET_SECURITY_MASTER_ROOT", str(root))
    reset_production_mode_a_security_master_for_tests()
    try:
        client = published_module("local_service_client").UnifiedLocalServiceClient(backend_url)
        request = {"request": {
            "schema_version": "unified_market_evidence_request.v1",
            "request_id": "a4-v1-synthetic", "execution_mode": "preview",
            "targets": [{"input": "2330", "market_hint": "TWSE"}],
            "data_needs": [{"type": "current_observation", "priority": "required"}],
        }}
        validation = asyncio.run(client.validate_request(request))
        assert validation["validation_status"] == "valid"
        preview = asyncio.run(client.preview_request(request))
        assert isinstance(preview, dict)
        assert preview
    finally:
        reset_production_mode_a_security_master_for_tests()


def test_historical_client_reads_real_synthetic_governed_outputs(backend_url, tmp_path, monkeypatch):
    from unittest.mock import patch
    from server.services import unified_mode_a, unified_mode_c
    from tests.helpers.phase_h_imp_7d_control_package import execute_fixture_package

    root = tmp_path / "synthetic-governed"
    execution = execute_fixture_package(root)
    identifier = execution["authorization"]["authorization_id"]
    # Fixture preparation alone uses the established explicit synthetic F3 seam.
    # HTTP acceptance below runs the unmodified backend and historical client.
    with patch.object(unified_mode_c, "CONTROL_ROOT", root), patch.object(
        unified_mode_c, "validate_mode_a_request",
        lambda request: unified_mode_a.validate_mode_a_request(request, allow_fixture_snapshot=True),
    ):
        prepared = unified_mode_c.build_mode_c_result_package({"control_package_id": identifier})
    monkeypatch.setenv("M8R_06_03_CONTROL_ROOT", str(root))
    before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in root.rglob("*") if p.is_file()}
    client = published_module("local_service_client").UnifiedLocalServiceClient(backend_url)
    result = asyncio.run(client.read_result(identifier))
    handoff = asyncio.run(client.export_ai_handoff(identifier))
    assert result["result_hash"] == prepared["result_hash"]
    assert result["canonical_result"] == prepared["canonical_result"]
    assert handoff["result_hash"] == result["result_hash"]
    assert handoff["audit_package_id"] == result["audit_package_id"]
    assert handoff["additional_market_network_executed"] is False
    assert isinstance(handoff["ai_ready_markdown"], str)
    assert handoff["service_contract_version"] == V1
    snapshot = published_module("tool_contracts").build_tool_contract_snapshot()
    assert len(snapshot.tools) == 6
    dispatch = published_module("server").dispatch_safe_tool
    for name in ("market_read_result", "market_export_ai_handoff"):
        envelope = asyncio.run(dispatch(name, {"control_package_id": identifier},
                                       client=client, tool_contract_snapshot=snapshot))
        assert envelope.isError is False
        assert envelope.structuredContent["result_hash"] == result["result_hash"]
        assert envelope.content[0].type == "text"
    after = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.rglob("*") if p.is_file()}
    assert after == before
