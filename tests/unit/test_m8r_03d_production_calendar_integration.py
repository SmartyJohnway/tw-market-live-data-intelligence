import json
import pytest
import uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan

TAIPEI = ZoneInfo("Asia/Taipei")

MOCK_HOLIDAY_RECORDS = [
    {"Name": "中華民國開國紀念日", "Date": "1150101", "Weekday": "四", "Description": "依規定放假1日。"},
    {"Name": "國曆新年開始交易日", "Date": "1150102", "Weekday": "五", "Description": "國曆新年開始交易。"}
]

PHASE_C_REGISTRY = {
    "schema_version": "m8_source_capability_registry.v1",
    "phase_c_activation_status": "conversation_driven_enabled_with_caveats",
    "active_runtime_source_families": ["TWSE_MIS", "TAIFEX_MIS", "TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI"],
    "twse_mis_runtime_executable": True,
    "twse_openapi_runtime_executable": True,
    "tpex_openapi_runtime_executable": True,
    "m8_active_consolidated_status": {
        "twse_mis_runtime_executable": True,
        "twse_openapi_runtime_executable": True,
        "tpex_openapi_runtime_executable": True
    },
    "sources": [
        {"source_family": "TWSE_MIS", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"},
        {"source_family": "TAIFEX_MIS", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"},
        {"source_family": "TWSE_OPENAPI", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"},
        {"source_family": "TPEX_OPENAPI", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"},
        {"source_family": "TAIFEX_OPENAPI", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"}
    ]
}

class MockHttpResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode('utf-8')
    def read(self):
        return self.data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def load_schema_compliant_request() -> dict:
    p = Path("tests/fixtures/m8r_03e/complete_snapshot/request.json")
    req = json.loads(p.read_text(encoding="utf-8"))
    req["execution_policy"]["network_allowed"] = True
    req["execution_policy"]["execution_profile"] = "phase_c_conversation_driven_one_shot.v1"
    # Generate unique request_id to prevent authorization replay issues during testing
    req["request_id"] = f"test-req-{uuid.uuid4()}"
    return req

def test_production_calendar_successful_fetch_and_caching(monkeypatch, tmp_path):
    def mock_urlopen(req, timeout=10):
        return MockHttpResponse(MOCK_HOLIDAY_RECORDS)
        
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    request_payload = load_schema_compliant_request()
    
    # Build execution plan to get correct preview aligned with generated_at_utc
    gen_time = "2026-01-02T14:30:00Z"
    plan = build_execution_plan(request_payload, bundle_type="snapshot", generated_at_utc=gen_time, source_capability_registry=PHASE_C_REGISTRY)
    preview = plan["execution_preview"]
    
    approval = {
        "schema_version": "m8r_phase_c_conversation_approval.v1",
        "approval_mode": "conversation_explicit_approval",
        "preview_id": preview["preview_id"],
        "request_id": request_payload["request_id"],
        "approval_status": "approved",
        "approved_at_utc": "2026-07-21T08:05:00Z",
        "approved_text_summary": "執行"
    }

    mock_source_data = {
        "TWSE_OPENAPI": {
            "observations": [
                {
                    "symbol": "2330",
                    "trade_date": "2026-01-02",
                    "open": "500.0",
                    "high": "510.0",
                    "low": "490.0",
                    "close": "505.0",
                    "volume": "1000",
                    "retrieved_at_utc": "2026-01-02T14:00:00Z"
                }
            ],
            "source_status": "success",
            "reported_trade_dates": ["2026-01-02"]
        }
    }
    
    def mock_fetch(groups, security_master):
        return {
            "group_results": [
                {
                    "source_family": "TWSE_OPENAPI",
                    "status": "success",
                    "results": mock_source_data["TWSE_OPENAPI"]
                }
            ],
            "network_calls_performed": True
        }
        
    executors = {"fetch_source_call_groups": mock_fetch}

    # Run in execute mode
    res = execute_watchlist(
        request_payload,
        mode="execute",
        bundle_type="snapshot",
        artifact_root=str(tmp_path / "artifacts"),
        run_id="run-prod-test",
        generated_at_utc=gen_time,
        preview=preview,
        approval=approval,
        executors=executors,
        source_capability_registry=PHASE_C_REGISTRY
    )
    
    assert res["status"] in ("success", "success_with_partial_coverage")
    
    # Verify that the calendar cache file was written to the tmp_path artifacts folder
    cache_file = tmp_path / "artifacts" / "twse_trading_calendar.json"
    assert cache_file.exists()
    
    # Read the cache file and verify it matches TWSE calendar schema version 1
    cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert cache_data["schema_version"] == "twse_trading_calendar.v1"
    assert cache_data["year"] == 2026

def test_production_calendar_fallback_on_network_failure(monkeypatch, tmp_path):
    def mock_urlopen_fail(req, timeout=10):
        raise IOError("Network connection refused")
        
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen_fail)
    
    request_payload = load_schema_compliant_request()
    
    gen_time = "2026-01-02T14:30:00Z"
    plan = build_execution_plan(request_payload, bundle_type="snapshot", generated_at_utc=gen_time, source_capability_registry=PHASE_C_REGISTRY)
    preview = plan["execution_preview"]
    
    approval = {
        "schema_version": "m8r_phase_c_conversation_approval.v1",
        "approval_mode": "conversation_explicit_approval",
        "preview_id": preview["preview_id"],
        "request_id": request_payload["request_id"],
        "approval_status": "approved",
        "approved_at_utc": "2026-07-21T08:05:00Z",
        "approved_text_summary": "執行"
    }

    mock_source_data = {
        "TWSE_OPENAPI": {
            "observations": [
                {
                    "symbol": "2330",
                    "trade_date": "2026-01-02",
                    "open": "500.0",
                    "high": "510.0",
                    "low": "490.0",
                    "close": "505.0",
                    "volume": "1000",
                    "retrieved_at_utc": "2026-01-02T14:00:00Z"
                }
            ],
            "source_status": "success",
            "reported_trade_dates": ["2026-01-02"]
        }
    }
    
    def mock_fetch(groups, security_master):
        return {
            "group_results": [
                {
                    "source_family": "TWSE_OPENAPI",
                    "status": "success",
                    "results": mock_source_data["TWSE_OPENAPI"]
                }
            ],
            "network_calls_performed": True
        }
        
    executors = {"fetch_source_call_groups": mock_fetch}

    # Run execution - this will trigger fallback logic because calendar fetch fails
    res = execute_watchlist(
        request_payload,
        mode="execute",
        bundle_type="snapshot",
        artifact_root=str(tmp_path / "artifacts"),
        run_id="run-prod-fail",
        generated_at_utc=gen_time,
        preview=preview,
        approval=approval,
        executors=executors,
        source_capability_registry=PHASE_C_REGISTRY
    )
    
    assert res["status"] in ("success", "success_with_partial_coverage")
    
    # Because of network failure, no cache file should be created
    cache_file = tmp_path / "artifacts" / "twse_trading_calendar.json"
    assert not cache_file.exists()
