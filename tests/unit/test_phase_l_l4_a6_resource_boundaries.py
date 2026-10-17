from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

import pytest

from server import resource_boundaries as rb


def test_resource_gate_is_single_slot_fail_fast_and_releases_after_exception():
    gate = rb.ResourceAdmissionGate(limit=1)
    assert gate.try_enter() is True
    assert gate.try_enter() is False
    gate.leave()
    with pytest.raises(RuntimeError):
        with gate.admitted() as admitted:
            assert admitted is True
            raise RuntimeError("synthetic")
    assert gate.active == 0


@pytest.mark.parametrize(
    "method,path,expected",
    [
        ("POST", "/api/unified/authorizations", rb.RESOURCE_INTENSIVE_ACTION),
        ("POST", "/api/unified/executions", rb.RESOURCE_INTENSIVE_ACTION),
        ("POST", "/api/unified/fetch-evidence", rb.RESOURCE_INTENSIVE_ACTION),
        ("POST", "/api/unified/result-package", rb.RESOURCE_INTENSIVE_ACTION),
        ("GET", "/api/unified/result-package/x/audit.json", rb.RESOURCE_INTENSIVE_PROJECTION),
        ("GET", "/api/unified/result-package/x/handoff", rb.RESOURCE_INTENSIVE_PROJECTION),
        ("POST", "/api/watchlist-mutations/preview", rb.PERSISTENT_MUTATION),
        ("POST", "/api/watchlist-mutations/commit", rb.PERSISTENT_MUTATION),
        ("POST", "/api/evidence-request-previews", rb.PERSISTENT_MUTATION),
        ("POST", "/api/unified/validate-request", rb.BOUNDED_OFFLINE_PLANNING),
        ("POST", "/api/unified/preview-request", rb.BOUNDED_OFFLINE_PLANNING),
        ("POST", "/api/m5k/conversation/handoff", rb.BOUNDED_OFFLINE_PLANNING),
        ("POST", "/api/m5k/live-observation/plan", rb.BOUNDED_OFFLINE_PLANNING),
        ("POST", "/api/m5k/watchlist/validate", rb.BOUNDED_OFFLINE_PLANNING),
        ("GET", "/api/health", rb.LIGHT_READ),
        ("GET", "/workbench/", rb.LIGHT_READ),
        ("POST", "/future/write-route", rb.PERSISTENT_MUTATION),
    ],
)
def test_route_classification_is_explicit(method, path, expected):
    assert rb.classify_request(method, path) == expected


def test_middleware_rejects_second_resource_request_without_queue_and_keeps_light_route_independent():
    gate = rb.ResourceAdmissionGate(limit=1)
    middleware = rb.ResourceAdmissionMiddleware(lambda *_: None, gate=gate)
    first_started = threading.Event()
    release_first = threading.Event()
    outputs = {}

    async def app(scope, receive, send):
        if scope["path"] == "/api/unified/executions":
            first_started.set()
            await asyncio.to_thread(release_first.wait, 2)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    middleware.app = app

    async def call(path):
        sent = []
        async def send(message):
            sent.append(message)
        method = "GET" if path == "/api/health" else "POST"
        await middleware({"type": "http", "method": method, "path": path}, lambda: None, send)
        return sent

    def run_first():
        outputs["first"] = asyncio.run(call("/api/unified/executions"))

    thread = threading.Thread(target=run_first)
    thread.start()
    assert first_started.wait(2)
    outputs["second"] = asyncio.run(call("/api/unified/authorizations"))
    outputs["light"] = asyncio.run(call("/api/health"))
    release_first.set()
    thread.join(2)
    assert not thread.is_alive()
    second_status = next(item["status"] for item in outputs["second"] if item["type"] == "http.response.start")
    light_status = next(item["status"] for item in outputs["light"] if item["type"] == "http.response.start")
    assert second_status == 503
    assert json.loads(outputs["second"][1]["body"]) == {"error": "resource_concurrency_limit"}
    assert light_status == 200
    assert gate.active == 0


def test_disk_admission_uses_observed_free_bytes_and_fails_closed(monkeypatch, tmp_path):
    class Usage:
        total = 100
        used = 60
        free = 40

    monkeypatch.setattr(rb.shutil, "disk_usage", lambda _path: Usage())
    assert rb.require_disk_capacity(tmp_path, 40) == 40
    with pytest.raises(rb.ResourceDiskAdmissionError) as caught:
        rb.require_disk_capacity(tmp_path, 41)
    assert caught.value.code == rb.RESOURCE_DISK_REASON
    monkeypatch.setattr(rb.shutil, "disk_usage", lambda _path: (_ for _ in ()).throw(OSError("unavailable")))
    with pytest.raises(rb.ResourceDiskAdmissionError) as caught:
        rb.require_disk_capacity(tmp_path, 1)
    assert caught.value.code == rb.RESOURCE_DISK_UNAVAILABLE_REASON


def test_sqlite_write_envelope_is_dynamic_and_nonzero(tmp_path):
    db = tmp_path / "sample.sqlite3"
    db.write_bytes(b"x" * 123)
    assert rb.sqlite_write_requirement(db, 45) == 336
    assert rb.sqlite_write_requirement(tmp_path / "new.sqlite3", 45) == 90


def test_a6_freezes_only_currently_supported_numeric_ceilings():
    from scripts.m8r_09_persistent_watchlists import LIMITS
    from server.unified_payload_bounds import MAX_UNIFIED_REQUEST_BYTES, MAX_UNIFIED_RESPONSE_BYTES
    from scripts.m8r_bounded_market_context_request import MAX_TARGETS
    from server.services.unified_mode_b2_execution import MAX_CHILD_TIMEOUT_SECONDS
    from pathlib import Path

    catalog = json.loads((Path(__file__).resolve().parents[2] / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    assert rb.MAX_RESOURCE_INTENSIVE_CONCURRENCY == 1
    assert LIMITS["watchlists"] == 32
    assert LIMITS["entries"] == 500
    assert LIMITS["import_bytes"] == 1024 * 1024
    assert MAX_UNIFIED_REQUEST_BYTES == 1024 * 1024
    assert MAX_UNIFIED_RESPONSE_BYTES == 8 * 1024 * 1024
    assert MAX_TARGETS == 10
    assert catalog["bounds"]["hard_operation_limit"] == 100
    assert MAX_CHILD_TIMEOUT_SECONDS == 130


def test_unified_target_ceiling_accepts_fifty_and_rejects_fifty_one():
    from tests.unit.test_m8r_06_02_mode_b1_preview import package, request

    exact = request()
    exact["targets"] = [{"input": f"synthetic-{index:02d}"} for index in range(50)]
    at_limit = package(exact)
    assert at_limit["preview"]["status"] != "rejected_resource_bound"

    over = request()
    over["targets"] = [{"input": f"synthetic-{index:02d}"} for index in range(51)]
    assert package(over)["preview"]["status"] == "rejected_resource_bound"


def test_watchlist_preview_and_commit_fail_before_sqlite_mutation_on_low_disk(monkeypatch, tmp_path):
    from scripts import m8r_09_persistent_watchlists as watchlists

    store = watchlists.PersistentWatchlistStore(root=tmp_path / "watchlists")
    create_command = {
        "schema_version": "persistent_watchlist_mutation_command.v1",
        "command_type": "create_watchlist",
        "actor_source": "human",
        "name": "Resource test",
    }
    preview_id = None

    def disk_full(*_args, **_kwargs):
        raise rb.ResourceDiskAdmissionError(rb.RESOURCE_DISK_REASON)

    monkeypatch.setattr(watchlists, "require_disk_capacity", disk_full)
    with pytest.raises(watchlists.WatchlistError, match=rb.RESOURCE_DISK_REASON):
        store.preview(create_command)
    con = store._connect()
    try:
        assert con.execute("SELECT COUNT(*) FROM mutation_previews").fetchone()[0] == 0
    finally:
        con.close()

    monkeypatch.undo()
    created_preview = store.preview(create_command)
    created = store.commit(
        preview_id=created_preview["preview_id"],
        preview_hash=created_preview["content_sha256"],
        confirmed=True,
    )["watchlist"]
    rename = store.preview({
        "schema_version": "persistent_watchlist_mutation_command.v1",
        "command_type": "rename_watchlist",
        "actor_source": "human",
        "watchlist_id": created["watchlist_id"],
        "expected_version": created["current_version"],
        "name": "Must not persist",
    })
    monkeypatch.setattr(watchlists, "require_disk_capacity", disk_full)
    with pytest.raises(watchlists.WatchlistError, match=rb.RESOURCE_DISK_REASON):
        store.commit(preview_id=rename["preview_id"], preview_hash=rename["content_sha256"], confirmed=True)
    current = store.get_watchlist(created["watchlist_id"])
    assert current["name"] == "Resource test"
    assert current["current_version"] == 1


def test_watchlist_schema_initialization_admits_disk_before_database_creation(monkeypatch, tmp_path):
    from scripts import m8r_09_persistent_watchlists as watchlists

    root = tmp_path / "new-watchlists"
    monkeypatch.setattr(
        watchlists,
        "require_disk_capacity",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            rb.ResourceDiskAdmissionError(rb.RESOURCE_DISK_REASON)
        ),
    )
    with pytest.raises(watchlists.WatchlistError, match=rb.RESOURCE_DISK_REASON):
        watchlists.PersistentWatchlistStore(root=root)
    assert not (root / watchlists.DATABASE_NAME).exists()


def test_watchlist_500_entry_fixture_is_accepted_and_501_rejected():
    from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore, WatchlistError

    # Directly exercise the same deterministic snapshot validator without
    # creating 500 revisions or touching installation-local production state.
    import tempfile
    from datetime import datetime, timezone
    from uuid import uuid4

    with tempfile.TemporaryDirectory(prefix="l4-a6-watchlist-") as directory:
        authority = PersistentWatchlistStore(root=Path(directory) / "authority")
        timestamp = datetime.now(timezone.utc).isoformat()
        def make_snapshot(count):
            return {
                "schema_version": "persistent_watchlist.v1",
                "watchlist_id": str(uuid4()),
                "name": "Synthetic bound fixture",
                "current_version": 1,
                "is_default": False,
                "deleted": False,
                "created_at": timestamp,
                "updated_at": timestamp,
                "entries": [
                    {
                        "watchlist_entry_id": str(uuid4()),
                        "instrument_id": f"TW{index:010d}",
                        "identity_scheme": "ISIN",
                        "enabled": True,
                        "display_order": index + 1,
                        "tags": [],
                        "notes": "",
                        "created_at": timestamp,
                        "updated_at": timestamp,
                        "resolved_under_security_master_release_id": None,
                    }
                    for index in range(count)
                ],
            }
        authority._validate_snapshot(make_snapshot(500))
        with pytest.raises(WatchlistError, match="WATCHLIST_RESOURCE_LIMIT_EXCEEDED"):
            authority._validate_snapshot(make_snapshot(501))


def test_mode_b2_disk_admission_precedes_control_artifact_publication(monkeypatch, tmp_path):
    from server.services import unified_mode_b2

    package = {
        "authorization": {"authorization_id": "auth", "authorization_hash": "a" * 64},
        "plan": {"plan_id": "plan", "plan_hash": "b" * 64},
        "preflight": {"preflight_id": "preflight", "preflight_hash": "c" * 64},
    }
    monkeypatch.setattr(
        unified_mode_b2,
        "require_disk_capacity",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            rb.ResourceDiskAdmissionError(rb.RESOURCE_DISK_REASON)
        ),
    )
    with pytest.raises(unified_mode_b2.ModeB2Error, match=rb.RESOURCE_DISK_REASON):
        unified_mode_b2._write_control_package(tmp_path, package)
    assert not list((tmp_path / "control").glob("*.json"))
