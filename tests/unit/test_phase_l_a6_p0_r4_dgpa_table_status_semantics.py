import pytest

from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import (
    daily_candidate_diagnostics,
    parse_daily_status,
    table_semantic_diagnostics,
)


FETCHED = "2026-10-16T13:00:00+08:00"
SUBJECT = "<div class='status-title'><span>115年10月16日</span><span>天然災害停止上班及上課情形</span></div>"
PROVENANCE = "<p>更新時間：115年10月16日 12:30</p><p>行政院人事行政總處</p>"
HEADER = "<tr><th>縣市名稱</th><th>是否停止上班上課情形</th></tr>"


def _page(table_rows: str) -> bytes:
    return ("<html><body>" + SUBJECT + PROVENANCE + "<table>" + HEADER + table_rows +
            "</table></body></html>").encode("utf-8")


def _parse(table_rows: str):
    return parse_daily_status(_page(table_rows), content_type="text/html; charset=utf-8", fetched_at=FETCHED)


def test_r3_header_and_no_notice_are_not_conflicting_status_facts():
    fact = _parse("<tr><td colspan='2'>無停班停課訊息。</td></tr>")
    assert fact["status_semantics"] == "NO_CLOSURE_NOTICE"
    diagnostics = fact["table_semantic_diagnostics"]
    assert diagnostics["row_count"] == 2
    assert diagnostics["schema_header_row_count"] == 1
    assert diagnostics["no_notice_row_count"] == 1
    assert diagnostics["rows"][0]["classification"] == "TABLE_SCHEMA_HEADER"
    assert diagnostics["rows"][1]["classification"] == "NO_NOTICE_ROW"


def test_header_plus_taipei_normal_row_is_adjudicated_from_td_status_cell():
    fact = _parse("<tr><td>臺北市</td><td>照常上班、照常上課</td></tr>")
    assert fact["status_semantics"] == "TAIPEI_NORMAL"
    rows = fact["table_semantic_diagnostics"]["rows"]
    assert rows[0]["classification"] == "TABLE_SCHEMA_HEADER"
    assert rows[1]["classification"] == "LOCALITY_NORMAL_STATUS"


def test_header_plus_taipei_morning_closure_is_adjudicated():
    fact = _parse("<tr><td>臺北市</td><td>上午停止上班、停止上課</td></tr>")
    assert fact["status_semantics"] == "TAIPEI_MORNING_CLOSURE"
    assert fact["closure_event"]["closure_scope"] == "morning"


def test_no_notice_and_actual_locality_closure_remain_conflicting():
    with pytest.raises(ValueError, match="dgpa_daily_status_conflict"):
        _parse("<tr><td colspan='2'>無停班停課訊息</td></tr>"
               "<tr><td>臺北市</td><td>上午停止上班上課</td></tr>")


def test_no_notice_conflicts_with_affirmative_closure_even_if_day_part_is_unresolved():
    with pytest.raises(ValueError, match="dgpa_daily_status_conflict"):
        _parse("<tr><td colspan='2'>無停班停課訊息</td></tr>"
               "<tr><td>臺北市</td><td>今天停止上班、停止上課</td></tr>")


@pytest.mark.parametrize("label", [
    "是否停止上班上課情形",
    "停止上班上課查詢",
    "停止上班及上課資訊",
    "天然災害停止上班上課說明",
])
def test_schema_and_helper_labels_are_never_closure_facts(label):
    body = _page(f"<tr><th colspan='2'>{label}</th></tr><tr><td colspan='2'>無停班停課訊息</td></tr>")
    fact = parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert fact["status_semantics"] == "NO_CLOSURE_NOTICE"
    diagnostics = table_semantic_diagnostics(body, "text/html; charset=utf-8")
    assert all(row["classification"] != "LOCALITY_CLOSURE_STATUS" for row in diagnostics["rows"])


def test_actual_taipei_normal_and_closure_rows_remain_a_true_conflict():
    with pytest.raises(ValueError, match="dgpa_daily_semantic_conflict"):
        _parse("<tr><td>臺北市</td><td>照常上班上課</td></tr>"
               "<tr><td>台北市</td><td>上午停止上班上課</td></tr>")


def test_r3_th_subject_candidate_is_schema_not_status_subject():
    body = _page("<tr><td colspan='2'>無停班停課訊息</td></tr>")
    diagnostics = daily_candidate_diagnostics(body, "text/html; charset=utf-8")
    assert diagnostics["raw_subject_match_count"] >= 1
    assert all(candidate["tag"] != "th" for candidate in diagnostics["candidates"])


def test_non_schema_th_subject_remains_eligible_semantic_subject():
    body = ("<html><body><table><tr><th colspan='2'>115年10月16日 天然災害停止上班及上課情形</th></tr>"
            "<tr><td colspan='2'>無停班停課訊息</td></tr></table>" + PROVENANCE + "</body></html>").encode()
    fact = parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    assert fact["status_semantics"] == "NO_CLOSURE_NOTICE"
    assert fact["subject_candidate_diagnostics"]["canonical_candidate_count"] == 1


def test_r3_large_ancestor_presentation_container_is_collapsed():
    body = ("<html><body><div><div class='subject'>115年10月16日 天然災害停止上班及上課情形</div>"
            "更新時間：115年10月16日 12:30 資料來源：各縣市政府 縣市名稱是否停止上班上課情形 "
            "無停班停課訊息</div><p>行政院人事行政總處</p></body></html>").encode()
    fact = parse_daily_status(body, content_type="text/html; charset=utf-8", fetched_at=FETCHED)
    diagnostics = fact["subject_candidate_diagnostics"]
    assert diagnostics["canonical_candidate_count"] == 1
    assert diagnostics["semantic_candidate_count"] == 1
    assert any(candidate.get("excluded_container_reason") == "ANCESTOR_PRESENTATION_CONTAINER"
               for candidate in diagnostics["candidates"])


def test_table_diagnostics_are_bounded_and_preserve_cell_roles():
    diagnostics = table_semantic_diagnostics(_page("<tr><td>臺北市</td><td>照常上班上課</td></tr>"))
    header, status = diagnostics["rows"]
    assert header["cell_tags"] == ["th", "th"]
    assert header["classification"] == "TABLE_SCHEMA_HEADER"
    assert status["cell_tags"] == ["td", "td"]
    assert status["locality"] == "臺北市"
    assert all(len(value) <= 200 for row in diagnostics["rows"] for value in row["normalized_cell_texts"])


def test_r4_request_budget_is_one_daily_four_index_one_detail_six_total():
    from scripts.phase_l_a6_p0_r1_dgpa_closure_authority import R4RequestBudget

    budget = R4RequestBudget()
    budget.reserve("daily")
    with pytest.raises(ValueError, match="request_budget_exceeded"):
        budget.reserve("daily")
    for _ in range(4):
        budget.reserve("index")
    with pytest.raises(ValueError, match="request_budget_exceeded"):
        budget.reserve("index")
    budget.reserve("detail")
    assert budget.counts() == {"daily": 1, "archive_index": 4, "archive_detail": 1, "total": 6}


def test_r4_source_drift_classification_requires_mutually_exclusive_status_facts():
    from scripts.run_phase_l_l3_a6_p0_r4_dgpa_table_status_observation import classify_daily_failure

    assert classify_daily_failure("dgpa_daily_status_conflict", {
        "page_status_signals": ["NO_CLOSURE_NOTICE"], "candidates": []
    }) == "R4_PARSER_CONTRACT_INSUFFICIENT"
    assert classify_daily_failure("dgpa_daily_status_conflict", {
        "page_status_signals": ["NO_CLOSURE_NOTICE", "TAIPEI_MORNING_CLOSURE"], "candidates": []
    }) == "DGPA_SOURCE_DRIFT_OBSERVED"


def test_conflict_diagnostics_distinguish_header_schema_from_locality_fact():
    body = _page("<tr><td colspan='2'>無停班停課訊息</td></tr>"
                 "<tr><td>臺北市</td><td>上午停止上班上課</td></tr>")
    diagnostics = daily_candidate_diagnostics(body, "text/html; charset=utf-8")
    rows = diagnostics["table_semantic_diagnostics"]["rows"]
    assert rows[0]["classification"] == "TABLE_SCHEMA_HEADER"
    assert rows[2]["classification"] == "LOCALITY_CLOSURE_STATUS"
    assert diagnostics["page_status_signals"] == ["NO_CLOSURE_NOTICE", "TAIPEI_MORNING_CLOSURE"]


def test_r4_runner_has_separate_authority_and_bounded_no_retry_dispatch():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    runner = (root / "scripts/run_phase_l_l3_a6_p0_r4_dgpa_table_status_observation.py").read_text(encoding="utf-8")
    assert "--execute-authorized-r4" in runner
    assert '"daily_max": 1' in runner
    assert '"archive_index_max": 4' in runner
    assert '"archive_detail_max": 1' in runner
    assert '"total_max": 6' in runner
    assert "time.sleep(" not in runner
    assert "retry(" not in runner.casefold()
    assert '"table_semantic_diagnostics.json"' in runner
    assert "execute_authorized_r4" in runner
    assert "P01_P18_performed\": False" in runner
    assert "a6_market_authority_consumed\": False" in runner
