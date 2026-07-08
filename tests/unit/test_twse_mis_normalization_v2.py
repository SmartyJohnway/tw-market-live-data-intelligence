from datetime import datetime, timedelta, timezone

import pytest

from scripts import probe_twse_mis
from scripts.probe_twse_mis import _parse_ladder, _safe_float, normalize_twse_mis_row


@pytest.fixture
def retrieved_at():
    return datetime(2024, 6, 21, 5, 30, 5, tzinfo=timezone.utc)


def normal_row(**overrides):
    row = {
        "c": "2330", "ex": "tse", "n": "台積電", "ch": "2330.tw",
        "z": "1015.0000", "y": "981.0000", "o": "1025.0000", "h": "1025.0000", "l": "1000.0000",
        "v": "30141", "tv": "1468", "a": "1020.0000_1025.0000_", "f": "2816_4021_",
        "b": "1015.0000_1010.0000_", "g": "40_183_", "u": "1079.0000", "w": "884.0000",
        "d": "20240621", "t": "13:30:00", "tlong": "1718951400000",
    }
    row.update(overrides)
    return row


def test_safe_numeric_parsing_zero_dash_empty_and_malformed():
    flags = []
    assert _safe_float("1,234.5", flags, "price") == 1234.5
    assert _safe_float("0", flags, "price") == 0.0
    assert _safe_float("-", flags, "price") is None
    assert _safe_float("", flags, "price") is None
    assert _safe_float("abc", flags, "price") is None
    assert "malformed_price" in flags


def test_bid_ladder_and_ask_ladder_parsing():
    flags = []
    bid_prices, bid_volumes = _parse_ladder("10.5_10.4_", "100_200_", flags, "bid")
    ask_prices, ask_volumes = _parse_ladder("10.6_10.7_", "110_220_", flags, "ask")
    assert bid_prices == [10.5, 10.4]
    assert bid_volumes == [100, 200]
    assert ask_prices == [10.6, 10.7]
    assert ask_volumes == [110, 220]
    assert flags == []


def test_normal_stock_row_contains_v2_contract(retrieved_at):
    normalized = normalize_twse_mis_row(normal_row(), retrieved_at)
    assert normalized["source_id"] == "twse_mis"
    assert normalized["source_authority"] == "unofficial_frontend_source"
    assert normalized["symbol"] == "2330"
    assert normalized["exchange"] == "tse"
    assert normalized["instrument_type"] == "stock_like"
    assert normalized["price"] == 1015.0
    assert normalized["volume"] == 30141
    assert normalized["bid_ladder"][0] == {"level": 1, "price": 1015.0, "volume": 40}
    assert normalized["ask_ladder"][0] == {"level": 1, "price": 1020.0, "volume": 2816}
    assert normalized["normalization_version"] == "twse_mis_snapshot_v2_draft"
    assert "data_quality_flags" in normalized
    assert "source_risk_flags" in normalized
    assert "unofficial_source_risk" in normalized["source_risk_flags"]
    assert normalized["normalization_status"] == "ok"


def test_tpex_row(retrieved_at):
    normalized = normalize_twse_mis_row(normal_row(c="8069", ex="otc", n="元太", ch="8069.tw"), retrieved_at)
    assert normalized["exchange"] == "otc"
    assert normalized["instrument_type"] == "stock_like"


def test_index_row_no_fake_bid_ask(retrieved_at):
    normalized = normalize_twse_mis_row(normal_row(c="t00", ch="t00.tw", n="發行量加權股價指數", a="-", b="-", f="-", g="-", u="-", w="-"), retrieved_at)
    assert normalized["instrument_type"] == "index"
    assert normalized["bid_ladder"] == []
    assert normalized["ask_ladder"] == []
    assert "missing_bid_ask" not in normalized["data_quality_flags"]


def test_missing_price_flags_partial(retrieved_at):
    normalized = normalize_twse_mis_row(normal_row(z="-"), retrieved_at)
    assert normalized["price"] is None
    assert "missing_price" in normalized["data_quality_flags"]
    assert normalized["normalization_status"] == "partial"


def test_malformed_bid_ask_flags_not_exception(retrieved_at):
    normalized = normalize_twse_mis_row(normal_row(a="bad_0.0000_", f="x_2_", b="10_11_", g="1_"), retrieved_at)
    assert "malformed_ask_price_level" in normalized["data_quality_flags"]
    assert "invalid_ask_price_level" in normalized["data_quality_flags"]
    assert "mismatched_bid_ladder_length" in normalized["data_quality_flags"]
    assert normalized["normalization_status"] == "partial"


def test_stale_and_delayed_timestamp_classification(retrieved_at):
    stale = normalize_twse_mis_row(normal_row(tlong=str(int((retrieved_at - timedelta(hours=1)).timestamp() * 1000))), retrieved_at)
    delayed = normalize_twse_mis_row(normal_row(tlong=str(int((retrieved_at - timedelta(minutes=10)).timestamp() * 1000))), retrieved_at)
    assert stale["freshness_status"] == "stale"
    assert stale["delay_status"] == "stale"
    assert "stale_source_timestamp" in stale["data_quality_flags"]
    assert delayed["freshness_status"] == "delayed"
    assert delayed["delay_status"] == "delayed_candidate"


def test_zero_dash_empty_strings_row(retrieved_at):
    normalized = normalize_twse_mis_row(normal_row(z="0", o="", h="-", l="--", a="0.0000__", f="0__"), retrieved_at)
    assert normalized["price"] == 0.0
    assert normalized["open"] is None
    assert normalized["high"] is None
    assert normalized["low"] is None
    assert "invalid_ask_price_level" in normalized["data_quality_flags"]


def test_source_time_unavailable(retrieved_at):
    normalized = normalize_twse_mis_row(normal_row(t="-", tlong="-"), retrieved_at)
    assert normalized["source_timestamp"] is None
    assert normalized["staleness_seconds"] is None
    assert "source_time_unavailable" in normalized["data_quality_flags"]


def test_malformed_and_partial_rows_return_structured_errors(retrieved_at):
    malformed = normalize_twse_mis_row(None, retrieved_at)
    partial = normalize_twse_mis_row({"z": "abc"}, retrieved_at)
    assert malformed["normalization_status"] == "invalid"
    assert "raw_row_not_object" in malformed["errors"]
    assert partial["normalization_status"] == "invalid"
    assert "missing_critical_symbol" in partial["errors"]
    assert "missing_critical_exchange" in partial["errors"]
    assert "malformed_price" in partial["data_quality_flags"]


def test_no_official_realtime_claim_in_risk_flags(retrieved_at):
    normalized = normalize_twse_mis_row(normal_row(), retrieved_at)
    assert "not_official_realtime_api" in normalized["source_risk_flags"]
    assert normalized["freshness_status"] in {"live_candidate", "delayed", "stale", "unknown"}


class _FakeResponse:
    status_code = 200

    def __init__(self, payload=None):
        self._payload = payload or {}

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self.headers = {}
        self._payload = payload
        self.urls = []

    def get(self, url, timeout):
        self.urls.append(url)
        if url.endswith("index.jsp"):
            return _FakeResponse({})
        return _FakeResponse(self._payload)


def _assert_probe_envelope_first_row_freshness(monkeypatch, freshness_status, delay_status, staleness_seconds):
    payload = {
        "msgArray": [{"c": "2330", "ex": "tse"}],
        "queryTime": {"sysTime": "13:30:00"},
        "userDelay": 5000,
        "cachedAlive": 15024,
        "rtcode": "0000",
        "rtmessage": "OK",
        "exKey": "msgArray",
        "referer": "",
    }

    monkeypatch.setattr(probe_twse_mis.requests, "Session", lambda: _FakeSession(payload))

    def fake_normalize(row, retrieved_at_utc_dt, top_level_telemetry=None):
        return {
            "symbol": row["c"],
            "exchange": row["ex"],
            "freshness_status": freshness_status,
            "delay_status": delay_status,
            "staleness_seconds": staleness_seconds,
            "normalization_version": "twse_mis_snapshot_v2_draft",
            "data_quality_flags": [],
            "source_risk_flags": ["unofficial_source_risk", "not_official_realtime_api"],
        }

    monkeypatch.setattr(probe_twse_mis, "normalize_twse_mis_row", fake_normalize)
    envelope = probe_twse_mis.probe(symbols=["tse_2330.tw"])
    assert envelope["freshness_status"] == freshness_status
    assert envelope["delay_status"] == delay_status
    assert envelope["staleness_seconds"] == staleness_seconds


def test_probe_envelope_uses_first_row_stale_freshness_without_network(monkeypatch):
    _assert_probe_envelope_first_row_freshness(monkeypatch, "stale", "stale", 3600)


def test_probe_envelope_uses_first_row_delayed_freshness_without_network(monkeypatch):
    _assert_probe_envelope_first_row_freshness(monkeypatch, "delayed", "delayed_candidate", 600)


def test_probe_envelope_uses_first_row_live_candidate_freshness_without_network(monkeypatch):
    _assert_probe_envelope_first_row_freshness(monkeypatch, "live_candidate", "not_delayed_candidate", 5)


def _load_static_matrix_fixture():
    import json
    from pathlib import Path

    fixture_path = Path(__file__).parents[1] / "fixtures" / "market_sources" / "twse_mis" / "normalization_v2_matrix.json"
    with fixture_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.mark.not_network
@pytest.mark.parametrize("case", _load_static_matrix_fixture()["cases"], ids=lambda case: case["name"])
def test_twse_mis_normalization_v2_static_fixture_matrix(case):
    retrieved_at = datetime.fromisoformat(_load_static_matrix_fixture()["retrieved_at_utc"].replace("Z", "+00:00"))

    normalized = normalize_twse_mis_row(case["row"], retrieved_at)
    expected = case["expect"]

    assert normalized["normalization_status"] == expected["normalization_status"]
    assert normalized["instrument_type"] == expected["instrument_type"]
    assert normalized["freshness_status"] == expected["freshness_status"]
    assert normalized["delay_status"] == expected["delay_status"]
    assert normalized["normalization_version"] == "twse_mis_snapshot_v2_draft"
    assert "unofficial_source_risk" in normalized["source_risk_flags"]
    assert "not_official_realtime_api" in normalized["source_risk_flags"]

    for flag in expected["data_quality_flags"]:
        assert flag in normalized["data_quality_flags"]

    for key, expected_value in expected.items():
        if key in {
            "normalization_status",
            "instrument_type",
            "freshness_status",
            "delay_status",
            "data_quality_flags",
        }:
            continue
        assert normalized[key] == expected_value
