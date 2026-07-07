from scripts.probe_twse_mis_rich_fields import (
    KNOWN_FORENSIC_FIELDS,
    build_probe_summary,
    classify_mis_value_shape,
    is_mis_placeholder,
    parse_mis_ladder,
    summarize_field_presence,
    summarize_ladder_shapes,
    validate_symbols,
    fetch_twse_mis_rows,
)


def test_parse_mis_ladder_handles_trailing_underscore():
    assert parse_mis_ladder("100.0_99.5_99.0_") == ["100.0", "99.5", "99.0"]


def test_parse_mis_ladder_returns_empty_for_placeholders():
    assert parse_mis_ladder(None) == []
    assert parse_mis_ladder("") == []
    assert parse_mis_ladder("-") == []


def test_classify_mis_value_shape_distinguishes_common_shapes():
    assert classify_mis_value_shape("123") == "integer_string"
    assert classify_mis_value_shape("123.45") == "decimal_string"
    assert classify_mis_value_shape("-123.45") == "negative_numeric_string"
    assert classify_mis_value_shape("") == "empty_string"
    assert classify_mis_value_shape("-") == "dash_placeholder"
    assert classify_mis_value_shape("1_2_3_") == "underscore_ladder"
    assert classify_mis_value_shape("abc") == "text"


def test_is_mis_placeholder_handles_required_values():
    for value in [None, "", "-", "--", "－"]:
        assert is_mis_placeholder(value)
    assert not is_mis_placeholder("0")


def test_build_probe_summary_sets_boundary_flags_and_source():
    summary = build_probe_summary(
        [{"z": "100.0", "y": "99.0", "key": "tse_2330.tw"}],
        [],
        {"symbols_requested": ["tse_2330.tw"], "retrieved_at_utc": "2026-07-07T00:00:00Z"},
    )
    assert summary["schema_version"] == "m7a_twse_mis_rich_field_probe_summary.v1"
    assert summary["source_id"] == "TWSE_MIS"
    assert summary["runtime_behavior_changed"] is False
    assert summary["normalization_changed"] is False
    assert summary["full_market_scan"] is False
    assert summary["polling"] is False
    assert summary["scheduler"] is False
    assert summary["startup_network"] is False
    assert summary["ci_network_required"] is False
    assert summary["raw_payload_committed"] is False


def test_summarize_field_presence_preserves_unknown_fields():
    summary = summarize_field_presence([{"z": "100.0", "unexpected_raw": "kept"}])
    assert "unexpected_raw" in summary
    assert summary["unexpected_raw"]["present_count"] == 1
    assert summary["unexpected_raw"]["candidate_semantic"] == "unknown_semantics_preserve_raw"


def test_ladder_shape_summary_detects_length_mismatch_candidates():
    summary = summarize_ladder_shapes([
        {"b": "100_99_", "g": "10_", "a": "101_102_", "f": "5_6_"},
        {"b": "98_", "g": "1_", "a": "103_", "f": "7_8_"},
    ])
    mismatches = summary["mismatch_candidates"]
    assert {item["side"] for item in mismatches} == {"bid", "ask"}


def test_validate_symbols_rejects_empty_and_excessive_bounds():
    try:
        validate_symbols([], 10)
    except ValueError as exc:
        assert "non-empty" in str(exc)
    else:
        raise AssertionError("empty symbols should fail")

    try:
        validate_symbols(["tse_2330.tw"], 11)
    except ValueError as exc:
        assert "<= 10" in str(exc)
    else:
        raise AssertionError("max-symbols > 10 should fail")


def test_build_probe_summary_includes_new_telemetry_fields():
    summary = build_probe_summary(
        [{"z": "100.0", "y": "99.0", "key": "tse_2330.tw"}],
        [],
        {
            "symbols_requested": ["tse_2330.tw"],
            "retrieved_at_utc": "2026-07-07T00:00:00Z",
            "session_bootstrap_attempts": [
                {"url_family": "https://mis.twse.com.tw/stock/fibest.jsp", "status": "failed", "error_class": "HTTPError", "http_status": 404}
            ],
            "api_attempts": [
                {"strategy": "direct_after_bootstrap_failure", "endpoint_family": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp", "status": "success", "http_status": 200}
            ],
            "successful_strategy": "direct_api_without_session"
        },
    )
    assert summary["session_bootstrap_attempts"] == [
        {"url_family": "https://mis.twse.com.tw/stock/fibest.jsp", "status": "failed", "error_class": "HTTPError", "http_status": 404}
    ]
    assert summary["api_attempts"] == [
        {"strategy": "direct_after_bootstrap_failure", "endpoint_family": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp", "status": "success", "http_status": 200}
    ]
    assert summary["successful_strategy"] == "direct_api_without_session"
    assert summary["request_evidence"]["session_tokens_committed"] is False
    assert summary["request_evidence"]["raw_response_body_committed"] is False


from unittest.mock import MagicMock, patch
import urllib.error

def test_fetch_twse_mis_rows_direct_api_fallback():
    mock_opener = MagicMock()

    def mock_open(req, timeout=10):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "/stock/api/getStockInfo.jsp" in url:
            mock_res = MagicMock()
            mock_res.status = 200
            mock_res.code = 200
            mock_res.read.return_value = b'{"msgArray": [{"z": "100.0", "y": "99.0", "key": "tse_2330.tw"}]}'
            return mock_res
        else:
            fp = MagicMock()
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, fp)

    mock_opener.open = mock_open

    with patch("urllib.request.build_opener", return_value=mock_opener):
        rows, failures, telemetry = fetch_twse_mis_rows(["tse_2330.tw"])

    assert len(rows) == 1
    assert rows[0]["z"] == "100.0"
    assert len(failures) == 0
    assert telemetry["successful_strategy"] == "direct_api_without_session"
    assert len(telemetry["session_bootstrap_attempts"]) == 5
    assert all(a["status"] == "failed" for a in telemetry["session_bootstrap_attempts"])
    assert len(telemetry["api_attempts"]) == 1
    assert telemetry["api_attempts"][0]["status"] == "success"
    assert telemetry["api_attempts"][0]["strategy"] == "direct_after_bootstrap_failure"


def test_fetch_twse_mis_rows_all_failed():
    mock_opener = MagicMock()

    def mock_open(req, timeout=10):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        fp = MagicMock()
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, fp)

    mock_opener.open = mock_open

    with patch("urllib.request.build_opener", return_value=mock_opener):
        rows, failures, telemetry = fetch_twse_mis_rows(["tse_2330.tw"])

    assert len(rows) == 0
    assert len(failures) == 1
    assert failures[0]["stage"] == "request"
    assert telemetry["successful_strategy"] == "none"


def test_known_forensic_fields_include_successful_probe_unknowns():
    assert "m" in KNOWN_FORENSIC_FIELDS
    assert "nu" in KNOWN_FORENSIC_FIELDS
    summary = summarize_field_presence([])
    assert summary["m"]["candidate_semantic"] == "unknown_semantics_preserve_raw"
    assert summary["nu"]["candidate_semantic"] == "unknown_semantics_preserve_raw"
