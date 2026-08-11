import json
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

from pathlib import Path
import pytest

@pytest.fixture()
def mock_validation(monkeypatch):
    from server import unified_workbench_router
    def fake_validate(req):
        return {
            "request_id": req.get("request_id"),
            "validation_status": "valid",
            "target_results": [{"canonical_identity": {"market": "TWSE"}}]
        }
    monkeypatch.setattr(unified_workbench_router, "validate_mode_a_request", fake_validate)

def test_production_boundary_enforced(monkeypatch, tmp_path):
    from server.services import unified_mode_a
    
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "test-prod",
        "execution_mode": "preview",
        "targets": [{"input": "2330"}],
        "data_needs": []
    }
    monkeypatch.setattr(unified_mode_a, "PRODUCTION_POINTER_PATH", tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError):
        unified_mode_a.validate_mode_a_request(req)

def test_api_returns_409_when_production_security_master_missing(monkeypatch, tmp_path):
    from server.services import unified_mode_a

    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "test-prod",
        "execution_mode": "preview",
        "targets": [{"input": "2330"}],
        "data_needs": []
    }
    monkeypatch.setattr(unified_mode_a, "PRODUCTION_POINTER_PATH", tmp_path / "missing.json")
    response = client.post("/api/unified/validate-request", json={"request": req})
    assert response.status_code == 409
    data = response.json()
    assert data["error"] == "canonical_security_master_unavailable"
    assert "trace_id" in data
    # Ensure no absolute paths or tracebacks are leaked
    error_str = str(data).lower()
    assert "tests/fixtures" not in error_str
    assert "traceback" not in error_str
    assert "\\" not in error_str and "/" not in data.get("detail", "")

def test_non_root_cwd_isolation(monkeypatch):
    import os
    from server.services.unified_mode_a import validate_mode_a_request
    
    # Change CWD to something else
    original_cwd = os.getcwd()
    try:
        os.chdir(os.path.dirname(__file__))
        req = {
            "schema_version": "unified_market_evidence_request.v1",
            "request_id": "test-prod",
            "execution_mode": "preview",
            "targets": [{"input": "2330"}],
            "data_needs": [{"type": "identity", "priority": "required"}]
        }
        # It should still find the files correctly and raise FileNotFoundError for production snapshot
        # rather than crashing with some other random path error, or if we pass allow_fixture_snapshot=True,
        # it should succeed!
        result = validate_mode_a_request(req, allow_fixture_snapshot=True)
        assert result["validation_status"] == "valid"
    finally:
        os.chdir(original_cwd)

def test_validate_request_valid_envelope(mock_validation):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "api-test",
        "execution_mode": "preview",
        "targets": [{"input": "2330"}],
        "data_needs": [{"type": "identity", "priority": "required"}]
    }
    response = client.post("/api/unified/validate-request", json={"request": req})
    assert response.status_code == 200
    data = response.json()
    assert data["validation_status"] == "valid"
    assert data["target_results"][0]["canonical_identity"]["market"] == "TWSE"


def test_mode_a_workbench_routes_and_health():
    root_response = client.get("/workbench/mode-a/")
    assert root_response.status_code == 200
    assert "Unified Market Evidence Operator Workbench" in root_response.text

    explicit_html_response = client.get(
        "/workbench/mode-a/UnifiedMarketEvidenceWorkbench.html"
    )
    assert explicit_html_response.status_code == 200
    assert "Unified Market Evidence Operator Workbench" in explicit_html_response.text

    assert client.get("/workbench/mode-a/unified-workbench.css").status_code == 200
    assert client.get("/workbench/mode-a/unified-workbench.js").status_code == 200
    assert client.get("/api/health").status_code == 200


def test_validate_request_oversized_body(mock_validation):
    large_payload = "a" * (1 * 1024 * 1024 + 1)
    response = client.post("/api/unified/validate-request", content=large_payload)
    assert response.status_code == 413

def test_validate_request_missing_envelope(mock_validation):
    response = client.post("/api/unified/validate-request", json={})
    assert response.status_code == 422
    assert "missing 'request' key" in response.json()["detail"]

def test_validate_request_malformed_json(mock_validation):
    response = client.post("/api/unified/validate-request", content="{invalid json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json()["detail"] == "malformed_json_body"

def test_validate_request_too_large():
    large_req = {"request": {"targets": [{"input": "A" * (1 * 1024 * 1024)}]}}
    response = client.post("/api/unified/validate-request", json=large_req)
    assert response.status_code == 413
    assert response.json()["detail"] == "request_too_large"


@pytest.fixture()
def mock_preview(monkeypatch):
    from server import unified_workbench_router

    def fake_preview(req):
        return {
            "validation": {"request_id": req.get("request_id")},
            "preview": {
                "schema_version": "unified_market_evidence_preview_response.v1",
                "request_id": req.get("request_id"),
                "status": "ready_for_confirmation",
                "caveats": [
                    "PREVIEW_ONLY",
                    "NO_NETWORK_EXECUTED",
                    "EXECUTION_NOT_AUTHORIZED",
                ],
            },
            "orchestration_plan": {"execution_authorized": False},
            "network_executed": False,
            "authorization_created": False,
            "authorization_consumed": False,
            "execution_performed": False,
        }

    monkeypatch.setattr(unified_workbench_router, "build_mode_b1_preview", fake_preview)


def test_preview_request_returns_offline_non_authorizing_envelope(mock_preview):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "preview-api-test",
        "execution_mode": "preview",
        "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }
    response = client.post("/api/unified/preview-request", json={"request": req})
    assert response.status_code == 200
    result = response.json()
    assert result["preview"]["status"] == "ready_for_confirmation"
    assert result["network_executed"] is False
    assert result["authorization_created"] is False
    assert result["authorization_consumed"] is False
    assert result["execution_performed"] is False
    assert result["orchestration_plan"]["execution_authorized"] is False


@pytest.mark.parametrize(
    ("body", "expected_status"),
    [
        ("{bad", 400),
        (json.dumps({}), 422),
        (json.dumps({"request": []}), 422),
    ],
)
def test_preview_request_transport_validation(body, expected_status):
    response = client.post(
        "/api/unified/preview-request",
        content=body,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == expected_status


def test_preview_request_dependency_failures_are_sanitized(monkeypatch):
    from server import unified_workbench_router
    from server.services.unified_mode_b1 import ModeB1PlanningUnavailable

    def unavailable(_request):
        raise ModeB1PlanningUnavailable("P:\\secret\\authority.json")

    monkeypatch.setattr(unified_workbench_router, "build_mode_b1_preview", unavailable)
    response = client.post("/api/unified/preview-request", json={"request": {}})
    assert response.status_code == 409
    result = response.json()
    assert result["error"] == "mode_b1_planning_dependency_unavailable"
    assert "trace_id" in result
    serialized = json.dumps(result)
    assert "secret" not in serialized
    assert "traceback" not in serialized.lower()


def test_malformed_preview_schema_authority_is_409_at_real_service_boundary(
    monkeypatch,
):
    """The router must receive the service's bounded conversion, not a mocked error."""
    from server.services import unified_mode_b1

    class FakeSecurityMaster:
        pointer = {
            "index_path": "data/security_master/runtime_identity_indexes/test/index.json",
            "manifest_path": "data/security_master/runtime_identity_indexes/test/manifest.json",
            "compact_index_sha256": "a" * 64,
            "compact_manifest_sha256": "b" * 64,
        }

    from server.services.unified_mode_a import validate_mode_a_request
    from scripts.m8r_06_02_mode_b1_preview import load_planning_authorities

    authorities = load_planning_authorities()
    authorities["preview_schema"] = {"type": "not-a-json-schema-type"}
    monkeypatch.setattr(
        unified_mode_b1,
        "validate_mode_a_request",
        lambda request: validate_mode_a_request(request, allow_fixture_snapshot=True),
    )
    monkeypatch.setattr(
        unified_mode_b1,
        "get_production_mode_a_security_master",
        lambda _pointer: FakeSecurityMaster(),
    )
    monkeypatch.setattr(unified_mode_b1, "load_planning_authorities", lambda: authorities)

    request = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "malformed-preview-schema-authority",
        "execution_mode": "preview",
        "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }
    response = client.post("/api/unified/preview-request", json={"request": request})
    assert response.status_code == 409
    result = response.json()
    assert result["error"] == "mode_b1_planning_dependency_unavailable"
    assert "trace_id" in result
    serialized = json.dumps(result).lower()
    assert "jsonschema" not in serialized
    assert "traceback" not in serialized
    assert "preview_schema" not in serialized
    assert "\\" not in serialized and "/" not in serialized


def test_invalid_preview_output_is_500_not_dependency_unavailable(monkeypatch):
    """A valid authority rejecting our generated output is an implementation defect."""
    from server.services import unified_mode_b1

    class FakeSecurityMaster:
        pointer = {
            "index_path": "data/security_master/runtime_identity_indexes/test/index.json",
            "manifest_path": "data/security_master/runtime_identity_indexes/test/manifest.json",
            "compact_index_sha256": "a" * 64,
            "compact_manifest_sha256": "b" * 64,
        }

    from server.services.unified_mode_a import validate_mode_a_request
    from scripts.m8r_06_02_mode_b1_preview import load_planning_authorities

    authorities = load_planning_authorities()
    authorities["preview_schema"] = {"type": "object", "required": ["missing"]}
    monkeypatch.setattr(
        unified_mode_b1,
        "validate_mode_a_request",
        lambda request: validate_mode_a_request(request, allow_fixture_snapshot=True),
    )
    monkeypatch.setattr(
        unified_mode_b1,
        "get_production_mode_a_security_master",
        lambda _pointer: FakeSecurityMaster(),
    )
    monkeypatch.setattr(unified_mode_b1, "load_planning_authorities", lambda: authorities)
    response = client.post(
        "/api/unified/preview-request",
        json={
            "request": {
                "schema_version": "unified_market_evidence_request.v1",
                "request_id": "invalid-preview-output",
                "execution_mode": "preview",
                "targets": [{"input": "2330", "market_hint": "TWSE"}],
                "data_needs": [
                    {"type": "current_observation", "priority": "required"}
                ],
            }
        },
    )
    assert response.status_code == 500
    result = response.json()
    assert result["error"] == "mode_b1_internal_error"
    assert "trace_id" in result
    assert "dependency" not in json.dumps(result).lower()


def test_real_sealed_candidate_preview_endpoint_executes_locally_without_monkeypatch():
    candidate = (
        Path(__file__).resolve().parents[2]
        / "data/security_master/runtime_identity_indexes"
        / "m8r06-01b-20260807T053540Z/index.json"
    )
    if not candidate.exists():
        pytest.skip("governed local candidate is Git-ignored")
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "sealed-mode-b1-preview",
        "execution_mode": "preview",
        "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }
    response = client.post("/api/unified/preview-request", json={"request": req})
    assert response.status_code == 200
    result = response.json()
    assert result["validation"]["target_results"][0]["canonical_identity"][
        "canonical_target_id"
    ] == "TWSE:2330"
    assert result["preview"]["status"] == "ready_for_confirmation"
    assert result["orchestration_plan"]["operations"][0]["security_types"] == [
        "equity"
    ]
    assert result["network_executed"] is False
    assert result["execution_performed"] is False
