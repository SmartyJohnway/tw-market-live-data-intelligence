from pathlib import Path
import json

import pytest

from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import R2RequestBudget, parse_daily_status

FETCHED = "2026-10-16T13:55:54+08:00"
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/phase_l/dgpa_daily_20261016_non_heading.html"


def _daily(title: str = "115年10月16日 天然災害停止上班及上課情形", status: str = "無停班停課訊息", tail: str = "") -> bytes:
    return (f"<html><h1>{title}</h1><p>更新時間：115年10月16日 12:30</p>"
            f"<p>行政院人事行政總處</p><p>{status}</p>{tail}</html>").encode("utf-8")


def test_non_heading_status_date_fixture_and_original_heading_shape():
    parsed = parse_daily_status(FIXTURE.read_bytes(), content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert parsed["target_date"] == "2026-10-16"
    assert parsed["status_kind"] == "explicit_no_notice"
    original = _daily("115年10月16日 停止上班上課情形")
    assert parse_daily_status(original, content_type="text/html", fetched_at=FETCHED)["target_date"] == "2026-10-16"


@pytest.mark.parametrize("status,scope", [
    ("臺北市照常上班上課", None),
    ("臺北市上午停止上班上課", "morning"),
    ("臺北市全天停止上班上課", "full_day"),
])
def test_daily_status_rows_are_adjudicated(status, scope):
    body = _daily(status="", tail=f"<table><tr><td>臺北市</td><td>{status}</td></tr></table>")
    parsed = parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert parsed["closure_event"] is None if scope is None else parsed["closure_event"]["closure_scope"] == scope


@pytest.mark.parametrize("body", [
    _daily("115年10月15日 天然災害停止上班及上課情形"),
    "<html><h1>天然災害停止上班及上課情形</h1><p>更新時間：115年10月16日 12:30</p><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>".encode(),
    "<html><h1>115年10月16日 天然災害停止上班及上課情形</h1><p>更新時間：115年10月15日 12:30</p><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>".encode(),
    "<html><h1>115年10月16日 天然災害停止上班及上課情形</h1><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>".encode(),
    "<html><footer>115年10月16日</footer><p>天然災害停止上班及上課情形</p><p>更新時間：115年10月16日 12:30</p><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>".encode(),
    "<html><a href='/information?pid=1&uid=374'>115年10月16日 天然災害停止上班及上課情形</a><p>更新時間：115年10月16日 12:30</p><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>".encode(),
    _daily(tail="<div><span>115年10月15日</span><span>天然災害停止上班及上課情形</span></div>"),
    _daily(tail="<div><span>115年10月16日</span><span>115年10月15日</span><span>天然災害停止上班及上課情形</span></div>"),
    _daily(status=""),
    _daily(status="無停班停課訊息", tail="<table><tr><td>臺北市</td><td>上午停止上班上課</td></tr></table>"),
])
def test_unbound_dates_or_incomplete_daily_semantics_fail_closed(body):
    with pytest.raises(ValueError):
        parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)


def test_missing_subject_attribution_and_status_fail_closed():
    cases = [
        "<html><h1>115年10月16日</h1><p>更新時間：115年10月16日 12:30</p><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>",
        "<html><h1>115年10月16日 天然災害停止上班及上課情形</h1><p>更新時間：115年10月16日 12:30</p><p>無停班停課訊息</p></html>",
        "<html><h1>115年10月16日 天然災害停止上班及上課情形</h1><p>更新時間：115年10月16日 12:30</p><p>行政院人事行政總處</p></html>",
    ]
    for body in cases:
        with pytest.raises(ValueError):
            parse_daily_status(body.encode(), content_type="text/html; charset=utf-8", fetched_at=FETCHED)


def test_conflicting_dates_and_malformed_utf8_fail_closed():
    ambiguous = "<html><div><span>115年10月16日</span><span>115年10月15日</span><span>天然災害停止上班及上課情形</span></div><p>更新時間：115年10月16日 12:30</p><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>".encode()
    with pytest.raises(ValueError, match="date_ambiguous"):
        parse_daily_status(ambiguous, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    with pytest.raises(ValueError, match="encoding_invalid"):
        parse_daily_status(_daily() + b"\xff", content_type="text/html; charset=utf-8", fetched_at=FETCHED)


def test_r2_get_budget_enforces_daily_one_index_four_detail_one_total_six():
    budget = R2RequestBudget()
    budget.reserve("daily")
    with pytest.raises(ValueError, match="budget_exceeded"):
        budget.reserve("daily")
    for _ in range(4):
        budget.reserve("index")
    with pytest.raises(ValueError, match="budget_exceeded"):
        budget.reserve("index")
    budget.reserve("detail")
    assert budget.counts() == {"daily": 1, "archive_index": 4, "archive_detail": 1, "total": 6}
    with pytest.raises(ValueError, match="budget_exceeded"):
        budget.reserve("detail")
    with pytest.raises(ValueError, match="unapproved_request_kind"):
        budget.reserve("market")


def test_r2_plan_is_scoped_and_runner_has_no_retry_or_market_dispatch():
    root = Path(__file__).resolve().parents[2]
    run = root / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-r2-20261016T055915Z"
    plan = json.loads((run / "r2_plan.json").read_text(encoding="utf-8"))
    assert plan["limits"] == {"daily_max": 1, "archive_index_max": 4, "archive_detail_max": 1, "total_max": 6}
    assert all(plan[key] is False for key in ("P01_P18_execution_allowed", "B01_B05_execution_allowed",
        "TWSE_T86_execution_allowed", "i3_resolver_modification_allowed", "a6_market_live_authority_consumption_allowed"))
    runner = (root / "scripts/run_phase_l_l3_a6_p0_r2_dgpa_closure_authority.py").read_text(encoding="utf-8")
    assert "time.sleep(" not in runner
    assert "retry(" not in runner.casefold()
    assert 'get("market"' not in runner
    assert "--execute-authorized-r2" in runner
