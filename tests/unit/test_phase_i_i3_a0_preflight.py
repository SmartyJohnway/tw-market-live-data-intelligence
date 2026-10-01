"""Research-only deterministic tests; never issue a market GET."""
import pytest
from scripts.run_phase_i_i3_a0_preflight import numeric, official_date, unpack, arithmetic, CORE


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs): raise AssertionError("external network forbidden")
    monkeypatch.setattr("socket.socket.connect", deny)
    monkeypatch.setattr("socket.create_connection", deny)


@pytest.mark.parametrize("value", ["-", "NULL", "", "1.5", "NaN", True])
def test_missing_invalid_not_zero(value):
    with pytest.raises(ValueError): numeric(value)


def test_signed_shares_and_dates():
    assert numeric("-1,234") == -1234
    assert numeric("0") == 0
    assert official_date("1150930") == official_date("20260930") == "2026-09-30"


def test_wrong_root_and_row_width_fail():
    with pytest.raises(ValueError): unpack("TWSE", {"fields": ["a"], "data": [[]]})
    with pytest.raises(ValueError): unpack("TPEX", {})


def test_whole_dataset_arithmetic_no_double_count():
    groups = {name: {"buy_shares": [name + "_buy"], "sell_shares": [name + "_sell"],
                     "net_shares": [name + "_net"]} for name in CORE + ["dealer_proprietary", "dealer_hedging"]}
    mapping = {"groups": groups, "total_net": ["total"]}
    row = {field: "0" for group in groups.values() for fields in group.values() for field in fields}
    row.update(total="5", foreign_and_mainland_excluding_foreign_dealer_buy="5",
               foreign_and_mainland_excluding_foreign_dealer_net="5")
    checks = arithmetic([row, row], mapping)
    assert all(check["rows_passed"] == 2 for check in checks.values())
    bad = dict(row, total="6")
    checks = arithmetic([row, bad], mapping)
    assert checks["institutional_total_net"]["rows_failed"] == 1
    assert checks["institutional_total_net"]["first_failure_reason"] == "arithmetic_inconsistency"


def test_current_hold_record_and_runtime_containment():
    from scripts.validate_phase_i_i3_a0_preflight import validate
    validate()


def test_go_cannot_be_claimed_from_incomplete_probe():
    import copy
    import json
    from scripts.run_phase_i_i3_a0_preflight import ROOT, RECORD
    from scripts.validate_phase_i_i3_a0_preflight import validate
    r = copy.deepcopy(json.loads((ROOT / RECORD).read_text(encoding="utf-8")))
    r["status"] = "GO_PASS"
    with pytest.raises(AssertionError): validate(r)


def test_missing_mapping_fails_before_io(monkeypatch):
    import scripts.run_phase_i_i3_a0_preflight as probe
    monkeypatch.setattr(probe, "preflight", lambda: pytest.fail("preflight reached"))
    monkeypatch.setattr(probe, "fixed_get", lambda *args: pytest.fail("transport reached"))
    with pytest.raises(ValueError, match="offline_mapping"):
        probe.run(probe.AUTHORITY, None)


def test_existing_record_latch_rejects_second_probe_before_io(monkeypatch):
    import scripts.run_phase_i_i3_a0_preflight as probe
    monkeypatch.setattr(probe, "preflight", lambda: ({}, {}))
    monkeypatch.setattr(probe, "fixed_get", lambda *args: pytest.fail("transport reached"))
    mapping = {market: {"code_field": "code", "date_field": "date", "total_net": ["total"],
                       "groups": {g: {} for g in CORE}} for market in probe.ENDPOINTS}
    from scripts.m8r_filesystem_safety import FilesystemSafetyError
    with pytest.raises(FilesystemSafetyError, match="atomic_replace_failed"):
        probe.run(probe.AUTHORITY, mapping)
