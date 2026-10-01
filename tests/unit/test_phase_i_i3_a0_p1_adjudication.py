"""P1 pure candidate-key adjudication tests with sockets denied."""
import json
import pytest
import scripts.run_phase_i_i3_a0_preflight as p

FIXTURES = p.ROOT / "tests/fixtures/phase_i_i3_a0"


def payload(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("external network forbidden")
    monkeypatch.setattr("socket.socket.connect", deny)
    monkeypatch.setattr("socket.create_connection", deny)


def test_p1_unique_candidate_a_and_ephemeral_projection(tmp_path):
    auth = p.load_adjudication_authority()
    fixtures = payload("dealer_sell_adjudication_scenarios.json")
    result = p.adjudicate_tpex_dealer_sell(fixtures["unique_candidate_a"], auth)
    assert result["selection_status"] == "RESOLVED"
    assert result["selected_candidate"] == "Dealers-TotalSell"
    assert all(s["rows_checked"] == s["rows_passed"] == 2 and s["rows_failed"] == s["missing_rows"] == 0
               for s in result["candidate_statistics"].values() if s["candidate"] == "Dealers-TotalSell")
    analysis = p.analyze_acquired_payloads(payload("twse_synthetic.json"), fixtures["unique_candidate_a"],
                                           p.load_mapping(), auth)
    assert analysis["status"] == "PASS"
    assert analysis["dealer_sell_adjudication"]["selected_candidate"] == "Dealers-TotalSell"
    assert analysis["sources"]["TPEX"]["selected_observation"]["common_core"]["dealer_total"]["sell_shares"] == 10
    p.write_analysis(tmp_path, "adjudication-summary.json", analysis)
    saved = (tmp_path / "adjudication-summary.json").read_bytes()
    assert b"candidate_statistics" in saved and b"selected_candidate" in saved
    assert json.dumps(fixtures["unique_candidate_a"], ensure_ascii=False).encode() not in saved
    # Analysis does not mutate the committed unresolved mapping object.
    assert p.load_mapping()["markets"]["TPEX"]["required_common_core"]["dealer_total"]["sell_shares"] is None


def test_p1_unique_candidate_b():
    rows = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_b"]
    result = p.adjudicate_tpex_dealer_sell(rows, p.load_adjudication_authority())
    assert result["selection_status"] == "RESOLVED"
    assert result["selected_candidate"] == "Dealers -TotalSell"


@pytest.mark.parametrize("scenario,status,selected", [
    ("both_candidates_valid", "AMBIGUOUS_ALIAS", None),
    ("neither_candidate_valid", "NO_MATCH", None),
    ("missing_candidate_fields", "MISSING_CANDIDATE_FIELD", None),
    ("malformed_integer", "NO_MATCH", None),
    ("zero_rows", "NO_MATCH", None),
])
def test_p1_hold_scenarios(scenario, status, selected):
    rows = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))[scenario]
    result = p.adjudicate_tpex_dealer_sell(rows, p.load_adjudication_authority())
    assert (result["selection_status"], result["selected_candidate"]) == (status, selected)


def test_p1_one_absent_candidate_field_blocks_otherwise_unique_selection():
    rows = payload("dealer_sell_adjudication_scenarios.json")["unique_candidate_a"]
    for row in rows:
        row.pop("Dealers -TotalSell")
    result = p.adjudicate_tpex_dealer_sell(rows, p.load_adjudication_authority())
    assert result["selection_status"] == "MISSING_CANDIDATE_FIELD"
    assert result["selected_candidate"] is None


def test_p1_partially_invalid_candidate_is_rejected():
    rows = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["one_candidate_row_mismatch"]
    result = p.adjudicate_tpex_dealer_sell(rows, p.load_adjudication_authority())
    assert result["selection_status"] == "RESOLVED"
    assert result["selected_candidate"] == "Dealers -TotalSell"
    bad = result["candidate_statistics"]["Dealers-TotalSell"]
    assert (bad["rows_checked"], bad["rows_passed"], bad["rows_failed"], bad["missing_rows"]) == (2, 1, 1, 0)
    assert bad["first_failure"] == "row_2:arithmetic_mismatch"


def test_p1_independent_institutional_total_gate():
    rows = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["institutional_total_mismatch"]
    result = p.adjudicate_tpex_dealer_sell(rows, p.load_adjudication_authority())
    assert result["candidate_statistics"]["Dealers-TotalSell"]["rows_failed"] == 0
    assert result["institutional_total_invariant"]["rows_failed"] == 1
    assert result["selection_status"] == "INSTITUTIONAL_TOTAL_MISMATCH"
    assert result["selected_candidate"] is None


def test_p1_candidate_order_does_not_affect_outcome():
    auth = p.load_adjudication_authority()
    rows = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
    first = p.adjudicate_tpex_dealer_sell(rows, auth)
    auth["candidate_sell_fields"].reverse()
    reversed_order = p.adjudicate_tpex_dealer_sell(rows, auth)
    assert first == reversed_order


def test_p1_arbitrary_candidate_or_semantic_injection_rejected():
    auth = p.load_adjudication_authority()
    rows = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
    auth["candidate_sell_fields"].append("Dealers-BetterSpelling")
    with pytest.raises(ValueError, match="unreviewed_adjudication_authority"):
        p.adjudicate_tpex_dealer_sell(rows, auth)


def test_p1_governance_validator_passes_under_network_denial():
    from scripts.validate_phase_i_i3_a0_p1 import validate
    record = json.loads((p.ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json").read_text(encoding="utf-8"))
    assert validate(record) is record


def test_p1_governance_validator_rejects_attempt_two_authority_drift():
    from scripts.validate_phase_i_i3_a0_p1 import validate
    record = json.loads((p.ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json").read_text(encoding="utf-8"))
    record["decision"]["fresh_attempt_2_authorized"] = True
    with pytest.raises(AssertionError):
        validate(record)
