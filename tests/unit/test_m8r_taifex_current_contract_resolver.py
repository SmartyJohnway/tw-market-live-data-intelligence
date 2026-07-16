from scripts.m8r_derivatives_conversational_intent import parse_derivatives_intent
from scripts.m8r_taifex_current_contract_resolver import FixtureUniverseProvider, nearest_strikes, resolve_current_contracts
from scripts.m8r_production_source_adapters import map_taifex_mis_detail_reason

U1 = {"contracts": [
    {"instrument_type":"future","product":"TX","expiry":"202608","contract_type":"monthly","session":"regular"},
    {"instrument_type":"option","product":"TXO","expiry":"202607W4","contract_type":"weekly","session":"regular","strike":"44900","call_put":"C"},
    {"instrument_type":"option","product":"TXO","expiry":"202607W4","contract_type":"weekly","session":"regular","strike":"44900","call_put":"P"},
    {"instrument_type":"option","product":"TXO","expiry":"202608","contract_type":"monthly","session":"regular","strike":"45000","call_put":"C"},
    {"instrument_type":"option","product":"TXO","expiry":"202608","contract_type":"monthly","session":"regular","strike":"45000","call_put":"P"},
]}
U2 = {"contracts": [
    {"instrument_type":"option","product":"TXO","expiry":"202608","contract_type":"monthly","session":"regular","strike":"45100","call_put":"C"},
    {"instrument_type":"option","product":"TXO","expiry":"202608","contract_type":"monthly","session":"regular","strike":"45100","call_put":"P"},
]}


def test_current_future_resolution():
    r = resolve_current_contracts(parse_derivatives_intent("現在台指期怎麼樣？"), FixtureUniverseProvider([U1]))
    t = r["resolved_exact_targets"][0]
    assert t["product"] == "TX"
    assert t["contract_type"] == "monthly"
    assert t["resolved_identity"]["expiry"]["authority"] == "current_contract_resolution_policy"


def test_option_current_defaults_to_nearest_executable_monthly_both():
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), FixtureUniverseProvider([U1], "45000"))
    assert r["discovered_universe_summary"]["selected_contract_type"] == "monthly"
    assert {t["call_put"] for t in r["resolved_exact_targets"]} == {"C", "P"}
    assert len(r["resolved_exact_targets"]) == 2


def test_monthly_and_weekly_preferences():
    m = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權近月月選 call 跟 put 怎麼樣？"), FixtureUniverseProvider([U1]))
    w = resolve_current_contracts(parse_derivatives_intent("現在最近到期的台指週選怎麼樣？"), FixtureUniverseProvider([U1]))
    assert m["discovered_universe_summary"]["selected_contract_type"] == "monthly"
    assert w["discovered_universe_summary"]["selected_contract_type"] == "weekly"


def test_explicit_strike_nearest_listed_and_no_full_chain_retention():
    r = resolve_current_contracts(parse_derivatives_intent("看一下台指選擇權四萬五附近的 call 跟 put"), FixtureUniverseProvider([U1]))
    assert {t["strike"] for t in r["resolved_exact_targets"]} == {"45000"}
    assert r["raw_payload_retained"] is False
    assert len(r["resolved_exact_targets"]) <= 6


def test_nearest_listed_strike_tie_selects_both():
    assert nearest_strikes(["44900", "45100"], "45000") == ["44900", "45100"]


def test_one_bounded_conversational_reresolution():
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), FixtureUniverseProvider([U1, U2], "45100", stale_first=True))
    assert r["reresolution_count"] == 1
    assert r["discovered_universe_summary"]["selected_expiry"] == "202608"


def test_exact_mode_no_fallback_when_stale():
    r = resolve_current_contracts(parse_derivatives_intent("TXO 202607 40000 C monthly"), FixtureUniverseProvider([U1]))
    assert r["resolution_status"] == "exact_contract_unavailable"
    assert r["reresolution_count"] == 0


def test_lower_level_mis_reason_mapping():
    assert map_taifex_mis_detail_reason("requested_month_not_available") == "source_identity_scope_unavailable"
    assert map_taifex_mis_detail_reason("option_exact_identity_not_unique") == "source_identity_not_unique"
    assert map_taifex_mis_detail_reason("runtime_symbol_mismatch") == "source_identity_mismatch"
    assert map_taifex_mis_detail_reason("weird") == "source_payload_invalid"
