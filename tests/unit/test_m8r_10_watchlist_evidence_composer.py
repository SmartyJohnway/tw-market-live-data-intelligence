from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.m8r_08g_identity_service import TaiwanMarketIdentityService
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore, WatchlistError
from server.services.watchlist_evidence_composer import (
    WatchlistEvidenceComposer,
    WatchlistEvidenceCompositionError,
    load_selection_provenance_for_request,
    validate_selection_provenance,
)
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.citation_builder import build_citation_index
from scripts.m8r_05c.evidence_projector import CURRENT_PROJECTOR_VERSION
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.result_builder import build_result
from tests.unit.test_m8r_06_ai_handoff_repair_02 import _plan_only_inputs


def _record(code: str, isin: str, market: str = "TWSE", kind: str = "common_share", name: str | None = None):
    return {
        "canonical_target_id": f"{market}:{code}",
        "identity": {"security_code": code, "isin": isin, "security_name_zh": name or f"名稱{code}"},
        "classification": {"market": market, "instrument_type": kind},
        "lifecycle": {"state": "listed", "resolution_status": "resolved", "as_of": "2026-09-11", "events": []},
        "execution_eligibility": {"status": "allowed", "reason_codes": []},
    }


@pytest.fixture
def service():
    return TaiwanMarketIdentityService(
        [
            _record("2330", "TW0002330008"),
            _record("6488", "TW0006488001", "TPEX"),
            _record("1234", "TW0001234001", kind="warrant"),
            _record("1111", "TW0001111000", name="同名"),
            _record("2222", "TW0002222000", name="同名"),
        ],
        release_id="security-master-test",
        manifest_hash="a" * 64,
    )


@pytest.fixture
def store(tmp_path, service):
    return PersistentWatchlistStore(root=tmp_path / "watchlists", identity_service=service)


def _command(kind: str, **kwargs):
    return {"schema_version": "persistent_watchlist_mutation_command.v1", "command_type": kind, "actor_source": "human", **kwargs}


def _commit(store, preview):
    return store.commit(preview_id=preview["preview_id"], preview_hash=preview["content_sha256"], confirmed=True)["watchlist"]


def _watchlist(store):
    current = _commit(store, store.preview(_command("create_watchlist", name="主要清單")))
    for query, market in (("2330", "TWSE"), ("6488", "TPEX"), ("1234", "TWSE")):
        current = _commit(store, store.preview(_command("add_entry", watchlist_id=current["watchlist_id"], expected_version=current["current_version"], query=query, market_hint=market)))
    return current


def _payload(current=None, *, temporary=None, selected=None, need="identity"):
    return {
        "schema_version": "watchlist_evidence_selection_request.v1",
        "expected_watchlist_version": current["current_version"] if current else None,
        "selected_entry_ids": selected if selected is not None else ([entry["watchlist_entry_id"] for entry in current["entries"]] if current else []),
        "temporary_targets": temporary or [],
        "data_needs": [{"type": need, "priority": "required", "parameters": {}, "client_need_reference": "need-1"}],
        "execution_mode": "execute",
        "response_preferences": {"include_citations": True, "include_currentness": True, "include_caveats": True, "include_audit_reference": True},
    }


def _validator(request):
    return {"validation_status": "valid", "request_id": request["request_id"]}


def test_selection_schemas_are_formal():
    root = Path("docs/contracts/schemas")
    for name in ("watchlist_evidence_selection_request.v1.schema.json", "watchlist_evidence_selection.v1.schema.json"):
        Draft202012Validator.check_schema(json.loads((root / name).read_text(encoding="utf-8")))


def test_persistent_selection_order_request_and_provenance(store):
    current = _watchlist(store)
    selected = [current["entries"][2]["watchlist_entry_id"], current["entries"][0]["watchlist_entry_id"]]
    result = WatchlistEvidenceComposer(store=store, request_validator=_validator).compose(_payload(current, selected=selected), watchlist_id=current["watchlist_id"])
    assert result["composition_status"] == "composed"
    assert [target["input"] for target in result["request"]["targets"]] == ["TW0002330008", "TW0001234001"]
    assert [target["client_target_reference"] for target in result["request"]["targets"]] == [current["entries"][0]["watchlist_entry_id"], current["entries"][2]["watchlist_entry_id"]]
    provenance = result["selection_provenance"]
    assert provenance["watchlist"]["version"] == current["current_version"]
    assert provenance["watchlist"]["revision_sha256"] == store.revision(current["watchlist_id"], current["current_version"])["content_sha256"]
    assert load_selection_provenance_for_request(result["request"], root=store.root) == provenance


def test_enabled_is_not_implicit_selection_and_explicit_enabled_selection(store):
    current = _watchlist(store)
    entry = current["entries"][0]
    current = _commit(store, store.preview(_command("set_entry_enabled", watchlist_id=current["watchlist_id"], expected_version=current["current_version"], watchlist_entry_id=entry["watchlist_entry_id"], enabled=False)))
    all_result = WatchlistEvidenceComposer(store=store, request_validator=_validator).compose(_payload(current), watchlist_id=current["watchlist_id"])
    assert len(all_result["request"]["targets"]) == 3
    enabled_ids = [item["watchlist_entry_id"] for item in current["entries"] if item["enabled"]]
    enabled_result = WatchlistEvidenceComposer(store=store, request_validator=_validator).compose(_payload(current, selected=enabled_ids), watchlist_id=current["watchlist_id"])
    assert len(enabled_result["request"]["targets"]) == 2


def test_temporary_targets_dedupe_persistent_wins_and_do_not_persist(store):
    current = _watchlist(store)
    before = store.get_watchlist(current["watchlist_id"])
    result = WatchlistEvidenceComposer(store=store, request_validator=_validator).compose(
        _payload(current, selected=[current["entries"][0]["watchlist_entry_id"]], temporary=[{"input": "2330", "market_hint": "TWSE"}, {"input": "6488", "market_hint": "TPEX"}]),
        watchlist_id=current["watchlist_id"],
    )
    assert [item["instrument_id"] for item in result["selected_targets"]] == ["TW0002330008", "TW0006488001"]
    assert result["deduplication_decisions"][0]["kept_source"] == "persistent_watchlist"
    assert store.get_watchlist(current["watchlist_id"])["entries"] == before["entries"]


def test_temporary_only_composition(store):
    result = WatchlistEvidenceComposer(store=store, request_validator=_validator).compose(_payload(temporary=[{"input": "2330", "market_hint": "TWSE"}]))
    assert result["request"]["targets"][0]["input"] == "TW0002330008"
    assert result["selection_provenance"]["watchlist"] is None


def test_ambiguous_and_not_found_temporary_targets_block(store):
    composer = WatchlistEvidenceComposer(store=store, request_validator=_validator)
    ambiguous = composer.compose(_payload(temporary=[{"input": "同名", "market_hint": None}]))
    missing = composer.compose(_payload(temporary=[{"input": "不存在", "market_hint": None}]))
    assert ambiguous["composition_status"] == "blocked" and ambiguous["blockers"][0]["code"] == "IDENTITY_AMBIGUOUS"
    assert len(ambiguous["blockers"][0]["candidates"]) == 2
    assert missing["composition_status"] == "blocked" and missing["blockers"][0]["code"] == "IDENTITY_NOT_FOUND"


def test_stale_version_fails_and_frozen_request_survives_mutation(store):
    current = _watchlist(store)
    composer = WatchlistEvidenceComposer(store=store, request_validator=_validator)
    result = composer.compose(_payload(current), watchlist_id=current["watchlist_id"])
    frozen = json.loads(json.dumps(result["request"]))
    updated = _commit(store, store.preview(_command("rename_watchlist", watchlist_id=current["watchlist_id"], expected_version=current["current_version"], name="新名稱")))
    assert result["request"] == frozen and updated["current_version"] == current["current_version"] + 1
    with pytest.raises(WatchlistEvidenceCompositionError, match="WATCHLIST_SELECTION_STALE"):
        composer.compose(_payload(current), watchlist_id=current["watchlist_id"])


def test_selection_sidecar_tamper_fails(store):
    current = _watchlist(store)
    result = WatchlistEvidenceComposer(store=store, request_validator=_validator).compose(_payload(current), watchlist_id=current["watchlist_id"])
    tampered = json.loads(json.dumps(result["selection_provenance"]))
    tampered["selected_targets"][0]["instrument_id"] = "TW0006488001"
    with pytest.raises(WatchlistEvidenceCompositionError, match="WATCHLIST_SELECTION_INTEGRITY_FAILED"):
        validate_selection_provenance(tampered, result["request"])


def test_validation_dependency_failure_leaves_no_orphan_sidecar(store):
    def unavailable(_request):
        raise RuntimeError("validation unavailable")
    with pytest.raises(RuntimeError, match="validation unavailable"):
        WatchlistEvidenceComposer(store=store, request_validator=unavailable).compose(_payload(temporary=[{"input": "2330", "market_hint": "TWSE"}]))
    assert not list((store.root / "evidence_selections").glob("*.json"))


def test_invalid_mode_a_result_leaves_no_orphan_sidecar(store):
    result = {"validation_status": "invalid"}
    with pytest.raises(
        WatchlistEvidenceCompositionError,
        match="WATCHLIST_SELECTION_VALIDATION_FAILED",
    ):
        WatchlistEvidenceComposer(
            store=store, request_validator=lambda _request: result
        ).compose(_payload(temporary=[{"input": "2330", "market_hint": "TWSE"}]))
    assert not list((store.root / "evidence_selections").glob("*.json"))


def test_unknown_or_unbounded_caller_fields_rejected(store):
    payload = _payload(temporary=[{"input": "2330", "market_hint": "TWSE"}])
    payload["raw_prompt"] = "secret"
    with pytest.raises(WatchlistEvidenceCompositionError, match="WATCHLIST_SELECTION_SCHEMA_INVALID"):
        WatchlistEvidenceComposer(store=store, request_validator=_validator).compose(payload)


def test_security_master_unavailable_fails_closed_without_mutating_watchlist(tmp_path):
    store = PersistentWatchlistStore(
        root=tmp_path / "watchlists",
        security_master_root=tmp_path / "missing-security-master",
    )
    current = _commit(store, store.preview(_command("create_watchlist", name="Offline")))
    before = store.get_watchlist(current["watchlist_id"])
    with pytest.raises(WatchlistError, match="SECURITY_MASTER_NOT_INITIALIZED"):
        WatchlistEvidenceComposer(store=store, request_validator=_validator).compose(
            _payload(
                current,
                selected=[],
                temporary=[{"input": "2330", "market_hint": "TWSE"}],
            ),
            watchlist_id=current["watchlist_id"],
        )
    assert store.get_watchlist(current["watchlist_id"]) == before


def test_persisted_identity_missing_from_current_release_is_visible_and_blocked(
    tmp_path, service
):
    root = tmp_path / "watchlists"
    original = PersistentWatchlistStore(root=root, identity_service=service)
    current = _watchlist(original)
    replacement = TaiwanMarketIdentityService(
        [_record("6488", "TW0006488001", "TPEX")],
        release_id="security-master-replacement",
        manifest_hash="b" * 64,
    )
    reopened = PersistentWatchlistStore(root=root, identity_service=replacement)
    stored = reopened.get_watchlist(current["watchlist_id"])
    selected_id = stored["entries"][0]["watchlist_entry_id"]
    result = WatchlistEvidenceComposer(
        store=reopened, request_validator=_validator
    ).compose(
        _payload(stored, selected=[selected_id]),
        watchlist_id=stored["watchlist_id"],
    )
    assert result["composition_status"] == "blocked"
    assert result["blockers"][0]["code"] == "IDENTITY_NOT_FOUND"
    assert reopened.get_watchlist(stored["watchlist_id"])["entries"][0][
        "instrument_id"
    ] == "TW0002330008"


def test_known_unsupported_cash_identity_is_composable_but_not_upgraded(store):
    current = _watchlist(store)
    unsupported = current["entries"][2]
    result = WatchlistEvidenceComposer(
        store=store, request_validator=_validator
    ).compose(
        _payload(current, selected=[unsupported["watchlist_entry_id"]]),
        watchlist_id=current["watchlist_id"],
    )
    assert result["composition_status"] == "composed"
    assert result["selected_targets"][0]["instrument_id"] == "TW0001234001"
    projection = store.get_watchlist(current["watchlist_id"])[
        "current_identity_projection"
    ][2]
    assert projection["persistable"] is True
    assert projection["executable"] is False


def test_default_and_hard_operation_bounds_warn_then_block(tmp_path):
    records = [
        _record(f"{index:04d}", f"TW{index:010d}") for index in range(1, 35)
    ]
    service = TaiwanMarketIdentityService(
        records,
        release_id="security-master-bounds",
        manifest_hash="c" * 64,
    )
    store = PersistentWatchlistStore(
        root=tmp_path / "watchlists", identity_service=service
    )
    current = _commit(store, store.preview(_command("create_watchlist", name="Bounds")))
    for index in range(1, 35):
        current = _commit(
            store,
            store.preview(
                _command(
                    "add_entry",
                    watchlist_id=current["watchlist_id"],
                    expected_version=current["current_version"],
                    query=f"{index:04d}",
                    market_hint="TWSE",
                )
            ),
        )
    composer = WatchlistEvidenceComposer(store=store, request_validator=_validator)
    warning = composer.compose(
        _payload(current, selected=[item["watchlist_entry_id"] for item in current["entries"][:11]]),
        watchlist_id=current["watchlist_id"],
    )
    assert warning["composition_status"] == "composed"
    assert "default_target_limit_exceeded" in warning["warnings"]
    hard_payload = _payload(
        current,
        selected=[item["watchlist_entry_id"] for item in current["entries"]],
    )
    hard_payload["data_needs"] = [
        {"type": need, "priority": "required", "parameters": {}}
        for need in ("identity", "current_observation", "official_eod_reference")
    ]
    blocked = composer.compose(hard_payload, watchlist_id=current["watchlist_id"])
    assert blocked["composition_status"] == "blocked"
    assert blocked["limits"]["operation_count"] == 102
    assert {item["code"] for item in blocked["blockers"]} == {
        "OPERATION_LIMIT_EXCEEDED"
    }
    assert blocked["request"] is None
    assert len(list((store.root / "evidence_selections").glob("*.json"))) == 1


def test_selection_provenance_is_projected_into_audit_identity():
    inputs = _plan_only_inputs()
    request_sha = hashlib.sha256(json.dumps(inputs.request, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    selection = {
        "schema_version": "watchlist_evidence_selection.v1",
        "selection_id": "de34c90a-b34f-44a6-9587-e771f31f9974",
        "content_sha256": "0" * 64,
        "request_id": inputs.request["request_id"],
        "request_sha256": request_sha,
        "watchlist": None,
        "selected_targets": [{
            "source": "temporary", "watchlist_entry_id": None, "temporary_input": inputs.request["targets"][0]["input"],
            "instrument_id": "TW0002330008", "canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330",
            "client_target_reference": "temporary_1",
        }],
        "temporary_targets": [{"input": inputs.request["targets"][0]["input"], "market_hint": "TWSE", "resolution_status": "resolved", "instrument_id": "TW0002330008", "canonical_target_id": "TWSE:2330"}],
        "deduplication_decisions": [],
        "created_at": "2026-09-11T00:00:00Z",
    }
    selection["content_sha256"] = hashlib.sha256(json.dumps({key: value for key, value in selection.items() if key != "content_sha256"}, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    result = build_result(inputs, projector_version=CURRENT_PROJECTOR_VERSION)
    audit = build_audit_package(
        result=result,
        inputs=inputs,
        citation_index=build_citation_index(build_lineage_map(inputs), inputs.bundle),
        result_relative_path="ai_context/unified_market_evidence_result.v1.json",
        selection_provenance=selection,
    )
    identity = audit["selection_provenance_identity"]
    assert identity["selection_id"] == selection["selection_id"]
    assert identity["request_sha256"] == request_sha
    assert identity["selected_instrument_ids"] == ["TW0002330008"]
