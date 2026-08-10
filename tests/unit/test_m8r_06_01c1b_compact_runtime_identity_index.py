from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.m8r_03d_f1_security_master_snapshot_adapter import (
    build_verified_security_master_lookup,
    resolve_verified_security_identity,
)
from scripts.m8r_06_01c1b_compact_runtime_identity_index import (
    AUTHORIZED_BUNDLE_ID,
    AUTHORIZED_SKILL_CONTRACT_HASH,
    BUNDLE_DIR,
    COMPACT_INDEX_SCHEMA_VERSION,
    COMPACT_MANIFEST_SCHEMA_VERSION,
    CompactArtifactValidationError,
    build_lookup_from_compact_index,
    compute_coverage,
    load_and_validate_compact_artifacts,
    materialize_compact_artifacts,
    run_resolver_equivalence,
    sha256_file,
    verify_bundle_integrity,
    write_json_file,
)

SYNTHETIC_SNAPSHOT_SHA = "a" * 64
SYNTHETIC_SKILL_HASH = "b" * 64


def _record(
    canonical_id: str,
    *,
    name_zh: str,
    name_en: str | None,
    isin: str,
    eligibility: str = "allowed",
    classification_status: str = "confirmed_official_single_lane",
    observation_status: str = "observed_in_latest_verified_snapshot",
) -> dict:
    market, code = canonical_id.split(":", 1)
    suffix = canonical_id.replace(":", "-").lower()
    return {
        "canonical_target_id": canonical_id,
        "record_id": f"record-{suffix}",
        "record_hash": ("1" if market == "TWSE" else "2") * 64,
        "identity": {
            "security_code": code,
            "security_name_zh": name_zh,
            "security_name_en": name_en,
            "isin": isin,
            "cfi": "ESVUFR",
        },
        "classification": {
            "asset_class": "equity",
            "instrument_family": "company_share",
            "instrument_type": "common_share",
            "market": market,
            "board": "main",
            "listed_common_stock_core_flag": True,
            "classification_status": classification_status,
            "reason_codes": ["SYNTHETIC"],
            "conflicts": [],
        },
        "observation": {
            "status": observation_status,
            "observed_at": "2026-08-07T05:35:40+00:00",
            "source_updated_date": "2026-08-07",
        },
        "lifecycle": {
            "state": "active_with_current_observation_basis",
            "resolution_status": "partial",
            "as_of": "2026-08-07",
            "basis_event_ids": [],
            "events": [],
        },
        "execution_eligibility": {
            "status": eligibility,
            "reason_codes": [] if eligibility == "allowed" else ["SYNTHETIC_BLOCK"],
        },
        "caveats": [f"caveat-{suffix}"],
    }


@pytest.fixture
def synthetic_snapshot() -> dict:
    return {
        "snapshot_id": "synthetic-security-master-v1",
        "generated_at_utc": "2026-08-07T05:35:40+00:00",
        "records": [
            _record(
                "TWSE:2330",
                name_zh="台積 電",
                name_en="Taiwan Semiconductor",
                isin="TW0002330008",
            ),
            _record(
                "TPEX:2330",
                name_zh="測試櫃買",
                name_en="Synthetic OTC",
                isin="TW0002330008",
                eligibility="blocked",
                classification_status="quarantine_conflict",
            ),
            _record(
                "TPEX:6488",
                name_zh="環球晶",
                name_en="Global Wafers",
                isin="TW0006488000",
            ),
            _record(
                "TWSE:9999",
                name_zh="測試夾具",
                name_en="Fixture Only",
                isin="TW0009999004",
                eligibility="blocked",
                observation_status="fixture_observation_only",
            ),
        ],
    }


@pytest.fixture
def synthetic_lineage(synthetic_snapshot: dict) -> dict:
    return {
        "source_bundle_id": "synthetic-bundle",
        "source_snapshot_id": synthetic_snapshot["snapshot_id"],
        "source_snapshot_artifact": "dryrun_snapshot.json",
        "source_snapshot_sha256": SYNTHETIC_SNAPSHOT_SHA,
        "source_skill_contract_hash": SYNTHETIC_SKILL_HASH,
    }


def _materialize(tmp_path: Path, synthetic_snapshot: dict):
    return materialize_compact_artifacts(
        synthetic_snapshot,
        SYNTHETIC_SNAPSHOT_SHA,
        tmp_path,
        source_bundle_id="synthetic-bundle",
        source_skill_contract_hash=SYNTHETIC_SKILL_HASH,
    )


def test_materialization_schema_hash_binding_and_determinism(
    tmp_path: Path,
    synthetic_snapshot: dict,
    synthetic_lineage: dict,
) -> None:
    first = _materialize(tmp_path / "run1", synthetic_snapshot)
    second = _materialize(tmp_path / "run2", synthetic_snapshot)
    assert first[0].read_bytes() == second[0].read_bytes()
    assert first[1].read_bytes() == second[1].read_bytes()
    assert sha256_file(first[0]) == sha256_file(second[0])
    assert sha256_file(first[1]) == sha256_file(second[1])
    index, manifest = load_and_validate_compact_artifacts(
        first[0], first[1], expected_lineage=synthetic_lineage
    )
    assert index["source_snapshot_id"] == synthetic_snapshot["snapshot_id"]
    assert index["source_snapshot_artifact"] == "dryrun_snapshot.json"
    assert manifest["generated_at_utc"] == synthetic_snapshot["generated_at_utc"]
    assert "compact_index_sha256" not in index


def test_lookup_uses_canonical_resolver_contract_and_exact_semantics(
    tmp_path: Path,
    synthetic_snapshot: dict,
) -> None:
    _, _, compact, _ = _materialize(tmp_path, synthetic_snapshot)
    lookup = build_lookup_from_compact_index(compact)
    assert set(lookup) == {"snapshot", "by_canonical", "by_isin", "by_code", "by_name"}
    assert lookup["snapshot"] == {"snapshot_id": synthetic_snapshot["snapshot_id"]}
    assert len(lookup["by_code"][(None, "2330")]) == 2
    assert len(lookup["by_isin"]["TW0002330008"]) == 2

    full_lookup = build_verified_security_master_lookup(synthetic_snapshot)
    queries = [
        ("TWSE:2330", None),
        ("2330", "TWSE"),
        ("2330", None),
        ("TW0002330008", None),
        ("台 積 電", None),
        ("tAiWaN sEmIcOnDuCtOr", None),
        ("TWSE:9999", None),
        ("NOT_FOUND", None),
    ]
    for query, market in queries:
        full = resolve_verified_security_identity(query, full_lookup, market_context=market)
        compact_result = resolve_verified_security_identity(query, lookup, market_context=market)
        assert compact_result == full


def test_coverage_is_derived_from_canonical_statuses(synthetic_snapshot: dict) -> None:
    assert compute_coverage(synthetic_snapshot) == {
        "knowledge_universe_count": 4,
        "runtime_eligible_count": 2,
        "quarantined_count": 1,
    }


def _rewrite_and_rebind(
    index_path: Path,
    manifest_path: Path,
    index: dict,
    manifest: dict,
) -> None:
    write_json_file(index_path, index)
    manifest["compact_index_sha256"] = sha256_file(index_path)
    write_json_file(manifest_path, manifest)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("invalid_index_json", "invalid_index_json"),
        ("invalid_manifest_json", "invalid_manifest_json"),
        ("bad_index_schema", "bad_index_schema"),
        ("bad_manifest_schema", "bad_manifest_schema"),
        ("wrong_index_schema_version", "wrong_index_schema_version"),
        ("wrong_manifest_schema_version", "wrong_manifest_schema_version"),
        ("index_id_mismatch", "index_id_mismatch"),
        ("source_bundle_id_mismatch", "authorized_source_bundle_id_mismatch"),
        ("source_snapshot_id_mismatch", "authorized_source_snapshot_id_mismatch"),
        ("source_snapshot_sha256_mismatch", "authorized_source_snapshot_sha256_mismatch"),
        ("source_skill_contract_hash_mismatch", "authorized_source_skill_contract_hash_mismatch"),
        ("record_count_mismatch", "index_record_count_mismatch"),
        ("duplicate_canonical_target_id", "duplicate_canonical_target_id"),
        ("compact_index_sha256_mismatch", "compact_index_sha256_mismatch"),
        ("index_schema_sha256_mismatch", "compact_index_schema_sha256_mismatch"),
        ("manifest_schema_sha256_mismatch", "compact_manifest_schema_sha256_mismatch"),
        ("invalid_compact_record", "bad_index_schema"),
    ],
)
def test_strict_validator_rejects_invalid_or_forged_artifacts(
    tmp_path: Path,
    synthetic_snapshot: dict,
    synthetic_lineage: dict,
    mutation: str,
    expected_code: str,
) -> None:
    index_path, manifest_path, index, manifest = _materialize(tmp_path, synthetic_snapshot)
    index = copy.deepcopy(index)
    manifest = copy.deepcopy(manifest)

    if mutation == "invalid_index_json":
        index_path.write_text("{", encoding="utf-8")
    elif mutation == "invalid_manifest_json":
        manifest_path.write_text("{", encoding="utf-8")
    elif mutation == "bad_index_schema":
        index.pop("records")
        _rewrite_and_rebind(index_path, manifest_path, index, manifest)
    elif mutation == "bad_manifest_schema":
        manifest.pop("coverage")
        write_json_file(manifest_path, manifest)
    elif mutation == "wrong_index_schema_version":
        index["schema_version"] = "m8r_06_01c1b_compact_identity_index.v2"
        _rewrite_and_rebind(index_path, manifest_path, index, manifest)
    elif mutation == "wrong_manifest_schema_version":
        manifest["manifest_schema_version"] = "m8r_06_01c1b_compact_index_manifest.v2"
        write_json_file(manifest_path, manifest)
    elif mutation == "index_id_mismatch":
        index["index_id"] = "forged-index"
        _rewrite_and_rebind(index_path, manifest_path, index, manifest)
    elif mutation in {
        "source_bundle_id_mismatch",
        "source_snapshot_id_mismatch",
        "source_snapshot_sha256_mismatch",
        "source_skill_contract_hash_mismatch",
    }:
        field = mutation.removesuffix("_mismatch")
        forged = "f" * 64 if field.endswith("sha256") or field.endswith("hash") else "forged"
        index[field] = forged
        manifest[field] = forged
        _rewrite_and_rebind(index_path, manifest_path, index, manifest)
    elif mutation == "record_count_mismatch":
        index["record_count"] += 1
        _rewrite_and_rebind(index_path, manifest_path, index, manifest)
    elif mutation == "duplicate_canonical_target_id":
        index["records"].append(copy.deepcopy(index["records"][0]))
        index["record_count"] += 1
        manifest["record_count"] += 1
        manifest["coverage"]["knowledge_universe_count"] += 1
        _rewrite_and_rebind(index_path, manifest_path, index, manifest)
    elif mutation == "compact_index_sha256_mismatch":
        manifest["compact_index_sha256"] = "f" * 64
        write_json_file(manifest_path, manifest)
    elif mutation == "index_schema_sha256_mismatch":
        manifest["compact_index_schema_sha256"] = "f" * 64
        write_json_file(manifest_path, manifest)
    elif mutation == "manifest_schema_sha256_mismatch":
        manifest["compact_manifest_schema_sha256"] = "f" * 64
        write_json_file(manifest_path, manifest)
    elif mutation == "invalid_compact_record":
        index["records"][0].pop("caveats")
        _rewrite_and_rebind(index_path, manifest_path, index, manifest)
    else:  # pragma: no cover
        raise AssertionError(mutation)

    with pytest.raises(CompactArtifactValidationError, match=f"^{expected_code}$"):
        load_and_validate_compact_artifacts(
            index_path,
            manifest_path,
            expected_lineage=synthetic_lineage,
        )


@pytest.mark.parametrize(
    ("missing", "expected_code"),
    [("index", "missing_index"), ("manifest", "missing_manifest")],
)
def test_strict_validator_rejects_missing_artifacts(
    tmp_path: Path,
    synthetic_snapshot: dict,
    synthetic_lineage: dict,
    missing: str,
    expected_code: str,
) -> None:
    index_path, manifest_path, _, _ = _materialize(tmp_path, synthetic_snapshot)
    (index_path if missing == "index" else manifest_path).unlink()
    with pytest.raises(CompactArtifactValidationError, match=f"^{expected_code}$"):
        load_and_validate_compact_artifacts(
            index_path,
            manifest_path,
            expected_lineage=synthetic_lineage,
        )


@pytest.mark.milestone
@pytest.mark.skipif(
    not (BUNDLE_DIR / "dryrun_snapshot.json").is_file(),
    reason="requires original sealed 01B bundle; normal CI uses synthetic fixtures",
)
def test_sealed_bundle_acceptance_and_exhaustive_resolver_equivalence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot, seal, snapshot_sha256 = verify_bundle_integrity()
    run1 = materialize_compact_artifacts(snapshot, snapshot_sha256, tmp_path / "run1")
    run2 = materialize_compact_artifacts(snapshot, snapshot_sha256, tmp_path / "run2")
    assert run1[0].read_bytes() == run2[0].read_bytes()
    assert run1[1].read_bytes() == run2[1].read_bytes()
    load_and_validate_compact_artifacts(run1[0], run1[1])
    metrics = run_resolver_equivalence(snapshot, run1[2])
    assert seal["bundle_id"] == AUTHORIZED_BUNDLE_ID
    assert snapshot_sha256 == "a851aa664727a02df87e88b086d956467ce9348aa8a9d9ef9dfc33cc415dc2b8"
    assert len(snapshot["records"]) == 43070
    assert metrics["resolver_semantic_equivalence"] == "PASS"
    assert metrics["all_canonical_ids_tested"] is True
    assert metrics["canonical_id_query_count"] == 43070
    assert metrics["non_runtime_eligible_cases_tested"] == 40746
    assert metrics["2330_twse_tested"] is True
    summary = {
        **metrics,
        "coverage": compute_coverage(snapshot),
        "index_hashes": [sha256_file(run1[0]), sha256_file(run2[0])],
        "manifest_hashes": [sha256_file(run1[1]), sha256_file(run2[1])],
    }
    with capsys.disabled():
        print("SEALED_C1B_ACCEPTANCE=" + json.dumps(summary, sort_keys=True))
