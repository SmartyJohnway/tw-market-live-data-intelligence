"""Schema-governed installation-local Security Master releases."""

from __future__ import annotations
import hashlib, json, os, re, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import jsonschema
from scripts.m8r_08g_identity_service import (
    CASH_MARKETS,
    TaiwanMarketIdentityService,
    instrument_id,
    listing_id,
    official_successor_migration,
    project_release_record,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SECURITY_MASTER_ROOT = REPO_ROOT / "data" / "security_master"
SCHEMA_ROOT = REPO_ROOT / "docs" / "contracts" / "schemas"
ACTIVE_POINTER_NAME = "active.json"
RELEASE_ID_RE = re.compile(r"^security-master-\d{8}T\d{6}Z$")
ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{10}$")
PRODUCER_VERSION = "m8r_08g_identity_service_release_producer.v1"
SCHEMA_FILES = {
    "index": "taiwan_market_identity_release_index.v1.schema.json",
    "record": "taiwan_market_identity_record.v1.schema.json",
    "candidate": "taiwan_market_identity_candidate.v1.schema.json",
    "status": "taiwan_market_identity_release_status.v1.schema.json",
    "qualification": "taiwan_market_identity_release_qualification.v1.schema.json",
    "manifest": "taiwan_market_identity_release_manifest.v1.schema.json",
    "release": "taiwan_market_identity_release.v1.schema.json",
    "active_pointer": "taiwan_market_identity_active_pointer.v1.schema.json",
}


class LocalSecurityMasterError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def release_id_for_now():
    return "security-master-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _json(v):
    return (json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def atomic_write_json(p: Path, v: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb", delete=False, dir=p.parent, prefix=".tmp-"
    ) as h:
        h.write(_json(v))
        tmp = Path(h.name)
    os.replace(tmp, p)


def _read(p: Path, code: str):
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise LocalSecurityMasterError(code) from e
    if not isinstance(v, dict):
        raise LocalSecurityMasterError(code)
    return v


def _dir(root: Path, kind: str, rid: str):
    if not RELEASE_ID_RE.fullmatch(rid):
        raise LocalSecurityMasterError("invalid_release_id")
    return root / kind / rid


def _schema(n):
    return _read(SCHEMA_ROOT / SCHEMA_FILES[n], "release_schema_missing")


def _valid(n, v, code):
    try:
        jsonschema.Draft202012Validator(_schema(n)).validate(v)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as e:
        raise LocalSecurityMasterError(code) from e


def _hashes():
    return {n: sha256_file(SCHEMA_ROOT / f) for n, f in SCHEMA_FILES.items()}


def _commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception as e:
        raise LocalSecurityMasterError("repository_commit_unavailable") from e


def _prov(p: dict):
    skill = p.get("producer_skill") if isinstance(p, dict) else None
    hashes = p.get("source_content_hashes") if isinstance(p, dict) else None
    if (
        not isinstance(skill, dict)
        or not isinstance(skill.get("skill_contract_hash"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", skill["skill_contract_hash"])
    ):
        raise LocalSecurityMasterError("producer_skill_contract_hash_missing")
    if (
        not isinstance(hashes, dict)
        or not hashes
        or not all(
            isinstance(x, str) and re.fullmatch(r"[0-9a-f]{64}", x)
            for x in hashes.values()
        )
    ):
        raise LocalSecurityMasterError("source_content_hashes_invalid")
    return {
        "source_type": p.get("source_type")
        or p.get("source")
        or "explicit_governed_import",
        "snapshot_id": p.get("snapshot_id"),
        "generated_at": p.get("generated_at"),
        "official_source_family": p.get("official_source_family"),
        "producer_skill": {
            "name": skill.get("name"),
            "skill_version": skill.get("skill_version"),
            "skill_contract_hash": skill["skill_contract_hash"],
        },
        "source_content_hashes": dict(sorted(hashes.items())),
    }


def build_candidate_release(
    *, root: Path, release_id: str, records: list[dict], source_provenance: dict
):
    d = _dir(root, "candidates", release_id)
    if d.exists() or _dir(root, "releases", release_id).exists():
        raise LocalSecurityMasterError("release_already_exists")
    p = _prov(source_provenance)
    idx = {
        "schema_version": "taiwan_market_identity_release_index.v1",
        "release_id": release_id,
        "record_count": len(records),
        "records": records,
        "source_provenance": p,
    }
    _valid("index", idx, "candidate_index_schema_invalid")
    d.mkdir(parents=True)
    atomic_write_json(d / "index.json", idx)
    meta = {
        "schema_version": "taiwan_market_identity_candidate.v1",
        "release_id": release_id,
        "state": "CANDIDATE",
        "created_at": utc_now(),
        "index_sha256": sha256_file(d / "index.json"),
    }
    _valid("candidate", meta, "candidate_schema_invalid")
    atomic_write_json(d / "candidate.json", meta)
    return d


def _reasons(r):
    if not isinstance(r, dict):
        return ["record_not_object"]
    try:
        lid = listing_id(r)
    except ValueError:
        return ["listing_id_invalid"]
    out = []
    ident = r.get("identity")
    cls = r.get("classification")
    life = r.get("lifecycle")
    if r.get("canonical_target_id") not in {None, lid}:
        out.append("canonical_target_id_listing_conflict")
    if not all(isinstance(x, dict) for x in (ident, cls, life)):
        return out + ["record_required_structure_invalid"]
    isin = ident.get("isin")
    explicit = r.get("instrument_id")
    if cls.get("market") in CASH_MARKETS:
        if not isinstance(isin, str) or not ISIN_RE.fullmatch(isin.upper()):
            out.append("cash_isin_invalid")
        if explicit is not None and explicit != (
            isin.upper() if isinstance(isin, str) else None
        ):
            out.append("instrument_id_isin_mismatch")
    if (
        life.get("state") in {"terminated", "delisted", "inactive"}
        and life.get("resolution_status") == "resolved"
        and not life.get("basis_event_ids")
    ):
        out.append("lifecycle_state_without_governed_basis")
    m = official_successor_migration(r)
    if m and m["predecessor"] == m["successor"]:
        out.append("successor_equals_predecessor")
    return out


def validate_release_candidate(*, root: Path, release_id: str):
    base = _dir(root, "candidates", release_id)
    idx = _read(base / "index.json", "candidate_index_missing")
    reasons = []
    try:
        _valid(
            "candidate",
            _read(base / "candidate.json", "candidate_metadata_missing"),
            "candidate_schema_invalid",
        )
    except LocalSecurityMasterError as e:
        reasons.append(e.code)
    try:
        _valid("index", idx, "candidate_index_schema_invalid")
    except LocalSecurityMasterError as e:
        reasons.append(e.code)
    records = idx.get("records") if isinstance(idx.get("records"), list) else []
    if idx.get("record_count") != len(records):
        reasons.append("candidate_record_count_mismatch")
    lids = set()
    canons = set()
    isins = {}
    projected = []
    for r in records:
        try:
            _valid("record", r, "record_schema_invalid")
            rr = _reasons(r)
        except LocalSecurityMasterError:
            rr = ["record_schema_invalid"]
        reasons += rr
        if rr:
            continue
        lid = listing_id(r)
        canon = r.get("canonical_target_id") or lid
        ins = instrument_id(r)
        if lid in lids:
            reasons.append("duplicate_listing_id")
        if canon in canons:
            reasons.append("duplicate_canonical_target_id")
        if ins and ins in isins and isins[ins] != lid:
            reasons.append("duplicate_instrument_id")
        lids.add(lid)
        canons.add(canon)
        isins[ins] = lid
        projected.append(project_release_record(r))
    counts = {
        "record_count": len(records),
        "knowledge_universe_count": len(projected),
        "execution_eligible_count": sum(
            (x.get("execution_eligibility") or {}).get("status")
            in {"allowed", "allowed_with_caveat"}
            for x in projected
        ),
        "quarantine_count": len(records) - len(projected),
    }
    return {
        "schema_version": "taiwan_market_identity_release_qualification.v1",
        "release_id": release_id,
        "status": "PASS" if not reasons else "FAIL",
        "validated_at": utc_now(),
        "checks": [
            {"name": "structural_identity_uniqueness_lifecycle", "passed": not reasons}
        ],
        "reason_codes": sorted(set(reasons)),
        "counts": counts,
    }


def _reject(root, rid, report):
    d = _dir(root, "rejected", rid)
    d.mkdir(parents=True, exist_ok=False)
    atomic_write_json(d / "qualification.json", report)
    meta = {
        "schema_version": "taiwan_market_identity_release_status.v1",
        "release_id": rid,
        "state": "REJECTED",
        "created_at": utc_now(),
        "reason_codes": report["reason_codes"],
    }
    _valid("status", meta, "rejected_status_schema_invalid")
    atomic_write_json(d / "release.json", meta)
    return d


def qualify_candidate_release(*, root: Path, release_id: str):
    report = validate_release_candidate(root=root, release_id=release_id)
    _valid("qualification", report, "qualification_report_schema_invalid")
    candidate = _dir(root, "candidates", release_id)
    atomic_write_json(candidate / "qualification.json", report)
    if report["status"] != "PASS":
        return None, _reject(root, release_id, report)
    idx = _read(candidate / "index.json", "candidate_index_missing")
    d = _dir(root, "releases", release_id)
    d.mkdir(parents=True, exist_ok=False)
    atomic_write_json(d / "index.json", idx)
    atomic_write_json(d / "qualification.json", report)
    h = _hashes()
    p = idx["source_provenance"]
    manifest = {
        "schema_version": "taiwan_market_identity_release_manifest.v1",
        "release_id": release_id,
        "state": "QUALIFIED",
        "created_at": utc_now(),
        "repository_commit": _commit(),
        "producer_version": PRODUCER_VERSION,
        "producer_skill_contract_hash": p["producer_skill"]["skill_contract_hash"],
        "source_provenance": p,
        "source_content_hashes": p["source_content_hashes"],
        "schema_versions": {n: _schema(n).get("$id") for n in SCHEMA_FILES},
        "release_index_schema_sha256": h["index"],
        "release_qualification_schema_sha256": h["qualification"],
        "release_manifest_schema_sha256": h["manifest"],
        "index_sha256": sha256_file(d / "index.json"),
        "qualification_report_sha256": sha256_file(d / "qualification.json"),
        **report["counts"],
    }
    _valid("manifest", manifest, "release_manifest_schema_invalid")
    atomic_write_json(d / "manifest.json", manifest)
    release = {
        "schema_version": "taiwan_market_identity_release.v1",
        "release_id": release_id,
        "state": "QUALIFIED",
        "manifest_sha256": sha256_file(d / "manifest.json"),
        "created_at": manifest["created_at"],
    }
    _valid("release", release, "release_schema_invalid")
    atomic_write_json(d / "release.json", release)
    return d, report


def build_qualified_release(**_):
    raise LocalSecurityMasterError("qualification_constructor_prohibited")


def load_qualified_release(*, root: Path, release_id: str):
    d = _dir(root, "releases", release_id)
    rel = _read(d / "release.json", "release_missing")
    man = _read(d / "manifest.json", "release_manifest_missing")
    idx = _read(d / "index.json", "release_index_missing")
    report = _read(d / "qualification.json", "release_qualification_missing")
    _valid("release", rel, "release_schema_invalid")
    _valid("manifest", man, "release_manifest_schema_invalid")
    _valid("index", idx, "release_index_schema_invalid")
    _valid("qualification", report, "release_qualification_schema_invalid")
    h = _hashes()
    if any(
        man.get(k) != h[n]
        for k, n in [
            ("release_index_schema_sha256", "index"),
            ("release_qualification_schema_sha256", "qualification"),
            ("release_manifest_schema_sha256", "manifest"),
        ]
    ):
        raise LocalSecurityMasterError("release_schema_hash_mismatch")
    if sha256_file(d / "manifest.json") != rel["manifest_sha256"]:
        raise LocalSecurityMasterError("release_manifest_hash_mismatch")
    if (
        sha256_file(d / "index.json") != man["index_sha256"]
        or sha256_file(d / "qualification.json") != man["qualification_report_sha256"]
    ):
        raise LocalSecurityMasterError("release_content_hash_mismatch")
    if report["status"] != "PASS":
        raise LocalSecurityMasterError("release_not_qualified")
    return rel, man, idx


def activate_qualified_release(*, root: Path, release_id: str):
    if (_dir(root, "retired", release_id) / "release.json").is_file():
        raise LocalSecurityMasterError("release_retired")
    _, m, _ = load_qualified_release(root=root, release_id=release_id)
    p = {
        "schema_version": "taiwan_market_identity_active_pointer.v1",
        "release_id": release_id,
        "activated_at": utc_now(),
        "release_manifest_sha256": sha256_file(
            _dir(root, "releases", release_id) / "manifest.json"
        ),
        "release_index_sha256": m["index_sha256"],
        "release_manifest_schema_sha256": m["release_manifest_schema_sha256"],
    }
    _valid("active_pointer", p, "active_pointer_schema_invalid")
    atomic_write_json(root / ACTIVE_POINTER_NAME, p)
    return p


def load_active_identity_service(*, root: Path):
    pth = root / ACTIVE_POINTER_NAME
    if not pth.is_file():
        raise LocalSecurityMasterError("NOT_INITIALIZED")
    p = _read(pth, "active_pointer_invalid")
    _valid("active_pointer", p, "active_pointer_schema_invalid")
    rel, m, idx = load_qualified_release(root=root, release_id=p["release_id"])
    if (
        p["release_manifest_sha256"]
        != sha256_file(_dir(root, "releases", p["release_id"]) / "manifest.json")
        or p["release_index_sha256"] != m["index_sha256"]
        or p["release_manifest_schema_sha256"] != m["release_manifest_schema_sha256"]
    ):
        raise LocalSecurityMasterError("active_pointer_binding_mismatch")
    return (
        TaiwanMarketIdentityService(
            idx["records"],
            release_id=p["release_id"],
            manifest_hash=p["release_manifest_sha256"],
        ),
        p,
        rel,
        m,
    )


def retire_qualified_release(*, root: Path, release_id: str, reason: str):
    load_qualified_release(root=root, release_id=release_id)
    p = root / ACTIVE_POINTER_NAME
    if (
        p.is_file()
        and _read(p, "active_pointer_invalid").get("release_id") == release_id
    ):
        raise LocalSecurityMasterError("active_release_cannot_retire")
    d = _dir(root, "retired", release_id)
    d.mkdir(parents=True, exist_ok=False)
    meta = {
        "schema_version": "taiwan_market_identity_release_status.v1",
        "release_id": release_id,
        "state": "RETIRED",
        "retired_at": utc_now(),
        "reason": reason,
    }
    _valid("status", meta, "retired_status_schema_invalid")
    atomic_write_json(d / "release.json", meta)
    return d


def list_releases(*, root: Path):
    active = (
        _read(root / ACTIVE_POINTER_NAME, "active_pointer_invalid").get("release_id")
        if (root / ACTIVE_POINTER_NAME).is_file()
        else None
    )
    out = []
    for kind, state in [
        ("releases", "QUALIFIED"),
        ("retired", "RETIRED"),
        ("rejected", "REJECTED"),
    ]:
        base = root / kind
        if base.is_dir():
            for d in sorted(x for x in base.iterdir() if x.is_dir()):
                if kind in {"rejected", "retired"}:
                    metadata = _read(
                        d / "release.json", f"{state.lower()}_status_missing"
                    )
                    _valid("status", metadata, f"{state.lower()}_status_schema_invalid")
                    if (
                        metadata.get("release_id") != d.name
                        or metadata.get("state") != state
                    ):
                        raise LocalSecurityMasterError(
                            f"{state.lower()}_status_binding_mismatch"
                        )
                out.append(
                    {
                        "release_id": d.name,
                        "state": "ACTIVE"
                        if kind == "releases" and d.name == active
                        else state,
                    }
                )
    return sorted(out, key=lambda x: (x["release_id"], x["state"]))
