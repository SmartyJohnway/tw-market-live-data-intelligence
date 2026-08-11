import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.services import unified_mode_c
from server.services.unified_mode_c import ModeCError, build_mode_c_result_package
from scripts.m8r_06_01c2_mode_a_security_master_loader import reset_production_mode_a_security_master_for_tests


PACKAGE_ID = "umea-v1-b723c9ae498a6a7fab68"


@pytest.fixture(autouse=True)
def reset_mode_a_runtime():
    reset_production_mode_a_security_master_for_tests()
    yield
    reset_production_mode_a_security_master_for_tests()


@pytest.fixture()
def mode_c_root(tmp_path, monkeypatch):
    source = Path("artifacts/m8r_06_03_workbench") / PACKAGE_ID
    root = tmp_path / "control"
    root.mkdir()
    shutil.copytree(source, root / PACKAGE_ID)
    for relative in ("ai_context", "audit", "mode_c"):
        shutil.rmtree(root / PACKAGE_ID / relative, ignore_errors=True)
    monkeypatch.setattr(unified_mode_c, "CONTROL_ROOT", root)
    return root / PACKAGE_ID


def test_mode_c_materializes_verified_live_package_without_network(mode_c_root, monkeypatch):
    monkeypatch.setattr(unified_mode_c, "validate_mode_a_request", unified_mode_c.validate_mode_a_request)
    result = build_mode_c_result_package({"control_package_id": PACKAGE_ID})
    assert result["result_status"] == "full_success"
    assert result["external_market_network_executed"] is False
    assert result["materialization"] == "newly_materialized"
    assert (mode_c_root / result["canonical_result_reference"]).is_file()
    assert build_mode_c_result_package({"control_package_id": PACKAGE_ID})["materialization"] == "existing_verified"


@pytest.mark.parametrize("relative", ["claims", "receipts", "bundles"])
def test_mode_c_rejects_missing_final_execution_artifacts(mode_c_root, relative):
    shutil.rmtree(mode_c_root / relative)
    with pytest.raises(ModeCError):
        build_mode_c_result_package({"control_package_id": PACKAGE_ID})


def test_mode_c_rejects_nonfinal_claim(mode_c_root):
    claim = next((mode_c_root / "claims").glob("*.json"))
    data = json.loads(claim.read_text())
    data["state"] = "claimed"
    claim.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ModeCError, match="mode_c_execution_not_finalized"):
        build_mode_c_result_package({"control_package_id": PACKAGE_ID})


def test_mode_c_rejects_evidence_tampering(mode_c_root):
    evidence = next((mode_c_root / "evidence").glob("*.json"))
    evidence.write_text("{}", encoding="utf-8")
    with pytest.raises(ModeCError, match="mode_c_lineage_verification_failed"):
        build_mode_c_result_package({"control_package_id": PACKAGE_ID})


def test_mode_c_rejects_f3_reconstruction_mismatch(mode_c_root, monkeypatch):
    monkeypatch.setattr(unified_mode_c, "validate_mode_a_request", lambda _request: {})
    with pytest.raises(ModeCError, match="mode_c_f3_reconstruction_mismatch"):
        build_mode_c_result_package({"control_package_id": PACKAGE_ID})


def test_mode_c_rejects_browser_privileged_fields():
    with pytest.raises(ModeCError, match="invalid_api_envelope"):
        build_mode_c_result_package({"control_package_id": PACKAGE_ID, "output_root": "C:/no"})


def test_mode_c_api_rejects_privileged_browser_paths():
    from server.main import app
    response = TestClient(app).post("/api/unified/result-package", json={
        "control_package_id": PACKAGE_ID, "receipt_path": "C:/outside.json"
    })
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_api_envelope"
