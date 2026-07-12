import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/protocol/M8A_OFFICIAL_EOD_ADAPTER_SCOPE_AND_CONTRACT_PREFLIGHT.md"
REGISTRY = ROOT / "docs/data_capabilities/m8a_official_eod_endpoint_contract_registry.json"
FIELD_MAPPING = ROOT / "docs/data_capabilities/m8a_official_eod_field_mapping.csv"
SCHEMA_DOC = ROOT / "docs/protocol/M8A_OFFICIAL_EOD_NORMALIZED_OBSERVATION_SCHEMA.md"
FAILURE_DOC = ROOT / "docs/protocol/M8A_OFFICIAL_EOD_FAILURE_CURRENTNESS_AND_NON_TRADING_DAY_CONTRACT.md"
BLUEPRINT = ROOT / "docs/protocol/M8A_01_03_COMBINED_IMPLEMENTATION_BLUEPRINT.md"
INVENTORY = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"
PROBES = ROOT / "research/probe_runs/m8a_official_eod_contract_preflight"

VALID_READINESS = {"go", "conditional_go", "no_go"}
RECONCILIATION = ROOT / "research/probe_runs/m8a_official_eod_contract_preflight/m8a_official_eod_currentness_reconciliation_20260711T102435Z.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_preflight_doc_exists_status_and_next_task():
    text = DOC.read_text(encoding="utf-8")
    assert "m8a_00_official_eod_adapter_scope_and_contract_preflight_complete" in text
    assert "M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE" in text
    assert "Final result: `pass_with_caveats`" in text


def test_contract_registry_schema_and_source_boundaries():
    data = load_json(REGISTRY)
    assert data["schema_version"] == "m8a_official_eod_endpoint_contract_registry.v1"
    by_source = {s["source_id"]: s for s in data["sources"]}
    assert {"TWSE_OPENAPI", "TPEX_OPENAPI"}.issubset(by_source)
    for source in by_source.values():
        assert source["selected_endpoint_contract_id"]
        assert source["readiness"] in VALID_READINESS
        assert source["adapter_implemented"] is False
        assert source["runtime_executable_now"] is False
        assert source["network_fetch_added"] is False


def test_required_endpoint_contract_fields():
    data = load_json(REGISTRY)
    required = {
        "preferred_endpoint",
        "date_semantics",
        "update_semantics",
        "response_contract",
        "field_contract",
        "failure_contract",
        "readiness",
        "caveats",
    }
    for source in data["sources"]:
        assert required.issubset(source)
        endpoint = source["preferred_endpoint"]
        assert endpoint["endpoint_url_template"].startswith("https://")
        assert endpoint["method"] == "GET"
        assert "required_parameters" in endpoint
        assert source["field_contract"]
        for field in source["field_contract"]:
            for key in [
                "source_field",
                "source_path",
                "normalized_field",
                "source_type",
                "normalized_type",
                "unit",
                "unit_evidence",
                "conversion_rule",
                "validation_rule",
                "AI_context_eligible",
                "evidence_status",
                "evidence_reference",
            ]:
                assert key in field


def test_field_mapping_matrix_columns_and_sources():
    with FIELD_MAPPING.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    required_columns = {
        "source_id",
        "endpoint_contract_id",
        "source_field",
        "source_label",
        "sample_value",
        "source_type",
        "nullable",
        "special_markers",
        "normalized_field",
        "normalized_type",
        "unit",
        "unit_status",
        "date_semantics",
        "identity_semantics",
        "conversion_rule",
        "validation_rule",
        "required_for_valid_row",
        "AI_context_eligible",
        "evidence_status",
        "evidence_reference",
        "open_question",
        "notes",
    }
    assert required_columns.issubset(rows[0].keys())
    assert {r["source_id"] for r in rows} >= {"TWSE_OPENAPI", "TPEX_OPENAPI"}


def test_normalized_schema_document_required_contracts():
    text = SCHEMA_DOC.read_text(encoding="utf-8")
    for token in [
        "m8a_official_eod_observation.v1",
        "source_id",
        "market",
        "symbol",
        "trade_date",
        "retrieved_at_utc",
        "source_status",
        "observation_status",
        "price",
        "activity",
        "field_validation",
        "provenance",
        "Partial-row policy",
        "Raw payload policy",
        "Derivation policy",
    ]:
        assert token in text


def test_identity_contract_documented():
    text = DOC.read_text(encoding="utf-8") + SCHEMA_DOC.read_text(encoding="utf-8")
    assert "Canonical instrument identity: `(market, symbol)`" in text or "Canonical identity is `(market, symbol)`" in text
    assert "listed" in text
    assert "tpex_otc" in text


def test_failure_currentness_contract_distinctions():
    text = FAILURE_DOC.read_text(encoding="utf-8")
    for token in [
        "empty_non_trading_day",
        "source_unavailable",
        "source_error",
        "schema_drift",
        "date_mismatch",
        "valid_zero_trade_row",
        "successful_eod_batch",
        "partial_source_success",
    ]:
        assert token in text


def test_implementation_blueprint_commits_and_next_task():
    text = BLUEPRINT.read_text(encoding="utf-8")
    for token in ["Commit 1", "Commit 2", "Commit 3", "Commit 4", "M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE"]:
        assert token in text


def test_currentness_reconciliation_artifact_and_registry_statuses():
    data = load_json(RECONCILIATION)
    assert data["calendar_evidence"]["probe_time_utc"] == "2026-07-11T10:24:35Z"
    assert data["calendar_evidence"]["probe_time_asia_taipei"] == "2026-07-11T18:24:35+08:00"
    assert data["calendar_evidence"]["expected_latest_completed_trade_date"] == "2026-07-09"
    assert data["calendar_evidence"]["scheduled_calendar_status"] == "scheduled_trading_day"
    assert data["calendar_evidence"]["emergency_closure_status"] == "emergency_closure_confirmed"
    assert data["calendar_evidence"]["actual_market_day_status"] == "emergency_closed"
    statuses = {r["source_id"]: r for r in data["source_reconciliations"]}
    assert statuses["TWSE_OPENAPI"]["reported_trade_date"] == "2026-07-09"
    assert statuses["TPEX_OPENAPI"]["reported_trade_date"] == "2026-07-09"
    for reconciliation in statuses.values():
        assert reconciliation["trading_day_lag"] == 0
        assert reconciliation["scheduled_calendar_status"] == "scheduled_trading_day"
        assert reconciliation["emergency_closure_status"] == "emergency_closure_confirmed"
        assert reconciliation["actual_market_day_status"] == "emergency_closed"
        assert reconciliation["currentness_reconciliation_status"] == "matches_expected_latest_trade_date_after_emergency_closure"
    registry = load_json(REGISTRY)
    for source in registry["sources"]:
        assert source["readiness"] == "conditional_go"
        assert source["currentness_reconciliation"]["currentness_reconciliation_status"] == "matches_expected_latest_trade_date_after_emergency_closure"


def test_calendar_authority_model_prevents_holiday_absence_shortcut():
    data = load_json(RECONCILIATION)
    calendar = data["calendar_evidence"]
    assert calendar["scheduled_calendar_status"] == "scheduled_trading_day"
    assert calendar["emergency_closure_status"] == "emergency_closure_confirmed"
    assert calendar["actual_market_day_status"] == "emergency_closed"
    assert calendar["expected_latest_completed_trade_date"] == "2026-07-09"
    assert any("holidaySchedule absence only" in item for item in calendar["evidence"])
    assert any("TWSE closure announcement" in item for item in calendar["evidence"])


def test_emergency_closure_rules_for_future_runtime_are_documented():
    failure_text = FAILURE_DOC.read_text(encoding="utf-8")
    blueprint_text = BLUEPRINT.read_text(encoding="utf-8")
    for token in [
        "scheduled_calendar_status",
        "emergency_closure_status",
        "actual_market_day_status",
        "Annual holidaySchedule absence must never by itself prove",
        "unresolved_date_mismatch",
    ]:
        assert token in failure_text
    assert "annual holiday absence alone cannot produce `actual_trading_day`" in blueprint_text


def test_field_specific_conversion_and_validation_rules():
    registry = load_json(REGISTRY)
    fields = {
        (source["source_id"], field["source_field"]): field
        for source in registry["sources"]
        for field in source["field_contract"]
    }
    assert "ROC yyyMMdd" in fields[("TWSE_OPENAPI", "Date")]["conversion_rule"]
    assert "exact trimmed source string" in fields[("TWSE_OPENAPI", "Code")]["conversion_rule"]
    assert "leading zeroes" in fields[("TWSE_OPENAPI", "Code")]["conversion_rule"]
    assert "alphabetic suffixes" in fields[("TPEX_OPENAPI", "SecuritiesCompanyCode")]["conversion_rule"]
    assert "Unicode security name" in fields[("TPEX_OPENAPI", "CompanyName")]["conversion_rule"]
    assert "do not apply numeric/date conversion" in fields[("TWSE_OPENAPI", "Name")]["conversion_rule"]
    assert "non-negative Decimal-compatible" in fields[("TWSE_OPENAPI", "OpeningPrice")]["conversion_rule"]
    assert "reject malformed or negative price" in fields[("TPEX_OPENAPI", "Close")]["validation_rule"]
    assert "signed Decimal-compatible" in fields[("TPEX_OPENAPI", "Change")]["conversion_rule"]
    assert "negative values are valid for change only" in fields[("TWSE_OPENAPI", "Change")]["validation_rule"]
    assert "non-negative integer" in fields[("TWSE_OPENAPI", "TradeVolume")]["conversion_rule"]
    assert "non-negative integer TWD trade value" in fields[("TPEX_OPENAPI", "TransactionAmount")]["conversion_rule"]
    assert "non-negative integer transaction count" in fields[("TPEX_OPENAPI", "TransactionNumber")]["conversion_rule"]
    assert fields[("TPEX_OPENAPI", "LatestBidPrice")]["AI_context_eligible"] is False
    assert "omit from normalized M8A core" in fields[("TPEX_OPENAPI", "LatestBidPrice")]["partial_row_policy"]
    assert fields[("TWSE_OPENAPI", "OpeningPrice")]["evidence_status"] in {"directly_observed", "inferred_with_caveat"}


def test_go_no_go_matrix_values():
    data = load_json(REGISTRY)
    readiness = data["implementation_readiness"]
    assert readiness["twse_endpoint_readiness"] in VALID_READINESS
    assert readiness["tpex_endpoint_readiness"] in VALID_READINESS
    assert readiness["twse_field_contract_readiness"] in VALID_READINESS
    assert readiness["tpex_field_contract_readiness"] in VALID_READINESS
    assert data["shared_contract_decision"]["shared_normalized_schema"] in {"accepted", "accepted_with_source_extensions", "rejected"}
    assert readiness["controlled_runtime_design"] in {"accepted", "conditional", "blocked"}
    assert readiness["combined_implementation_pr_feasible"] in {"yes", "conditional", "no"}
    assert readiness["currentness_reconciliation_required"] is True
    assert readiness["currentness_reconciliation_status"] == "matches_expected_latest_trade_date_after_emergency_closure"
    assert readiness["calendar_authority_model_required"] is True


def test_boundary_preservation_inventory():
    inv = load_json(INVENTORY)["rich_observation_contract"]["milestone_snapshots"]["state_at_m8a_00_preflight"]
    for key in [
        "adapter_implemented",
        "runtime_fetch_implemented",
        "network_runtime_added",
        "context_integration_added",
        "conversation_integration_added",
        "frontend_changed",
        "server_changed",
        "mcp_changed",
        "scheduler_added",
        "polling_added",
        "startup_fetch_added",
        "hidden_fetch_added",
        "db_write_added",
        "raw_payload_committed",
        "taifex_scope_added",
        "tpex_mis_introduced",
        "rotc_route_introduced",
    ]:
        assert inv[key] is False
    assert inv["currentness_reconciliation_required"] is True
    assert inv["latest_probe_currentness_reconciliation_status"] == "matches_expected_latest_trade_date_after_emergency_closure"
    assert inv["calendar_authority_model_required"] is True


def test_probe_artifacts_compactness():
    if not PROBES.exists():
        return
    for path in PROBES.glob("*.json"):
        data = load_json(path)
        payload = json.dumps(data, ensure_ascii=False).lower()
        assert "cookie" not in payload
        assert "authorization" not in payload
        assert "raw_payload" not in payload
        probes = data.get("probes") or [data] if "probe_id" in data else data.get("probes", [])
        for probe in probes:
            if not isinstance(probe, dict):
                continue
            assert probe.get("source_id")
            assert probe.get("requested_at_utc")
            assert len(probe.get("representative_rows", [])) <= 5


def test_existing_m8_closure_preserved():
    inv = load_json(INVENTORY)["rich_observation_contract"]
    m8 = inv["milestone_snapshots"]["state_at_m8_00_acceptance"]
    assert m8["final_acceptance_status"] == "pass_with_caveats"
    assert m8["completed_tasks"] == ["M8-00-00", "M8-00-01", "M8-00-02", "M8-00-03", "M8-00-04", "M8-00-05", "M8-00-06", "M8-00-07", "M8-00-08"]
    assert m8["final_acceptance_doc"] == "docs/protocol/M8_00_FINAL_ACCEPTANCE_AND_CLOSURE.md"
