"""Dormant, bounded TPEx E-Data Shop API transport.

This module performs at most one caller-authorized GET per invocation. It
requires an explicit HTTPS base URL and credentials, keeps response bytes in
memory only, follows no redirects, and never parses EDIS files or discovers
history. Callers should treat credentials as secrets even though GET query
parameters are required by the official executable examples.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from email.message import Message
from hashlib import sha256
import math
import re
from typing import Callable, Literal, Mapping, Protocol
from urllib.error import HTTPError
from urllib.parse import quote_plus, unquote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


Operation = Literal["subscribed_product_list", "subscribed_file_download"]


class TPExEDISTransportError(ValueError):
    """Argument/configuration rejection containing only a stable error code."""

    def __init__(self, error_code: str) -> None:
        self.error_code = error_code
        super().__init__(error_code)


@dataclass(frozen=True)
class TPExEDISProductFile:
    product_name: str
    file_name: str


@dataclass(frozen=True)
class TPExEDISTransportResult:
    status: Literal["success", "provider_error", "transport_failed"]
    operation: Operation
    http_status: int | None = None
    content_type: str | None = None
    response_byte_count: int = 0
    response_sha256: str | None = None
    error_code: str | None = None
    list_parse_status: Literal["parsed", "unrecognized_format"] | None = None
    product_files: tuple[TPExEDISProductFile, ...] = ()
    raw_text: str | None = field(default=None, repr=False)
    file_name: str | None = None
    raw_bytes: bytes | None = field(default=None, repr=False)


class _Response(Protocol):
    status: int
    headers: Mapping[str, str]

    def read(self, size: int = -1) -> bytes: ...
    def close(self) -> None: ...


HTTPGet = Callable[[Request, float], _Response]


class _NoRedirectHandler(HTTPRedirectHandler):
    """Refuse redirects so query credentials cannot be forwarded elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _default_http_get(request: Request, timeout_seconds: float) -> _Response:
    opener = build_opener(_NoRedirectHandler())
    try:
        return opener.open(request, timeout=timeout_seconds)  # type: ignore[return-value]
    except HTTPError as response:
        # HTTPError is also a bounded, readable response. The caller classifies
        # its body before handling its status without exposing its URL.
        return response  # type: ignore[return-value]


_ZH_PROVIDER_ERRORS: tuple[tuple[str, str], ...] = (
    ("請輸入帳號。", "account_missing"),
    ("請輸入密碼。", "password_missing"),
    ("請輸入需獲取選項。", "step_missing_or_invalid"),
    ("帳號停用中", "account_inactive"),
    ("帳號尚未啟用，請先執行驗證", "account_not_confirmed"),
    ("密碼錯誤", "password_invalid"),
    ("會員並未開啟API下載功能", "api_download_not_enabled"),
    ("此會員查無期限內的訂閱紀錄", "no_valid_api_subscription"),
)
_EN_PROVIDER_ERRORS: tuple[tuple[str, str], ...] = (
    ("please enter your account", "account_missing"),
    ("please enter password", "password_missing"),
    ("please enter the required options", "step_missing_or_invalid"),
    ("account is inactive", "account_inactive"),
    ("account is in active", "account_inactive"),
    ("account not confirm", "account_not_confirmed"),
    ("password is wrong", "password_invalid"),
    ("the member has not enabled the api download", "api_download_not_enabled"),
    (
        "this member checks subscription records for an unlimited period",
        "no_valid_api_subscription",
    ),
)
_STEP1_ZH_ERRORS: tuple[tuple[str, str], ...] = (
    ("請輸入檔案名稱", "file_name_missing"),
    ("查無此檔案名稱", "file_name_not_found"),
    ("此商品目前並無販售", "product_not_for_sale"),
    ("此商品目前不提供API下載服務", "product_api_download_unavailable"),
    ("查無訂閱方案或訂閱方案已經過期", "subscription_absent_or_expired"),
    ("超過可下載期限", "download_link_expired"),
)
_STEP1_EN_ERRORS: tuple[tuple[str, str], ...] = (
    ("please enter a filename", "file_name_missing"),
    ("no such file name found", "file_name_not_found"),
    ("this item is currently not for sale", "product_not_for_sale"),
    (
        "this product does not provide api download service",
        "product_api_download_unavailable",
    ),
    (
        "check no subscription plan or subscription plan has expired",
        "subscription_absent_or_expired",
    ),
)
_DOWNLOAD_LIMIT_ZH = re.compile(r"下載次數最多為\s*\d+\s*次")
_DOWNLOAD_LIMIT_EN = re.compile(r"maximum\s+\d+\s+times", re.IGNORECASE)
_LINK_EXPIRY_ZH = re.compile(r"連結失效日\s*[:：]\s*\d{4}-\d{2}-\d{2}")
_LINK_EXPIRY_EN = re.compile(r"link\s+expire\s+date\s*:\s*\d{4}-\d{2}-\d{2}", re.IGNORECASE)
_ZH_LIST_ENTRY = re.compile(
    r"\s*商品名稱：(?P<product>[^,\r\n<]+?)\s*,\s*檔案名稱："
    r"(?P<file>[^<\r\n]+?)<br\s*/>\s*"
)


def _validate_common(
    *,
    base_url: str,
    account: str,
    password: str,
    lang: str | None,
    timeout_seconds: float,
    max_response_bytes: int,
) -> str:
    try:
        parts = urlsplit(base_url)
    except (TypeError, ValueError) as exc:
        raise TPExEDISTransportError("invalid_base_url") from None
    if (
        not isinstance(base_url, str)
        or parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
        or any(ord(char) < 32 or ord(char) == 127 for char in base_url)
    ):
        raise TPExEDISTransportError("invalid_base_url")
    if not isinstance(account, str) or not account or not isinstance(password, str) or not password:
        raise TPExEDISTransportError("invalid_credentials")
    try:
        account.encode("utf-8")
        password.encode("utf-8")
    except UnicodeEncodeError:
        raise TPExEDISTransportError("invalid_credentials") from None
    if any(ord(char) < 32 or ord(char) == 127 for char in account + password):
        raise TPExEDISTransportError("invalid_credentials")
    if lang is not None and lang not in {"zh", "en"}:
        raise TPExEDISTransportError("invalid_language")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        raise TPExEDISTransportError("invalid_timeout")
    if isinstance(max_response_bytes, bool) or not isinstance(max_response_bytes, int) or max_response_bytes <= 0:
        raise TPExEDISTransportError("invalid_response_limit")
    return f"{parts.scheme}://{parts.netloc}"


def _validate_file_name(file_name: str) -> None:
    if not isinstance(file_name, str) or not file_name or file_name in {".", ".."}:
        raise TPExEDISTransportError("invalid_file_name")
    if any(ord(char) < 32 or ord(char) == 127 for char in file_name):
        raise TPExEDISTransportError("invalid_file_name")
    try:
        file_name.encode("utf-8")
    except UnicodeEncodeError:
        raise TPExEDISTransportError("invalid_file_name") from None
    probe = file_name
    for _ in range(3):
        if (
            probe in {".", ".."}
            or "/" in probe
            or "\\" in probe
            or any(ord(char) < 32 or ord(char) == 127 for char in probe)
        ):
            raise TPExEDISTransportError("invalid_file_name")
        decoded = unquote(probe)
        if decoded == probe:
            break
        probe = decoded


def _build_request(
    *,
    base_url: str,
    operation: Operation,
    account: str,
    password: str,
    lang: str | None,
    file_name: str | None,
) -> Request:
    step = "0" if operation == "subscribed_product_list" else "1"
    params: list[tuple[str, str]] = [
        ("step", step),
        ("account", account),
        ("pwd", password),
    ]
    if lang is not None:
        params.append(("lang", lang))
    if file_name is not None:
        params.append(("fileName", file_name))
    url = f"{base_url}/download/getApi?{urlencode(params, quote_via=quote_plus)}"
    return Request(url, method="GET")


def _response_status(response: _Response) -> int | None:
    status = getattr(response, "status", None)
    if status is None:
        status = getattr(response, "code", None)
    return status if isinstance(status, int) else None


def _content_type(response: _Response) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    getter = getattr(headers, "get", None)
    value = getter("Content-Type") if getter else None
    return value if isinstance(value, str) else None


def _contains_secret(body: bytes, account: str, password: str) -> bool:
    for secret in (account, password):
        for encoded in (secret.encode("utf-8"), quote_plus(secret).encode("ascii")):
            if encoded and encoded in body:
                return True
    return False


def _decode_declared_text(body: bytes, content_type: str | None) -> str | None:
    if not content_type:
        return None
    try:
        header = Message()
        header["Content-Type"] = content_type
        charset = header.get_content_charset()
        if not charset:
            return None
        return body.decode(charset)
    except (LookupError, UnicodeDecodeError, ValueError):
        return None


def _provider_error(body: bytes, operation: Operation, content_type: str | None) -> str | None:
    text = _decode_declared_text(body, content_type)
    if text is None:
        # Charset is required for exposing Step-0 text, but a UTF-8 scan is
        # still useful solely to recognize exact documented provider errors.
        # It is never used to decode or reinterpret a successful Step-1 body.
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return None
    text = text.replace("\u3000", " ")
    compact = re.sub(r"\s+", " ", text).strip()
    folded = compact.casefold()
    for phrase, code in _ZH_PROVIDER_ERRORS:
        if phrase in compact:
            return code
    for phrase, code in _EN_PROVIDER_ERRORS:
        if phrase in folded:
            return code
    if operation == "subscribed_file_download":
        for phrase, code in _STEP1_ZH_ERRORS:
            if phrase in compact:
                return code
        for phrase, code in _STEP1_EN_ERRORS:
            if phrase in folded:
                return code
        if _DOWNLOAD_LIMIT_ZH.search(compact) or _DOWNLOAD_LIMIT_EN.search(compact):
            return "download_count_exceeded"
        if _LINK_EXPIRY_ZH.search(compact) or _LINK_EXPIRY_EN.search(compact):
            return "download_link_expired"
    return None


def _parse_product_files(text: str) -> tuple[str, tuple[TPExEDISProductFile, ...]]:
    if not text:
        return "unrecognized_format", ()
    entries: list[TPExEDISProductFile] = []
    offset = 0
    while offset < len(text):
        match = _ZH_LIST_ENTRY.match(text, offset)
        if match is None:
            return "unrecognized_format", ()
        product = match.group("product").strip()
        file_name = match.group("file").strip()
        if not product or not file_name:
            return "unrecognized_format", ()
        entries.append(TPExEDISProductFile(product, file_name))
        offset = match.end()
    return ("parsed", tuple(entries)) if entries else ("unrecognized_format", ())


def _failure(
    operation: Operation,
    code: str,
    *,
    http_status: int | None = None,
    content_type: str | None = None,
    response_byte_count: int = 0,
) -> TPExEDISTransportResult:
    return TPExEDISTransportResult(
        status="transport_failed",
        operation=operation,
        http_status=http_status,
        content_type=content_type,
        response_byte_count=response_byte_count,
        error_code=code,
    )


def _request(
    *,
    operation: Operation,
    base_url: str,
    account: str,
    password: str,
    lang: str | None,
    file_name: str | None,
    timeout_seconds: float,
    max_response_bytes: int,
    http_get: HTTPGet | None,
) -> TPExEDISTransportResult:
    base = _validate_common(
        base_url=base_url,
        account=account,
        password=password,
        lang=lang,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
    )
    if operation == "subscribed_file_download":
        _validate_file_name(file_name)  # type: ignore[arg-type]
        if _contains_secret(file_name.encode("utf-8"), account, password):
            raise TPExEDISTransportError("invalid_file_name")
    try:
        request = _build_request(
            base_url=base,
            operation=operation,
            account=account,
            password=password,
            lang=lang,
            file_name=file_name,
        )
    except Exception:
        raise TPExEDISTransportError("invalid_request_parameters") from None
    try:
        response = (http_get or _default_http_get)(request, float(timeout_seconds))
    except Exception:
        # A transport exception may contain the fully credentialed URL.
        return _failure(operation, "transport_failure")

    try:
        status = _response_status(response)
        content_type = _content_type(response)
    except Exception:
        try:
            response.close()
        except Exception:
            pass
        return _failure(operation, "transport_failure")
    content_type_contains_secret = content_type is not None and _contains_secret(
        content_type.encode("utf-8"), account, password
    )
    if content_type_contains_secret:
        content_type = None
    try:
        body = response.read(max_response_bytes + 1)
    except Exception:
        return _failure(operation, "transport_failure", http_status=status, content_type=content_type)
    finally:
        try:
            response.close()
        except Exception:
            pass
    if not isinstance(body, bytes):
        return _failure(operation, "invalid_response_body", http_status=status, content_type=content_type)
    if len(body) > max_response_bytes:
        return _failure(operation, "response_too_large", http_status=status, content_type=content_type)
    if content_type_contains_secret or _contains_secret(body, account, password):
        return _failure(operation, "response_contains_credentials", http_status=status, content_type=content_type)

    provider_error = _provider_error(body, operation, content_type)
    if provider_error is not None:
        return TPExEDISTransportResult(
            status="provider_error",
            operation=operation,
            http_status=status,
            content_type=content_type,
            response_byte_count=len(body),
            error_code=provider_error,
        )
    if status is not None and 300 <= status < 400:
        return _failure(operation, "redirect_not_followed", http_status=status, content_type=content_type, response_byte_count=len(body))
    if status is None or not 200 <= status < 300:
        return _failure(operation, "provider_response_unclassified", http_status=status, content_type=content_type, response_byte_count=len(body))

    digest = sha256(body).hexdigest()
    if operation == "subscribed_file_download":
        return TPExEDISTransportResult(
            status="success",
            operation=operation,
            http_status=status,
            content_type=content_type,
            response_byte_count=len(body),
            response_sha256=digest,
            file_name=file_name,
            raw_bytes=body,
        )

    raw_text = _decode_declared_text(body, content_type)
    if raw_text is None:
        return _failure(operation, "response_text_encoding_unrecognized", http_status=status, content_type=content_type, response_byte_count=len(body))
    parse_status, product_files = _parse_product_files(raw_text)
    return TPExEDISTransportResult(
        status="success",
        operation=operation,
        http_status=status,
        content_type=content_type,
        response_byte_count=len(body),
        response_sha256=digest,
        list_parse_status=parse_status,
        product_files=product_files,
        raw_text=raw_text,
    )


def get_subscribed_product_files(
    *,
    base_url: str,
    account: str,
    password: str,
    timeout_seconds: float,
    max_response_bytes: int,
    lang: Literal["zh", "en"] | None = None,
    http_get: HTTPGet | None = None,
) -> TPExEDISTransportResult:
    """Perform one bounded Step-0 GET and retain its text only in memory."""
    return _request(
        operation="subscribed_product_list",
        base_url=base_url,
        account=account,
        password=password,
        lang=lang,
        file_name=None,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        http_get=http_get,
    )


def download_subscribed_file(
    *,
    base_url: str,
    account: str,
    password: str,
    file_name: str,
    timeout_seconds: float,
    max_response_bytes: int,
    lang: Literal["zh", "en"] | None = None,
    http_get: HTTPGet | None = None,
) -> TPExEDISTransportResult:
    """Perform one bounded Step-1 GET and return the successful body opaque."""
    return _request(
        operation="subscribed_file_download",
        base_url=base_url,
        account=account,
        password=password,
        lang=lang,
        file_name=file_name,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        http_get=http_get,
    )
