"""M8R-06-01C1B governed compact runtime identity index.

The compact artifact is derived only from the authorized sealed 01B bundle.  It
preserves every field that can affect the canonical resolver while omitting
evidence-only fields that the resolver never reads or returns.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.m8r_03d_f1_security_master_snapshot_adapter import (  # noqa: E402
    QUARANTINE,
    build_verified_security_master_lookup,
    resolve_verified_security_identity,
)
from scripts.m8r_06_security_master_candidate_paths import (  # noqa: E402
    LEGACY_ACCEPTED_CANDIDATE_A,
    input_bundle_dir,
    runtime_immutable_seal_path,
    runtime_index_dir,
    source_immutable_seal_path,
    validate_candidate_id,
)

# Historical constants remain frozen-A compatibility evidence only.  Rotatable
# production generation derives all authority from an explicit candidate ID.
AUTHORIZED_BUNDLE_ID = LEGACY_ACCEPTED_CANDIDATE_A
AUTHORIZED_SKILL_CONTRACT_HASH = (
    "488b3e04af2e318cd387b0dfdcbad02be4f2c3f495539c3e436698464f37d77a"
)
COMPACT_INDEX_SCHEMA_VERSION = "m8r_06_01c1b_compact_identity_index.v1"
COMPACT_MANIFEST_SCHEMA_VERSION = "m8r_06_01c1b_compact_index_manifest.v1"
PRODUCER_VERSION = "m8r_06_01c1b_compact_runtime_identity_index.v2"
SOURCE_SNAPSHOT_ARTIFACT = "dryrun_snapshot.json"

BUNDLE_DIR = input_bundle_dir(REPO_ROOT, AUTHORIZED_BUNDLE_ID)
COMMITTED_MANIFEST_PATH = source_immutable_seal_path(REPO_ROOT, AUTHORIZED_BUNDLE_ID)
COMPACT_INDEX_DIR = runtime_index_dir(REPO_ROOT, AUTHORIZED_BUNDLE_ID)
COMPACT_INDEX_SCHEMA_PATH = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "schemas"
    / "tw_compact_runtime_identity_index.v1.schema.json"
)
COMPACT_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "schemas"
    / "tw_compact_runtime_identity_index_manifest.v1.schema.json"
)

RESOLVER_RECORD_FIELDS = (
    "canonical_target_id",
    "record_id",
    "record_hash",
    "identity",
    "classification",
    "lifecycle",
    "execution_eligibility",
    "observation",
    "caveats",
)


class CompactArtifactValidationError(ValueError):
    """Fail-closed compact artifact validation error with a stable code."""


def _fail(code: str) -> None:
    raise CompactArtifactValidationError(code)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_value(path: Path, *, error_code: str = "invalid_json") -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail(f"missing_{path.name}")
    except (OSError, json.JSONDecodeError):
        _fail(error_code)
    return value


def load_json_file(path: Path, *, error_code: str = "invalid_json") -> dict[str, Any]:
    value = _read_json_value(path, error_code=error_code)
    if not isinstance(value, dict):
        _fail(error_code)
    return value


def write_json_file(path: Path, value: dict[str, Any]) -> None:
    """Write canonical deterministic JSON bytes with LF line endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _count_component(component: str, payload: Any) -> int:
    if component == "classification_records":
        return len(payload.get("records") or []) if isinstance(payload, dict) else len(payload)
    if component == "lifecycle_events":
        return len(payload.get("events") or []) if isinstance(payload, dict) else len(payload)
    if component == "dryrun_snapshot":
        return len(payload.get("records") or [])
    raise AssertionError(component)


def verify_bundle_integrity(
    candidate_id: str = AUTHORIZED_BUNDLE_ID,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Verify every sealed component, raw payload, count, and lineage field."""
    candidate = validate_candidate_id(candidate_id)
    root = repo_root.resolve()
    bundle_dir = input_bundle_dir(root, candidate)
    manifest_path = source_immutable_seal_path(root, candidate)
    seal = load_json_file(manifest_path, error_code="invalid_authorized_manifest")
    if seal.get("bundle_id") != candidate:
        _fail("authorized_bundle_id_mismatch")
    if candidate == AUTHORIZED_BUNDLE_ID and seal.get("skill_contract_hash") != AUTHORIZED_SKILL_CONTRACT_HASH:
        _fail("authorized_skill_contract_hash_mismatch")
    if seal.get("bundle_persisted_in_git") is not False:
        _fail("authorized_bundle_persistence_mismatch")

    components = {
        "classification_records": ("classification_records.json", "count"),
        "lifecycle_events": ("lifecycle_events.json", "count"),
        "source_evidence_manifest": ("source_evidence_manifest.json", None),
        "qualification_report": ("qualification_report.json", None),
        "dryrun_snapshot": (SOURCE_SNAPSHOT_ARTIFACT, "record_count"),
        "dryrun_manifest": ("dryrun_manifest.json", None),
    }
    expected_files = {"immutable_manifest.json"}
    loaded: dict[str, Any] = {}
    for component, (filename, count_key) in components.items():
        info = seal.get(component) or {}
        path = bundle_dir / filename
        expected_files.add(filename)
        if not path.is_file():
            _fail(f"missing_authorized_{component}")
        if sha256_file(path) != info.get("sha256"):
            _fail(f"authorized_{component}_sha256_mismatch")
        payload = _read_json_value(path, error_code=f"invalid_authorized_{component}")
        loaded[component] = payload
        if count_key and _count_component(component, payload) != info.get(count_key):
            _fail(f"authorized_{component}_count_mismatch")

    raw_payloads = seal.get("raw_payloads") or []
    if not raw_payloads:
        _fail("authorized_raw_payload_manifest_missing")
    for item in raw_payloads:
        filename = item.get("file_name")
        if not filename:
            _fail("authorized_raw_payload_manifest_invalid")
        relative = Path("raw_payloads") / filename
        path = bundle_dir / relative
        expected_files.add(relative.as_posix())
        if not path.is_file():
            _fail("authorized_raw_payload_missing")
        if sha256_file(path) != item.get("sha256"):
            _fail("authorized_raw_payload_sha256_mismatch")

    actual_files = {
        path.relative_to(bundle_dir).as_posix()
        for path in bundle_dir.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        _fail("authorized_bundle_file_set_mismatch")

    # The bundle-local manifest is producer-stage metadata.  The independently
    # committed manifest_path is the finalized authority and cryptographically
    # binds the actual component bytes verified above.
    load_json_file(
        bundle_dir / "immutable_manifest.json",
        error_code="invalid_bundled_producer_manifest",
    )

    snapshot = loaded["dryrun_snapshot"]
    if any(
        (record.get("observation") or {}).get("status") == "fixture_observation_only"
        for record in snapshot.get("records") or []
    ):
        _fail("authorized_fixture_snapshot_rejected")
    source_skill_hash = (snapshot.get("source_skill") or {}).get("skill_contract_hash")
    if source_skill_hash != seal.get("skill_contract_hash"):
        _fail("source_snapshot_skill_contract_hash_mismatch")
    snapshot_id = snapshot.get("snapshot_id")
    if not snapshot_id or snapshot_id == SOURCE_SNAPSHOT_ARTIFACT:
        _fail("source_snapshot_semantic_id_missing")
    return snapshot, seal, seal["dryrun_snapshot"]["sha256"]


def compute_coverage(snapshot: dict[str, Any]) -> dict[str, int]:
    records = snapshot.get("records") or []
    runtime_eligible = sum(
        (record.get("execution_eligibility") or {}).get("status")
        in {"allowed", "allowed_with_caveat"}
        for record in records
    )
    quarantined = sum(
        (record.get("classification") or {}).get("classification_status") in QUARANTINE
        for record in records
    )
    return {
        "knowledge_universe_count": len(records),
        "runtime_eligible_count": runtime_eligible,
        "quarantined_count": quarantined,
    }


def build_compact_index(
    snapshot: dict[str, Any],
    snapshot_sha256: str,
    *,
    source_bundle_id: str = AUTHORIZED_BUNDLE_ID,
    source_skill_contract_hash: str = AUTHORIZED_SKILL_CONTRACT_HASH,
) -> dict[str, Any]:
    records = [
        {field: copy.deepcopy(record.get(field)) for field in RESOLVER_RECORD_FIELDS}
        for record in snapshot.get("records") or []
    ]
    return {
        "schema_version": COMPACT_INDEX_SCHEMA_VERSION,
        "index_id": source_bundle_id,
        "source_bundle_id": source_bundle_id,
        "source_snapshot_id": snapshot["snapshot_id"],
        "source_snapshot_artifact": SOURCE_SNAPSHOT_ARTIFACT,
        "source_snapshot_sha256": snapshot_sha256,
        "source_skill_contract_hash": source_skill_contract_hash,
        "generated_at_utc": snapshot["generated_at_utc"],
        "record_count": len(records),
        "records": records,
    }


def _normalize_name(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "").casefold()


def build_lookup_from_compact_index(compact_index: dict[str, Any]) -> dict[str, Any]:
    """Build the exact lookup contract consumed by the canonical resolver."""
    lookup: dict[str, Any] = {
        "snapshot": {"snapshot_id": compact_index["source_snapshot_id"]},
        "by_canonical": {},
        "by_isin": {},
        "by_code": {},
        "by_name": {},
    }
    for record in compact_index.get("records") or []:
        canonical_id = record["canonical_target_id"]
        identity = record.get("identity") or {}
        market = (record.get("classification") or {}).get("market")
        lookup["by_canonical"][canonical_id] = record
        isin = identity.get("isin")
        if isin:
            lookup["by_isin"].setdefault(isin.upper(), []).append(record)
        code = identity.get("security_code")
        if code:
            lookup["by_code"].setdefault((market, code), []).append(record)
            lookup["by_code"].setdefault((None, code), []).append(record)
        for key in ("security_name_zh", "security_name_en"):
            normalized = _normalize_name(identity.get(key))
            if normalized:
                lookup["by_name"].setdefault(normalized, []).append(record)
    return lookup


def build_compact_manifest(
    compact_index: dict[str, Any],
    compact_index_sha256: str,
    coverage: dict[str, int],
) -> dict[str, Any]:
    return {
        "manifest_schema_version": COMPACT_MANIFEST_SCHEMA_VERSION,
        "compact_index_schema_version": COMPACT_INDEX_SCHEMA_VERSION,
        "index_id": compact_index["index_id"],
        "source_bundle_id": compact_index["source_bundle_id"],
        "source_snapshot_id": compact_index["source_snapshot_id"],
        "source_snapshot_artifact": compact_index["source_snapshot_artifact"],
        "source_snapshot_sha256": compact_index["source_snapshot_sha256"],
        "source_skill_contract_hash": compact_index["source_skill_contract_hash"],
        "compact_index_sha256": compact_index_sha256,
        "compact_index_schema_sha256": sha256_file(COMPACT_INDEX_SCHEMA_PATH),
        "compact_manifest_schema_sha256": sha256_file(COMPACT_MANIFEST_SCHEMA_PATH),
        "compact_index_path": (
            "data/security_master/runtime_identity_indexes/"
            f"{compact_index['index_id']}/index.json"
        ),
        "record_count": compact_index["record_count"],
        "coverage": coverage,
        "generated_at_utc": compact_index["generated_at_utc"],
        "validation_status": "PASSED",
        "producer_version": PRODUCER_VERSION,
        "artifact_persisted_in_git": False,
        "reproduction_semantics": "REQUIRES_ORIGINAL_SEALED_01B_BUNDLE",
    }


def materialize_compact_artifacts(
    snapshot: dict[str, Any],
    snapshot_sha256: str,
    output_dir: Path,
    *,
    source_bundle_id: str = AUTHORIZED_BUNDLE_ID,
    source_skill_contract_hash: str = AUTHORIZED_SKILL_CONTRACT_HASH,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    index = build_compact_index(
        snapshot,
        snapshot_sha256,
        source_bundle_id=source_bundle_id,
        source_skill_contract_hash=source_skill_contract_hash,
    )
    index_path = output_dir / "index.json"
    manifest_path = output_dir / "manifest.json"
    write_json_file(index_path, index)
    manifest = build_compact_manifest(index, sha256_file(index_path), compute_coverage(snapshot))
    write_json_file(manifest_path, manifest)
    return index_path, manifest_path, index, manifest


def build_runtime_immutable_seal(
    compact_index: dict[str, Any],
    compact_manifest: dict[str, Any],
    *,
    index_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Build the reviewed authority binding for one rotatable runtime candidate."""
    coverage = compact_manifest["coverage"]
    return {
        "schema_version": "m8r_06_01c1b_immutable_candidate_seal.v1",
        "source_bundle_id": compact_index["source_bundle_id"],
        "source_snapshot_id": compact_index["source_snapshot_id"],
        "source_snapshot_sha256": compact_index["source_snapshot_sha256"],
        "source_skill_contract_hash": compact_index["source_skill_contract_hash"],
        "compact_index_id": compact_index["index_id"],
        "compact_index_sha256": sha256_file(index_path),
        "compact_manifest_sha256": sha256_file(manifest_path),
        "compact_index_schema_sha256": sha256_file(COMPACT_INDEX_SCHEMA_PATH),
        "compact_manifest_schema_sha256": sha256_file(COMPACT_MANIFEST_SCHEMA_PATH),
        "record_count": compact_index["record_count"],
        "knowledge_universe_count": coverage["knowledge_universe_count"],
        "runtime_eligible_count": coverage["runtime_eligible_count"],
        "quarantined_count": coverage["quarantined_count"],
        "artifact_persisted_in_git": False,
        "reproduction_semantics": "REQUIRES_ORIGINAL_SEALED_01B_BUNDLE",
        "fresh_reprobe_equivalence": False,
    }


def authorized_lineage(
    candidate_id: str = AUTHORIZED_BUNDLE_ID,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    snapshot, seal, snapshot_sha256 = verify_bundle_integrity(
        candidate_id, repo_root=repo_root
    )
    return {
        "source_bundle_id": seal["bundle_id"],
        "source_snapshot_id": snapshot["snapshot_id"],
        "source_snapshot_artifact": SOURCE_SNAPSHOT_ARTIFACT,
        "source_snapshot_sha256": snapshot_sha256,
        "source_skill_contract_hash": seal["skill_contract_hash"],
    }


def _validate_schema(value: dict[str, Any], path: Path, code: str) -> None:
    schema = load_json_file(path, error_code="invalid_compact_schema_json")
    try:
        jsonschema.Draft202012Validator(schema).validate(value)
    except jsonschema.ValidationError:
        _fail(code)


def load_and_validate_compact_artifacts(
    index_path: Path,
    manifest_path: Path,
    *,
    expected_lineage: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not index_path.is_file():
        _fail("missing_index")
    if not manifest_path.is_file():
        _fail("missing_manifest")
    index = load_json_file(index_path, error_code="invalid_index_json")
    manifest = load_json_file(manifest_path, error_code="invalid_manifest_json")

    if index.get("schema_version") != COMPACT_INDEX_SCHEMA_VERSION:
        _fail("wrong_index_schema_version")
    if manifest.get("manifest_schema_version") != COMPACT_MANIFEST_SCHEMA_VERSION:
        _fail("wrong_manifest_schema_version")
    if manifest.get("compact_index_schema_version") != COMPACT_INDEX_SCHEMA_VERSION:
        _fail("wrong_manifest_index_schema_version")
    _validate_schema(index, COMPACT_INDEX_SCHEMA_PATH, "bad_index_schema")
    _validate_schema(manifest, COMPACT_MANIFEST_SCHEMA_PATH, "bad_manifest_schema")

    if index.get("index_id") != manifest.get("index_id"):
        _fail("index_id_mismatch")
    for field in (
        "source_bundle_id",
        "source_snapshot_id",
        "source_snapshot_artifact",
        "source_snapshot_sha256",
        "source_skill_contract_hash",
    ):
        if index.get(field) != manifest.get(field):
            _fail(f"{field}_mismatch")

    lineage = expected_lineage or authorized_lineage()
    for field, expected in lineage.items():
        if index.get(field) != expected or manifest.get(field) != expected:
            _fail(f"authorized_{field}_mismatch")

    records = index.get("records") or []
    if index.get("record_count") != len(records):
        _fail("index_record_count_mismatch")
    if manifest.get("record_count") != len(records):
        _fail("manifest_record_count_mismatch")
    if (manifest.get("coverage") or {}).get("knowledge_universe_count") != len(records):
        _fail("coverage_record_count_mismatch")
    canonical_ids = [record.get("canonical_target_id") for record in records]
    if len(canonical_ids) != len(set(canonical_ids)):
        _fail("duplicate_canonical_target_id")

    if manifest.get("compact_index_sha256") != sha256_file(index_path):
        _fail("compact_index_sha256_mismatch")
    if manifest.get("compact_index_schema_sha256") != sha256_file(COMPACT_INDEX_SCHEMA_PATH):
        _fail("compact_index_schema_sha256_mismatch")
    if manifest.get("compact_manifest_schema_sha256") != sha256_file(COMPACT_MANIFEST_SCHEMA_PATH):
        _fail("compact_manifest_schema_sha256_mismatch")
    return index, manifest


def _normalized_query(name: str) -> str:
    transformed = name.swapcase() if any(character.isascii() for character in name) else name
    return " ".join(transformed)


def build_resolver_query_corpus(snapshot: dict[str, Any]) -> tuple[list[tuple[str, str | None]], dict[str, Any]]:
    """Build a deterministic, exhaustive governed resolver corpus."""
    records = snapshot.get("records") or []
    cases: set[tuple[str, str | None]] = set()
    isin_groups: dict[str, list[dict[str, Any]]] = {}
    code_groups: dict[str, list[dict[str, Any]]] = {}
    normalized_names: dict[str, str] = {}
    for record in records:
        cases.add((record["canonical_target_id"], None))
        identity = record.get("identity") or {}
        isin = identity.get("isin")
        if isin:
            isin_groups.setdefault(isin.upper(), []).append(record)
        code = identity.get("security_code")
        if code:
            code_groups.setdefault(code, []).append(record)
        for key in ("security_name_zh", "security_name_en"):
            name = identity.get(key)
            normalized = _normalize_name(name)
            if normalized and normalized not in normalized_names:
                normalized_names[normalized] = name

    isin_collision_groups = {key: group for key, group in isin_groups.items() if len(group) > 1}
    code_collision_groups = {key: group for key, group in code_groups.items() if len(group) > 1}
    cases.update((key, None) for key in isin_collision_groups)
    cases.update((key, None) for key in code_collision_groups)
    cases.update((_normalized_query(name), None) for name in normalized_names.values())

    for market in ("TWSE", "TPEX"):
        market_records = sorted(
            (record for record in records if (record.get("classification") or {}).get("market") == market),
            key=lambda record: record["canonical_target_id"],
        )
        opposite = "TPEX" if market == "TWSE" else "TWSE"
        cases.update((record["canonical_target_id"], opposite) for record in market_records[:8])

    cases.add(("2330", "TWSE"))
    tpex_records = sorted(
        (record for record in records if record["canonical_target_id"].startswith("TPEX:")),
        key=lambda record: record["canonical_target_id"],
    )
    if tpex_records:
        cases.add(((tpex_records[0].get("identity") or {})["security_code"], "TPEX"))
    cases.update({("NOT_FOUND_C1B_SENTINEL", None), ("ZZ0000000000", None)})

    quarantined = [
        record
        for record in records
        if (record.get("classification") or {}).get("classification_status") in QUARANTINE
    ]
    non_runtime = [
        record
        for record in records
        if (record.get("execution_eligibility") or {}).get("status") == "blocked"
    ]
    fixture_records = [
        record
        for record in records
        if (record.get("observation") or {}).get("status") == "fixture_observation_only"
    ]
    metrics = {
        "all_canonical_ids_tested": True,
        "canonical_id_query_count": len(records),
        "isin_collision_groups_tested": len(isin_collision_groups),
        "code_collision_groups_tested": len(code_collision_groups),
        "collision_groups_tested": len(isin_collision_groups) + len(code_collision_groups),
        "quarantine_cases_tested": len(quarantined),
        "non_runtime_eligible_cases_tested": len(non_runtime),
        "normalized_name_queries_tested": len(normalized_names),
        "fixture_observation_only_cases_tested": len(fixture_records),
        "market_mismatch_cases_tested": min(8, sum(1 for r in records if r["canonical_target_id"].startswith("TWSE:")))
        + min(8, sum(1 for r in records if r["canonical_target_id"].startswith("TPEX:"))),
        "2330_twse_tested": ("2330", "TWSE") in cases,
        "real_tpex_cases_tested": 1 if tpex_records else 0,
    }
    ordered = sorted(cases, key=lambda item: (item[0], item[1] or ""))
    metrics["resolver_tested_query_count"] = len(ordered)
    return ordered, metrics


def run_resolver_equivalence(
    snapshot: dict[str, Any], compact_index: dict[str, Any]
) -> dict[str, Any]:
    full_lookup = build_verified_security_master_lookup(snapshot)
    compact_lookup = build_lookup_from_compact_index(compact_index)
    cases, metrics = build_resolver_query_corpus(snapshot)
    for query, market_context in cases:
        full = resolve_verified_security_identity(
            query,
            full_lookup,
            market_context=market_context,
        )
        compact = resolve_verified_security_identity(
            query,
            compact_lookup,
            market_context=market_context,
        )
        if full != compact:
            raise AssertionError(
                json.dumps(
                    {
                        "query": query,
                        "market_context": market_context,
                        "full": full,
                        "compact": compact,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
    metrics["resolver_semantic_equivalence"] = "PASS"
    return metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--verify-resolver", action="store_true")
    args = parser.parse_args(argv)
    try:
        candidate_id = validate_candidate_id(args.candidate_id)
        snapshot, seal, snapshot_sha256 = verify_bundle_integrity(candidate_id)
        output_dir = runtime_index_dir(REPO_ROOT, candidate_id)
        index_path, manifest_path, index, _ = materialize_compact_artifacts(
            snapshot,
            snapshot_sha256,
            output_dir,
            source_bundle_id=seal["bundle_id"],
            source_skill_contract_hash=seal["skill_contract_hash"],
        )
        index, manifest = load_and_validate_compact_artifacts(
            index_path,
            manifest_path,
            expected_lineage=authorized_lineage(candidate_id),
        )
        runtime_seal = build_runtime_immutable_seal(
            index, manifest, index_path=index_path, manifest_path=manifest_path
        )
        write_json_file(runtime_immutable_seal_path(REPO_ROOT, candidate_id), runtime_seal)
        print(f"index_sha256={sha256_file(index_path)}")
        print(f"manifest_sha256={sha256_file(manifest_path)}")
        print(f"coverage={json.dumps(compute_coverage(snapshot), sort_keys=True)}")
        if args.verify_resolver:
            print(json.dumps(run_resolver_equivalence(snapshot, index), sort_keys=True))
    except (CompactArtifactValidationError, AssertionError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
