from __future__ import annotations

import io
import json
import uuid

from server import operational_diagnostics as ops


def test_trace_ids_are_uuid_and_invalid_input_gets_new_trace():
    expected = str(uuid.uuid4())
    assert ops.normalize_trace_id(expected.upper()) == expected
    assert ops.normalize_trace_id("not-a-trace") is None
    trace, token = ops.bind_trace_id("not-a-trace")
    try:
        assert ops.normalize_trace_id(trace) == trace
        assert ops.current_trace_id() == trace
    finally:
        ops.reset_trace_id(token)


def test_event_contract_is_fixed_bounded_and_drops_unknown_fields():
    trace = str(uuid.uuid4())
    event = ops.build_event(
        component="mcp", event_code="mcp.tool.completed", status="ok", trace_id=trace,
        reason_code="x" * 400,
        references={"request_id": "req", "secret": "must-not-appear"},
        metrics={"duration_ms": 12.5, "unknown_metric": 999},
    )
    assert event["trace_id"] == trace
    assert event["request_id"] == "req"
    assert len(event["reason_code"]) == ops.MAX_STRING_CHARS
    assert "secret" not in event and "unknown_metric" not in event["metrics"]
    encoded = ops.serialize_event(event).encode("utf-8")
    assert len(encoded) <= ops.MAX_EVENT_BYTES


def test_event_does_not_accept_payload_environment_or_authorization_bodies():
    event = ops.build_event(
        component="local_service", event_code="http.request.completed", status="ok",
        references={
            "request": "raw", "authorization": "raw", "environment": "raw",
            "credential": "raw", "token": "raw", "raw_evidence": "raw",
        },
    )
    serialized = ops.serialize_event(event)
    for forbidden in ("authorization", "environment", '"request"', "credential", "token", "raw_evidence"):
        assert forbidden not in serialized


def test_oversized_manual_event_is_rejected_deterministically():
    event = {
        "schema_version": ops.EVENT_SCHEMA_VERSION,
        "timestamp_utc": "2026-10-13T00:00:00+00:00",
        "level": "INFO", "component": "test", "event_code": "test.event",
        "trace_id": str(uuid.uuid4()), "status": "ok", "oversized": "x" * 5000,
    }
    try:
        ops.serialize_event(event)
    except ValueError as exc:
        assert str(exc) == "operational_event_too_large"
    else:
        raise AssertionError("oversized event was not rejected")


def test_jsonl_sink_is_ephemeral_bounded_and_fail_open(tmp_path, monkeypatch):
    sink = tmp_path / "operational-events.jsonl"
    event = ops.build_event(component="test", event_code="test.event", status="ok")
    assert ops.emit_jsonl(event, sink) is True
    lines = sink.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["event_code"] == "test.event"

    sink.write_bytes(b"x" * ops.MAX_EVENT_FILE_BYTES)
    assert ops.emit_jsonl(event, sink) is True
    assert sink.stat().st_size < ops.MAX_EVENT_FILE_BYTES

    missing_parent = tmp_path / "missing" / "events.jsonl"
    assert ops.emit_jsonl(event, missing_parent) is False
    assert not missing_parent.parent.exists()

    directory_target = tmp_path / "directory-target"
    directory_target.mkdir()
    assert ops.emit_jsonl(event, directory_target) is False


def test_stderr_event_is_one_line_and_failure_is_contained():
    stream = io.StringIO()
    event = ops.build_event(component="mcp", event_code="mcp.tool.completed", status="ok")
    assert ops.emit_stderr(event, stream) is True
    output = stream.getvalue()
    assert output.count("\n") == 1
    assert json.loads(output)["component"] == "mcp"

    class Broken:
        def write(self, _value):
            raise OSError("synthetic")
        def flush(self):
            raise AssertionError("unreachable")

    assert ops.emit_stderr(event, Broken()) is False
