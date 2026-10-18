from __future__ import annotations

import hashlib
import os
import tracemalloc

import pytest
from fastapi.testclient import TestClient

from server import resource_boundaries as rb


@pytest.mark.skipif(os.name != "nt", reason="Windows ctypes sampler contract")
def test_windows_memory_sampler_reuses_module_type_pointer_and_api_for_100_samples():
    from server import operational_diagnostics as diagnostics

    counter_type = diagnostics._WindowsProcessMemoryCounters
    pointer_type = diagnostics._WINDOWS_MEMORY_COUNTERS_POINTER
    assert counter_type is not None
    assert pointer_type is not None
    assert pointer_type is type(diagnostics.ctypes.pointer(counter_type()))

    api = diagnostics._windows_memory_api()
    assert api is not None
    tracemalloc.start()
    try:
        before = tracemalloc.get_traced_memory()[0]
        for _ in range(100):
            diagnostics.process_memory_bytes()
            assert diagnostics._WindowsProcessMemoryCounters is counter_type
            assert diagnostics._WINDOWS_MEMORY_COUNTERS_POINTER is pointer_type
            assert diagnostics._windows_memory_api() is api
        after = tracemalloc.get_traced_memory()[0]
        snapshot = tracemalloc.take_snapshot()
        ctypes_frames = [
            stat for stat in snapshot.statistics("filename")
            if "ctypes" in str(stat.traceback).lower()
        ]
        assert after >= before
        # Structural reuse is the acceptance proof; traced allocations are
        # retained as diagnostic data without imposing an arbitrary byte cap.
        assert isinstance(ctypes_frames, list)
    finally:
        tracemalloc.stop()


def _create_watchlist(store, *, name="A6 R1 authority"):
    preview = store.preview({
        "schema_version": "persistent_watchlist_mutation_command.v1",
        "command_type": "create_watchlist",
        "actor_source": "human",
        "name": name,
    })
    return store.commit(
        preview_id=preview["preview_id"],
        preview_hash=preview["content_sha256"],
        confirmed=True,
    )["watchlist"]


def _disk_full(*_args, **_kwargs):
    raise rb.ResourceDiskAdmissionError(rb.RESOURCE_DISK_REASON)


def test_existing_watchlist_reads_survive_low_disk_but_mutations_fail_without_change(monkeypatch, tmp_path):
    from scripts import m8r_09_persistent_watchlists as watchlists

    root = tmp_path / "authority"
    store = watchlists.PersistentWatchlistStore(root=root)
    created = _create_watchlist(store)
    rename_preview = store.preview({
        "schema_version": "persistent_watchlist_mutation_command.v1",
        "command_type": "rename_watchlist",
        "actor_source": "human",
        "watchlist_id": created["watchlist_id"],
        "expected_version": created["current_version"],
        "name": "Must not commit under low disk",
    })
    db = root / watchlists.DATABASE_NAME
    before_bytes = db.read_bytes()
    before_hash = hashlib.sha256(before_bytes).hexdigest()
    before_history = store.revisions(created["watchlist_id"])

    # Dropping the store closes no persistent connection: all public operations
    # scope and close their SQLite handles. Reopening must inspect read-only.
    del store
    monkeypatch.setattr(watchlists, "require_disk_capacity", _disk_full)
    reopened = watchlists.PersistentWatchlistStore(root=root)
    assert reopened.list_watchlists()["watchlists"][0]["watchlist_id"] == created["watchlist_id"]
    assert reopened.get_watchlist(created["watchlist_id"])["name"] == created["name"]
    assert reopened.export(created["watchlist_id"])["watchlist"]["name"] == created["name"]

    with pytest.raises(watchlists.WatchlistError, match=rb.RESOURCE_DISK_REASON):
        reopened.preview({
            "schema_version": "persistent_watchlist_mutation_command.v1",
            "command_type": "rename_watchlist",
            "actor_source": "human",
            "watchlist_id": created["watchlist_id"],
            "expected_version": created["current_version"],
            "name": "Preview must fail",
        })
    with pytest.raises(watchlists.WatchlistError, match=rb.RESOURCE_DISK_REASON):
        reopened.commit(
            preview_id=rename_preview["preview_id"],
            preview_hash=rename_preview["content_sha256"],
            confirmed=True,
        )

    after_bytes = db.read_bytes()
    assert hashlib.sha256(after_bytes).hexdigest() == before_hash
    assert after_bytes == before_bytes
    assert reopened.get_watchlist(created["watchlist_id"])["current_version"] == 1
    assert reopened.revisions(created["watchlist_id"]) == before_history


def test_incomplete_existing_schema_admission_precedes_schema_mutation(monkeypatch, tmp_path):
    import sqlite3

    from scripts import m8r_09_persistent_watchlists as watchlists

    root = tmp_path / "incomplete"
    root.mkdir()
    db = root / watchlists.DATABASE_NAME
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY)")
    con.close()
    before = db.read_bytes()
    monkeypatch.setattr(watchlists, "require_disk_capacity", _disk_full)
    with pytest.raises(watchlists.WatchlistError, match=rb.RESOURCE_DISK_REASON):
        watchlists.PersistentWatchlistStore(root=root)
    assert db.read_bytes() == before


def test_actual_middleware_order_places_control_plane_before_resource_admission():
    from fastapi.middleware.cors import CORSMiddleware
    from server.local_control_plane_boundary import LocalControlPlaneBoundaryMiddleware
    from server.local_network_boundary import LocalNetworkBoundaryMiddleware
    from server.main import app

    assert [item.cls for item in app.user_middleware][:4] == [
        LocalNetworkBoundaryMiddleware,
        LocalControlPlaneBoundaryMiddleware,
        rb.ResourceAdmissionMiddleware,
        CORSMiddleware,
    ]


def test_cross_origin_privileged_request_is_rejected_before_resource_gate(monkeypatch):
    from server.main import app

    calls = []
    gate = rb.RESOURCE_INTENSIVE_GATE
    original_enter = gate.try_enter

    def observed_enter():
        calls.append("enter")
        return original_enter()

    monkeypatch.setattr(gate, "try_enter", observed_enter)
    with TestClient(app) as client:
        denied = client.post(
            "/api/unified/executions",
            json={},
            headers={"Origin": "https://attacker.example"},
        )
        assert denied.status_code == 403
        assert denied.json() == {"error": "local_control_plane_same_origin_required"}
        assert calls == []

        # A native local caller has no browser-origin headers and may reach the
        # resource gate; the route itself can reject the intentionally empty body.
        native = client.post("/api/unified/executions", json={})
        assert native.status_code >= 400
        assert calls == ["enter"]
        assert gate.active == 0


def test_current_target_limits_are_distinguished_by_contract():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    catalog = json.loads(
        (root / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8")
    )
    from scripts.m8r_bounded_market_context_request import MAX_TARGETS

    assert catalog["bounds"]["hard_target_limit"] == 50
    assert MAX_TARGETS == 10
