from __future__ import annotations

import importlib.util
import io
import json
import sys
from email.message import Message
from pathlib import Path
import urllib.error
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


@pytest.mark.parametrize("location", [None, "https://example.test/redirected?token=do-not-persist#frag"])
def test_http_307_is_sanitized_and_never_followed(monkeypatch, location):
    budget = probe_sources.BootstrapDispatchBudget(10)
    headers = Message()
    if location is not None:
        headers["Location"] = location

    class ErrorOpener:
        dispatched = 0

        def open(self, request, timeout):
            self.dispatched += 1
            assert budget.used_dispatches == 1
            raise urllib.error.HTTPError(
                request.full_url, 307, "Temporary Redirect", headers, io.BytesIO(b"diagnostic body")
            )

    opener = ErrorOpener()
    monkeypatch.setattr(
        probe_sources.urllib.request,
        "build_opener",
        lambda *_args: opener,
    )
    result = probe_sources.probe(
        "https://example.test/start",
        ["example.test"],
        dispatch_budget=budget,
        max_followed_redirects=1,
    )
    assert opener.dispatched == 1
    assert result["http_status"] == 307
    assert result["transport_error_code"] == "BOOTSTRAP_HTTP_REDIRECT_NOT_FOLLOWED"
    assert result["redirect_followed"] is False
    assert result["redirect_location_present"] is (location is not None)
    if location is None:
        assert result["redirect_location_allowed"] is False
        assert result["redirect_location_scheme"] is None
    else:
        assert result["redirect_location_allowed"] is True
        assert result["redirect_location_scheme"] == "https"
        assert result["redirect_location_host"] == "example.test"
        assert result["redirect_location_path_or_sanitized_url"] == "/redirected"
        assert "token" not in str(result)
        assert "do-not-persist" not in str(result)


def test_307_disallowed_location_is_reported_not_dispatched(monkeypatch):
    budget = probe_sources.BootstrapDispatchBudget(10)
    headers = Message()
    headers["Location"] = "https://evil.example/secret?key=private"

    class ErrorOpener:
        dispatched = 0

        def open(self, request, timeout):
            self.dispatched += 1
            raise urllib.error.HTTPError(
                request.full_url, 307, "Temporary Redirect", headers, io.BytesIO(b"")
            )

    opener = ErrorOpener()
    monkeypatch.setattr(probe_sources.urllib.request, "build_opener", lambda *_args: opener)
    result = probe_sources.probe(
        "https://example.test/start",
        ["example.test"],
        dispatch_budget=budget,
        max_followed_redirects=1,
    )
    assert opener.dispatched == 1
    assert budget.used_dispatches == 1
    assert result["redirect_location_host"] == "evil.example"
    assert result["redirect_location_allowed"] is False
    assert result["redirect_followed"] is False
    assert "private" not in str(result)


@pytest.mark.parametrize("status", [404, 500])
def test_non_redirect_http_errors_keep_ordinary_classification(monkeypatch, status):
    budget = probe_sources.BootstrapDispatchBudget(10)

    class ErrorOpener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(
                request.full_url, status, "HTTP failure", Message(), io.BytesIO(b"failure")
            )

    monkeypatch.setattr(probe_sources.urllib.request, "build_opener", lambda *_args: ErrorOpener())
    result = probe_sources.probe(
        "https://example.test/start",
        ["example.test"],
        dispatch_budget=budget,
        max_followed_redirects=1,
    )
    assert result["acquisition_status"] == "http_error"
    assert result["http_status"] == status
    assert "transport_error_code" not in result
    assert "redirect_followed" not in result


def test_lifecycle_schema_drift_stops_materializer_before_next_probe_and_phase_e(
    monkeypatch, tmp_path, capsys
):
    spec = importlib.util.spec_from_file_location(
        "a6_sm_b1_r2_materializer",
        ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "BUNDLE_BASE", tmp_path / "bundles")
    # This downstream fake drift test starts after the separately tested R3
    # source-contract guard; the real current manifest cannot authorize probes.
    monkeypatch.setattr(module, "_require_tpex_lifecycle_data_contract", lambda _manifest: None)
    calls = []
    report = {}
    qualification_calls = []
    export_calls = []

    def fake_probe(url, _allowed_hosts, *, save_raw=None, dispatch_budget=None, **_kwargs):
        dispatch_budget.reserve_before_dispatch()
        save_raw.parent.mkdir(parents=True, exist_ok=True)
        save_raw.write_bytes(b"sanitized test capture")
        if "strMode=2" in url:
            source_id = "twse_isin_mode2_zh"
        elif "strMode=4" in url:
            source_id = "twse_isin_mode4_zh"
        elif "suspendListing" in url:
            source_id = "twse_delisted"
        elif "tpex.org.tw" in url:
            source_id = "tpex_delisted"
        else:
            source_id = "twse_etn_expired"
        calls.append(source_id)
        return {
            "acquisition_status": "data",
            "transport_success": True,
            "http_status": 200,
            "byte_count": 24,
                "dispatch_reservations": 1,
            "source_id": source_id,
        }

    monkeypatch.setattr(module, "probe", fake_probe)
    monkeypatch.setattr(module, "find_source_contract", lambda *_args: {})
    monkeypatch.setattr(
        module,
        "parse_html",
        lambda *_args, **_kwargs: {
            "acquisition_status": "data",
            "records": [{"identity": {"security_code": "2330"}}],
        },
    )
    monkeypatch.setattr(
        module,
        "classify_all",
        lambda *_args: {
            "record_count": 1,
            "records": [{"identity": {}, "classification": {}, "observation": {}}],
        },
    )
    monkeypatch.setattr(module, "parse_twse_delisted", lambda *_args: [])

    def drift(*_args):
        raise module.LifecycleSchemaDrift("no_html_tables")

    monkeypatch.setattr(module, "parse_tpex_delisted", drift)
    monkeypatch.setattr(
        module,
        "_write_failure_report",
        lambda *_args, **kwargs: report.update(
            {"sources": _args[4], "decision": _args[5], "reason": _args[6]}
        ),
    )
    monkeypatch.setattr(
        module,
        "qualify_record",
        lambda *_args: qualification_calls.append(True),
    )
    monkeypatch.setattr(
        module,
        "export_verified_security_master_snapshot",
        lambda **_kwargs: export_calls.append(True),
    )

    assert module.main() == 1
    assert calls == [
        "twse_isin_mode2_zh",
        "twse_isin_mode4_zh",
        "twse_delisted",
        "tpex_delisted",
    ]
    assert "twse_etn_expired" not in calls
    assert len(report["sources"]) == 4
    drift = report["sources"][-1]
    assert drift["bootstrap_failure_code"] == "BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT"
    assert "transport_error_code" not in drift
    assert drift["lifecycle_schema_drift"] == {
        "source_id": "tpex_delisted",
        "parser": "parse_tpex_delisted",
        "issue_code": "no_html_tables",
        "sanitized_detail": {},
        "dispatch_reservations_used": 4,
        "probe_dispatch_reservations": 1,
    }
    assert drift["acquisition_status"] == "schema_drift"
    assert report["decision"] == "BLOCKED_BY_LIFECYCLE_SCHEMA_DRIFT"
    assert report["reason"] == "BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT"
    assert qualification_calls == []
    assert export_calls == []
    assert "HARD STOP: BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT" in capsys.readouterr().out


def test_lifecycle_drift_detail_retains_shape_without_source_header_text():
    spec = importlib.util.spec_from_file_location(
        "a6_sm_b1_r2_detail_materializer",
        ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    drift = module.LifecycleSchemaDrift(
        "unrecognized_lifecycle_header",
        {"observed_header_candidates": [["sensitive source header", "second"]]},
    )
    assert module._sanitize_lifecycle_drift_detail(drift) == {
        "observed_header_candidate_count": 1,
        "observed_header_widths": [2],
        "truncated": False,
    }
    assert "sensitive source header" not in str(module._sanitize_lifecycle_drift_detail(drift))


def test_lifecycle_drift_failure_report_preserves_code_without_retry_authority(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "a6_sm_b1_r2_failure_report_materializer",
        ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    bundle_id = "m8r06-01b-20261010T000000Z"
    bundle_dir = tmp_path / "input_bundles" / bundle_id
    probe = {
        "source_id": "tpex_delisted",
        "parser_selected": "parse_tpex_delisted",
        "acquisition_status": "schema_drift",
        "bootstrap_failure_code": "BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT",
        "lifecycle_schema_drift": {
            "source_id": "tpex_delisted",
            "parser": "parse_tpex_delisted",
            "issue_code": "no_html_tables",
            "sanitized_detail": {},
            "dispatch_reservations_used": 4,
            "probe_dispatch_reservations": 1,
        },
    }
    module._write_failure_report(
        bundle_dir,
        "2026-10-10T00:00:00+00:00",
        "2026-10-10",
        bundle_id,
        [probe],
        "BLOCKED_BY_LIFECYCLE_SCHEMA_DRIFT",
        "BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT",
        repo_root=tmp_path,
    )
    reports = list(tmp_path.rglob("*.json"))
    report = next(json.loads(path.read_text()) for path in reports if "bootstrap_failure_code" in path.read_text())
    assert report["bootstrap_failure_code"] == "BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT"
    assert report["source_probes"][0]["lifecycle_schema_drift"]["dispatch_reservations_used"] == 4
    assert report["authorized_next_task"] == "independent_review_required_no_bootstrap_retry"
    assert report["exporter_dry_run_attempted"] is False
    assert report["production_input_bundle_created"] is False
