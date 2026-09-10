from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from scripts.m8r_08g_identity_service import TaiwanMarketIdentityService
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore, WatchlistError, canonical_json, validate_contract


def record(code: str, isin: str, market: str = "TWSE", kind: str = "common_share", *, successor: str | None = None):
    events = [] if successor is None else [{"event_type": "official_isin_successor", "predecessor_isin": isin, "successor_isin": successor, "official_evidence": True, "evidence": ["fixture"]}]
    return {"canonical_target_id": f"{market}:{code}", "identity": {"security_code": code, "isin": isin, "security_name_zh": f"名稱{code}"}, "classification": {"market": market, "instrument_type": kind}, "lifecycle": {"state": "listed", "resolution_status": "resolved", "as_of": "2026-09-10", "events": events}, "execution_eligibility": {"status": "allowed", "reason_codes": []}}


@pytest.fixture
def service():
    return TaiwanMarketIdentityService([record("2330", "TW0002330008"), record("6488", "TW0006488001", "TPEX"), record("0050", "TW0000050004", kind="etf"), record("1234", "TW0001234001", kind="warrant"), record("8888", "TW0008888001", successor="TW0008888002"), record("8889", "TW0008888002")], release_id="release-x", manifest_hash="a" * 64)


@pytest.fixture
def store(tmp_path, service):
    return PersistentWatchlistStore(root=tmp_path / "watchlists", identity_service=service)


def command(kind, **kwargs):
    return {"schema_version": "persistent_watchlist_mutation_command.v1", "command_type": kind, "actor_source": "human", **kwargs}


def commit(store, preview):
    return store.commit(preview_id=preview["preview_id"], preview_hash=preview["content_sha256"], confirmed=True)


def create(store, name="Primary"):
    return commit(store, store.preview(command("create_watchlist", name=name)))["watchlist"]


def add(store, watchlist, query="2330", market="TWSE"):
    return commit(store, store.preview(command("add_entry", watchlist_id=watchlist["watchlist_id"], expected_version=watchlist["current_version"], query=query, market_hint=market)))["watchlist"]


def test_formal_schemas_parse_and_fresh_state(store):
    root = Path("docs/contracts/schemas")
    for path in root.glob("persistent_watchlist*.schema.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    assert store.list_watchlists() == {"state": "NO_WATCHLISTS", "watchlists": []}
    assert store.verify_integrity()["status"] == "PASS"


def test_domain_schema_positive_and_negative_contracts(store):
    watchlist = create(store)
    validate_contract(watchlist, "persistent_watchlist.v1.schema.json")
    bad = dict(watchlist); bad.pop("watchlist_id")
    with pytest.raises(WatchlistError, match="WATCHLIST_SCHEMA_INVALID"):
        validate_contract(bad, "persistent_watchlist.v1.schema.json")
    revision = store.revision(watchlist["watchlist_id"], 1)
    validate_contract(revision, "persistent_watchlist_revision.v1.schema.json")


def test_create_add_isin_version_revision_and_restart(tmp_path, service):
    root = tmp_path / "install-a"
    store = PersistentWatchlistStore(root=root, identity_service=service)
    watchlist = add(store, create(store))
    entry = watchlist["entries"][0]
    assert entry["instrument_id"] == "TW0002330008" and entry["cached_listing_id"] == "TWSE:2330"
    assert watchlist["current_version"] == 2
    original = store.revision(watchlist["watchlist_id"], 1)
    reopened = PersistentWatchlistStore(root=root, identity_service=service)
    assert reopened.get_watchlist(watchlist["watchlist_id"])["entries"][0]["instrument_id"] == "TW0002330008"
    assert reopened.revision(watchlist["watchlist_id"], 1) == original


def test_preview_is_not_semantic_write_replay_expiry_and_hash(store):
    watchlist = create(store)
    preview = store.preview(command("rename_watchlist", watchlist_id=watchlist["watchlist_id"], expected_version=1, name="Renamed"))
    assert store.get_watchlist(watchlist["watchlist_id"])["name"] == "Primary"
    with pytest.raises(WatchlistError, match="WATCHLIST_CONFIRMATION_MISMATCH"):
        store.commit(preview_id=preview["preview_id"], preview_hash="0" * 64, confirmed=True)
    result = commit(store, preview)
    assert result["watchlist"]["name"] == "Renamed"
    with pytest.raises(WatchlistError, match="WATCHLIST_CONFIRMATION_ALREADY_CONSUMED"):
        commit(store, preview)


def test_conflict_duplicate_tags_notes_rollback_delete_restore_export(store):
    watchlist = add(store, create(store)); entry = watchlist["entries"][0]
    stale = store.preview(command("set_entry_enabled", watchlist_id=watchlist["watchlist_id"], expected_version=2, watchlist_entry_id=entry["watchlist_entry_id"], enabled=False))
    current = commit(store, store.preview(command("set_entry_tags", watchlist_id=watchlist["watchlist_id"], expected_version=2, watchlist_entry_id=entry["watchlist_entry_id"], tags=[" Alpha ", "Alpha"]))) ["watchlist"]
    with pytest.raises(WatchlistError, match="WATCHLIST_VERSION_CONFLICT"): commit(store, stale)
    with pytest.raises(WatchlistError, match="WATCHLIST_ENTRY_ALREADY_EXISTS"):
        store.preview(command("add_entry", watchlist_id=watchlist["watchlist_id"], expected_version=current["current_version"], query="2330", market_hint="TWSE"))
    rolled = commit(store, store.preview(command("rollback_watchlist", watchlist_id=watchlist["watchlist_id"], expected_version=current["current_version"], target_version=2)))["watchlist"]
    deleted = commit(store, store.preview(command("delete_watchlist", watchlist_id=watchlist["watchlist_id"], expected_version=rolled["current_version"])))["watchlist"]
    assert deleted["deleted"] is True
    restored = commit(store, store.preview(command("restore_watchlist", watchlist_id=watchlist["watchlist_id"], expected_version=deleted["current_version"])))["watchlist"]
    assert restored["deleted"] is False
    exported = store.export(restored["watchlist_id"], include_history=True)
    assert exported["content_sha256"] and len(exported["revisions"]) == restored["current_version"]


def test_known_unsupported_persists_but_derivative_and_unavailable_do_not(store):
    watchlist = create(store)
    persisted = add(store, watchlist, "1234")
    projection = store.get_watchlist(persisted["watchlist_id"])["current_identity_projection"][0]
    assert projection["persistable"] is True and projection["executable"] is False
    with pytest.raises(WatchlistError, match="IDENTITY_NOT_FOUND"):
        store.preview(command("add_entry", watchlist_id=watchlist["watchlist_id"], expected_version=persisted["current_version"], query="TX", market_hint="TAIFEX"))
    empty = PersistentWatchlistStore(root=store.root.parent / "uninitialized", security_master_root=store.root.parent / "no-security-master")
    missing = create(empty)
    with pytest.raises(WatchlistError, match="SECURITY_MASTER_NOT_INITIALIZED"):
        empty.preview(command("add_entry", watchlist_id=missing["watchlist_id"], expected_version=1, query="2330", market_hint="TWSE"))


def test_legacy_import_partial_and_installation_isolation(store, service, tmp_path):
    watchlist = create(store)
    legacy = {"categories": [{"instruments": [{"id": "twse:2330", "symbol": "2330", "market": "twse", "enabled": True}, {"id": "taifex:tx", "symbol": "TX", "market": "taifex"}]}]}
    preview = store.preview(command("import_legacy_watchlist", watchlist_id=watchlist["watchlist_id"], expected_version=1, legacy_watchlist=legacy, actor_source="import"))
    assert preview["deferred_items"][0]["reason_code"] == "IDENTITY_SCHEME_UNSUPPORTED"
    committed = commit(store, preview)["watchlist"]
    assert len(committed["entries"]) == 1
    other = PersistentWatchlistStore(root=tmp_path / "install-b", identity_service=service)
    assert other.list_watchlists()["state"] == "NO_WATCHLISTS"


def test_api_preview_commit_and_legacy_compatibility(monkeypatch, store):
    import server.main as main
    monkeypatch.setattr(main, "_persistent_watchlist_store", lambda: store)
    client = TestClient(main.app)
    assert client.get("/api/watchlists").json()["state"] == "NO_WATCHLISTS"
    payload = command("create_watchlist", name="API")
    preview = client.post("/api/watchlist-mutations/preview", json=payload).json()
    response = client.post("/api/watchlist-mutations/commit", json={"preview_id": preview["preview_id"], "preview_hash": preview["content_sha256"], "confirmed": True})
    assert response.status_code == 200 and client.get("/api/watchlist").status_code == 200


def test_default_switch_is_atomic_and_versions_both_watchlists(store):
    first = create(store, "First")
    second = create(store, "Second")
    assert first["is_default"] is True and second["is_default"] is False
    preview = store.preview(command("set_default_watchlist", watchlist_id=second["watchlist_id"], expected_version=second["current_version"]))
    assert preview["expected_versions"] == {first["watchlist_id"]: 1, second["watchlist_id"]: 1}
    commit(store, preview)
    rows = {x["name"]: x for x in store.list_watchlists()["watchlists"]}
    assert rows["First"]["is_default"] is False and rows["First"]["current_version"] == 2
    assert rows["Second"]["is_default"] is True and rows["Second"]["current_version"] == 2


def test_expiry_and_transaction_rollback_leave_state_unchanged(tmp_path, service, monkeypatch):
    clock = ["2026-09-10T00:00:00Z"]
    store = PersistentWatchlistStore(root=tmp_path / "clocked", identity_service=service, now=lambda: clock[0])
    watchlist = create(store)
    preview = store.preview(command("rename_watchlist", watchlist_id=watchlist["watchlist_id"], expected_version=1, name="Late"))
    clock[0] = "2026-09-10T00:11:00Z"
    with pytest.raises(WatchlistError, match="WATCHLIST_CONFIRMATION_EXPIRED"): commit(store, preview)
    assert store.get_watchlist(watchlist["watchlist_id"])["name"] == "Primary"
    clock[0] = "2026-09-10T00:12:00Z"
    preview = store.preview(command("rename_watchlist", watchlist_id=watchlist["watchlist_id"], expected_version=1, name="Atomic"))
    monkeypatch.setattr(store, "_write_snapshot", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("injected")))
    with pytest.raises(RuntimeError, match="injected"): commit(store, preview)
    assert store.get_watchlist(watchlist["watchlist_id"])["name"] == "Primary"


def test_limits_and_integrity_tamper_fail_closed(store, monkeypatch):
    watchlist = create(store)
    monkeypatch.setitem(__import__("scripts.m8r_09_persistent_watchlists", fromlist=["LIMITS"]).LIMITS, "watchlists", 1)
    with pytest.raises(WatchlistError, match="WATCHLIST_RESOURCE_LIMIT_EXCEEDED"):
        store.preview(command("create_watchlist", name="Second"))
    con = store._connect()
    try:
        con.execute("UPDATE revisions SET content_sha256=? WHERE watchlist_id=? AND version=1", ("0" * 64, watchlist["watchlist_id"]))
    finally: con.close()
    with pytest.raises(WatchlistError, match="WATCHLIST_VERSION_CHAIN_BROKEN"):
        store.verify_integrity()


def test_successor_migration_is_explicit(store):
    watchlist = add(store, create(store), "8888")
    entry = watchlist["entries"][0]
    preview = store.preview(command("confirm_identity_migration", watchlist_id=watchlist["watchlist_id"], expected_version=2, watchlist_entry_id=entry["watchlist_entry_id"]))
    assert preview["command"]["resolved_successor"] == "TW0008888002"


def test_current_legacy_template_is_import_only_and_unified_mcp_is_unchanged(store):
    template = json.loads(Path("config/m5k_default_watchlist.json").read_text(encoding="utf-8"))
    watchlist = create(store)
    preview = store.preview(command("import_legacy_watchlist", watchlist_id=watchlist["watchlist_id"], expected_version=1, legacy_watchlist=template, actor_source="import"))
    # The test identity authority intentionally resolves only a subset; no legacy
    # listing identifier is accepted as a durable identity without resolution.
    assert preview["command"]["accepted_entries"]
    assert preview["deferred_items"]
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    assert {tool.name for tool in build_tool_contract_snapshot().tools} == {"market_describe_capabilities", "market_validate_request", "market_preview_request", "market_read_result", "market_export_ai_handoff", "market_fetch_evidence"}
