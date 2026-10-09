from __future__ import annotations

import importlib.util
import sys
from email.message import Message
from pathlib import Path
from urllib.request import HTTPRedirectHandler

import pytest


ROOT = Path(__file__).resolve().parents[2]
SKILL_SCRIPTS = ROOT / "skills/tw-security-master-classifier/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
import probe_sources  # noqa: E402


class FakeResponse:
    def __init__(self, url: str, body: bytes = b"<html>bounded fixture</html>") -> None:
        self.status = 200
        self._url = url
        self._body = body
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"

    def geturl(self) -> str:
        return self._url

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


class FakeOpener:
    def __init__(self, handler, steps, budget):
        self.handler = handler
        self.steps = list(steps)
        self.budget = budget
        self.starting_dispatches = budget.used_dispatches
        self.dispatched_urls: list[str] = []

    def open(self, request, timeout):
        assert self.budget.used_dispatches == self.starting_dispatches + len(self.dispatched_urls) + 1
        self.dispatched_urls.append(request.full_url)
        kind, value = self.steps.pop(0)
        if kind == "redirect":
            headers = {"Location": value}
            redirected = self.handler.redirect_request(
                request, None, 302, "Found", headers, value
            )
            if redirected is None:
                raise AssertionError("fake redirect unexpectedly declined")
            return self.open(redirected, timeout=0)
        return FakeResponse(request.full_url, value)


def install_fake_opener(monkeypatch, steps, budget):
    created = []

    def build_opener(handler, _https_handler):
        opener = FakeOpener(handler, steps, budget)
        created.append(opener)
        return opener

    monkeypatch.setattr(probe_sources.urllib.request, "build_opener", build_opener)
    return created


def test_runtime_inherited_urllib_redirect_bounds_are_observed():
    handler = probe_sources.SafeRedirectHandler(["example.test"])
    assert issubclass(probe_sources.SafeRedirectHandler, HTTPRedirectHandler)
    assert handler.max_repeats == HTTPRedirectHandler.max_repeats
    assert handler.max_redirections == HTTPRedirectHandler.max_redirections
    assert isinstance(handler.max_repeats, int)
    assert isinstance(handler.max_redirections, int)


def test_no_redirect_uses_one_reserved_and_dispatched_request(monkeypatch):
    budget = probe_sources.BootstrapDispatchBudget(10)
    openers = install_fake_opener(monkeypatch, [("response", b"<html>fixture</html>")], budget)
    result = probe_sources.probe(
        "https://example.test/start",
        ["example.test"],
        dispatch_budget=budget,
        max_followed_redirects=1,
    )
    assert result["transport_success"] is True
    assert result["redirect_count"] == 0
    assert result["dispatch_reservations"] == 1
    assert len(openers[0].dispatched_urls) == 1


def test_one_allowed_redirect_dispatches_twice_and_passes_bound(monkeypatch):
    budget = probe_sources.BootstrapDispatchBudget(10)
    openers = install_fake_opener(
        monkeypatch,
        [("redirect", "https://example.test/final"), ("response", b"<html>fixture</html>")],
        budget,
    )
    result = probe_sources.probe(
        "https://example.test/start",
        ["example.test"],
        dispatch_budget=budget,
        max_followed_redirects=1,
    )
    assert result["transport_success"] is True
    assert result["redirect_count"] == 1
    assert result["dispatch_reservations"] == 2
    assert len(openers[0].dispatched_urls) == 2


def test_second_redirect_target_is_not_dispatched(monkeypatch):
    budget = probe_sources.BootstrapDispatchBudget(10)
    openers = install_fake_opener(
        monkeypatch,
        [
            ("redirect", "https://example.test/second"),
            ("redirect", "https://example.test/third"),
        ],
        budget,
    )
    result = probe_sources.probe(
        "https://example.test/start",
        ["example.test"],
        dispatch_budget=budget,
        max_followed_redirects=1,
    )
    assert result["acquisition_status"] == "redirect_limit_exceeded"
    assert result["transport_error_code"] == "BOOTSTRAP_REDIRECT_LIMIT_EXCEEDED"
    assert result["dispatch_reservations"] == 2
    assert openers[0].dispatched_urls == [
        "https://example.test/start",
        "https://example.test/second",
    ]


def test_disallowed_redirect_host_is_rejected_before_target_dispatch(monkeypatch):
    budget = probe_sources.BootstrapDispatchBudget(10)
    openers = install_fake_opener(
        monkeypatch, [("redirect", "https://evil.test/target")], budget
    )
    result = probe_sources.probe(
        "https://example.test/start",
        ["example.test"],
        dispatch_budget=budget,
        max_followed_redirects=1,
    )
    assert result["acquisition_status"] == "redirect_rejected"
    assert result["transport_error_code"] == "BOOTSTRAP_REDIRECT_REJECTED"
    assert result["dispatch_reservations"] == 1
    assert openers[0].dispatched_urls == ["https://example.test/start"]


def test_five_probe_complete_envelope_uses_shared_ten_slot_budget(monkeypatch):
    budget = probe_sources.BootstrapDispatchBudget(10)
    total_dispatched = 0
    for index in range(5):
        url = f"https://example.test/start-{index}"
        openers = install_fake_opener(
            monkeypatch,
            [("redirect", f"https://example.test/final-{index}"), ("response", b"ok")],
            budget,
        )
        result = probe_sources.probe(
            url,
            ["example.test"],
            dispatch_budget=budget,
            max_followed_redirects=1,
        )
        assert result["transport_success"] is True
        assert result["dispatch_reservations"] == 2
        total_dispatched += len(openers[0].dispatched_urls)

    assert budget.used_dispatches == 10
    assert budget.remaining_dispatches == 0
    assert total_dispatched == 10

    extra_opener = install_fake_opener(monkeypatch, [("response", b"unused")], budget)
    extra = probe_sources.probe(
        "https://example.test/eleventh",
        ["example.test"],
        dispatch_budget=budget,
        max_followed_redirects=1,
    )
    assert extra["acquisition_status"] == "dispatch_budget_exhausted"
    assert extra["transport_error_code"] == "BOOTSTRAP_DISPATCH_BUDGET_EXHAUSTED"
    assert extra["dispatch_reservations"] == 0
    assert extra_opener[0].dispatched_urls == []


def test_materializer_binds_one_shared_ten_dispatch_budget_and_exact_sources():
    spec = importlib.util.spec_from_file_location(
        "a6p1_materializer", ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.IDENTITY_MODES == [2, 4]
    assert module.BOOTSTRAP_LOGICAL_PROBE_COUNT == 5
    assert module.BOOTSTRAP_MAX_REDIRECTS_PER_PROBE == 1
    assert module.BOOTSTRAP_MAX_DISPATCHES_PER_PROBE == 2
    assert module.BOOTSTRAP_MAX_TOTAL_DISPATCHES == 10
    source = (ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py").read_text()
    assert source.count("dispatch_budget=dispatch_budget") == 2
    assert '"twse_delisted"' in source
    assert '"tpex_delisted"' in source
    assert '"twse_etn_expired"' in source
    for code in (
        "BOOTSTRAP_REDIRECT_LIMIT_EXCEEDED",
        "BOOTSTRAP_DISPATCH_BUDGET_EXHAUSTED",
        "BOOTSTRAP_REDIRECT_REJECTED",
    ):
        with pytest.raises(RuntimeError, match=code):
            module._stop_on_bootstrap_transport_limit({"transport_error_code": code})
