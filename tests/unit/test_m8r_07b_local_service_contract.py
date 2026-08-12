"""Focused no-network contract coverage for the Local Service additions."""
from fastapi.testclient import TestClient

from server.main import app
from server.services import unified_local_service


client = TestClient(app)


def _capability(payload, capability_id):
    return next(item for item in payload["capabilities"] if item["capability_id"] == capability_id)


def _market(capability, market):
    return next(item for item in capability["markets"] if item["market"] == market)


def test_capability_contract_is_deterministic_and_preserves_dispositions():
    first = client.get("/api/unified/capabilities")
    second = client.get("/api/unified/capabilities")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    payload = first.json()
    assert payload["service_contract_version"] == "unified_market_evidence_local_service.v1"
    assert _market(_capability(payload, "current_observation"), "TWSE")["disposition"] == "executable"
    assert _market(_capability(payload, "current_observation"), "TPEX")["disposition"] == "executable"
    assert _market(_capability(payload, "official_eod_reference"), "TWSE")["disposition"] == "executable"
    assert _market(_capability(payload, "official_eod_reference"), "TPEX")["disposition"] == "executable"
    assert _market(_capability(payload, "official_eod_reference"), "TAIFEX")["disposition"] == "provisional"
    assert _capability(payload, "recent_performance")["routing_disposition"] == "plan_only"
    session = _capability(payload, "session_status")
    assert session["routing_disposition"] == "blocked"
    assert all(item["disposition"] != "executable" for item in session["markets"])


def test_capability_authority_failure_is_bounded_and_leaks_no_path(monkeypatch, tmp_path):
    monkeypatch.setattr(unified_local_service, "CATALOG_PATH", tmp_path / "missing.json")
    response = client.get("/api/unified/capabilities")
    assert response.status_code == 409
    assert response.json()["error"] == "capability_authority_unavailable"
    assert str(tmp_path) not in str(response.json())


def test_handoff_route_is_a_thin_bounded_transport(monkeypatch):
    from server import unified_workbench_router
    expected = {"service_contract_version": "unified_market_evidence_local_service.v1", "execution_outcome": "succeeded"}
    monkeypatch.setattr(unified_workbench_router, "build_mode_c_ai_handoff", lambda package_id: {**expected, "control_package_id": package_id})
    response = client.get("/api/unified/result-package/umea-v1-test/handoff")
    assert response.status_code == 200
    assert response.json() == {**expected, "control_package_id": "umea-v1-test"}
