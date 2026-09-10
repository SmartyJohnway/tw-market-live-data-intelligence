"""Installation-local persistent watchlists for M8R-09.

This domain has no market-data execution capability.  It stores explicit user
state only; the Taiwan Market Identity Service is read-only input to identity
sensitive previews.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import jsonschema

from scripts.m8r_08g_identity_service import CASH_MARKETS, instrument_id, listing_id, official_successor_migration
from scripts.m8r_08g_security_master_releases import LocalSecurityMasterError, load_active_identity_service


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "data" / "watchlists"
DATABASE_NAME = "watchlists.sqlite3"
SCHEMA_VERSION = 1
PREVIEW_TTL = timedelta(minutes=10)
LIMITS = {"watchlists": 32, "entries": 500, "tags": 20, "tag_length": 64, "notes_length": 4096, "name_length": 120, "import_bytes": 1024 * 1024, "json_depth": 20}
ACTORS = {"human", "ai_assisted", "import", "migration", "rollback", "system_metadata_reconcile"}
SCHEMA_ROOT = REPO_ROOT / "docs" / "contracts" / "schemas"
_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}


class WatchlistError(Exception):
    def __init__(self, code: str, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(message or code)
        self.code, self.details = code, details or {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_contract(instance: Any, schema_name: str) -> None:
    """Validate M8R-09 domain documents against the tracked JSON authority."""
    if not _SCHEMA_CACHE:
        for path in SCHEMA_ROOT.glob("persistent_watchlist*.schema.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            _SCHEMA_CACHE[path.name] = data
            _SCHEMA_CACHE[data["$id"]] = data
    schema = _SCHEMA_CACHE.get(schema_name)
    if schema is None:
        raise WatchlistError("WATCHLIST_SCHEMA_INVALID", details={"schema": schema_name})
    resolver = jsonschema.RefResolver.from_schema(schema, store=_SCHEMA_CACHE)
    errors = sorted(jsonschema.Draft202012Validator(schema, resolver=resolver, format_checker=jsonschema.FormatChecker()).iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        raise WatchlistError("WATCHLIST_SCHEMA_INVALID", details={"schema": schema_name, "message": errors[0].message})


def _depth(value: Any) -> int:
    if isinstance(value, dict): return 1 + max((_depth(v) for v in value.values()), default=0)
    if isinstance(value, list): return 1 + max((_depth(v) for v in value), default=0)
    return 0


def _normal_text(value: Any, *, limit: int, code: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise WatchlistError(code)
    if len(value) > limit: raise WatchlistError("WATCHLIST_RESOURCE_LIMIT_EXCEEDED", details={"field": code, "limit": limit})
    return value.strip()


def _normal_tags(value: Any) -> list[str]:
    if not isinstance(value, list): raise WatchlistError("WATCHLIST_SCHEMA_INVALID", details={"field": "tags"})
    if len(value) > LIMITS["tags"]: raise WatchlistError("WATCHLIST_RESOURCE_LIMIT_EXCEEDED", details={"field": "tags"})
    tags: list[str] = []
    for item in value:
        tag = _normal_text(item, limit=LIMITS["tag_length"], code="tag")
        if tag not in tags: tags.append(tag)
    return tags


class PersistentWatchlistStore:
    """SQLite authority with preview-bound transactional semantic mutations."""

    def __init__(self, *, root: Path | None = None, identity_service: Any | None = None, security_master_root: Path | None = None, now: Callable[[], str] = utc_now):
        self.root = (root or DEFAULT_ROOT).resolve()
        self.identity_service = identity_service
        self.security_master_root = security_master_root or (REPO_ROOT / "data" / "security_master")
        self.now = now
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / DATABASE_NAME
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        try:
            con = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("PRAGMA busy_timeout=5000")
            return con
        except sqlite3.DatabaseError as exc:
            raise WatchlistError("WATCHLIST_STORAGE_CORRUPT", str(exc)) from exc

    def _initialize(self) -> None:
        con = self._connect()
        try:
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok": raise WatchlistError("WATCHLIST_STORAGE_CORRUPT", integrity)
            con.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
            rows = [r[0] for r in con.execute("SELECT version FROM schema_migrations ORDER BY version")]
            if any(v > SCHEMA_VERSION for v in rows): raise WatchlistError("WATCHLIST_STORAGE_SCHEMA_UNSUPPORTED")
            if not rows:
                try:
                    con.executescript("""
                    CREATE TABLE watchlists (watchlist_id TEXT PRIMARY KEY, name TEXT NOT NULL, current_version INTEGER NOT NULL, is_default INTEGER NOT NULL, deleted INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                    CREATE TABLE entries (watchlist_entry_id TEXT PRIMARY KEY, watchlist_id TEXT NOT NULL REFERENCES watchlists(watchlist_id), instrument_id TEXT NOT NULL, payload_json TEXT NOT NULL, UNIQUE(watchlist_id, instrument_id));
                    CREATE TABLE revisions (watchlist_id TEXT NOT NULL REFERENCES watchlists(watchlist_id), version INTEGER NOT NULL, payload_json TEXT NOT NULL, content_sha256 TEXT NOT NULL, PRIMARY KEY(watchlist_id, version));
                    CREATE TABLE mutation_previews (preview_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, content_sha256 TEXT NOT NULL, expires_at TEXT NOT NULL, consumed_at TEXT);
                    """)
                    con.execute("INSERT INTO schema_migrations(version) VALUES (?)", (SCHEMA_VERSION,))
                except Exception:
                    raise
            elif rows != [SCHEMA_VERSION]: raise WatchlistError("WATCHLIST_STORAGE_SCHEMA_UNSUPPORTED")
        except sqlite3.DatabaseError as exc:
            raise WatchlistError("WATCHLIST_STORAGE_CORRUPT", str(exc)) from exc
        finally: con.close()

    @contextmanager
    def _write(self):
        con = self._connect(); con.execute("BEGIN IMMEDIATE")
        try:
            yield con; con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK"); raise
        finally: con.close()

    def _service(self):
        if self.identity_service is not None: return self.identity_service
        try:
            return load_active_identity_service(root=self.security_master_root)[0]
        except LocalSecurityMasterError as exc:
            if str(exc) == "NOT_INITIALIZED": raise WatchlistError("SECURITY_MASTER_NOT_INITIALIZED") from exc
            raise WatchlistError("SECURITY_MASTER_UNAVAILABLE", str(exc)) from exc

    def _release_id(self, service: Any) -> str | None:
        return getattr(service, "release_id", None)

    def _watchlist(self, con: sqlite3.Connection, watchlist_id: str, *, include_deleted: bool = True) -> dict[str, Any]:
        row = con.execute("SELECT * FROM watchlists WHERE watchlist_id=?", (watchlist_id,)).fetchone()
        if row is None or (row["deleted"] and not include_deleted): raise WatchlistError("WATCHLIST_NOT_FOUND")
        entries = [json.loads(r[0]) for r in con.execute("SELECT payload_json FROM entries WHERE watchlist_id=? ORDER BY json_extract(payload_json, '$.display_order'), watchlist_entry_id", (watchlist_id,))]
        return {"schema_version": "persistent_watchlist.v1", "watchlist_id": row["watchlist_id"], "name": row["name"], "current_version": row["current_version"], "is_default": bool(row["is_default"]), "deleted": bool(row["deleted"]), "created_at": row["created_at"], "updated_at": row["updated_at"], "entries": entries}

    def _validate_snapshot(self, snapshot: dict[str, Any]) -> None:
        if len(snapshot["entries"]) > LIMITS["entries"]: raise WatchlistError("WATCHLIST_RESOURCE_LIMIT_EXCEEDED", details={"field": "entries"})
        seen: set[str] = set()
        for idx, entry in enumerate(snapshot["entries"], 1):
            if entry["instrument_id"] in seen: raise WatchlistError("WATCHLIST_ENTRY_ALREADY_EXISTS", details={"instrument_id": entry["instrument_id"]})
            seen.add(entry["instrument_id"]); entry["display_order"] = idx
            if len(entry.get("notes", "")) > LIMITS["notes_length"]: raise WatchlistError("WATCHLIST_RESOURCE_LIMIT_EXCEEDED", details={"field": "notes"})
            entry["tags"] = _normal_tags(entry.get("tags", []))
        validate_contract(snapshot, "persistent_watchlist.v1.schema.json")

    def _revision(self, *, snapshot: dict[str, Any], mutation_type: str, actor: str, affected_entries: list[str], affected_instruments: list[str], confirmation: dict[str, Any], previous_hash: str | None) -> dict[str, Any]:
        payload = {"schema_version": "persistent_watchlist_revision.v1", "watchlist_id": snapshot["watchlist_id"], "version": snapshot["current_version"], "previous_version": snapshot["current_version"] - 1 if snapshot["current_version"] > 1 else None, "created_at": snapshot["updated_at"], "mutation_type": mutation_type, "actor_source": actor, "affected_entry_ids": sorted(affected_entries), "affected_instrument_ids": sorted(affected_instruments), "confirmation": confirmation, "snapshot": copy.deepcopy(snapshot), "previous_revision_sha256": previous_hash}
        payload["content_sha256"] = sha256_json(payload)
        validate_contract(payload, "persistent_watchlist_revision.v1.schema.json")
        return payload

    def _write_snapshot(self, con: sqlite3.Connection, snapshot: dict[str, Any], *, mutation_type: str, actor: str, affected_entries: list[str], affected_instruments: list[str], confirmation: dict[str, Any]) -> dict[str, Any]:
        self._validate_snapshot(snapshot)
        prev = con.execute("SELECT content_sha256 FROM revisions WHERE watchlist_id=? AND version=?", (snapshot["watchlist_id"], snapshot["current_version"] - 1)).fetchone()
        revision = self._revision(snapshot=snapshot, mutation_type=mutation_type, actor=actor, affected_entries=affected_entries, affected_instruments=affected_instruments, confirmation=confirmation, previous_hash=prev[0] if prev else None)
        con.execute("UPDATE watchlists SET name=?, current_version=?, is_default=?, deleted=?, updated_at=? WHERE watchlist_id=?", (snapshot["name"], snapshot["current_version"], int(snapshot["is_default"]), int(snapshot["deleted"]), snapshot["updated_at"], snapshot["watchlist_id"]))
        con.execute("DELETE FROM entries WHERE watchlist_id=?", (snapshot["watchlist_id"],))
        for entry in snapshot["entries"]:
            con.execute("INSERT INTO entries VALUES (?,?,?,?)", (entry["watchlist_entry_id"], snapshot["watchlist_id"], entry["instrument_id"], canonical_json(entry)))
        con.execute("INSERT INTO revisions VALUES (?,?,?,?)", (snapshot["watchlist_id"], snapshot["current_version"], canonical_json(revision), revision["content_sha256"]))
        return revision

    def list_watchlists(self, *, include_deleted: bool = False) -> dict[str, Any]:
        con = self._connect()
        try:
            sql = "SELECT watchlist_id FROM watchlists" + ("" if include_deleted else " WHERE deleted=0") + " ORDER BY created_at, watchlist_id"
            rows = [self._watchlist(con, r[0], include_deleted=True) for r in con.execute(sql)]
            return {"state": "NO_WATCHLISTS" if not rows else "OK", "watchlists": rows}
        finally: con.close()

    def get_watchlist(self, watchlist_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        con = self._connect()
        try:
            stored = self._watchlist(con, watchlist_id, include_deleted=include_deleted)
        finally: con.close()
        stored["current_identity_projection"] = self._identity_projection(stored["entries"])
        return stored

    def _identity_projection(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        try: service = self._service()
        except WatchlistError as exc: return [{"watchlist_entry_id": e["watchlist_entry_id"], "instrument_id": e["instrument_id"], "identity_status": exc.code} for e in entries]
        out = []
        for entry in entries:
            resolution = service.resolve(entry["instrument_id"])
            if resolution.status != "resolved": out.append({"watchlist_entry_id": entry["watchlist_entry_id"], "instrument_id": entry["instrument_id"], "identity_status": "unresolved", "routing_available": False}); continue
            desc = service.describe(resolution.selected); migration = official_successor_migration(resolution.selected)
            out.append({"watchlist_entry_id": entry["watchlist_entry_id"], "instrument_id": entry["instrument_id"], "identity_status": "resolved", "persistable": True, "executable": desc["execution_eligibility"].get("status") == "allowed", "current_listing_id": desc["listing_id"], "execution_eligibility": desc["execution_eligibility"], "identity_migration": migration})
        return out

    def revisions(self, watchlist_id: str) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            self._watchlist(con, watchlist_id)
            return [json.loads(r[0]) for r in con.execute("SELECT payload_json FROM revisions WHERE watchlist_id=? ORDER BY version", (watchlist_id,))]
        finally: con.close()

    def revision(self, watchlist_id: str, version: int) -> dict[str, Any]:
        con = self._connect()
        try:
            row = con.execute("SELECT payload_json FROM revisions WHERE watchlist_id=? AND version=?", (watchlist_id, version)).fetchone()
            if not row: raise WatchlistError("WATCHLIST_NOT_FOUND")
            return json.loads(row[0])
        finally: con.close()

    def _resolve_entry(self, service: Any, query: str, market_hint: str | None) -> dict[str, Any]:
        resolution = service.resolve(query, market_hint=market_hint)
        if resolution.status == "ambiguous": raise WatchlistError("IDENTITY_AMBIGUOUS", details={"candidates": [service.describe(x) for x in resolution.candidates]})
        if resolution.status != "resolved": raise WatchlistError("IDENTITY_NOT_FOUND")
        record = resolution.selected; desc = service.describe(record)
        if desc["market"] not in CASH_MARKETS or not desc["instrument_id"]: raise WatchlistError("IDENTITY_SCHEME_UNSUPPORTED")
        now = self.now()
        return {"watchlist_entry_id": str(uuid.uuid4()), "instrument_id": desc["instrument_id"], "identity_scheme": "ISIN", "enabled": True, "display_order": 1, "tags": [], "notes": "", "created_at": now, "updated_at": now, "resolved_under_security_master_release_id": self._release_id(service), "display_name": (record.get("identity") or {}).get("security_name_zh") or (record.get("identity") or {}).get("security_name_en"), "cached_market": desc["market"], "cached_security_code": desc["security_code"], "cached_listing_id": desc["listing_id"], "instrument_type": desc["instrument_type"]}

    def _legacy_items(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        if len(canonical_json(source).encode("utf-8")) > LIMITS["import_bytes"]: raise WatchlistError("WATCHLIST_IMPORT_TOO_LARGE")
        if _depth(source) > LIMITS["json_depth"]: raise WatchlistError("WATCHLIST_RESOURCE_LIMIT_EXCEEDED", details={"field": "json_depth"})
        items = source.get("items") if isinstance(source, dict) else None
        if not isinstance(items, list):
            items = []
            for category in source.get("categories", []) if isinstance(source, dict) else []:
                items.extend(category.get("instruments", []) if isinstance(category, dict) else [])
        if not isinstance(items, list): raise WatchlistError("WATCHLIST_SCHEMA_INVALID")
        return [x for x in items if isinstance(x, dict)]

    def preview(self, command: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(command, dict) or command.get("schema_version") != "persistent_watchlist_mutation_command.v1": raise WatchlistError("WATCHLIST_SCHEMA_INVALID")
        validate_contract(command, "persistent_watchlist_mutation_command.v1.schema.json")
        typ, actor = command.get("command_type"), command.get("actor_source")
        if typ not in {"create_watchlist", "rename_watchlist", "set_default_watchlist", "add_entry", "remove_entry", "set_entry_enabled", "reorder_entries", "set_entry_tags", "set_entry_notes", "delete_watchlist", "restore_watchlist", "rollback_watchlist", "import_legacy_watchlist", "confirm_identity_migration"} or actor not in ACTORS: raise WatchlistError("WATCHLIST_SCHEMA_INVALID")
        command = copy.deepcopy(command); watchlist_id = command.get("watchlist_id"); expected: dict[str, int] = {}; warnings: list[str] = []; deferred: list[dict[str, Any]] = []; additional_after: list[dict[str, Any]] = []
        before = None
        if typ != "create_watchlist":
            if not isinstance(watchlist_id, str) or not isinstance(command.get("expected_version"), int): raise WatchlistError("WATCHLIST_SCHEMA_INVALID")
            con = self._connect()
            try: before = self._watchlist(con, watchlist_id)
            finally: con.close()
            expected[watchlist_id] = command["expected_version"]
            if before["current_version"] != command["expected_version"]: raise WatchlistError("WATCHLIST_VERSION_CONFLICT", details={"current_version": before["current_version"]})
        now = self.now(); service = None
        if typ == "create_watchlist":
            name = _normal_text(command.get("name"), limit=LIMITS["name_length"], code="name")
            con = self._connect(); count = con.execute("SELECT COUNT(*) FROM watchlists").fetchone()[0]; default_row = con.execute("SELECT watchlist_id FROM watchlists WHERE is_default=1 AND deleted=0").fetchone()
            if count >= LIMITS["watchlists"]: raise WatchlistError("WATCHLIST_RESOURCE_LIMIT_EXCEEDED", details={"field": "watchlists"})
            watchlist_id = str(uuid.uuid4()); command["watchlist_id"] = watchlist_id
            after = {"schema_version": "persistent_watchlist.v1", "watchlist_id": watchlist_id, "name": name, "current_version": 1, "is_default": bool(command.get("set_default", False)) or not bool(default_row), "deleted": False, "created_at": now, "updated_at": now, "entries": []}
            if after["is_default"] and default_row:
                prior = self._watchlist(con, default_row["watchlist_id"])
                expected[prior["watchlist_id"]] = prior["current_version"]
                prior["current_version"] += 1; prior["is_default"] = False; prior["updated_at"] = now
                additional_after.append(prior)
            con.close()
        else:
            after = copy.deepcopy(before); after["current_version"] += 1; after["updated_at"] = now
            if typ == "rename_watchlist": after["name"] = _normal_text(command.get("name"), limit=LIMITS["name_length"], code="name")
            elif typ == "set_default_watchlist":
                if after["deleted"]:
                    raise WatchlistError("WATCHLIST_NOT_FOUND")
                after["is_default"] = True
                con = self._connect()
                try:
                    prior_row = con.execute("SELECT watchlist_id FROM watchlists WHERE is_default=1 AND deleted=0 AND watchlist_id<>?", (watchlist_id,)).fetchone()
                    if prior_row:
                        prior = self._watchlist(con, prior_row["watchlist_id"])
                        expected[prior["watchlist_id"]] = prior["current_version"]
                        prior["current_version"] += 1; prior["is_default"] = False; prior["updated_at"] = now
                        additional_after.append(prior)
                finally: con.close()
            elif typ == "add_entry":
                service = self._service(); entry = self._resolve_entry(service, command.get("query", ""), command.get("market_hint")); command["resolved_entry"] = entry
                if any(x["instrument_id"] == entry["instrument_id"] for x in after["entries"]): raise WatchlistError("WATCHLIST_ENTRY_ALREADY_EXISTS", details={"instrument_id": entry["instrument_id"]})
                entry["enabled"] = bool(command.get("enabled", True)); entry["tags"] = _normal_tags(command.get("tags", [])); entry["notes"] = command.get("notes", "") if isinstance(command.get("notes", ""), str) else ""; entry["display_order"] = len(after["entries"]) + 1; after["entries"].append(entry)
            elif typ == "remove_entry":
                if not any(x["watchlist_entry_id"] == command.get("watchlist_entry_id") for x in after["entries"]): raise WatchlistError("WATCHLIST_ENTRY_NOT_FOUND")
                after["entries"] = [x for x in after["entries"] if x["watchlist_entry_id"] != command.get("watchlist_entry_id")]
            elif typ == "set_entry_enabled":
                e = next((x for x in after["entries"] if x["watchlist_entry_id"] == command.get("watchlist_entry_id")), None)
                if not e: raise WatchlistError("WATCHLIST_ENTRY_NOT_FOUND")
                e["enabled"] = bool(command.get("enabled")); e["updated_at"] = now
            elif typ == "set_entry_tags":
                e = next((x for x in after["entries"] if x["watchlist_entry_id"] == command.get("watchlist_entry_id")), None)
                if not e: raise WatchlistError("WATCHLIST_ENTRY_NOT_FOUND")
                e["tags"] = _normal_tags(command.get("tags", [])); e["updated_at"] = now
            elif typ == "set_entry_notes":
                e = next((x for x in after["entries"] if x["watchlist_entry_id"] == command.get("watchlist_entry_id")), None)
                if not e: raise WatchlistError("WATCHLIST_ENTRY_NOT_FOUND")
                e["notes"] = command.get("notes", "") if isinstance(command.get("notes"), str) and len(command["notes"]) <= LIMITS["notes_length"] else (_ for _ in ()).throw(WatchlistError("WATCHLIST_RESOURCE_LIMIT_EXCEEDED")); e["updated_at"] = now
            elif typ == "reorder_entries":
                ordered = command.get("watchlist_entry_ids")
                if not isinstance(ordered, list) or set(ordered) != {x["watchlist_entry_id"] for x in after["entries"]}: raise WatchlistError("WATCHLIST_SCHEMA_INVALID")
                lookup = {x["watchlist_entry_id"]: x for x in after["entries"]}; after["entries"] = [lookup[x] for x in ordered]
            elif typ == "delete_watchlist": after["deleted"] = True; after["is_default"] = False
            elif typ == "restore_watchlist": after["deleted"] = False
            elif typ == "rollback_watchlist": after = copy.deepcopy(self.revision(watchlist_id, int(command.get("target_version", 0)))["snapshot"]); after["current_version"] = before["current_version"] + 1; after["updated_at"] = now; after["deleted"] = False
            elif typ == "import_legacy_watchlist":
                service = self._service(); accepted: list[dict[str, Any]] = []
                for item in self._legacy_items(command.get("legacy_watchlist")):
                    market = str(item.get("market") or "").upper()
                    if market not in CASH_MARKETS: deferred.append({"item": item.get("id") or item.get("symbol"), "reason_code": "IDENTITY_SCHEME_UNSUPPORTED"}); continue
                    try: entry = self._resolve_entry(service, str(item.get("symbol") or item.get("name") or ""), market)
                    except WatchlistError as exc: deferred.append({"item": item.get("id") or item.get("symbol"), "reason_code": exc.code}); continue
                    if entry["instrument_id"] in {x["instrument_id"] for x in after["entries"]} | {x["instrument_id"] for x in accepted}: deferred.append({"item": item.get("id") or item.get("symbol"), "reason_code": "WATCHLIST_ENTRY_ALREADY_EXISTS"}); continue
                    entry["enabled"] = bool(item.get("enabled", True)); entry["tags"] = _normal_tags(item.get("tags", [])); entry["notes"] = item.get("notes", "") if isinstance(item.get("notes", ""), str) else ""; accepted.append(entry)
                command["accepted_entries"] = accepted; after["entries"].extend(accepted)
            elif typ == "confirm_identity_migration":
                service = self._service(); e = next((x for x in after["entries"] if x["watchlist_entry_id"] == command.get("watchlist_entry_id")), None)
                if not e: raise WatchlistError("WATCHLIST_ENTRY_NOT_FOUND")
                res = service.resolve(e["instrument_id"])
                if res.status != "resolved" or not official_successor_migration(res.selected): raise WatchlistError("IDENTITY_MIGRATION_REVIEW_REQUIRED")
                successor = official_successor_migration(res.selected)["successor"]; new = self._resolve_entry(service, successor, None); new["watchlist_entry_id"] = e["watchlist_entry_id"]; new["tags"], new["notes"], new["enabled"], new["created_at"] = e["tags"], e["notes"], e["enabled"], e["created_at"]; after["entries"][after["entries"].index(e)] = new; command["resolved_successor"] = successor
        self._validate_snapshot(after)
        preview = {"schema_version": "persistent_watchlist_mutation_preview.v1", "preview_id": str(uuid.uuid4()), "command": command, "watchlist_id": watchlist_id, "expected_versions": expected, "before": before, "after": after, "additional_after": additional_after, "warnings": warnings, "deferred_items": deferred, "security_master_release_id": self._release_id(service) if service else None, "created_at": now, "expires_at": (datetime.fromisoformat(now.replace("Z", "+00:00")) + PREVIEW_TTL).isoformat(timespec="seconds").replace("+00:00", "Z")}
        preview["content_sha256"] = sha256_json(preview)
        with self._write() as con: con.execute("INSERT INTO mutation_previews VALUES (?,?,?,?,NULL)", (preview["preview_id"], canonical_json(preview), preview["content_sha256"], preview["expires_at"]))
        return preview

    def commit(self, *, preview_id: str, preview_hash: str, confirmed: bool) -> dict[str, Any]:
        if confirmed is not True: raise WatchlistError("WATCHLIST_CONFIRMATION_REQUIRED")
        with self._write() as con:
            row = con.execute("SELECT * FROM mutation_previews WHERE preview_id=?", (preview_id,)).fetchone()
            if not row: raise WatchlistError("WATCHLIST_CONFIRMATION_MISMATCH")
            if row["consumed_at"]: raise WatchlistError("WATCHLIST_CONFIRMATION_ALREADY_CONSUMED")
            preview = json.loads(row["payload_json"])
            if preview_hash != row["content_sha256"]: raise WatchlistError("WATCHLIST_CONFIRMATION_MISMATCH")
            if datetime.fromisoformat(preview["expires_at"].replace("Z", "+00:00")) <= datetime.fromisoformat(self.now().replace("Z", "+00:00")): raise WatchlistError("WATCHLIST_CONFIRMATION_EXPIRED")
            for watchlist_id, version in preview["expected_versions"].items():
                live = self._watchlist(con, watchlist_id)
                if live["current_version"] != version: raise WatchlistError("WATCHLIST_VERSION_CONFLICT", details={"current_version": live["current_version"]})
            bound = preview.get("security_master_release_id")
            if bound:
                if self._release_id(self._service()) != bound: raise WatchlistError("WATCHLIST_PREVIEW_STALE_IDENTITY_CONTEXT")
            snapshot = preview["after"]; typ, actor = preview["command"]["command_type"], preview["command"]["actor_source"]
            if typ == "create_watchlist": con.execute("INSERT INTO watchlists VALUES (?,?,?,?,?,?,?)", (snapshot["watchlist_id"], snapshot["name"], snapshot["current_version"], int(snapshot["is_default"]), int(snapshot["deleted"]), snapshot["created_at"], snapshot["updated_at"]))
            confirmation = {"preview_id": preview_id, "preview_hash": preview_hash, "actor_source": actor, "confirmed_at": self.now()}
            affected = [x["watchlist_entry_id"] for x in snapshot["entries"]]; instruments = [x["instrument_id"] for x in snapshot["entries"]]
            revision = self._write_snapshot(con, snapshot, mutation_type=typ, actor=actor, affected_entries=affected, affected_instruments=instruments, confirmation=confirmation)
            for other in preview.get("additional_after", []):
                self._write_snapshot(con, other, mutation_type="set_default_watchlist", actor=actor, affected_entries=[], affected_instruments=[], confirmation=confirmation)
            con.execute("UPDATE mutation_previews SET consumed_at=? WHERE preview_id=?", (self.now(), preview_id))
            return {"watchlist": snapshot, "revision": revision}

    def export(self, watchlist_id: str, *, include_history: bool = False) -> dict[str, Any]:
        payload = {"schema_version": "persistent_watchlist_export.v1", "watchlist": self.get_watchlist(watchlist_id, include_deleted=True)}
        payload["watchlist"].pop("current_identity_projection", None)
        if include_history: payload["revisions"] = self.revisions(watchlist_id)
        payload["content_sha256"] = sha256_json(payload)
        validate_contract(payload, "persistent_watchlist_export.v1.schema.json")
        return payload

    def verify_integrity(self) -> dict[str, Any]:
        con = self._connect()
        try:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok": raise WatchlistError("WATCHLIST_STORAGE_CORRUPT")
            if con.execute("PRAGMA foreign_key_check").fetchall(): raise WatchlistError("WATCHLIST_STORAGE_CORRUPT")
            for row in con.execute("SELECT watchlist_id,current_version FROM watchlists"):
                revision_rows = list(con.execute("SELECT payload_json,content_sha256 FROM revisions WHERE watchlist_id=? ORDER BY version", (row["watchlist_id"],)))
                revisions = [json.loads(r["payload_json"]) for r in revision_rows]
                if not revisions or revisions[-1]["version"] != row["current_version"]: raise WatchlistError("WATCHLIST_VERSION_CHAIN_BROKEN")
                prev = None
                for revision, persisted_hash in zip(revisions, (r["content_sha256"] for r in revision_rows)):
                    claimed = revision.pop("content_sha256"); actual = sha256_json(revision); revision["content_sha256"] = claimed
                    if claimed != actual or claimed != persisted_hash or revision["previous_revision_sha256"] != prev: raise WatchlistError("WATCHLIST_VERSION_CHAIN_BROKEN")
                    prev = claimed
                current = self._watchlist(con, row["watchlist_id"])
                if canonical_json(current) != canonical_json(revisions[-1]["snapshot"]):
                    raise WatchlistError("WATCHLIST_VERSION_CHAIN_BROKEN")
            return {"status": "PASS", "schema_version": SCHEMA_VERSION}
        finally: con.close()


def production_store() -> PersistentWatchlistStore:
    return PersistentWatchlistStore()
