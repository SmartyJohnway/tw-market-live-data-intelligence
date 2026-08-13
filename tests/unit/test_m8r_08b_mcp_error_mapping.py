from server.unified_mcp.error_mapping import map_internal_error, map_local_service_error
from server.unified_mcp.local_service_client import DEFAULT_SERVICE_URL, LocalServiceClientError, UnifiedLocalServiceClient, validate_loopback_service_url


def test_loopback_url_validation_rejects_every_non_local_shape():
    assert validate_loopback_service_url(DEFAULT_SERVICE_URL) == DEFAULT_SERVICE_URL
    assert validate_loopback_service_url("http://localhost:8123") == "http://localhost:8123"
    assert validate_loopback_service_url("http://[::1]:8123") == "http://[::1]:8123"
    rejected = (
        "http://0.0.0.0:8000", "http://192.168.1.5:8000", "https://127.0.0.1:8000",
        "http://example.test:8000", "http://user:pass@127.0.0.1:8000",
        "http://127.0.0.1:8000/api", "http://127.0.0.1:8000?x=1",
        "http://127.0.0.1:8000#x", "http://127.0.0.1",
    )
    for value in rejected:
        try:
            UnifiedLocalServiceClient(value)
        except LocalServiceClientError as exc:
            assert exc.code == "local_service_url_invalid"
        else:
            raise AssertionError(value)


def test_bounded_upstream_error_preserves_only_governed_fields():
    result = map_local_service_error(LocalServiceClientError(
        "local_service_http_error", status_code=409,
        payload={"error": "mode_c_execution_not_finalized", "trace_id": "trace", "secret": "do-not-leak", "path": "C:/secret"},
    ))
    assert result.isError is True
    assert result.structuredContent == {"http_status": 409, "error": "mode_c_execution_not_finalized", "trace_id": "trace"}
    assert "secret" not in result.content[0].text
    assert "C:/" not in result.content[0].text


def test_adapter_errors_are_opaque_and_do_not_echo_exception_text():
    result = map_local_service_error(LocalServiceClientError("local_service_timeout"))
    assert result.isError is True
    assert result.structuredContent["error"] == "local_service_timeout"
    internal = map_internal_error()
    assert internal.structuredContent["error"] == "mcp_adapter_internal_error"
    assert "trace_id" in internal.structuredContent
