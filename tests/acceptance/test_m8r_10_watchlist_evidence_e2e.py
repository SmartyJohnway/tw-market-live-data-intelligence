"""Fresh-install, offline M8R-10 Watchlist-to-evidence acceptance."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
from scripts.m8r_06_02_mode_b1_preview import (
    build_mode_b1_preview_package,
    load_planning_authorities,
)
from scripts.m8r_08g_identity_service import TaiwanMarketIdentityService
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore
from server.services import unified_mode_b2, unified_mode_b2_execution, unified_mode_c
from server.services.unified_mode_a import validate_mode_a_request
from server.services.watchlist_evidence_composer import WatchlistEvidenceComposer


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "m8r_05a_f3"


class _FixturePlanningSecurityMaster:
    pointer = {
        "index_path": "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json",
        "manifest_path": "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot_manifest.json",
        "compact_index_sha256": "a" * 64,
        "compact_manifest_sha256": "b" * 64,
    }


def _command(command_type: str, **values):
    return {
        "schema_version": "persistent_watchlist_mutation_command.v1",
        "command_type": command_type,
        "actor_source": "human",
        **values,
    }


def _commit(store: PersistentWatchlistStore, preview: dict) -> dict:
    return store.commit(
        preview_id=preview["preview_id"],
        preview_hash=preview["content_sha256"],
        confirmed=True,
    )["watchlist"]


def _identity_service() -> TaiwanMarketIdentityService:
    verified = load_f3_verified_security_master(
        FIXTURE_ROOT / "verified_security_master_snapshot.json",
        FIXTURE_ROOT / "verified_security_master_snapshot_manifest.json",
        allow_fixture_snapshot=True,
    )
    return TaiwanMarketIdentityService(
        verified.snapshot["records"],
        release_id="m8r10-deterministic-qualified-fixture",
        manifest_hash="c" * 64,
    )


def test_fresh_install_watchlist_to_deterministic_result_audit_and_handoff(
    tmp_path: Path, monkeypatch
):
    """Exercise the complete product chain without production state or network."""
    install_root = tmp_path / "fresh-install"
    watchlist_root = install_root / "watchlists"
    control_root = install_root / "control"
    counter_root = install_root / "source-invocations"
    service = _identity_service()

    store = PersistentWatchlistStore(root=watchlist_root, identity_service=service)
    assert store.list_watchlists() == {"state": "NO_WATCHLISTS", "watchlists": []}
    created = _commit(
        store,
        store.preview(_command("create_watchlist", name="Fresh install")),
    )
    persisted = _commit(
        store,
        store.preview(
            _command(
                "add_entry",
                watchlist_id=created["watchlist_id"],
                expected_version=created["current_version"],
                query="2330",
                market_hint="TWSE",
            )
        ),
    )
    assert persisted["entries"][0]["instrument_id"] == "TW0002330008"

    # A fresh service instance must recover the exact persisted version.
    restarted = PersistentWatchlistStore(root=watchlist_root, identity_service=service)
    current = restarted.get_watchlist(persisted["watchlist_id"])
    assert current["current_version"] == 2
    assert (ROOT / "frontend" / "unified-workbench" / "UnifiedMarketEvidenceWorkbench.html").is_file()

    def fixture_validation(request: dict) -> dict:
        return validate_mode_a_request(request, allow_fixture_snapshot=True)

    composition = WatchlistEvidenceComposer(
        store=restarted,
        request_validator=fixture_validation,
        now=lambda: "2026-09-11T00:00:00Z",
    ).compose(
        {
            "schema_version": "watchlist_evidence_selection_request.v1",
            "expected_watchlist_version": current["current_version"],
            "selected_entry_ids": [current["entries"][0]["watchlist_entry_id"]],
            "temporary_targets": [],
            "data_needs": [
                {
                    "type": "current_observation",
                    "priority": "required",
                    "parameters": {},
                    "client_need_reference": "fresh-install-current",
                }
            ],
            "execution_mode": "execute",
            "response_preferences": {
                "include_citations": True,
                "include_currentness": True,
                "include_caveats": True,
                "include_audit_reference": True,
            },
        },
        watchlist_id=current["watchlist_id"],
    )
    request = composition["request"]
    validation = composition["validation"]
    assert composition["composition_status"] == "composed"
    assert validation["validation_status"] == "valid"

    preview_package = build_mode_b1_preview_package(
        request,
        validation,
        _FixturePlanningSecurityMaster(),
        planning_timestamp="2026-09-11T00:00:00Z",
        authorities=load_planning_authorities(),
    )
    preview = preview_package["preview"]
    plan = preview_package["orchestration_plan"]
    assert preview["status"] == "ready_for_confirmation"
    assert len(plan["operations"]) == 1

    monkeypatch.setattr(unified_mode_b2, "CONTROL_ROOT", control_root)
    monkeypatch.setattr(
        unified_mode_b2, "build_mode_b1_preview", lambda _request: preview_package
    )
    monkeypatch.setattr(
        unified_mode_b2,
        "load_selection_provenance_for_request",
        lambda _request: composition["selection_provenance"],
    )
    authorization = unified_mode_b2.build_mode_b2_authorization(
        {
            "request": request,
            "expected_preview_id": preview["internal_execution_reference"]["preview_id"],
            "expected_plan_id": plan["plan_id"],
            "expected_plan_hash": plan["plan_hash"],
            "confirm_authorization": True,
            "approval_scope_mode": "whole_plan_executable_scope",
        }
    )
    assert authorization["selection_provenance_bound"] is True

    monkeypatch.setenv("M8R_06_03_CONTROL_ROOT", str(control_root))
    monkeypatch.setenv("M8R_06_03_EXECUTION_ENVIRONMENT", "test")
    monkeypatch.setenv("M8R_06_03_TEST_SOURCE_TRANSPORT", "deterministic")
    monkeypatch.setenv("M8R_06_03_TEST_INVOCATION_COUNTER", str(counter_root))
    execution = unified_mode_b2_execution.execute_mode_b2_once(
        {
            "control_package_id": authorization["control_package_id"],
            "confirm_execution": True,
            "operator_confirmation_reference": "m8r10-fresh-install-e2e",
            "confirm_network_execution": True,
        }
    )
    assert execution["consumption_state"] == "consumed_success"
    assert execution["external_market_network_attempted"] is False
    assert execution["external_market_network_executed"] is False
    assert len(list(counter_root.glob("*.invoked"))) == 1

    monkeypatch.setattr(unified_mode_c, "CONTROL_ROOT", control_root)
    monkeypatch.setattr(unified_mode_c, "validate_mode_a_request", fixture_validation)
    result = unified_mode_c.build_mode_c_result_package(
        {"control_package_id": authorization["control_package_id"]}
    )
    audit = unified_mode_c.read_mode_c_audit(authorization["control_package_id"])
    handoff = unified_mode_c.build_mode_c_ai_handoff(authorization["control_package_id"])
    provenance = result["selection_provenance_identity"]
    assert result["result_status"] == "full_success"
    assert provenance["watchlist_id"] == current["watchlist_id"]
    assert provenance["watchlist_version"] == current["current_version"]
    assert provenance["selected_instrument_ids"] == ["TW0002330008"]
    assert audit["selection_provenance_identity"] == provenance
    assert handoff["selection_provenance_identity"] == provenance
    assert handoff["canonical_result"] == result["canonical_result"]
    assert handoff["additional_market_network_executed"] is False
    assert len(list(counter_root.glob("*.invoked"))) == 1
    assert json.loads(
        (control_root / authorization["authorization_id"] / "control" / "selection_provenance.json").read_text(
            encoding="utf-8"
        )
    ) == composition["selection_provenance"]
