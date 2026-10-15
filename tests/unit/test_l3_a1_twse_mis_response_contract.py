from __future__ import annotations

import copy
import json
import socket
import urllib.error
from pathlib import Path

import pytest

from scripts.m5k_common import execute_live_observation


ROOT = Path(__file__).resolve().parents[2]
TWSE_SUCCESS = json.loads((ROOT / "tests/fixtures/market_sources/twse_mis/success.json").read_text(encoding="utf-8"))
MATRIX = json.loads((ROOT / "tests/fixtures/market_sources/twse_mis/normalization_v2_matrix.json").read_text(encoding="utf-8"))
TPEX_ROW = next(case["row"] for case in MATRIX["cases"] if case["name"] == "tpex_stock")


def _watchlist(*targets: tuple[str, str, str]) -> dict:
    return {
        "schema_version": "m5k_watchlist.v1",
        "watchlist_id": "l3-a1-test",
        "categories": [{
            "category_id": "test",
            "label": "test",
            "instruments": [
                {"symbol": symbol, "market": market, "instrument_type": instrument_type,
                 "preferred_sources": ["TWSE_MIS"], "enabled": True}
                for symbol, market, instrument_type in targets
            ],
        }],
    }


class _Response:
    status = 200

    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self.body


def _run(monkeypatch: pytest.MonkeyPatch, response: bytes | dict | Exception, *targets: tuple[str, str, str], allow_individual_fallback: bool = False):
    import scripts.m5k_common as m5k

    body = response if isinstance(response, (bytes, Exception)) else json.dumps(response, ensure_ascii=False).encode("utf-8")
    calls: list[str] = []

    def fake_urlopen(req, **_kwargs):
        calls.append(req.full_url)
        if isinstance(body, Exception):
            raise body
        return _Response(body)

    external: list[str] = []
    original_connect = socket.socket.connect

    def guarded_connect(sock, address):
        host = address[0] if isinstance(address, tuple) and address else address
        if host not in {"127.0.0.1", "::1", "localhost"}:
            external.append(str(host))
            raise AssertionError("external socket use is forbidden in L3-A1 tests")
        return original_connect(sock, address)

    def forbidden_create_connection(*_args, **_kwargs):
        external.append("create_connection")
        raise AssertionError("socket.create_connection is forbidden in L3-A1 tests")

    monkeypatch.setattr(m5k.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", forbidden_create_connection)
    result = execute_live_observation(
        _watchlist(*targets), write_latest=False,
        allow_individual_fallback=allow_individual_fallback,
    )
    assert external == []
    assert len(calls) == 1
    return result


def _one_row(row: dict) -> dict:
    payload = {key: value for key, value in TWSE_SUCCESS.items() if key != "msgArray"}
    payload["msgArray"] = [copy.deepcopy(row)]
    return payload


def _first_twse_row() -> dict:
    return copy.deepcopy(TWSE_SUCCESS["msgArray"][0])


def _failure(result: dict) -> dict:
    assert result["observations"] == []
    assert len(result["failures"]) == 1
    return result["failures"][0]


def test_g01_matching_channel_cannot_override_contradictory_returned_identity(monkeypatch):
    row = _first_twse_row()
    row.update(key="tse_2330.tw_20261015", ch="2330.tw", c="2317", ex="otc", z="1015.0000")
    result = _run(monkeypatch, _one_row(row), ("2330", "twse", "equity"), allow_individual_fallback=True)
    failure = _failure(result)
    assert failure["reason"] == "source_response_identity_conflict"
    assert failure["investigation_summary"]["expected_symbol"] == "2330"
    assert failure["investigation_summary"]["returned"]["c"] == "2317"


@pytest.mark.parametrize(
    "mutation, expected_reason",
    [
        (lambda row: row.update(c="2317"), "source_response_identity_conflict"),
        (lambda row: row.update(key="otc_2330.tw_20261015"), "source_response_identity_conflict"),
        (lambda row: row.update(ex="otc"), "source_response_identity_mismatch"),
        (lambda row: row.update(ch="2317.tw"), "source_response_identity_conflict"),
        (lambda row: row.update(c="2330", ex="tse", ch="2317.tw"), "source_response_identity_conflict"),
        (lambda row: row.update(c="2330", ex="otc", key="tse_2330.tw_20261015"), "source_response_identity_conflict"),
        (lambda row: row.update(key="malformed-key"), "source_response_contract_invalid"),
        (lambda row: row.update(ch="2330"), "source_response_contract_invalid"),
    ],
    ids=["symbol", "key-route", "market", "channel-symbol", "cross-field-symbol", "cross-field-market", "malformed-key", "malformed-channel"],
)
def test_returned_identity_mismatches_fail_closed(monkeypatch, mutation, expected_reason):
    row = _first_twse_row()
    mutation(row)
    failure = _failure(_run(monkeypatch, _one_row(row), ("2330", "twse", "equity")))
    assert failure["reason"] == expected_reason


def test_required_identity_facts_missing_is_contract_failure(monkeypatch):
    row = _first_twse_row()
    row["key"] = "tse_2330.tw_20261015"
    row.pop("ch")
    failure = _failure(_run(monkeypatch, _one_row(row), ("2330", "twse", "equity")))
    assert failure["reason"] == "source_response_contract_invalid"


def test_identity_free_unmatched_row_never_inherits_caller_identity(monkeypatch):
    row = _first_twse_row()
    for field in ("c", "ex", "ch", "key"):
        row.pop(field, None)
    failure = _failure(_run(monkeypatch, _one_row(row), ("2330", "twse", "equity")))
    assert failure["reason"] == "missing_from_source_response:tse_2330.tw"


@pytest.mark.parametrize(
    "error, reason, details",
    [
        (OSError("offline transport failure"), "source_failed:transport", {"detail": "OSError"}),
        (urllib.error.HTTPError("https://mis.invalid", 429, "limited", {}, None), "source_failed:http_status", {"status_code": 429}),
    ],
    ids=["transport", "http-status"],
)
def test_transport_failure_is_not_relabelled_as_missing(monkeypatch, error, reason, details):
    failure = _failure(_run(monkeypatch, error, ("2330", "twse", "equity")))
    assert failure["reason"] == reason
    assert failure["investigation_summary"] == details


def test_coherent_twse_row_preserves_success_and_value(monkeypatch):
    result = _run(monkeypatch, _one_row(_first_twse_row()), ("2330", "twse", "equity"))
    assert len(result["observations"]) == 1
    assert result["observations"][0]["status"] == "ok"
    assert result["observations"][0]["symbol"] == "2330"
    assert result["observations"][0]["market"] == "twse"
    assert result["observations"][0]["value"] == 1015.0


def test_coherent_tpex_otc_row_remains_accepted(monkeypatch):
    result = _run(monkeypatch, _one_row(TPEX_ROW), ("8069", "tpex", "equity"))
    assert len(result["observations"]) == 1
    assert result["observations"][0]["status"] == "ok"
    assert result["observations"][0]["market"] == "tpex"


def test_tpex_request_rejects_tse_returned_exchange(monkeypatch):
    row = copy.deepcopy(TPEX_ROW)
    row["ex"] = "tse"
    failure = _failure(_run(monkeypatch, _one_row(row), ("8069", "tpex", "equity")))
    assert failure["reason"] == "source_response_identity_mismatch"


def test_valid_identity_preserves_reference_only_semantics(monkeypatch):
    row = _first_twse_row()
    row.update(z="-", y="981.0000")
    result = _run(monkeypatch, _one_row(row), ("2330", "twse", "equity"))
    failure = _failure(result)
    assert failure["reason"] == "reference_value_only"
    assert failure["investigation_summary"]["observation"]["price_source_field"] == "y"


def test_valid_identity_preserves_stale_timestamp_semantics(monkeypatch):
    result = _run(monkeypatch, _one_row(_first_twse_row()), ("2330", "twse", "equity"))
    observation = result["observations"][0]
    assert observation["status"] == "ok"
    assert observation["delay_seconds"] is not None
    assert observation["delay_seconds"] > 0


@pytest.mark.parametrize(
    "body, expected_reason",
    [
        (b"\xff\xfe{", "source_response_decode_failed"),
        (b"{not json", "source_response_contract_invalid"),
        (b"[]", "source_response_contract_invalid"),
        (b"{}", "source_response_contract_invalid"),
        (b'{"msgArray":{}}', "source_response_contract_invalid"),
        (b'{"msgArray":[],"rtcode":"0000"}', None),
        (b'{"msgArray":[],"rtCode":"0000"}', None),
        (b'{"msgArray":[]}', "source_response_contract_invalid"),
        (b'{"msgArray":[],"rtcode":"0000","rtCode":"9999"}', "source_response_contract_invalid"),
        (b'{"msgArray":[null],"rtcode":"0000"}', "source_response_contract_invalid"),
        (b'{"msgArray":[],"rtcode":"9999"}', "source_response_contract_invalid"),
        (b'{"msgArray":[],"rtcode":"0000","rtcode":"0000"}', "source_response_contract_invalid"),
    ],
    ids=["invalid-utf8", "invalid-json", "root-array", "missing-envelope", "wrong-array-type", "valid-empty", "rtCode-alias", "missing-rtcode", "conflicting-rtcode-alias", "non-object-row", "provider-failure", "duplicate-json-key"],
)
def test_decode_and_envelope_contract(monkeypatch, body, expected_reason):
    result = _run(monkeypatch, body, ("2330", "twse", "equity"))
    failure = _failure(result)
    if expected_reason is None:
        assert failure["reason"].startswith("missing_from_source_response:")
    else:
        assert failure["reason"] == expected_reason
    encoded = json.dumps(result, ensure_ascii=False)
    assert "raw_payload" not in encoded
    assert "response_sample" not in encoded


@pytest.mark.parametrize("second_row", ["identical", "conflicting"], ids=["identical-duplicate", "conflicting-duplicate"])
def test_duplicate_rows_for_requested_target_fail_closed(monkeypatch, second_row):
    row = _first_twse_row()
    duplicate = copy.deepcopy(row)
    if second_row == "conflicting":
        duplicate["z"] = "999.0000"
    result = _run(monkeypatch, _one_row(row) | {"msgArray": [row, duplicate]}, ("2330", "twse", "equity"))
    assert _failure(result)["reason"] == "source_response_duplicate_ambiguous"


def test_unmatched_extra_row_does_not_bind_to_requested_target(monkeypatch):
    extra = _first_twse_row()
    extra.update(c="2317", ch="2317.tw", key="tse_2317.tw_20261015")
    failure = _failure(_run(monkeypatch, _one_row(extra), ("2330", "twse", "equity")))
    assert failure["reason"] == "missing_from_source_response:tse_2330.tw"


def test_mixed_batch_keeps_valid_target_and_fails_only_incoherent_target(monkeypatch):
    twse = _first_twse_row()
    tpex = copy.deepcopy(TPEX_ROW)
    tpex.update(c="6488", ex="tse", ch="6488.tw", key="otc_6488.tw_20261015")
    response = _one_row(twse) | {"msgArray": [twse, tpex]}
    result = _run(monkeypatch, response, ("2330", "twse", "equity"), ("6488", "tpex", "equity"))
    assert [row["symbol"] for row in result["observations"]] == ["2330"]
    assert [(row["symbol"], row["reason"]) for row in result["failures"]] == [("6488", "source_response_identity_conflict")]


def test_taiex_t00_contract_remains_valid(monkeypatch):
    row = copy.deepcopy(TWSE_SUCCESS["msgArray"][2])
    result = _run(monkeypatch, _one_row(row), ("TAIEX", "twse", "index"))
    assert len(result["observations"]) == 1
    assert result["observations"][0]["symbol"] == "TAIEX"
    assert result["observations"][0]["status"] == "ok"
