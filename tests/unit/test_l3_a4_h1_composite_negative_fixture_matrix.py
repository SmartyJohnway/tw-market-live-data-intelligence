from __future__ import annotations

import copy
import json
import socket
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
from scripts.m8r_06_03_production_adapter import production_operation_adapter
from server.services import phase_h_h1_tpex_composite as h1


ROOT = Path(__file__).resolve().parents[2]
TARGET = {
    "canonical_target_id": "TPEX:6488",
    "market": "TPEX",
    "security_code": "6488",
}
EXECUTOR = "phase_h_h1_tpex_composite_executor"
OBSERVED = "2026-10-15T02:03:04Z"
FIXTURE_ROWS = json.loads(
    (ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8")
)


def _cmode_row(**overrides):
    row = {
        "Date": "1151007",
        "SecuritiesCompanyCode": "6488",
        "CompanyName": "Fixture TPEx",
        "AlteredTrading": "",
        "PeriodicTrading": "",
        "ManagedStock": "",
        "MatchingFrequency": "",
        "SuspensionOfTrading": "Ｙ",
        " FinancialAnnouncements": "",
    }
    row.update(overrides)
    return row


def _rows():
    return {
        h1.SOURCES[0]["source_id"]: copy.deepcopy(FIXTURE_ROWS["tpex_attention"]),
        h1.SOURCES[1]["source_id"]: copy.deepcopy(FIXTURE_ROWS["tpex_disposition"]),
        h1.SOURCES[2]["source_id"]: [_cmode_row()],
    }


def _response(source, rows=None, **overrides):
    raw = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    value = {
        "raw_bytes": raw,
        "status": 200,
        "content_type": "application/json; charset=utf-8",
        "effective_url": source["endpoint"],
        "retrieved_at": OBSERVED,
        "tls_policy": "fixture-no-network",
        "redirect_count": 0,
    }
    value.update(overrides)
    return value


def _request():
    return {
        "operation_id": "umeop-op-v1-00000000000000000000",
        "execution_request_id": "umereq-v1-00000000000000000000",
        "execution_request_hash": "0" * 64,
        "executor_id": EXECUTOR,
        "capability_id": "trading_status_context",
        "market": "TPEX",
        "approved_security_identifiers": ["TPEX:6488"],
        "approved_security_types": ["equity"],
        "network_authorized": True,
        "timeout_seconds": 15,
    }


def _provider_for(rows=None, failures=None, overrides=None):
    rows = rows or _rows()
    failures = failures or {}
    overrides = overrides or {}
    calls = []

    def provide(source):
        source_id = source["source_id"]
        calls.append(source_id)
        failure = failures.get(source_id)
        if failure is not None:
            raise failure
        return _response(source, rows[source_id], **overrides.get(source_id, {}))

    return provide, calls


def _run(tmp_path, provider, *, response_log=None):
    return h1.execute_composite_operation(
        _request(),
        DispatchRuntimeContext(str(tmp_path), "execute-approved"),
        target=TARGET,
        executor_id=EXECUTOR,
        response_provider=provider,
        response_log=response_log,
    )


@pytest.fixture(autouse=True)
def _deny_external_network(monkeypatch):
    def denied(*_args, **_kwargs):
        pytest.fail("external network access attempted in L3-A4 fixture test")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(urllib.request, "urlopen", denied)


def _component_evidence(root: Path, result: dict, index: int) -> dict:
    artifact = [item for item in result["evidence_artifacts"] if item["artifact_role"] == "component_evidence"][index]
    return json.loads((root / artifact["relative_path"]).read_text(encoding="utf-8"))


def _component_sidecar(root: Path, result: dict, index: int) -> dict:
    artifact = [item for item in result["evidence_artifacts"] if item["artifact_role"] == "supporting_governance"][index]
    return json.loads((root / artifact["relative_path"]).read_text(encoding="utf-8"))


def test_h1_composite_healthy_baseline_writes_bound_components_sidecars_and_primary(tmp_path):
    provider, calls = _provider_for()
    response_log = []
    result = _run(tmp_path, provider, response_log=response_log)

    assert result["status"] == "succeeded"
    assert result["evidence_contract"] == h1.COMPOSITE_CONTRACT
    assert len(result["evidence_artifacts"]) == 7
    assert calls == [source["source_id"] for source in h1.SOURCES]
    assert [entry["source_id"] for entry in response_log] == calls
    assert all(entry["outcome"] == "succeeded" for entry in response_log)
    assert all("raw_bytes" not in entry and "payload" not in entry for entry in response_log)
    assert all(entry["response_sha256"] and entry["response_bytes"] > 0 for entry in response_log)
    assert all(_component_evidence(tmp_path, result, i)["target"] == TARGET for i in range(3))
    assert all(_component_sidecar(tmp_path, result, i)["canonical_target_id"] == "TPEX:6488" for i in range(3))
    assert all(_component_sidecar(tmp_path, result, i)["attempts"][0]["outcome"] == "succeeded" for i in range(3))


@pytest.mark.parametrize("source_index", [0, 1, 2])
def test_timeout_is_source_local_for_each_fixed_source(tmp_path, source_index):
    source_id = h1.SOURCES[source_index]["source_id"]
    error = TimeoutError("sensitive timeout detail")
    provider, _ = _provider_for(failures={source_id: error})
    log = []
    result = _run(tmp_path, provider, response_log=log)

    assert result["status"] == "succeeded"
    assert log[source_index]["failure_code"] == "source_failed:transport_failure"
    evidence = _component_evidence(tmp_path, result, source_index)
    sidecar = _component_sidecar(tmp_path, result, source_index)
    assert evidence["status"] == "source_failed"
    assert evidence["caveats"] == ["source_failed:transport_failure"]
    assert evidence["source"]["source_contract_id"] == h1.SOURCES[source_index]["source_contract_id"]
    assert evidence["citation_ids"]
    assert sidecar["attempts"][0]["failure_code"] == "source_failed:transport_failure"
    assert sidecar["attempts"][0]["outcome"] == "failed"
    assert sidecar["attempts"][0]["coverage_result"] == evidence["status"]
    assert sidecar["attempts"][0]["citation_ids"] == evidence["citation_ids"]
    primary = next(item for item in result["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    composite = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert composite["status"] == "partial"
    assert composite["aggregate_coverage"]["declared_scope_complete"] is False
    assert composite["components"][source_index]["component_status"] == "source_failed"
    assert all(
        component["component_status"] == "partial"
        for index, component in enumerate(composite["components"])
        if index != source_index
    )
    assert log[source_index]["source_id"] == h1.SOURCES[source_index]["source_id"]
    serialized = json.dumps([evidence, sidecar, log], ensure_ascii=False)
    assert "sensitive" not in serialized


@pytest.mark.parametrize("error", [
    ConnectionError("sensitive connection detail"),
    urllib.error.URLError("sensitive URL detail"),
])
def test_connection_and_url_errors_use_bounded_transport_code(tmp_path, error):
    source_id = h1.SOURCES[1]["source_id"]
    provider, _ = _provider_for(failures={source_id: error})
    log = []
    result = _run(tmp_path, provider, response_log=log)
    assert log[1]["failure_code"] == "source_failed:transport_failure"
    assert _component_evidence(tmp_path, result, 1)["status"] == "source_failed"
    assert "sensitive" not in json.dumps(log, ensure_ascii=False)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"status": 503}, "source_failed:http_or_content_type"),
        ({"content_type": "text/html"}, "source_failed:http_or_content_type"),
        ({"effective_url": "https://elsewhere.invalid/"}, "source_failed:redirect_or_effective_url_mismatch"),
        ({"redirect_count": 1}, "source_failed:redirect_or_effective_url_mismatch"),
    ],
)
def test_status_mime_and_endpoint_response_contract_are_fail_closed(tmp_path, overrides, expected):
    source_id = h1.SOURCES[0]["source_id"]
    provider, _ = _provider_for(overrides={source_id: overrides})
    result = _run(tmp_path, provider)
    assert _component_evidence(tmp_path, result, 0)["status"] == "source_failed"
    assert _component_sidecar(tmp_path, result, 0)["attempts"][0]["failure_code"] == expected


@pytest.mark.parametrize(
    ("raw_bytes", "expected"),
    [
        (b"\xff\xfe", "source_failed:strict_json_decode"),
        (b"{not json", "source_failed:strict_json_decode"),
        (b"{}", "source_failed:invalid_top_level_rows"),
        (b'"string"', "source_failed:invalid_top_level_rows"),
        (b"[{},1]", "source_failed:invalid_top_level_rows"),
        (b"[1]", "source_failed:invalid_top_level_rows"),
    ],
)
def test_decode_json_and_root_shape_failures_remain_source_local(tmp_path, raw_bytes, expected):
    source_id = h1.SOURCES[0]["source_id"]
    provider, _ = _provider_for(overrides={source_id: {"raw_bytes": raw_bytes}})
    result = _run(tmp_path, provider)
    assert _component_sidecar(tmp_path, result, 0)["attempts"][0]["failure_code"] == expected


@pytest.mark.parametrize(
    ("source_index", "mutation", "expected"),
    [
        (0, lambda row: row.pop("SecuritiesCompanyCode"), "source_failed:missing_required_field:SecuritiesCompanyCode"),
        (1, lambda row: row.__setitem__("DispositionReasons", 4), "source_failed:invalid_required_field_type:DispositionReasons"),
        (2, lambda row: row.__setitem__("Date", "not-a-date"), "source_failed:date_contract_drift:source_failed:unresolved_source_record_date:Date"),
    ],
)
def test_required_field_type_and_date_contract_drift_fail_source_locally(tmp_path, source_index, mutation, expected):
    rows = _rows()
    source = h1.SOURCES[source_index]
    mutation(rows[source["source_id"]][0])
    provider, _ = _provider_for(rows=rows)
    result = _run(tmp_path, provider)
    assert _component_sidecar(tmp_path, result, source_index)["attempts"][0]["failure_code"] == expected


@pytest.mark.parametrize(
    ("source_index", "field", "value"),
    [
        (0, "ClosePrice", 123),
        (1, "DispositionReasons", None),
        (2, " FinancialAnnouncements", []),
    ],
)
def test_invalid_required_field_type_is_source_local_for_all_sources(tmp_path, source_index, field, value):
    rows = _rows()
    source = h1.SOURCES[source_index]
    rows[source["source_id"]][0][field] = value
    provider, _ = _provider_for(rows=rows)
    result = _run(tmp_path, provider)
    assert _component_sidecar(tmp_path, result, source_index)["attempts"][0]["failure_code"] == f"source_failed:invalid_required_field_type:{field}"


@pytest.mark.parametrize(
    ("source_index", "raw_date"),
    [(0, "2026-02-30"), (1, "not-a-date"), (2, "2026-02-30")],
)
def test_date_contract_drift_is_source_local_for_all_sources(tmp_path, source_index, raw_date):
    rows = _rows()
    source = h1.SOURCES[source_index]
    rows[source["source_id"]][0]["Date"] = raw_date
    provider, _ = _provider_for(rows=rows)
    result = _run(tmp_path, provider)
    assert _component_sidecar(tmp_path, result, source_index)["attempts"][0]["failure_code"].startswith("source_failed:date_contract_drift:")


@pytest.mark.parametrize("source_index", [0, 2])
def test_exact_target_duplicate_rows_are_ambiguous_for_attention_and_cmode(tmp_path, source_index):
    rows = _rows()
    source_id = h1.SOURCES[source_index]["source_id"]
    rows[source_id] = rows[source_id] * 2
    provider, _ = _provider_for(rows=rows)
    result = _run(tmp_path, provider)
    assert _component_sidecar(tmp_path, result, source_index)["attempts"][0]["failure_code"] == "binding_failed:ambiguous_exact_target_rows"
    # The composite wraps this source-local binding rejection in its established
    # failed-source evidence shape while retaining the typed binding code.
    assert _component_evidence(tmp_path, result, source_index)["status"] == "source_failed"


def test_multiple_exact_disposition_rows_are_valid_and_preserved(tmp_path):
    rows = _rows()
    source_id = h1.SOURCES[1]["source_id"]
    rows[source_id].append({**rows[source_id][0], "DispositionReasons": "second retained disposition"})
    provider, _ = _provider_for(rows=rows)
    result = _run(tmp_path, provider)
    evidence = _component_evidence(tmp_path, result, 1)
    assert evidence["status"] == "partial"
    assert len(evidence["items"]) == 2
    assert evidence["items"][1]["official_reason"] == "second retained disposition"


@pytest.mark.parametrize("source_index", [0, 1, 2])
def test_unmatched_target_rows_keep_existing_no_match_semantics(tmp_path, source_index):
    rows = _rows()
    source_id = h1.SOURCES[source_index]["source_id"]
    rows[source_id][0]["SecuritiesCompanyCode"] = "9999"
    provider, _ = _provider_for(rows=rows)
    result = _run(tmp_path, provider)
    evidence = _component_evidence(tmp_path, result, source_index)
    assert evidence["status"] == "partial"
    assert evidence["items"] == []
    if source_index == 2:
        assert evidence["native_observation_count"] == 0
        assert any(caveat.startswith("cmode_exact_no_match:") for caveat in evidence["caveats"])


def test_valid_empty_list_remains_a_non_failure_partial_component(tmp_path):
    rows = _rows()
    rows[h1.SOURCES[0]["source_id"]] = []
    provider, _ = _provider_for(rows=rows)
    result = _run(tmp_path, provider)
    evidence = _component_evidence(tmp_path, result, 0)
    assert evidence["status"] == "partial"
    assert evidence["coverage"]["retrieval_succeeded"] is True
    assert evidence["coverage"]["source_contract_validated"] is True
    assert evidence["items"] == []


def test_response_ceiling_rejects_before_decode(tmp_path, monkeypatch):
    monkeypatch.setattr(h1, "MAX_RESPONSE_BYTES", 32)
    source_id = h1.SOURCES[0]["source_id"]
    provider, _ = _provider_for(overrides={source_id: {"raw_bytes": b"x" * 33}})
    result = _run(tmp_path, provider)
    assert _component_sidecar(tmp_path, result, 0)["attempts"][0]["failure_code"] == "source_failed:response_ceiling_exceeded"


def test_non_bytes_transport_invariant_propagates_instead_of_becoming_source_failure(tmp_path):
    source_id = h1.SOURCES[0]["source_id"]
    provider, _ = _provider_for(overrides={source_id: {"raw_bytes": "{}"}})
    with pytest.raises(TypeError, match="phase_h_composite_response_bytes_invariant_invalid"):
        _run(tmp_path, provider)


@pytest.mark.parametrize("error", [AssertionError("provider invariant"), TypeError("unexpected programming error")])
def test_unexpected_provider_exceptions_propagate_for_dispatch_failure_boundary(tmp_path, error):
    source_id = h1.SOURCES[0]["source_id"]
    provider, _ = _provider_for(failures={source_id: error})
    with pytest.raises(type(error)):
        _run(tmp_path, provider)


def test_unenumerated_normalization_failure_propagates(tmp_path, monkeypatch):
    def unexpected(*_args, **_kwargs):
        raise h1.H1NormalizationError("source_failed:unlisted_new_contract_code")

    monkeypatch.setattr(h1, "normalize_representative_tpex_h1_component", unexpected)
    provider, _ = _provider_for()
    with pytest.raises(h1.H1NormalizationError, match="unlisted_new_contract_code"):
        _run(tmp_path, provider)


def test_unexpected_normalizer_type_error_propagates(tmp_path, monkeypatch):
    def unexpected(*_args, **_kwargs):
        raise TypeError("normalizer implementation defect")

    monkeypatch.setattr(h1, "normalize_representative_tpex_h1_component", unexpected)
    provider, _ = _provider_for()
    with pytest.raises(TypeError, match="normalizer implementation defect"):
        _run(tmp_path, provider)


def test_composite_invariant_failure_propagates_after_component_checks(tmp_path, monkeypatch):
    def invariant_failure(*_args, **_kwargs):
        raise AssertionError("composite invariant failed")

    monkeypatch.setattr(h1, "validate_trading_status_context_composite", invariant_failure)
    provider, _ = _provider_for()
    with pytest.raises(AssertionError, match="composite invariant failed"):
        _run(tmp_path, provider)


def test_all_source_failures_preserve_source_failed_composite_semantics(tmp_path):
    failures = {source["source_id"]: TimeoutError("offline fixture") for source in h1.SOURCES}
    provider, calls = _provider_for(failures=failures)
    result = _run(tmp_path, provider)
    assert result["status"] == "succeeded"
    assert calls == [source["source_id"] for source in h1.SOURCES]
    primary = next(item for item in result["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    composite = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert composite["status"] == "source_failed"
    assert [item["component_status"] for item in composite["components"]] == ["source_failed"] * 3
    assert all(item["attempts"][0]["failure_code"] == "source_failed:transport_failure" for item in [
        _component_sidecar(tmp_path, result, index) for index in range(3)
    ])


def test_production_adapter_dispatches_fixed_composite_route_and_persists_sanitized_artifacts(tmp_path, monkeypatch):
    rows = _rows()
    responses = {
        source["source_id"]: _response(source, rows[source["source_id"]])
        for source in h1.SOURCES
    }
    calls = []

    def fake_get(endpoint, *, timeout_seconds):
        calls.append((endpoint, timeout_seconds))
        source = next(item for item in h1.SOURCES if item["endpoint"] == endpoint)
        return responses[source["source_id"]]

    monkeypatch.setattr(h1, "official_get", fake_get)
    result = production_operation_adapter(
        _request(), DispatchRuntimeContext(str(tmp_path), "execute-approved")
    )
    assert result["status"] == "succeeded"
    assert calls == [(source["endpoint"], 15) for source in h1.SOURCES]
    for artifact in result["evidence_artifacts"]:
        raw = (tmp_path / artifact["relative_path"]).read_bytes()
        assert b"raw_payload" not in raw
        assert b"response_sample" not in raw
        assert b"sensitive timeout detail" not in raw
    response_bodies = [responses[source["source_id"]]["raw_bytes"] for source in h1.SOURCES]
    artifact_bodies = [
        (tmp_path / artifact["relative_path"]).read_bytes()
        for artifact in result["evidence_artifacts"]
    ]
    assert all(body not in artifact for body in response_bodies for artifact in artifact_bodies)


def test_production_adapter_does_not_swallow_provider_assertion(tmp_path, monkeypatch):
    def invariant_failure(*_args, **_kwargs):
        raise AssertionError("synthetic provider invariant")

    monkeypatch.setattr(h1, "official_get", invariant_failure)
    with pytest.raises(AssertionError, match="synthetic provider invariant"):
        production_operation_adapter(
            _request(), DispatchRuntimeContext(str(tmp_path), "execute-approved")
        )
