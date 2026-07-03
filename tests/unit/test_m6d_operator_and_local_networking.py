import platform
import sys

from fastapi.middleware.cors import CORSMiddleware

from scripts.ssl_policy import platform_ssl_diagnostics
from server.main import app


def test_operator_diagnostics_windows_python313_hint(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(sys, "version_info", (3, 13, 1, "final", 0))
    diag = platform_ssl_diagnostics(environ={})
    assert diag["windows_detected"] is True
    assert diag["python_313_detected"] is True
    assert "--ssl-policy compatibility" in diag["operator_hint"]
    assert diag["network_calls"] is False


def test_fastapi_cors_local_only_and_noncredentialed():
    cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    opts = cors.kwargs
    assert opts["allow_origins"] == ["null"]
    assert "localhost" in opts["allow_origin_regex"]
    assert "127\\.0\\.0\\.1" in opts["allow_origin_regex"]
    assert opts["allow_credentials"] is False
    assert opts["allow_methods"] == ["GET", "POST"]
    assert "*" not in opts["allow_origins"]
