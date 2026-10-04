"""Bounded retry policy for future I3-A3 live acceptance.

A single Owner authorization may cover multiple dispatches, but only to the
same reviewed endpoint and only for explicitly transient transport failures.
"""
from __future__ import annotations

MAX_HTTP_DISPATCHES_PER_MARKET = 10
MAX_RETRIES_PER_MARKET = MAX_HTTP_DISPATCHES_PER_MARKET - 1
BACKOFF_SECONDS = (1, 2, 4, 8, 10, 10, 10, 10, 10)

RETRYABLE_REASON_CLASSIFICATIONS = frozenset({
    "connection_reset",
    "timeout",
    "connection_refused",
    "dns_resolution_failed",
    "os_network_error",
})
RETRYABLE_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})
RETRYABLE_ERROR_CODES = frozenset({"content_length_mismatch"})


def retryable_transport_failure(telemetry: dict) -> bool:
    """Return True only for a narrow, transport-level transient allowlist."""
    if telemetry.get("complete_body_received") is True:
        return False
    error_code = telemetry.get("error_code")
    reason = telemetry.get("reason_classification")
    status = telemetry.get("http_status")
    if error_code == "URLError" and reason in RETRYABLE_REASON_CLASSIFICATIONS:
        return True
    if error_code == "http_status_not_200" and status in RETRYABLE_HTTP_STATUS:
        return True
    if error_code in RETRYABLE_ERROR_CODES and telemetry.get("failure_phase") == "response_body_read":
        return True
    return False


def retry_delay_seconds(next_attempt_number: int) -> int:
    """Delay before attempt 2..10; no value exists for an 11th dispatch."""
    if type(next_attempt_number) is not int or not 2 <= next_attempt_number <= MAX_HTTP_DISPATCHES_PER_MARKET:
        raise ValueError("retry_attempt_out_of_bounds")
    return BACKOFF_SECONDS[next_attempt_number - 2]