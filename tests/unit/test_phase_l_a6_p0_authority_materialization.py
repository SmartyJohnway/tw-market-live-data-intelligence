from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from scripts.phase_l_a6_p0_authority import (
    AcquisitionBudget, assess_closure_completeness, compare_calendar_snapshots,
    derive_resolver_coverage_dates, validate_2026_calendar,
)
from scripts.twse_trading_calendar import build_twse_trading_calendar_from_holiday_schedule


def _calendar():
    return build_twse_trading_calendar_from_holiday_schedule(
        year=2026, holiday_schedule_records=[], generated_at_utc="2026-10-16T00:00:00Z")


def test_p0_acquisition_ceiling_and_per_authority_caps():
    budget = AcquisitionBudget()
    for _ in range(3):
        budget.reserve("TWSE_HOLIDAY_SCHEDULE")
    for _ in range(3):
        budget.reserve("NCDR_DGPA_CLOSURE_CAP")
    assert (budget.calendar_count, budget.closure_count, budget.total) == (3, 3, 6)
    with pytest.raises(ValueError, match="p0_total_acquisition_limit_exceeded"):
        budget.check_total()
    with pytest.raises(ValueError, match="p0_calendar_acquisition_limit_exceeded"):
        budget.reserve("TWSE_HOLIDAY_SCHEDULE")
    with pytest.raises(ValueError, match="p0_closure_acquisition_limit_exceeded"):
        budget.reserve("NCDR_DGPA_CLOSURE_CAP")
    with pytest.raises(ValueError, match="p0_unapproved_source_authority"):
        budget.reserve("OTHER")


def test_calendar_artifact_full_year_contract_and_inspected_invalid_records():
    cal = _calendar()
    stats = validate_2026_calendar(cal)
    assert stats["date_count"] == 365
    assert stats["invalid_record_count"] == 0
    broken = dict(cal, invalid_records=[{"index": 0, "reason": "invalid"}])
    with pytest.raises(ValueError, match="calendar_invalid_records_present"):
        validate_2026_calendar(broken)
    broken = dict(cal, dates=cal["dates"][:-1])
    with pytest.raises(ValueError, match="calendar_2026_date_coverage_invalid"):
        validate_2026_calendar(broken)


def test_resolver_window_starts_today_and_reaches_prior_calendar_trading_day():
    cal = _calendar()
    moment = datetime(2026, 10, 16, 11, 38, tzinfo=ZoneInfo("Asia/Taipei"))
    dates = derive_resolver_coverage_dates(moment, cal)
    assert dates[0] == "2026-10-16"
    assert dates[-1] < dates[0]
    by_date = {x["date"]: x["is_trading_day"] for x in cal["dates"]}
    assert by_date[dates[-1]] is True


def test_calendar_snapshot_change_is_not_latest_wins():
    first = _calendar()
    second = json.loads(json.dumps(first))
    second["dates"][0]["is_trading_day"] = not second["dates"][0]["is_trading_day"]
    assert compare_calendar_snapshots(first, second) == "CALENDAR_AUTHORITY_SNAPSHOT_CHANGED"
    second = json.loads(json.dumps(first))
    second["generated_at_utc"] = "2026-10-17T00:00:00Z"
    assert compare_calendar_snapshots(first, second) == "NORMALIZED_SNAPSHOT_IDENTICAL"


@pytest.mark.parametrize("parsed", [
    {"closure_query_succeeded": True, "events": []},
    {"closure_query_succeeded": True, "events": [{"target_date": "2026-10-16", "area_name": "臺北市"}]},
])
def test_empty_or_repeated_feed_facts_do_not_prove_window_completeness(parsed):
    result = assess_closure_completeness(parsed, ["2026-10-16", "2026-10-15"])
    assert result["coverage_dates"] == ["2026-10-16", "2026-10-15"]
    assert result["closure_authority_complete"] is False
    assert "does not attest exhaustive historical coverage" in result["completeness_reason"]


def test_p0_scope_plan_forbids_a6_market_and_bootstrap_dispatch():
    root = Path(__file__).resolve().parents[2]
    plan_path = root / "docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z/p0_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["planned_logical_invocations"] == 0
    assert plan["market_source_recertification_authorized_here"] is False
    assert plan["P01_P18_execution_allowed"] is False
    assert plan["B01_B05_execution_allowed"] is False
    assert plan["calendar_max_acquisitions"] == 3
    assert plan["closure_max_acquisitions"] == 3
    assert plan["total_max_acquisitions"] == 6


def test_p0_runner_has_no_retry_sleep_or_non_p0_acquisition_seam():
    root = Path(__file__).resolve().parents[2]
    source = (root / "scripts/run_phase_l_l3_a6_p0_authority_materialization.py").read_text(encoding="utf-8")
    assert "time.sleep(" not in source
    assert "retry(" not in source.lower()
    assert "schedule(" not in source.lower()
    assert "scripts.m5k_common" not in source
    assert 'plan.get("P01_P18_execution_allowed") is not False' in source
    assert 'plan.get("B01_B05_execution_allowed") is not False' in source
    assert source.count("_load_production_calendar(evaluation") == 1
    assert source.count("fetch_and_parse_closure_feed(target_date=None, timeout=10)") == 1
