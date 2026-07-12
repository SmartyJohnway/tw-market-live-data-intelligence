"""Controlled TAIFEX OpenAPI client: GET-only, allowlisted, no raw retention."""
from __future__ import annotations
import json, urllib.request, urllib.error
from typing import Any
from scripts.m8b_taifex_derivatives_observation import utc_now

BASE_URL = "https://openapi.taifex.com.tw/v1"
ALLOWED_ENDPOINTS = {
    "DailyMarketReportFut", "DailyMarketReportOpt", "FinalSettlementPrice",
    "OpenInterestOfLargeTradersFutures", "OpenInterestOfLargeTradersOptions",
    "PutCallRatio", "BlockTrade",
}

class TaifexOpenApiError(RuntimeError):
    def __init__(self, status: str, metadata: dict):
        super().__init__(status); self.status = status; self.metadata = metadata

def endpoint_url(endpoint: str) -> str:
    if endpoint not in ALLOWED_ENDPOINTS:
        raise TaifexOpenApiError("rejected_invalid_scope", {"reason": "endpoint_not_allowlisted", "endpoint": endpoint})
    return f"{BASE_URL}/{endpoint}"

def fetch_endpoint(endpoint: str, *, timeout: int = 20) -> dict:
    url = endpoint_url(endpoint)
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "tw-market-live-data-intelligence/taifex-openapi-controlled"})
    started = utc_now()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode(); ctype = resp.headers.get("Content-Type", ""); body = resp.read()
    except urllib.error.HTTPError as exc:
        raise TaifexOpenApiError("source_error", {"http_status": exc.code, "url": url, "raw_payload_retained": False}) from exc
    except Exception as exc:
        raise TaifexOpenApiError("source_unavailable", {"error_type": type(exc).__name__, "url": url, "raw_payload_retained": False}) from exc
    try:
        parsed: Any = json.loads(body.decode("utf-8-sig"))
    except Exception as exc:
        raise TaifexOpenApiError("schema_drift", {"http_status": status, "content_type": ctype, "reason": "non_json_body", "raw_payload_retained": False}) from exc
    if not isinstance(parsed, list):
        raise TaifexOpenApiError("schema_drift", {"http_status": status, "content_type": ctype, "top_level_type": type(parsed).__name__, "raw_payload_retained": False})
    return {"http_status": status, "content_type": ctype, "top_level_type": "array", "row_count": len(parsed), "rows": parsed,
            "metadata": {"url": url, "method": "GET", "started_at_utc": started, "completed_at_utc": utc_now(), "raw_payload_retained": False}}
