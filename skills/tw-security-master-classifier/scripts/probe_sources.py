#!/usr/bin/env python3
"""Safely probe one allowlisted official source and report transport/schema semantics."""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from common import file_sha256
from isin_parser import classify_payload


MAX_BYTES = 20 * 1024 * 1024
DEFAULT_ERROR_SIGNATURES = ["error", "errors", "rate limit", "maintenance", "temporarily unavailable", "服務暫停", "系統維護"]


class RedirectRejected(Exception):
    pass


class BootstrapRedirectLimitExceeded(Exception):
    code = "BOOTSTRAP_REDIRECT_LIMIT_EXCEEDED"


class BootstrapDispatchBudgetExhausted(Exception):
    code = "BOOTSTRAP_DISPATCH_BUDGET_EXHAUSTED"


class BootstrapDispatchBudget:
    """Shared fail-closed counter for one production Security Master bootstrap."""

    def __init__(self, maximum_total_dispatches: int = 10) -> None:
        if type(maximum_total_dispatches) is not int or maximum_total_dispatches < 1:
            raise ValueError("bootstrap_dispatch_budget_invalid")
        self.maximum_total_dispatches = maximum_total_dispatches
        self.used_dispatches = 0

    @property
    def remaining_dispatches(self) -> int:
        return self.maximum_total_dispatches - self.used_dispatches

    def reserve_before_dispatch(self) -> int:
        if self.used_dispatches >= self.maximum_total_dispatches:
            raise BootstrapDispatchBudgetExhausted(
                "BOOTSTRAP_DISPATCH_BUDGET_EXHAUSTED"
            )
        self.used_dispatches += 1
        return self.used_dispatches


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_url(url: str, allowed_hosts: list[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts or parsed.username or parsed.password:
        raise ValueError("URL must be HTTPS on an allowlisted official host")


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(
        self,
        allowed_hosts: list[str],
        *,
        dispatch_budget: BootstrapDispatchBudget | None = None,
        max_followed_redirects: int | None = None,
    ) -> None:
        super().__init__()
        self.allowed_hosts = allowed_hosts
        self.redirect_count = 0
        self.dispatch_budget = dispatch_budget
        self.max_followed_redirects = max_followed_redirects

    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> urllib.request.Request | None:
        original_method = req.get_method().upper()
        original_data = req.data
        absolute = urljoin(req.full_url, newurl)
        try:
            validate_url(absolute, self.allowed_hosts)
        except ValueError as exc:
            raise RedirectRejected("BOOTSTRAP_REDIRECT_REJECTED") from exc
        if (
            self.max_followed_redirects is not None
            and self.redirect_count >= self.max_followed_redirects
        ):
            raise BootstrapRedirectLimitExceeded(
                "BOOTSTRAP_REDIRECT_LIMIT_EXCEEDED"
            )
        if self.dispatch_budget is not None:
            # urllib dispatches the returned request only after this reservation.
            # Reserve only after checking that urllib will preserve the source
            # request method/body. A 301/302/303 must not turn governed POST into GET.
            redirected = super().redirect_request(req, fp, code, msg, headers, absolute)
            if redirected is None:
                return None
            if redirected.get_method().upper() != original_method or redirected.data != original_data:
                raise RedirectRejected("BOOTSTRAP_REDIRECT_METHOD_CHANGED")
            self.dispatch_budget.reserve_before_dispatch()
            self.redirect_count += 1
            return redirected
        redirected = super().redirect_request(req, fp, code, msg, headers, absolute)
        if redirected is None:
            return None
        if redirected.get_method().upper() != original_method or redirected.data != original_data:
            raise RedirectRejected("BOOTSTRAP_REDIRECT_METHOD_CHANGED")
        self.redirect_count += 1
        return redirected


def find_source_contract(manifest: dict[str, Any], source_id: str | None, url: str) -> dict[str, Any]:
    found: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("id") == source_id or (not source_id and value.get("url") == url):
                found.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(manifest)
    if source_id and not found:
        raise ValueError(f"unknown source id: {source_id}")
    return found[0].get("payload_contract", {}) if found else {}


def assess_json(data: bytes, contract: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"payload_parseable": False, "schema_valid": False, "semantic_data_present": False, "acquisition_status": "schema_drift"}

    expected = contract.get("expected_json_type")
    json_type = "array" if isinstance(payload, list) else "object" if isinstance(payload, dict) else type(payload).__name__
    schema_valid = expected in (None, json_type)
    count = len(payload) if isinstance(payload, list) else 1 if isinstance(payload, dict) else 0
    minimum = int(contract.get("minimum_record_count", 1))
    required_any = contract.get("required_fields_any", [])
    records = payload if isinstance(payload, list) else [payload] if isinstance(payload, dict) else []
    fields_ok = not required_any or any(isinstance(record, dict) and any(field in record for field in required_any) for record in records)
    serialized = json.dumps(payload, ensure_ascii=False).casefold()
    signatures = contract.get("error_signatures", DEFAULT_ERROR_SIGNATURES)
    found = [signature for signature in signatures if signature.casefold() in serialized]
    semantic = schema_valid and count >= minimum and fields_ok and not found
    return {
        "payload_parseable": True,
        "schema_valid": schema_valid and fields_ok,
        "semantic_data_present": semantic,
        "acquisition_status": "data" if semantic else "semantic_error" if found else "schema_drift",
        "json_type": json_type,
        "record_count": count,
        "error_signatures_found": found,
    }


def _base(url: str, observed_at: str) -> dict[str, Any]:
    return {
        "requested_url": url,
        "request_method": "GET",
        "request_content_type": None,
        "final_url": None,
        "redirect_count": 0,
        "observed_at": observed_at,
        "transport_success": False,
        "payload_parseable": False,
        "schema_valid": False,
        "semantic_data_present": False,
    }


def probe(
    url: str,
    allowed_hosts: list[str],
    *,
    contract: dict[str, Any] | None = None,
    timeout: float = 20,
    save_raw: Path | None = None,
    dispatch_budget: BootstrapDispatchBudget | None = None,
    max_followed_redirects: int | None = None,
    method: str = "GET",
    body: bytes | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    validate_url(url, allowed_hosts)
    if (
        not isinstance(method, str)
        or not method.isascii()
        or method != method.upper()
        or method not in {"GET", "POST"}
    ):
        raise ValueError("BOOTSTRAP_METHOD_REJECTED")
    if (method == "GET" and body is not None) or (method == "POST" and not isinstance(body, bytes)):
        raise ValueError("BOOTSTRAP_REQUEST_BODY_INVALID")
    observed_at = datetime.now(timezone.utc).isoformat()
    base = _base(url, observed_at)
    base["request_method"] = method
    base["request_content_type"] = content_type
    handler = SafeRedirectHandler(
        allowed_hosts,
        dispatch_budget=dispatch_budget,
        max_followed_redirects=max_followed_redirects,
    )
    opener = urllib.request.build_opener(handler, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    request_headers = {"User-Agent": "tw-security-master-classifier/1.1 (+official-source-validation)"}
    if content_type is not None:
        request_headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    dispatches_before = dispatch_budget.used_dispatches if dispatch_budget else None
    try:
        if dispatch_budget is not None:
            # Reserve the initial request before opener.open can dispatch it.
            dispatch_budget.reserve_before_dispatch()
        with opener.open(request, timeout=timeout) as response:
            final_url = response.geturl()
            validate_url(final_url, allowed_hosts)
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError(f"payload exceeds {MAX_BYTES} bytes")
            content_type = response.headers.get_content_type()
            status = response.status
    except RedirectRejected as exc:
        return {
            **base,
            "redirect_count": handler.redirect_count,
            "dispatch_reservations": _dispatch_delta(dispatch_budget, dispatches_before),
            "acquisition_status": "redirect_rejected",
            "transport_error_code": "BOOTSTRAP_REDIRECT_REJECTED",
            "error": str(exc),
        }
    except BootstrapRedirectLimitExceeded:
        return {
            **base,
            "redirect_count": handler.redirect_count,
            "dispatch_reservations": _dispatch_delta(dispatch_budget, dispatches_before),
            "acquisition_status": "redirect_limit_exceeded",
            "transport_error_code": "BOOTSTRAP_REDIRECT_LIMIT_EXCEEDED",
        }
    except BootstrapDispatchBudgetExhausted:
        return {
            **base,
            "redirect_count": handler.redirect_count,
            "dispatch_reservations": _dispatch_delta(dispatch_budget, dispatches_before),
            "acquisition_status": "dispatch_budget_exhausted",
            "transport_error_code": "BOOTSTRAP_DISPATCH_BUDGET_EXHAUSTED",
        }
    except urllib.error.HTTPError as exc:
        data = exc.read(256 * 1024)
        result = {
            **base,
            "final_url": exc.geturl(),
            "redirect_count": handler.redirect_count,
            "dispatch_reservations": _dispatch_delta(dispatch_budget, dispatches_before),
            "http_status": exc.code,
            "content_type": exc.headers.get_content_type() if exc.headers else None,
            "acquisition_status": "http_error",
            "raw_payload_sha256": file_sha256(data),
        }
        if 300 <= exc.code < 400:
            location = exc.headers.get("Location") if exc.headers is not None else None
            sanitized = {
                "redirect_location_present": bool(location),
                "redirect_location_scheme": None,
                "redirect_location_host": None,
                "redirect_location_path_or_sanitized_url": None,
                "redirect_location_allowed": False,
                "redirect_followed": False,
                "transport_error_code": "BOOTSTRAP_HTTP_REDIRECT_NOT_FOLLOWED",
            }
            if location:
                target = urljoin(exc.geturl(), location)
                parsed_target = urlparse(target)
                sanitized["redirect_location_scheme"] = parsed_target.scheme.lower() or None
                sanitized["redirect_location_host"] = parsed_target.hostname.lower() if parsed_target.hostname else None
                # Exclude query, fragment, username, and password from durable telemetry.
                sanitized["redirect_location_path_or_sanitized_url"] = parsed_target.path or "/"
                try:
                    validate_url(target, allowed_hosts)
                    sanitized["redirect_location_allowed"] = True
                except (TypeError, ValueError):
                    sanitized["redirect_location_allowed"] = False
            result.update(sanitized)
        return result
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {**base, "redirect_count": handler.redirect_count, "dispatch_reservations": _dispatch_delta(dispatch_budget, dispatches_before), "acquisition_status": "network_error", "error_type": type(exc).__name__}

    if save_raw:
        save_raw.parent.mkdir(parents=True, exist_ok=True)
        save_raw.write_bytes(data)
    common = {
        **base,
        "final_url": final_url,
        "redirect_count": handler.redirect_count,
        "dispatch_reservations": _dispatch_delta(dispatch_budget, dispatches_before),
        "transport_success": True,
        "http_status": status,
        "content_type": content_type,
        "byte_count": len(data),
        "raw_payload_sha256": file_sha256(data),
    }
    if content_type == "application/json" or data.lstrip().startswith((b"{", b"[")):
        return {**common, **assess_json(data, contract or {})}
    text = data.decode("utf-8", errors="replace")
    acquisition = classify_payload(text)
    semantic = acquisition == "data"
    return {**common, "payload_parseable": True, "schema_valid": semantic, "semantic_data_present": semantic, "acquisition_status": acquisition}


def _dispatch_delta(
    dispatch_budget: BootstrapDispatchBudget | None, before: int | None
) -> int | None:
    if dispatch_budget is None or before is None:
        return None
    return dispatch_budget.used_dispatches - before


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-id")
    parser.add_argument("--manifest", type=Path, default=root / "references/source-manifest.json")
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--save-raw", type=Path)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    try:
        contract = find_source_contract(manifest, args.source_id, args.url)
        result = probe(args.url, manifest["allowed_hosts"], contract=contract, timeout=args.timeout, save_raw=args.save_raw)
    except ValueError as exc:
        result = {**_base(args.url, datetime.now(timezone.utc).isoformat()), "acquisition_status": "rejected", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["acquisition_status"] in {"data", "security_block", "schema_drift", "semantic_error", "http_error", "network_error"} else 2


if __name__ == "__main__":
    sys.exit(main())
