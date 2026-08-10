from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest
from fastapi.testclient import TestClient

from scripts.m8r_03d_f1_security_master_snapshot_adapter import (
    resolve_verified_security_identity,
)
from scripts.m8r_06_01c1b_compact_runtime_identity_index import (
    COMPACT_INDEX_SCHEMA_PATH,
    COMPACT_MANIFEST_SCHEMA_PATH,
    materialize_compact_artifacts,
    sha256_file,
    write_json_file,
)
from scripts.m8r_06_01c2_mode_a_security_master_loader import (
    ACTIVATION_CONSISTENCY_MODEL,
    POINTER_PATH,
    POINTER_SCHEMA_PATH,
    POINTER_CHANGE_REQUIRES_RESTART,
    ModeASecurityMasterUnavailable,
    get_production_mode_a_security_master,
    load_mode_a_security_master,
    reset_production_mode_a_security_master_for_tests,
)
from scripts import m8r_06_01c2_mode_a_security_master_loader as c2_loader
from server.main import app
from server.services import unified_mode_a

SYNTHETIC_SNAPSHOT_SHA = "a" * 64
SYNTHETIC_SKILL_HASH = "b" * 64
SYNTHETIC_BUNDLE_ID = "synthetic-c2-bundle"


@pytest.fixture(autouse=True)
def _reset_process_runtime() -> None:
    reset_production_mode_a_security_master_for_tests()
    yield
    reset_production_mode_a_security_master_for_tests()


def _record(
    canonical_id: str,
    *,
    name_zh: str,
    name_en: str,
    isin: str,
    eligibility: str = "allowed",
    eligibility_reasons: list[str] | None = None,
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
            "classification_status": "confirmed_official_single_lane",
            "reason_codes": ["SYNTHETIC_C2"],
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
            "reason_codes": eligibility_reasons or [],
        },
        "caveats": [f"caveat-{suffix}"],
    }


def _snapshot(*, include_fixture: bool = False) -> dict:
    records = [
        _record(
            "TWSE:2330",
            name_zh="台積電",
            name_en="Taiwan Semiconductor",
            isin="TW0002330008",
        ),
        _record(
            "TPEX:6488",
            name_zh="環球晶",
            name_en="Global Wafers",
            isin="TW0006488000",
        ),
        _record(
            "TWSE:9999",
            name_zh="不支援證券",
            name_en="Unsupported Security",
            isin="TW0009999004",
            eligibility="blocked",
            eligibility_reasons=["unsupported_instrument_type"],
        ),
    ]
    if include_fixture:
        records.append(
            _record(
                "TWSE:8888",
                name_zh="夾具證券",
                name_en="Fixture Security",
                isin="TW0008888000",
                eligibility="blocked",
                eligibility_reasons=["fixture_observation_only"],
                observation_status="fixture_observation_only",
            )
        )
    return {
        "snapshot_id": "synthetic-c2-snapshot",
        "generated_at_utc": "2026-08-07T05:35:40+00:00",
        "records": records,
    }


def _build_repo(tmp_path: Path, *, include_fixture: bool = False) -> dict:
    snapshot = _snapshot(include_fixture=include_fixture)
    index_id = SYNTHETIC_BUNDLE_ID
    artifact_dir = (
        tmp_path
        / "data"
        / "security_master"
        / "runtime_identity_indexes"
        / index_id
    )
    index_path, manifest_path, index, manifest = materialize_compact_artifacts(
        snapshot,
        SYNTHETIC_SNAPSHOT_SHA,
        artifact_dir,
        source_bundle_id=index_id,
        source_skill_contract_hash=SYNTHETIC_SKILL_HASH,
    )
    runtime_count = sum(
        r["execution_eligibility"]["status"] in {"allowed", "allowed_with_caveat"}
        for r in snapshot["records"]
    )
    relative_index = index_path.relative_to(tmp_path).as_posix()
    relative_manifest = manifest_path.relative_to(tmp_path).as_posix()
    relative_seal = (
        "docs/reviews/m8r06-01c1b-runtime-index-manifest/immutable_manifest.json"
    )
    seal = {
        "schema_version": "m8r_06_01c1b_immutable_candidate_seal.v1",
        "source_bundle_id": index_id,
        "source_snapshot_id": snapshot["snapshot_id"],
        "source_snapshot_sha256": SYNTHETIC_SNAPSHOT_SHA,
        "source_skill_contract_hash": SYNTHETIC_SKILL_HASH,
        "compact_index_id": index_id,
        "compact_index_sha256": sha256_file(index_path),
        "compact_manifest_sha256": sha256_file(manifest_path),
        "compact_index_schema_sha256": sha256_file(COMPACT_INDEX_SCHEMA_PATH),
        "compact_manifest_schema_sha256": sha256_file(COMPACT_MANIFEST_SCHEMA_PATH),
        "record_count": len(snapshot["records"]),
        "knowledge_universe_count": len(snapshot["records"]),
        "runtime_eligible_count": runtime_count,
        "quarantined_count": 0,
        "artifact_persisted_in_git": False,
        "reproduction_semantics": "REQUIRES_ORIGINAL_SEALED_01B_BUNDLE",
        "fresh_reprobe_equivalence": False,
    }
    seal_path = tmp_path / relative_seal
    write_json_file(seal_path, seal)
    pointer = {
        "schema_version": "m8r_06_mode_a_security_master_pointer.v1",
        "selection_id": "synthetic-c2-selection",
        "artifact_type": "compact_runtime_identity_index",
        "index_id": index_id,
        "index_path": relative_index,
        "manifest_path": relative_manifest,
        "immutable_seal_path": relative_seal,
        "source_bundle_id": index_id,
        "source_snapshot_id": snapshot["snapshot_id"],
        "source_snapshot_sha256": SYNTHETIC_SNAPSHOT_SHA,
        "source_skill_contract_hash": SYNTHETIC_SKILL_HASH,
        "compact_index_sha256": seal["compact_index_sha256"],
        "compact_manifest_sha256": seal["compact_manifest_sha256"],
        "compact_index_schema_sha256": seal["compact_index_schema_sha256"],
        "compact_manifest_schema_sha256": seal["compact_manifest_schema_sha256"],
        "record_count": seal["record_count"],
        "knowledge_universe_count": seal["knowledge_universe_count"],
        "runtime_eligible_count": seal["runtime_eligible_count"],
        "quarantined_count": seal["quarantined_count"],
        "activation_mode": "governed_local_candidate",
        "artifact_persisted_in_git": False,
    }
    pointer_path = tmp_path / "config" / "m8r_06_mode_a_security_master_pointer.json"
    write_json_file(pointer_path, pointer)
    return {
        "root": tmp_path,
        "pointer": pointer,
        "pointer_path": pointer_path,
        "seal": seal,
        "seal_path": seal_path,
        "index": index,
        "index_path": index_path,
        "manifest": manifest,
        "manifest_path": manifest_path,
    }


def _request(targets: list[dict], *, request_id: str = "c2-test") -> dict:
    return {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": request_id,
        "execution_mode": "preview",
        "targets": targets,
        "data_needs": [{"type": "identity", "priority": "required"}],
    }


def _reason(exc: pytest.ExceptionInfo[ModeASecurityMasterUnavailable]) -> str:
    return exc.value.reason_code


def test_committed_pointer_schema_and_selection_contract() -> None:
    pointer = json.loads(POINTER_PATH.read_text(encoding="utf-8"))
    schema = json.loads(POINTER_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(pointer)
    assert pointer["artifact_type"] == "compact_runtime_identity_index"
    assert pointer["activation_mode"] == "governed_local_candidate"
    assert pointer["artifact_persisted_in_git"] is False


def test_runtime_loader_builds_canonical_lookup(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    runtime = load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert set(runtime.lookup) == {"snapshot", "by_canonical", "by_isin", "by_code", "by_name"}
    result = resolve_verified_security_identity(
        "2330", runtime.lookup, market_context="TWSE"
    )
    assert result["selected"]["canonical_target_id"] == "TWSE:2330"
    assert runtime.validation["valid"] is True


def test_process_provider_activates_once_and_keeps_immutable_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _build_repo(tmp_path)
    strict_loader = load_mode_a_security_master
    calls = 0

    def counted(pointer_path):
        nonlocal calls
        calls += 1
        return strict_loader(pointer_path, repo_root=tmp_path)

    monkeypatch.setattr(c2_loader, "load_mode_a_security_master", counted)
    first = get_production_mode_a_security_master(repo["pointer_path"])
    second = get_production_mode_a_security_master(tmp_path / "different-pointer.json")
    assert first is second
    assert calls == 1
    assert ACTIVATION_CONSISTENCY_MODEL == "PROCESS_LIFETIME_IMMUTABLE_SELECTION"
    assert POINTER_CHANGE_REQUIRES_RESTART is True


def test_failed_activation_is_not_cached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _build_repo(tmp_path)
    strict_loader = load_mode_a_security_master
    with pytest.raises(ModeASecurityMasterUnavailable):
        get_production_mode_a_security_master(tmp_path / "missing.json")
    monkeypatch.setattr(
        c2_loader,
        "load_mode_a_security_master",
        lambda pointer_path: strict_loader(pointer_path, repo_root=tmp_path),
    )
    runtime = get_production_mode_a_security_master(repo["pointer_path"])
    assert runtime.validation["valid"] is True


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda p: p.update(schema_version="unsupported.v9"), "unsupported_pointer_schema_version"),
        (lambda p: p.update(index_path="../outside/index.json"), "index_path_not_authorized"),
        (lambda p: p.update(index_path="C:/outside/index.json"), "pointer_schema_invalid"),
        (lambda p: p.update(index_path="data/security_master/runtime_identity_indexes/other/index.json"), "pointer_index_path_mismatch"),
        (lambda p: p.update(immutable_seal_path="docs/reviews/other.json"), "pointer_immutable_seal_path_mismatch"),
    ],
)
def test_pointer_contract_and_path_fail_closed(
    tmp_path: Path, mutation, expected: str
) -> None:
    repo = _build_repo(tmp_path)
    pointer = copy.deepcopy(repo["pointer"])
    mutation(pointer)
    write_json_file(repo["pointer_path"], pointer)
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert _reason(exc) == expected


def test_missing_and_malformed_pointer_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "config" / "missing.json"
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(missing, repo_root=tmp_path)
    assert _reason(exc) == "pointer_missing"
    missing.parent.mkdir(parents=True)
    missing.write_text("{bad", encoding="utf-8")
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(missing, repo_root=tmp_path)
    assert _reason(exc) == "pointer_malformed"


@pytest.mark.parametrize(
    ("component", "expected"),
    [
        ("index_path", "candidate_index_missing"),
        ("manifest_path", "candidate_manifest_missing"),
        ("seal_path", "immutable_seal_missing"),
    ],
)
def test_missing_candidate_dependencies_fail_closed(
    tmp_path: Path, component: str, expected: str
) -> None:
    repo = _build_repo(tmp_path)
    repo[component].unlink()
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert _reason(exc) == expected


def test_pointer_seal_binding_and_seal_tamper_fail_closed(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    seal = copy.deepcopy(repo["seal"])
    seal["runtime_eligible_count"] += 1
    write_json_file(repo["seal_path"], seal)
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert _reason(exc) == "pointer_seal_runtime_eligible_count_mismatch"


def test_pointer_tamper_fail_closed(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    pointer = copy.deepcopy(repo["pointer"])
    pointer["compact_index_sha256"] = "f" * 64
    write_json_file(repo["pointer_path"], pointer)
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert _reason(exc) == "pointer_seal_compact_index_sha256_mismatch"


def test_manifest_tamper_fails_closed(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    repo["manifest_path"].write_bytes(repo["manifest_path"].read_bytes() + b" ")
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert _reason(exc) == "pointer_manifest_sha256_mismatch"


def test_index_tamper_fails_closed(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    repo["index_path"].write_bytes(repo["index_path"].read_bytes() + b" ")
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert _reason(exc) == "pointer_index_sha256_mismatch"


def test_coverage_mismatch_fails_closed(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    pointer = copy.deepcopy(repo["pointer"])
    seal = copy.deepcopy(repo["seal"])
    pointer["runtime_eligible_count"] += 1
    seal["runtime_eligible_count"] += 1
    write_json_file(repo["pointer_path"], pointer)
    write_json_file(repo["seal_path"], seal)
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert _reason(exc) == "pointer_coverage_runtime_eligible_count_mismatch"


def test_fixture_compact_candidate_rejected_in_production(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path, include_fixture=True)
    with pytest.raises(ModeASecurityMasterUnavailable) as exc:
        load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    assert _reason(exc) == "fixture_compact_candidate_rejected_in_production"


def test_mode_a_functional_semantics_with_governed_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _build_repo(tmp_path)
    runtime = load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    monkeypatch.setattr(
        unified_mode_a, "get_production_mode_a_security_master", lambda _: runtime
    )
    targets = [
        {"input": "2330", "market_hint": "TWSE"},
        {"input": "6488", "market_hint": "TPEX"},
        {"input": "NO_SUCH_SECURITY"},
        {"input": "6488", "market_hint": "TWSE"},
        {"input": "TWSE:9999"},
        {"input": "TWSE:2330"},
    ]
    result = unified_mode_a.validate_mode_a_request(_request(targets))
    statuses = [row["resolution_status"] for row in result["target_results"]]
    assert statuses == [
        "resolved",
        "resolved",
        "not_found",
        "market_mismatch",
        "unsupported_security_type",
        "duplicate",
    ]


def test_invalid_schema_and_target_limit_preserve_f3_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _build_repo(tmp_path)
    runtime = load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    monkeypatch.setattr(
        unified_mode_a, "get_production_mode_a_security_master", lambda _: runtime
    )
    invalid = _request([{"input": "2330"}])
    invalid["unexpected"] = True
    result = unified_mode_a.validate_mode_a_request(invalid)
    assert result["request_schema_status"] == "invalid"
    too_many = _request([{"input": str(i)} for i in range(51)])
    result = unified_mode_a.validate_mode_a_request(too_many)
    assert any(i["code"] == "TARGET_LIMIT_EXCEEDED" for i in result["blocking_issues"])


def test_api_transitions_from_409_to_governed_200(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = TestClient(app)
    request = _request([{"input": "2330", "market_hint": "TWSE"}], request_id="api-c2")
    monkeypatch.setattr(unified_mode_a, "PRODUCTION_POINTER_PATH", tmp_path / "missing.json")
    response = client.post("/api/unified/validate-request", json={"request": request})
    assert response.status_code == 409
    assert response.json()["error"] == "canonical_security_master_unavailable"

    repo = _build_repo(tmp_path / "valid")
    runtime = load_mode_a_security_master(repo["pointer_path"], repo_root=repo["root"])
    monkeypatch.setattr(
        unified_mode_a, "get_production_mode_a_security_master", lambda _: runtime
    )
    response = client.post("/api/unified/validate-request", json={"request": request})
    assert response.status_code == 200
    assert response.json()["target_results"][0]["resolution_status"] == "resolved"


def test_api_reuses_one_successful_process_activation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _build_repo(tmp_path)
    runtime = load_mode_a_security_master(repo["pointer_path"], repo_root=tmp_path)
    calls = 0

    def counted_strict_loader(_):
        nonlocal calls
        calls += 1
        return runtime

    monkeypatch.setattr(c2_loader, "load_mode_a_security_master", counted_strict_loader)
    client = TestClient(app)
    payload = {
        "request": _request(
            [{"input": "2330", "market_hint": "TWSE"}],
            request_id="api-process-cache",
        )
    }
    first = client.post("/api/unified/validate-request", json=payload)
    second = client.post("/api/unified/validate-request", json=payload)
    assert first.status_code == second.status_code == 200
    assert calls == 1


@pytest.mark.skipif(
    not (
        POINTER_PATH.parents[1]
        / "data/security_master/runtime_identity_indexes/m8r06-01b-20260807T053540Z/index.json"
    ).is_file(),
    reason="accepted local C1B compact candidate is not materialized",
)
def test_sealed_candidate_production_activation(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_mode_a_security_master()
    monkeypatch.setattr(
        unified_mode_a, "get_production_mode_a_security_master", lambda _: runtime
    )
    allowed_tpex = next(
        record
        for record in runtime.index["records"]
        if record["classification"]["market"] == "TPEX"
        and record["execution_eligibility"]["status"] in {"allowed", "allowed_with_caveat"}
    )
    blocked = next(
        record
        for record in runtime.index["records"]
        if record["execution_eligibility"]["status"] == "blocked"
    )
    tpex_code = allowed_tpex["identity"]["security_code"]
    twse_codes = {
        record["identity"]["security_code"]
        for record in runtime.index["records"]
        if record["classification"]["market"] == "TWSE"
    }
    mismatch = next(
        record
        for record in runtime.index["records"]
        if record["classification"]["market"] == "TPEX"
        and record["identity"]["security_code"] not in twse_codes
    )
    result = unified_mode_a.validate_mode_a_request(
        _request(
            [
                {"input": "2330", "market_hint": "TWSE"},
                {"input": tpex_code, "market_hint": "TPEX"},
                {"input": "C2_NOT_FOUND_SENTINEL"},
                {"input": mismatch["identity"]["security_code"], "market_hint": "TWSE"},
                {"input": blocked["canonical_target_id"]},
            ],
            request_id="sealed-c2-activation",
        )
    )
    statuses = [row["resolution_status"] for row in result["target_results"]]
    assert statuses[0] == "resolved"
    assert statuses[1] == "resolved"
    assert statuses[2] == "not_found"
    assert statuses[3] == "market_mismatch"
    assert statuses[4] in {"unsupported_security_type", "quarantined"}


@pytest.mark.skipif(
    not (
        POINTER_PATH.parents[1]
        / "data/security_master/runtime_identity_indexes/m8r06-01b-20260807T053540Z/index.json"
    ).is_file(),
    reason="accepted local C1B compact candidate is not materialized",
)
def test_real_sealed_pointer_http_e2e_without_runtime_monkeypatch() -> None:
    reset_production_mode_a_security_master_for_tests()
    response = TestClient(app).post(
        "/api/unified/validate-request",
        json={
            "request": _request(
                [{"input": "2330", "market_hint": "TWSE"}],
                request_id="sealed-real-http-c2",
            )
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["validation_status"] == "valid"
    assert result["target_results"][0]["resolution_status"] == "resolved"
    assert (
        result["target_results"][0]["canonical_identity"]["canonical_target_id"]
        == "TWSE:2330"
    )
