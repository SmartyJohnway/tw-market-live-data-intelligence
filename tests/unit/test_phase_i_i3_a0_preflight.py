"""Offline mechanics only; hypothetical TPEx mapping is NOT source authority."""
import ast
import copy
import hashlib
import json
import pytest
import scripts.run_phase_i_i3_a0_preflight as p

FIXTURES = p.ROOT / "tests/fixtures/phase_i_i3_a0"


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("external network forbidden")
    monkeypatch.setattr("socket.socket.connect", deny)
    monkeypatch.setattr("socket.create_connection", deny)
    monkeypatch.setattr(p, "fixed_get", deny)


def payload(market):
    name = "twse_synthetic.json" if market == "TWSE" else "tpex_synthetic_hypothesis_only.json"
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def hypothetical_tpex():
    m = copy.deepcopy(p.load_mapping()["markets"]["TPEX"])
    # Explicit test hypothesis, not an adjudication or a formal authority.
    m["required_common_core"]["dealer_total"]["sell_shares"] = ["Dealers-TotalSell"]
    return m


@pytest.mark.parametrize("value", ["-", "NULL", "", "1.5", "NaN", True, "12,34", "1,,000", 1.5])
def test_missing_invalid_not_zero(value):
    with pytest.raises(ValueError):
        p.numeric(value)


def test_signed_shares_and_dates():
    assert p.numeric("-1,234") == -1234
    assert p.numeric("0") == 0
    assert p.official_date("1150930", "ROC_YYYMMDD") == "2026-09-30"
    assert p.official_date("20260930", "Gregorian_YYYYMMDD") == "2026-09-30"


@pytest.mark.parametrize("value,encoding", [("1150931", "ROC_YYYMMDD"), ("20260230", "Gregorian_YYYYMMDD"),
                                           ("1150930", "Gregorian_YYYYMMDD")])
def test_invalid_dates(value, encoding):
    with pytest.raises(ValueError):
        p.official_date(value, encoding)


def test_wrong_root_and_row_width_fail():
    with pytest.raises(ValueError):
        p.unpack("TWSE", {"fields": ["a"], "data": [[]]})
    with pytest.raises(ValueError):
        p.unpack("TPEX", {})


@pytest.mark.parametrize("market", ["TWSE", "TPEX"])
def test_synthetic_engine_mechanics_only(market):
    m = p.load_mapping()["markets"][market] if market == "TWSE" else hypothetical_tpex()
    result = p.analyze_market(market, payload(market), m)
    assert result["status"] == "PASS"
    assert result["exact_matches"] == 1 and result["row_count"] == 2
    assert result["selected_observation"]["trade_date"] == "2026-09-30"
    assert result["selected_observation"]["unit"] == "share"
    assert all(c["rows_passed"] == 2 and c["rows_failed"] == 0 for n, c in result["arithmetic"].items()
               if n != "dealer_component_net")
    if market == "TPEX":
        c = result["arithmetic"]["dealer_component_net"]
        assert c["status"] == p.NOT_APPLICABLE
        assert c["rows_checked"] == c["rows_failed"] == c["missing_field_rows"] == 0
    else:
        assert result["arithmetic"]["dealer_component_net"]["rows_passed"] == 2


def test_formal_full_path_blocked_not_synthetic_pass(monkeypatch):
    from pathlib import Path
    twse, tpex, authority = payload("TWSE"), payload("TPEX"), p.load_mapping()
    monkeypatch.setattr(Path, "read_bytes", lambda *args: pytest.fail("pure analyzer read filesystem"))
    with pytest.raises(ValueError, match="mapping_unresolved"):
        p.analyze_acquired_payloads(twse, tpex, authority)


def test_hypothetical_mapping_cannot_become_authority():
    forged = copy.deepcopy(p.load_mapping())
    forged["markets"]["TPEX"] = hypothetical_tpex()
    forged["mapping_status"] = "RESOLVED"
    with pytest.raises(ValueError, match="unreviewed_mapping_authority"):
        p.analyze_acquired_payloads(payload("TWSE"), payload("TPEX"), forged)


@pytest.mark.parametrize("kind", ["absent", "duplicate", "wrong_field", "name_only"])
def test_exact_binding_no_name_fallback(kind):
    rows = payload("TPEX")
    if kind == "absent":
        rows[0]["SecuritiesCompanyCode"] = "9999"
    elif kind == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif kind == "wrong_field":
        for row in rows:
            row["wrong_code"] = row.pop("SecuritiesCompanyCode")
    else:
        rows[0]["CompanyName"] = "5347"
        rows[0]["SecuritiesCompanyCode"] = "9999"
    with pytest.raises(ValueError):
        p.analyze_market("TPEX", rows, hypothetical_tpex())


def test_multiple_dates_rejected():
    rows = payload("TPEX")
    rows[1]["Date"] = "1150929"
    with pytest.raises(ValueError, match="multiple_source_dates"):
        p.analyze_market("TPEX", rows, hypothetical_tpex())


@pytest.mark.parametrize("kind", ["missing", "blank", "dash", "decimal", "boolean", "bad_comma"])
def test_every_row_required_numeric_validation(kind):
    rows = payload("TPEX")
    key = "SecuritiesInvestmentTrustCompanies-TotalBuy"
    if kind == "missing":
        del rows[1][key]
    else:
        rows[1][key] = {"blank": "", "dash": "-", "decimal": "2.5", "boolean": True, "bad_comma": "12,34"}[kind]
    with pytest.raises((KeyError, ValueError)):
        p.analyze_market("TPEX", rows, hypothetical_tpex())


@pytest.mark.parametrize("group", [*p.CORE, "institutional_total_net_shares"])
def test_whole_dataset_arithmetic_mismatch(group):
    m = hypothetical_tpex()
    rows = payload("TPEX")
    spec = m["required_common_core"][group]
    key = spec[0] if isinstance(spec, list) else spec["net_shares"][0]
    rows[1][key] = str(p.numeric(rows[1][key]) + 1)
    result = p.analyze_market("TPEX", rows, m)
    check = "institutional_total_net" if group == "institutional_total_net_shares" else group
    assert result["status"] == "FAIL"
    assert result["arithmetic"][check]["rows_failed"] == 1


def test_twse_conditional_component_mismatch():
    body = payload("TWSE")
    m = p.load_mapping()["markets"]["TWSE"]
    key = m["source_native_optional"]["dealer_proprietary"]["net_shares"][0]
    body["data"][1][body["fields"].index(key)] = "21"
    result = p.analyze_market("TWSE", body, m)
    assert result["arithmetic"]["dealer_component_net"]["status"] == "FAIL"


def test_missing_optional_split_not_required():
    body = payload("TWSE")
    m = p.load_mapping()["markets"]["TWSE"]
    key = m["source_native_optional"]["dealer_proprietary"]["net_shares"][0]
    index = body["fields"].index(key)
    body["fields"].pop(index)
    for row in body["data"]:
        row.pop(index)
    result = p.analyze_market("TWSE", body, m)
    assert result["status"] == "PASS"
    assert result["arithmetic"]["dealer_component_net"]["status"] == p.NOT_APPLICABLE


def test_field_keys_not_trimmed():
    rows = payload("TPEX")
    key = " Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Total Sell"
    for row in rows:
        row[key.strip()] = row.pop(key)
    with pytest.raises(KeyError):
        p.analyze_market("TPEX", rows, hypothetical_tpex())


def test_mapping_path_hash_and_structure_fail_closed(tmp_path, monkeypatch):
    arbitrary = tmp_path / "mapping.json"
    arbitrary.write_bytes(p.DEFAULT_MAPPING_AUTHORITY.read_bytes())
    with pytest.raises(ValueError, match="unreviewed_mapping_path"):
        p.load_mapping(arbitrary)
    monkeypatch.setattr(p, "MAPPING_SHA", "0" * 64)
    with pytest.raises(ValueError, match="unreviewed_mapping_hash"):
        p.load_mapping()


@pytest.mark.parametrize("corruption", ["market", "duplicate", "date", "scope", "optional"])
def test_mapping_validation(corruption):
    a = p.load_mapping()
    if corruption == "market":
        a["markets"]["OTHER"] = a["markets"]["TPEX"]
    elif corruption == "duplicate":
        g = a["markets"]["TWSE"]["required_common_core"]
        g["investment_trust"]["buy_shares"] = g["investment_trust"]["sell_shares"]
    elif corruption == "date":
        a["markets"]["TPEX"]["date_field"] = "guessed_date"
    elif corruption == "scope":
        a["authority_scope"] = "PRODUCTION"
    else:
        a["markets"]["TPEX"]["source_native_optional"] = None
    with pytest.raises(ValueError):
        p.validate_mapping(a)


def test_current_hold_record_and_runtime_containment():
    from scripts.validate_phase_i_i3_a0_preflight import validate
    assert hashlib.sha256((p.ROOT / p.RECORD).read_bytes()).hexdigest() == p.HISTORICAL_SHA
    validate()


def test_go_cannot_be_claimed_from_incomplete_probe():
    from scripts.validate_phase_i_i3_a0_preflight import validate
    r = json.loads((p.ROOT / p.RECORD).read_text(encoding="utf-8"))
    r["status"] = "GO_PASS"
    with pytest.raises(AssertionError):
        validate(r)


def test_old_authority_and_p0_cli_cannot_rearm():
    with pytest.raises(ValueError, match="fresh_a0_rearm"):
        p.run(p.AUTHORITY, p.load_mapping())
    with pytest.raises(ValueError, match="fresh_a0_rearm"):
        p.main(["--owner-authorization-reference", p.AUTHORITY])
    with pytest.raises(ValueError, match="offline_fixture_paths"):
        p.main([])


def test_no_input_network_subprocess_dependency():
    tree = ast.parse(Path_source())
    forbidden = {"input", "stdin", "subprocess", "urllib", "requests"}
    assert not any(isinstance(node, ast.Name) and node.id in forbidden for node in ast.walk(tree))
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) and
                   any(alias.name.split(".")[0] in forbidden for alias in node.names) for node in ast.walk(tree))


def Path_source():
    return (p.ROOT / "scripts/run_phase_i_i3_a0_preflight.py").read_text(encoding="utf-8")


def test_contained_summary_no_raw_body(tmp_path):
    body = payload("TWSE")
    result = {"sources": {"TWSE": p.analyze_market("TWSE", body, p.load_mapping()["markets"]["TWSE"])},
              "status": "PASS", "trade_date_symmetry": "same",
              "per_target_network_request_required": False,
              "raw_payload_persistence": "NONE", "market_network_calls": 0}
    p.write_analysis(tmp_path, "attempt_2_synthetic_summary.json", result)
    saved = (tmp_path / "attempt_2_synthetic_summary.json").read_text(encoding="utf-8")
    assert '"data"' not in saved and '"fields"' not in saved
    assert json.dumps(body, ensure_ascii=False) not in saved
    with pytest.raises(ValueError, match="historical_attempt_immutable"):
        p.write_analysis(tmp_path, p.RECORD, result)
    with pytest.raises(Exception):
        p.write_analysis(tmp_path, "../outside.json", result)
    with pytest.raises(ValueError, match="unreviewed_output_fields"):
        p.write_analysis(tmp_path, "raw.json", {"raw_body": body})


@pytest.mark.parametrize("body", [b"\xff", b"{", b'{"x":1,"x":2}', b" " * (p.MAX_BYTES + 1)],
                         ids=["invalid_utf8", "invalid_json", "duplicate_json_key", "oversize"])
def test_bad_payload(body):
    with pytest.raises((ValueError, UnicodeError)):
        p.decode_payload(body)


def test_nested_raw_summary_rejected(tmp_path):
    source = p.analyze_market("TWSE", payload("TWSE"), p.load_mapping()["markets"]["TWSE"])
    source["raw_body"] = payload("TWSE")
    with pytest.raises(ValueError, match="unreviewed_source_summary"):
        p.write_analysis(tmp_path, "nested_raw.json", {"sources": {"TWSE": source}, "status": "PASS",
            "trade_date_symmetry": "same", "per_target_network_request_required": False,
            "raw_payload_persistence": "NONE", "market_network_calls": 0})


def test_mapping_validator():
    from scripts.validate_phase_i_i3_a0_mapping import validate
    assert validate()["mapping_status"] == "UNRESOLVED"


def test_p0_validator_cannot_claim_pass_or_rearm():
    from scripts.validate_phase_i_i3_a0_p0 import validate, RECORD
    validate()
    record = json.loads((p.ROOT / RECORD).read_text(encoding="utf-8"))
    record["final_decision"] = "OFFLINE_HARNESS_CLOSURE_PASS"
    record["fresh_a0_rearm_ready"] = True
    with pytest.raises(AssertionError):
        validate(record)
