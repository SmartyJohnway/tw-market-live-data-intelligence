"""Deterministic V1 installation journeys using isolated installation roots.

These are release-candidate acceptance tests.  They intentionally use an
in-memory identity authority rather than a live Security Master acquisition.
"""

from __future__ import annotations

from scripts.m8r_08g_identity_service import TaiwanMarketIdentityService
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore


def _record(code: str, isin: str, *, kind: str = "common_share") -> dict:
    return {
        "canonical_target_id": f"TWSE:{code}",
        "identity": {"security_code": code, "isin": isin, "security_name_zh": f"測試{code}"},
        "classification": {"market": "TWSE", "instrument_type": kind},
        "lifecycle": {"state": "listed", "resolution_status": "resolved", "as_of": "2026-09-12", "events": []},
        "execution_eligibility": {"status": "allowed", "reason_codes": []},
    }


def _service() -> TaiwanMarketIdentityService:
    return TaiwanMarketIdentityService(
        [_record("2330", "TW0002330008"), _record("0050", "TW0000050004", kind="etf")],
        release_id="v1-deterministic-fixture",
        manifest_hash="a" * 64,
    )


def _command(command_type: str, **values: object) -> dict:
    return {
        "schema_version": "persistent_watchlist_mutation_command.v1",
        "command_type": command_type,
        "actor_source": "import" if command_type == "import_legacy_watchlist" else "human",
        **values,
    }


def _commit(store: PersistentWatchlistStore, preview: dict) -> dict:
    return store.commit(preview_id=preview["preview_id"], preview_hash=preview["content_sha256"], confirmed=True)


def _create_and_add(store: PersistentWatchlistStore) -> dict:
    created = _commit(store, store.preview(_command("create_watchlist", name="V1 release journey")))["watchlist"]
    return _commit(
        store,
        store.preview(
            _command(
                "add_entry",
                watchlist_id=created["watchlist_id"],
                expected_version=created["current_version"],
                query="2330",
                market_hint="TWSE",
                tags=["core"],
                notes="persisted across restart",
            )
        ),
    )["watchlist"]


def test_fresh_install_bootstrap_persists_isin_watchlist_and_identity_projection(tmp_path):
    root = tmp_path / "fresh-install"
    store = PersistentWatchlistStore(root=root / "watchlists", identity_service=_service())
    assert store.list_watchlists() == {"state": "NO_WATCHLISTS", "watchlists": []}

    watchlist = _create_and_add(store)
    entry = watchlist["entries"][0]
    assert entry["instrument_id"] == "TW0002330008"
    assert entry["cached_listing_id"] == "TWSE:2330"

    restarted = PersistentWatchlistStore(root=root / "watchlists", identity_service=_service())
    restored = restarted.get_watchlist(watchlist["watchlist_id"])
    assert restored["entries"][0]["tags"] == ["core"]
    assert restored["entries"][0]["notes"] == "persisted across restart"
    assert restarted.verify_integrity()["status"] == "PASS"


def test_existing_schema_one_installation_opens_without_reset_or_history_loss(tmp_path):
    root = tmp_path / "pre-v1-install"
    before = PersistentWatchlistStore(root=root / "watchlists", identity_service=_service())
    original = _create_and_add(before)
    first_revision = before.revision(original["watchlist_id"], 1)

    candidate = PersistentWatchlistStore(root=root / "watchlists", identity_service=_service())
    after = candidate.get_watchlist(original["watchlist_id"])
    assert after["current_version"] == original["current_version"]
    assert candidate.revision(original["watchlist_id"], 1) == first_revision
    assert candidate.verify_integrity()["status"] == "PASS"


def test_v0_1_legacy_import_requires_preview_and_commits_only_resolved_entries(tmp_path):
    store = PersistentWatchlistStore(root=tmp_path / "legacy-install" / "watchlists", identity_service=_service())
    watchlist = _commit(store, store.preview(_command("create_watchlist", name="Migrated")))["watchlist"]
    legacy = {
        "schema_version": "m5n_watchlist.v1",
        "categories": [{"instruments": [
            {"id": "twse:2330", "symbol": "2330", "market": "twse", "enabled": True},
            {"id": "taifex:tx", "symbol": "TX", "market": "taifex", "enabled": True},
        ]}],
    }
    preview = store.preview(
        _command(
            "import_legacy_watchlist",
            watchlist_id=watchlist["watchlist_id"],
            expected_version=watchlist["current_version"],
            legacy_watchlist=legacy,
        )
    )
    assert preview["command"]["accepted_entries"]
    assert preview["deferred_items"] == [{"item": "taifex:tx", "reason_code": "IDENTITY_SCHEME_UNSUPPORTED"}]
    committed = _commit(store, preview)["watchlist"]
    assert [entry["instrument_id"] for entry in committed["entries"]] == ["TW0002330008"]
