import pytest

from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import daily_candidate_diagnostics, parse_daily_status
from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import _DailyStatusError

FETCHED = "2026-10-16T13:00:00+08:00"


def _page(subjects: str, status: str = "無停班停課訊息") -> bytes:
    return ("<html><body>" + subjects +
        "<p>更新時間：115年10月16日 12:30</p><p>行政院人事行政總處</p>" + status + "</body></html>").encode("utf-8")


def _parse(subjects: str, status: str = "無停班停課訊息"):
    return parse_daily_status(_page(subjects, status), content_type="text/html; charset=utf-8", fetched_at=FETCHED)


@pytest.mark.parametrize("status,expected", [
    ("無停班停課訊息", "NO_CLOSURE_NOTICE"),
    ("<table><tr><td>臺北市</td><td>照常上班上課</td></tr></table>", "TAIPEI_NORMAL"),
])
def test_equivalent_duplicate_presentations_collapse(status, expected):
    subjects = ("<div><span>115年10月16日</span><span>天然災害停止上班及上課情形</span></div>"
                "<section><p>115年10月16日 天然災害停止上班及上課情形</p></section>")
    fact = _parse(subjects, status)
    diagnostics = fact["subject_candidate_diagnostics"]
    assert diagnostics["raw_subject_match_count"] >= 2
    assert diagnostics["semantic_candidate_count"] >= 2
    assert diagnostics["canonical_candidate_count"] == 1
    assert fact["status_semantics"] == expected


def test_nested_duplicate_semantic_text_collapses_to_one_canonical_candidate():
    subjects = ("<div><span>115年10月16日</span><div><strong>天然災害停止上班及上課情形</strong></div></div>"
                "<div class='mobile'><p>115年10月16日 天然災害停止上班及上課情形</p></div>")
    diagnostics = _parse(subjects)["subject_candidate_diagnostics"]
    assert diagnostics["canonical_candidate_count"] == 1


@pytest.mark.parametrize("subjects", [
    "<p>115年10月16日 天然災害停止上班及上課情形</p><p>115年10月15日 天然災害停止上班及上課情形</p>",
    "<div><span>115年10月16日</span><span>115年10月15日</span><span>天然災害停止上班及上課情形</span></div>",
])
def test_conflicting_bound_dates_fail_closed(subjects):
    with pytest.raises(ValueError, match="semantic_conflict|date_ambiguous"):
        _parse(subjects)


def test_no_notice_and_taipei_closure_are_conflicting_semantics():
    subjects = "<h1>115年10月16日 天然災害停止上班及上課情形</h1>"
    with pytest.raises(ValueError, match="status_conflict"):
        _parse(subjects, "無停班停課訊息<table><tr><td>臺北市</td><td>上午停止上班上課</td></tr></table>")


def test_nav_footer_script_and_archive_link_subjects_are_not_candidates():
    noise = ("<nav><p>115年10月16日 天然災害停止上班及上課情形</p></nav>"
             "<footer><p>115年10月16日 天然災害停止上班及上課情形</p></footer>"
             "<script>天然災害停止上班及上課情形</script>"
             "<a href='/information?pid=1&uid=374'>115年10月16日天然災害停止上班及上課情形</a>")
    subjects = noise + "<h1>115年10月16日 天然災害停止上班及上課情形</h1>"
    diagnostics = _parse(subjects)["subject_candidate_diagnostics"]
    assert diagnostics["canonical_candidate_count"] == 1
    assert all("版權" not in c["short_bounded_excerpt"] for c in diagnostics["candidates"])


def test_unbound_separate_subject_is_not_allowed_to_borrow_date():
    subjects = ("<p>115年10月16日 天然災害停止上班及上課情形</p>"
                "<aside>天然災害停止上班及上課情形</aside>")
    with pytest.raises(ValueError, match="semantic_ambiguity"):
        _parse(subjects)


def test_diagnostics_are_attached_to_semantic_conflict():
    subjects = ("<p>115年10月16日 天然災害停止上班及上課情形</p>"
                "<p>115年10月15日 天然災害停止上班及上課情形</p>")
    with pytest.raises(_DailyStatusError) as caught:
        _parse(subjects)
    assert caught.value.diagnostics["semantic_candidate_count"] == 2
    assert len(caught.value.diagnostics["candidates"]) == 2


def test_fallback_diagnostics_expose_mutually_exclusive_status_facts():
    body = _page("<h1>115年10月16日 天然災害停止上班及上課情形</h1>",
        "無停班停課訊息<table><tr><td>臺北市</td><td>上午停止上班上課</td></tr></table>")
    diagnostics = daily_candidate_diagnostics(body, "text/html; charset=utf-8")
    assert diagnostics["page_status_signals"] == ["NO_CLOSURE_NOTICE", "TAIPEI_MORNING_CLOSURE"]
    assert diagnostics["candidates"][0]["normalized_status_semantics"] == "CONFLICTING_PAGE_STATUS"


def test_r3_runner_is_one_daily_no_retry_and_same_host_bounded():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    runner = (root / "scripts/run_phase_l_l3_a6_p0_r3_dgpa_semantic_reobservation.py").read_text(encoding="utf-8")
    assert '"daily_max": 1' in runner
    assert '"archive_index_max": 4' in runner
    assert '"archive_detail_max": 1' in runner
    assert "time.sleep(" not in runner
    assert "retry(" not in runner.casefold()
    assert "--execute-authorized-r3" in runner
    assert '"subject_candidate_diagnostics.json"' in runner
