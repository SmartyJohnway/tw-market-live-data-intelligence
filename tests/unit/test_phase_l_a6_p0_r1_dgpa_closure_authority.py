from datetime import datetime
import json
from pathlib import Path

import pytest

from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import (
    RequestBudget, R5RequestBudget, adjudicate_archive_window, archive_window_needs_cross_page_confirmation,
    parse_archive_index, parse_archive_index_with_diagnostics, parse_daily_status,
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


def test_daily_non_heading_semantic_region_supports_r1_dom_shape():
    fixture = Path(__file__).resolve().parents[1] / "fixtures/phase_l/dgpa_daily_20261016_non_heading.html"
    body = fixture.read_bytes()
    fact = parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert fact["target_date"] == "2026-10-16"
    assert fact["status_kind"] == "explicit_no_notice"


def test_daily_wrong_date_and_missing_status_fail_closed():
    wrong = DAILY.replace("10月16日".encode(), "10月15日".encode(), 1)
    with pytest.raises(ValueError, match="displayed_date_mismatch"):
        parse_daily_status(wrong, content_type="text/html", fetched_at=FETCHED)
    missing = "<h1>115年10月16日 天然災害停止上班及上課情形</h1><p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p>".encode()
    with pytest.raises(ValueError, match="status_missing"):
        parse_daily_status(missing, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    with pytest.raises(ValueError, match="fetch_before_evaluation"):
        parse_daily_status(DAILY, content_type="text/html; charset=utf-8", fetched_at="2026-10-16T10:00:00+08:00")


@pytest.mark.parametrize(("body", "reason"), [
    ("<html><p>行政院人事行政總處</p><p>更新時間：115年10月16日 11:45</p><p>無停班停課訊息</p></html>", "subject_missing"),
    ("<html><footer>115年10月16日</footer><p>天然災害停止上班及上課情形</p><p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>", "displayed_date_mismatch"),
    ("<html><div>115年10月15日</div><div>天然災害停止上班及上課情形</div><div>更新時間：115年10月16日 11:45</div><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>", "displayed_date_mismatch"),
    ("<html><div>115年10月16日</div><div>天然災害停止上班及上課情形</div><div>更新時間：115年10月15日 11:45</div><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>", "update_date_mismatch"),
    ("<html><h1>115年10月16日 天然災害停止上班及上課情形</h1><p>更新時間：115年10月16日 11:45</p><p>無停班停課訊息</p></html>", "provenance_missing"),
    ("<html><h1>115年10月16日 天然災害停止上班及上課情形</h1><p>行政院人事行政總處</p><p>無停班停課訊息</p></html>", "provenance_missing"),
    ("<html><h1>115年10月16日 天然災害停止上班及上課情形</h1><p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p></html>", "status_missing"),
    ("<html><h1>115年10月16日 天然災害停止上班及上課情形</h1><p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p><p>無停班停課訊息</p><table><tr><td>臺北市</td><td>上午停止上班上課</td></tr></table></html>", "status_conflict"),
])
def test_daily_semantic_gaps_and_conflicts_fail_closed(body, reason):
    with pytest.raises(ValueError, match=reason):
        parse_daily_status(body.encode(), content_type="text/html; charset=utf-8", fetched_at=FETCHED)


def test_daily_conflicting_status_region_dates_fail_closed():
    body = """<html><div><span>115年10月16日</span><span>115年10月15日</span>
      <span>天然災害停止上班及上課情形</span></div>
      <p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p>
      <p>無停班停課訊息</p></html>""".encode()
    with pytest.raises(ValueError, match="date_ambiguous"):
        parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)


def test_invalid_utf8_fails_closed():
    with pytest.raises(ValueError, match="encoding_invalid"):
        parse_daily_status(DAILY + b"\xff", content_type="text/html; charset=utf-8", fetched_at=FETCHED)


@pytest.mark.parametrize(("status", "scope"), [("上午停止上班上課", "morning"), ("全天停止上班上課", "full_day"), ("下午停止上班上課", "afternoon")])
def test_daily_taipei_closure_is_mapped(status, scope):
    body = f"<h1>115年10月16日 停止上班上課情形</h1><p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p><table><tr><td>臺北市</td><td>{status}</td></tr></table>".encode()
    fact = parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert fact["closure_event"]["closure_scope"] == scope


def test_daily_taipei_normal_work_is_explicitly_adjudicated():
    body = "<h1>115年10月16日 停止上班上課情形</h1><p>更新時間：115年10月16日 11:45</p><p>行政院人事行政總處</p><table><tr><td>臺北市</td><td>照常上班上課</td></tr></table>".encode()
    fact = parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert fact["status_kind"] == "county_rows_present"
    assert fact["closure_event"] is None


def _archive_page(rows):
    return ("<h1>歷次天然災害停止上班上課訊息</h1><table>" + rows + "</table>").encode()


def test_archive_roc_date_and_detail_url():
    body = _archive_page('<tr><td>115/10/16</td><td><a href="/information?pid=123&uid=374">115年10月15日天然災害停止辦公及上課情形</a></td></tr>')
    items = parse_archive_index(body, content_type="text/html; charset=utf-8", base_url="https://www.dgpa.gov.tw/informationlist?uid=374&page=1")
    assert items[0]["target_event_date"] == "2026-10-15"
    assert items[0]["archive_publication_date"] == "2026-10-16"
    assert items[0]["detail_url"] == "https://www.dgpa.gov.tw/information?pid=123&uid=374"
    assert items[0]["event_title"] == "115年10月15日天然災害停止辦公及上課情形"
    assert items[0]["publication_date_source"] == "same_item_structured_date_cell"


@pytest.mark.parametrize(("label", "publication", "event"), [
    ("115.07.20 115年7月19日天然災害停止辦公及上課情形", "2026-07-20", "2026-07-19"),
    ("115/07/20 115年7月20日天然災害停止上班及上課情形", "2026-07-20", "2026-07-20"),
    ("115-07-20 115年7月20日天然災害停止辦公及上課情形", "2026-07-20", "2026-07-20"),
])
def test_archive_combined_link_parses_publication_and_event_roles(label, publication, event):
    body = f'<h1>歷次天然災害停止上班上課訊息</h1><a href="/information?pid=123&uid=374">{label}</a>'.encode()
    items, diagnostics = parse_archive_index_with_diagnostics(body, content_type="text/html; charset=utf-8",
        base_url="https://www.dgpa.gov.tw/informationlist?uid=374&page=1")
    item = items[0]
    assert item["archive_publication_date"] == publication
    assert item["target_event_date"] == event
    assert item["event_title"].startswith("115年")
    assert item["source_item_text"] == label
    assert diagnostics["requested_page"] == 1
    assert diagnostics["items"][0]["parse_status"] == "PASS"


def test_archive_publication_prefix_does_not_make_event_title_ambiguous():
    body = _archive_page('<tr><td><a href="/information?pid=123&uid=374">115.07.20 115年7月19日天然災害停止辦公及上課情形</a></td></tr>')
    items = parse_archive_index(body, content_type="text/html; charset=utf-8",
        base_url="https://www.dgpa.gov.tw/informationlist?uid=374&page=1")
    assert items[0]["archive_publication_date"] == "2026-07-20"
    assert items[0]["target_event_date"] == "2026-07-19"


@pytest.mark.parametrize(("anchor", "row", "reason"), [
    ("115年7月19日天然災害停止辦公及上課情形", "", "publication_date_missing"),
    ("115.07.20 115年7月19日及115年7月18日天然災害停止辦公及上課情形", "", "event_date_ambiguous"),
    ("115.07.20 一般公告連結", "", "item_title_invalid"),
])
def test_archive_missing_or_ambiguous_item_roles_fail_closed_with_diagnostics(anchor, row, reason):
    body = f'<h1>歷次天然災害停止上班上課訊息</h1>{row}<a href="/information?pid=123&uid=374">{anchor}</a>'.encode()
    with pytest.raises(ValueError, match=reason) as error:
        parse_archive_index_with_diagnostics(body, content_type="text/html; charset=utf-8",
            base_url="https://www.dgpa.gov.tw/informationlist?uid=374&page=1")
    assert error.value.diagnostics["items"][0]["raw_item_excerpt"]
    assert error.value.diagnostics["items"][0]["parse_status"]


def test_archive_unrelated_page_date_does_not_supply_item_publication_date():
    body = '<h1>115.07.20 歷次天然災害停止上班上課訊息</h1><a href="/information?pid=123&uid=374">115年7月19日天然災害停止辦公及上課情形</a>'.encode()
    with pytest.raises(ValueError, match="publication_date_missing"):
        parse_archive_index(body, content_type="text/html; charset=utf-8",
            base_url="https://www.dgpa.gov.tw/informationlist?uid=374&page=1")


def test_archive_page_marker_must_match_requested_page():
    body = "<h1>歷次天然災害停止上班上課訊息</h1><p>第 2/10 頁</p><a href='/information?pid=123&uid=374'>115.07.20 115年7月19日天然災害停止辦公及上課情形</a>".encode()
    with pytest.raises(ValueError, match="page_identity_mismatch"):
        parse_archive_index(body, content_type="text/html; charset=utf-8",
            base_url="https://www.dgpa.gov.tw/informationlist?uid=374&page=1")


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


def test_archive_newest_page_older_than_target_requires_cross_page_confirmation():
    pages = [{"page": 1, "items": [{"target_event_date": "2026-10-14", "detail_url": "https://www.dgpa.gov.tw/information?pid=1&uid=374"}]}]
    assert archive_window_needs_cross_page_confirmation(pages, "2026-10-15") is True
    pages.append({"page": 2, "items": [{"target_event_date": "2026-10-13", "detail_url": "https://www.dgpa.gov.tw/information?pid=2&uid=374"}]})
    assert archive_window_needs_cross_page_confirmation(pages, "2026-10-15") is False


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


def test_r5_budget_prohibits_daily_and_caps_archive_dispatches():
    budget = R5RequestBudget()
    with pytest.raises(ValueError, match="budget_exceeded"):
        budget.reserve("daily")
    for _ in range(4):
        budget.reserve("index")
    budget.reserve("detail")
    assert budget.counts() == {"daily": 0, "archive_index": 4, "archive_detail": 1, "total": 5}
    with pytest.raises(ValueError, match="budget_exceeded"):
        budget.reserve("index")


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
