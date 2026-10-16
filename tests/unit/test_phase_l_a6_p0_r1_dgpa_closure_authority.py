from datetime import datetime
import json
from pathlib import Path

import pytest

from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import (
    RequestBudget, adjudicate_archive_window, parse_archive_index, parse_daily_status,
    parse_detail_status, resolve_only_with_complete_authority, validate_official_url,
)
from scripts.phase_i_i3_execution_date import resolve_i3_twse_source_trade_date
from scripts.phase_l_a6_p0_authority import normalized_calendar_sha256

FETCHED = "2026-10-16T12:00:00+08:00"
DAILY = """<html><h1>115年10月16日 停止上班上課情形</h1>
<p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p>
<p>無停班停課訊息</p></html>""".encode()


def test_daily_exact_date_and_explicit_negative():
    fact = parse_daily_status(DAILY, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert fact["target_date"] == "2026-10-16"
    assert fact["status_kind"] == "explicit_no_notice"
    assert fact["page_update_timestamp"] == "115年10月16日 11:45"
    assert fact["closure_event"] is None


def test_daily_wrong_date_and_missing_status_fail_closed():
    wrong = DAILY.replace("10月16日".encode(), "10月15日".encode())
    with pytest.raises(ValueError, match="displayed_date_mismatch"):
        parse_daily_status(wrong, content_type="text/html", fetched_at=FETCHED)
    missing = b"<h1>115\xe5\xb9\xb410\xe6\x9c\x8816\xe6\x97\xa5</h1><p>\xe4\xba\xba\xe4\xba\x8b\xe8\xa1\x8c\xe6\x94\xbf\xe7\xb8\xbd\xe8\x99\x95</p>"
    with pytest.raises(ValueError, match="status_missing"):
        parse_daily_status(missing, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    with pytest.raises(ValueError, match="fetch_before_evaluation"):
        parse_daily_status(DAILY, content_type="text/html; charset=utf-8", fetched_at="2026-10-16T10:00:00+08:00")


def test_invalid_utf8_fails_closed():
    with pytest.raises(ValueError, match="encoding_invalid"):
        parse_daily_status(DAILY + b"\xff", content_type="text/html; charset=utf-8", fetched_at=FETCHED)


@pytest.mark.parametrize(("status", "scope"), [("上午停止上班上課", "morning"), ("全天停止上班上課", "full_day"), ("下午停止上班上課", "afternoon")])
def test_daily_taipei_closure_is_mapped(status, scope):
    body = f"<h1>115年10月16日 停止上班上課情形</h1><p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p><table><tr><td>臺北市</td><td>{status}</td></tr></table>".encode()
    fact = parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert fact["closure_event"]["closure_scope"] == scope


def _archive_page(rows):
    return ("<h1>歷次天然災害停止上班上課訊息</h1><table>" + rows + "</table>").encode()


def test_archive_roc_date_and_detail_url():
    body = _archive_page('<tr><td>115/10/16</td><td><a href="/information?pid=123&uid=374">115年10月15日天然災害停止辦公及上課情形</a></td></tr>')
    items = parse_archive_index(body, content_type="text/html; charset=utf-8", base_url="https://www.dgpa.gov.tw/informationlist?uid=374&page=1")
    assert items[0]["target_event_date"] == "2026-10-15"
    assert items[0]["archive_publication_date"] == "2026-10-16"
    assert items[0]["detail_url"] == "https://www.dgpa.gov.tw/information?pid=123&uid=374"


def test_archive_window_crossing_target_proves_scoped_negative():
    def item(day, pid):
        return {"target_event_date": day, "detail_url": f"https://www.dgpa.gov.tw/information?pid={pid}&uid=374"}
    result = adjudicate_archive_window([{"page": 1, "items": [item("2026-10-17", 1), item("2026-10-14", 2)]}], "2026-10-15")
    assert result["historical_negative_evidence"] is True
    assert result["coverage_dates"] == ["2026-10-17", "2026-10-14"]


def test_archive_page_sequence_can_continue_and_target_requires_detail():
    def item(day, pid):
        return {"target_event_date": day, "detail_url": f"https://www.dgpa.gov.tw/information?pid={pid}&uid=374"}
    result = adjudicate_archive_window([
        {"page": 1, "items": [item("2026-10-18", 1), item("2026-10-16", 2)]},
        {"page": 2, "items": [item("2026-10-15", 3), item("2026-10-13", 4)]},
    ], "2026-10-15")
    assert result["historical_archive_target_entry_present"] is True
    assert result["historical_negative_evidence"] is False
    assert result["matching_entries"][0]["detail_url"].endswith("pid=3&uid=374")
    not_crossed = adjudicate_archive_window([{ "page": 1, "items": [item("2026-10-18", 1)] }], "2026-10-15")
    assert not_crossed["historical_negative_evidence"] is False


def test_archive_order_gap_and_target_duplicate_conflict_fail_closed():
    def item(day, pid):
        return {"target_event_date": day, "detail_url": f"https://www.dgpa.gov.tw/information?pid={pid}&uid=374"}
    with pytest.raises(ValueError, match="order_unresolved"):
        adjudicate_archive_window([{"page": 1, "items": [item("2026-10-14", 1), item("2026-10-17", 2)]}], "2026-10-15")
    with pytest.raises(ValueError, match="pagination_gap"):
        adjudicate_archive_window([{"page": 2, "items": [item("2026-10-14", 1)]}], "2026-10-15")
    with pytest.raises(ValueError, match="duplicate_target_conflict"):
        adjudicate_archive_window([{"page": 1, "items": [item("2026-10-15", 1), item("2026-10-15", 2)]}], "2026-10-15")


def test_archive_target_detail_resolves_only_taipei():
    body = "<h1>115年10月15日天然災害停止辦公及上課情形</h1><table><tr><td>臺北市</td><td>上午停止上班上課</td></tr><tr><td>新北市</td><td>全天停止上班上課</td></tr></table>".encode()
    fact = parse_detail_status(body, content_type="text/html; charset=utf-8", target_date="2026-10-15")
    assert fact["closure_scope"] == "morning"
    assert fact["closure_event"]["area_name"] == "臺北市"


def test_request_budget_and_domain_are_bounded():
    budget = RequestBudget()
    for _ in range(2):
        budget.reserve("daily")
    with pytest.raises(ValueError, match="budget_exceeded"):
        budget.reserve("daily")
    for _ in range(6):
        budget.reserve("index")
    with pytest.raises(ValueError, match="budget_exceeded"):
        budget.reserve("index")
    with pytest.raises(ValueError, match="unapproved_domain"):
        validate_official_url("https://example.com/information?pid=1&uid=374")
    validate_official_url("https://www.dgpa.gov.tw/typh/daily/nds.html?uid=31")


def test_total_request_budget_is_ten():
    budget = RequestBudget()
    for _ in range(2): budget.reserve("daily")
    for _ in range(6): budget.reserve("index")
    for _ in range(2): budget.reserve("detail")
    assert budget.total == 10
    with pytest.raises(ValueError, match="budget_exceeded"):
        budget.reserve("detail")


def test_existing_i3_resolver_requires_completeness_and_derives_date_from_calendar():
    root = Path(__file__).resolve().parents[2]
    calendar_path = root / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z/twse_trading_calendar_2026.json"
    calendar = json.loads(calendar_path.read_text(encoding="utf-8"))
    assert normalized_calendar_sha256(calendar) == "28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8"
    with pytest.raises(ValueError, match="closure_coverage_unresolved"):
        resolve_i3_twse_source_trade_date(evaluation_time="2026-10-16T11:38:22+08:00", official_calendar=calendar,
            closure_events=[], calendar_authority_ref="calendar", closure_authority_ref="closure", closure_authority_complete=False)
    binding = resolve_i3_twse_source_trade_date(evaluation_time="2026-10-16T11:38:22+08:00", official_calendar=calendar,
        closure_events=[], calendar_authority_ref="calendar", closure_authority_ref="closure", closure_authority_complete=True)
    assert binding["resolved_source_trade_date"] == "2026-10-15"


def test_incomplete_authority_never_invokes_resolver():
    calls = []
    assert resolve_only_with_complete_authority(False, lambda **kw: calls.append(kw)) is None
    assert calls == []
