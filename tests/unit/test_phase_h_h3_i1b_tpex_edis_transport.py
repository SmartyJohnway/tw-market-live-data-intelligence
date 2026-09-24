"""Offline contract tests for the dormant bounded TPEx E-Data Shop transport."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from server.services import phase_h_h3_tpex_edis_adapter as phase_h_h3_edis_adapter
from server.services.phase_h_h3_tpex_edis_transport import (
    TPExEDISTransportError,
    _NoRedirectHandler,
    download_subscribed_file,
    get_subscribed_product_files,
)


BASE_URL = "https://transport-fixture.invalid"
ACCOUNT = "TEST_ACCOUNT_DO_NOT_USE"
PASSWORD = "TEST_PASSWORD_DO_NOT_USE"
FILE_NAME = "API_filename_日本 & B.zip"
TIMEOUT = 3.25
MAX_BYTES = 128


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, headers: dict[str, str] | None = None):
        self.body = body
        self.status = status
        self.headers = headers or {"Content-Type": "text/plain; charset=utf-8"}
        self.read_sizes: list[int] = []
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return self.body if size < 0 else self.body[:size]

    def close(self) -> None:
        self.closed = True


class FakeGet:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls: list[tuple[object, float]] = []

    def __call__(self, request, timeout_seconds: float) -> FakeResponse:
        self.calls.append((request, timeout_seconds))
        return self.response


def _step0(http_get, **overrides):
    args = {
        "base_url": BASE_URL,
        "account": ACCOUNT,
        "password": PASSWORD,
        "timeout_seconds": TIMEOUT,
        "max_response_bytes": MAX_BYTES,
        "http_get": http_get,
    }
    args.update(overrides)
    return get_subscribed_product_files(**args)


def _step1(http_get, **overrides):
    args = {
        "base_url": BASE_URL,
        "account": ACCOUNT,
        "password": PASSWORD,
        "file_name": FILE_NAME,
        "timeout_seconds": TIMEOUT,
        "max_response_bytes": MAX_BYTES,
        "http_get": http_get,
    }
    args.update(overrides)
    return download_subscribed_file(**args)


def _public_repr(result) -> str:
    return repr(result) + repr(asdict(result))


def _assert_no_credentials(result) -> None:
    public = _public_repr(result)
    assert ACCOUNT not in public
    assert PASSWORD not in public


def test_step0_constructs_one_encoded_get_with_optional_language() -> None:
    response = FakeResponse(
        "商品名稱：API檔案名稱, 檔案名稱：API_filename.zip<br/>".encode("utf-8")
    )
    fake = FakeGet(response)
    result = _step0(
        fake,
        account=f"{ACCOUNT}+&",
        password=f"{PASSWORD} /?",
        lang="zh",
    )

    assert result.status == "success"
    assert result.operation == "subscribed_product_list"
    assert len(fake.calls) == 1
    request, timeout = fake.calls[0]
    assert request.method == "GET"
    parsed = urlsplit(request.full_url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "transport-fixture.invalid"
    assert parsed.path == "/download/getApi"
    assert parse_qs(parsed.query, strict_parsing=True) == {
        "step": ["0"],
        "account": [f"{ACCOUNT}+&"],
        "pwd": [f"{PASSWORD} /?"],
        "lang": ["zh"],
    }
    assert timeout == TIMEOUT
    assert response.read_sizes == [MAX_BYTES + 1]
    assert response.closed
    assert result.list_parse_status == "parsed"
    assert [(entry.product_name, entry.file_name) for entry in result.product_files] == [
        ("API檔案名稱", "API_filename.zip")
    ]
    assert result.raw_text == response.body.decode("utf-8")
    assert result.response_byte_count == len(response.body)
    assert result.response_sha256 == sha256(response.body).hexdigest()
    _assert_no_credentials(result)


def test_step0_omits_language_when_not_supplied_and_unknown_format_is_not_guessed() -> None:
    response = FakeResponse(b"provider returned a new list format")
    fake = FakeGet(response)
    result = _step0(fake)
    request, _ = fake.calls[0]
    query = parse_qs(urlsplit(request.full_url).query, strict_parsing=True)
    assert query["step"] == ["0"]
    assert "lang" not in query
    assert result.status == "success"
    assert result.list_parse_status == "unrecognized_format"
    assert result.product_files == ()


def test_step0_requires_declared_text_encoding_instead_of_guessing() -> None:
    response = FakeResponse(b"response without declared charset", headers={"Content-Type": "text/plain"})
    result = _step0(FakeGet(response))
    assert result.status == "transport_failed"
    assert result.error_code == "response_text_encoding_unrecognized"
    assert result.raw_text is None


def test_step1_preserves_exact_file_name_and_success_body_as_opaque_bytes() -> None:
    opaque = b"\x00\xffnot-assumed-to-be-zip-or-text\r\n"
    response = FakeResponse(opaque, headers={"Content-Type": "application/octet-stream"})
    fake = FakeGet(response)
    result = _step1(fake, lang="en")

    request, timeout = fake.calls[0]
    assert len(fake.calls) == 1
    assert request.method == "GET"
    query = parse_qs(urlsplit(request.full_url).query, strict_parsing=True)
    assert query == {
        "step": ["1"],
        "account": [ACCOUNT],
        "pwd": [PASSWORD],
        "lang": ["en"],
        "fileName": [FILE_NAME],
    }
    assert result.status == "success"
    assert result.file_name == FILE_NAME
    assert result.raw_bytes == opaque
    assert result.raw_text is None
    assert result.response_sha256 == sha256(opaque).hexdigest()
    assert result.response_byte_count == len(opaque)
    assert timeout == TIMEOUT
    assert response.read_sizes == [MAX_BYTES + 1]
    _assert_no_credentials(result)


@pytest.mark.parametrize("lang", ["zh", "en"])
def test_only_documented_languages_are_accepted(lang: str) -> None:
    fake = FakeGet(FakeResponse(b"text"))
    assert _step0(fake, lang=lang).status == "success"


def test_invalid_language_and_unsafe_file_names_are_rejected_before_dispatch() -> None:
    fake = FakeGet(FakeResponse(b"unused"))
    with pytest.raises(TPExEDISTransportError) as lang_error:
        _step0(fake, lang="ja")
    assert str(lang_error.value) == "invalid_language"

    for unsafe in (
        "",
        "../secret.zip",
        r"folder\file.zip",
        "line\nfeed.zip",
        "line\rfeed.zip",
        "bad\x00name.zip",
        "%2e%2e%2fsecret.zip",
        "%252e%252e%252fsecret.zip",
        "%00secret.zip",
    ):
        with pytest.raises(TPExEDISTransportError) as file_error:
            _step1(fake, file_name=unsafe)
        assert str(file_error.value) == "invalid_file_name"
    assert fake.calls == []


def test_base_url_must_be_explicit_https_origin_without_embedded_auth() -> None:
    fake = FakeGet(FakeResponse(b"text"))
    for bad_url in (
        "http://transport-fixture.invalid",
        "https://user:pass@transport-fixture.invalid",
        "https://transport-fixture.invalid/path",
        "https://transport-fixture.invalid?token=x",
    ):
        with pytest.raises(TPExEDISTransportError) as error:
            _step0(fake, base_url=bad_url)
        assert str(error.value) == "invalid_base_url"
    assert fake.calls == []


def test_oversized_body_reads_only_limit_plus_one_and_fails_closed() -> None:
    response = FakeResponse(b"x" * (MAX_BYTES + 10))
    fake = FakeGet(response)
    result = _step1(fake)
    assert result.status == "transport_failed"
    assert result.error_code == "response_too_large"
    assert response.read_sizes == [MAX_BYTES + 1]
    assert result.raw_bytes is None
    assert result.response_sha256 is None
    _assert_no_credentials(result)


@pytest.mark.parametrize(
    ("operation", "message", "code"),
    [
        ("step0", "請輸入帳號。", "account_missing"),
        ("step0", "Please enter password", "password_missing"),
        ("step0", "請輸入需獲取選項。", "step_missing_or_invalid"),
        ("step0", "Account is inActive", "account_inactive"),
        ("step0", "帳號尚未啟用，請先執行驗證", "account_not_confirmed"),
        ("step0", "Password is wrong", "password_invalid"),
        ("step0", "會員並未開啟API下載功能", "api_download_not_enabled"),
        ("step0", "此會員查無期限內的訂閱紀錄", "no_valid_api_subscription"),
        ("step0", "尚無期限內的 API 檔案", "no_valid_api_subscription"),
        ("step1", "請輸入檔案名稱", "file_name_missing"),
        ("step1", "No such file name found", "file_name_not_found"),
        ("step1", "此商品目前並無販售", "product_not_for_sale"),
        ("step1", "This product does not provide Api download service", "product_api_download_unavailable"),
        ("step1", "查無訂閱方案或訂閱方案已經過期", "subscription_absent_or_expired"),
        ("step1", "下載次數最多為 5 次", "download_count_exceeded"),
        ("step1", "連結失效日：2026-09-24。", "download_link_expired"),
    ],
)
def test_documented_provider_errors_are_classified_even_on_http_200(operation: str, message: str, code: str) -> None:
    fake = FakeGet(FakeResponse(message.encode("utf-8"), status=200))
    result = _step0(fake) if operation == "step0" else _step1(fake)
    assert result.status == "provider_error"
    assert result.error_code == code
    assert result.raw_text is None
    assert result.raw_bytes is None
    _assert_no_credentials(result)


def test_documented_error_is_checked_even_when_charset_is_not_declared() -> None:
    fake = FakeGet(
        FakeResponse("密碼錯誤".encode("utf-8"), status=200, headers={"Content-Type": "text/plain"})
    )
    result = _step1(fake)
    assert result.status == "provider_error"
    assert result.error_code == "password_invalid"
    assert result.raw_bytes is None


def test_undecodable_declared_textual_step1_response_fails_closed() -> None:
    fake = FakeGet(FakeResponse(b"\x81\x40\x81\x41", headers={"Content-Type": "text/plain"}))
    result = _step1(fake)
    assert result.status == "transport_failed"
    assert result.error_code == "provider_response_unclassified"
    assert result.raw_bytes is None


def test_decoded_unknown_textual_step1_response_remains_opaque_success() -> None:
    body = b"new provider text not covered by documented error messages"
    result = _step1(FakeGet(FakeResponse(body, headers={"Content-Type": "text/plain; charset=utf-8"})))
    assert result.status == "success"
    assert result.raw_bytes == body
    assert result.raw_text is None


def test_step1_binary_body_containing_credentials_is_rejected() -> None:
    body = b"\x00\xff" + ACCOUNT.encode("ascii") + b"\x00"
    result = _step1(
        FakeGet(FakeResponse(body, headers={"Content-Type": "application/octet-stream"}))
    )
    assert result.status == "transport_failed"
    assert result.error_code == "response_contains_credentials"
    assert result.raw_bytes is None


def test_unknown_non_success_provider_response_is_not_guessed_or_http_mapped() -> None:
    fake = FakeGet(FakeResponse(b"unrecognized provider message", status=503))
    result = _step1(fake)
    assert result.status == "transport_failed"
    assert result.error_code == "provider_response_unclassified"
    assert result.http_status == 503
    assert result.raw_bytes is None


def test_http_status_is_not_mapped_to_password_or_file_semantics() -> None:
    fake = FakeGet(FakeResponse(b"unrecognized", status=401))
    result = _step1(fake)
    assert result.error_code == "provider_response_unclassified"
    assert result.error_code != "password_invalid"
    assert result.error_code != "file_name_not_found"


def test_cross_host_redirect_is_not_followed_and_credentials_are_not_forwarded() -> None:
    response = FakeResponse(
        b"redirect",
        status=302,
        headers={"Content-Type": "text/plain", "Location": "https://other.invalid/collect"},
    )
    fake = FakeGet(response)
    result = _step1(fake)
    assert result.status == "transport_failed"
    assert result.error_code == "redirect_not_followed"
    assert len(fake.calls) == 1
    assert _NoRedirectHandler().redirect_request(None, None, 302, "Found", {}, "https://other.invalid/collect") is None
    _assert_no_credentials(result)


def test_transport_exception_containing_secret_url_is_sanitized() -> None:
    def raising_get(request, timeout_seconds):
        raise RuntimeError(f"socket failed for {request.full_url}")

    result = _step0(raising_get)
    assert result.status == "transport_failed"
    assert result.error_code == "transport_failure"
    public = _public_repr(result)
    assert ACCOUNT not in public
    assert PASSWORD not in public
    assert "transport-fixture.invalid" not in public


def test_credentials_are_not_returned_when_provider_echoes_them() -> None:
    response = FakeResponse(f"echo {ACCOUNT} {PASSWORD}".encode("utf-8"))
    result = _step0(FakeGet(response))
    assert result.error_code == "response_contains_credentials"
    _assert_no_credentials(result)


def test_credentials_in_response_headers_are_not_returned_as_metadata() -> None:
    response = FakeResponse(
        b"opaque",
        headers={"Content-Type": f"text/plain; note={ACCOUNT}"},
    )
    result = _step0(FakeGet(response))
    assert result.status == "transport_failed"
    assert result.error_code == "response_contains_credentials"
    assert result.content_type is None
    _assert_no_credentials(result)


def test_secrets_never_appear_in_transport_configuration_errors() -> None:
    with pytest.raises(TPExEDISTransportError) as error:
        _step0(FakeGet(FakeResponse(b"")), base_url="not a URL")
    assert ACCOUNT not in repr(error.value)
    assert PASSWORD not in repr(error.value)


def test_transport_does_not_write_files_or_call_h3_i1a(tmp_path: Path, monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("transport called the H3-I1A parser")

    monkeypatch.setattr(phase_h_h3_edis_adapter, "normalize_tpex_edis_daily_quote", forbidden)
    result = _step1(FakeGet(FakeResponse(b"opaque")))
    assert result.raw_bytes == b"opaque"
    assert list(tmp_path.iterdir()) == []
