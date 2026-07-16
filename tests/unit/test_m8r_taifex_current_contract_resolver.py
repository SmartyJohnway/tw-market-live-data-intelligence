from scripts.m8r_derivatives_conversational_intent import parse_derivatives_intent
from scripts.m8r_taifex_current_contract_resolver import (
    CompositeReferenceUniverseProvider,
    FixtureUniverseProvider,
    nearest_strikes,
    resolve_current_contracts,
)
from scripts.m8r_production_source_adapters import map_taifex_mis_detail_reason

U1 = {"source_family":"TAIFEX_MIS", "discovered_at_utc":"2026-07-16T00:00:00Z", "contracts": [
    {"instrument_type":"future","product":"TX","expiry":"202608","contract_type":"monthly","session":"regular"},
    {"instrument_type":"option","product":"TXO","expiry":"202607W4","contract_type":"weekly","session":"regular","strike":"44900","call_put":"C"},
    {"instrument_type":"option","product":"TXO","expiry":"202607W4","contract_type":"weekly","session":"regular","strike":"44900","call_put":"P"},
    {"instrument_type":"option","product":"TXO","expiry":"202608","contract_type":"monthly","session":"regular","strike":"45000","call_put":"C"},
    {"instrument_type":"option","product":"TXO","expiry":"202608","contract_type":"monthly","session":"regular","strike":"45000","call_put":"P"},
]}
U2 = {"source_family":"TAIFEX_MIS", "discovered_at_utc":"2026-07-16T00:00:01Z", "contracts": [
    {"instrument_type":"option","product":"TXO","expiry":"202608","contract_type":"monthly","session":"regular","strike":"45100","call_put":"C"},
    {"instrument_type":"option","product":"TXO","expiry":"202608","contract_type":"monthly","session":"regular","strike":"45100","call_put":"P"},
]}
EMPTY = {"source_family":"TAIFEX_MIS", "discovered_at_utc":"2026-07-16T00:00:02Z", "contracts": []}


def test_nearest_active_weekly_wins_when_earlier_than_monthly():
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), FixtureUniverseProvider([U1, U1], "44950"))
    assert r["discovered_universe_summary"]["selected_contract_type"] == "weekly"
    assert r["discovered_universe_summary"]["selected_expiry"] == "202607W4"
    assert {t["call_put"] for t in r["resolved_exact_targets"]} == {"C", "P"}


def test_explicit_monthly_and_weekly_preferences():
    m = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權近月月選 call 跟 put 怎麼樣？"), FixtureUniverseProvider([U1, U1], "45000"))
    w = resolve_current_contracts(parse_derivatives_intent("現在最近到期的台指週選怎麼樣？"), FixtureUniverseProvider([U1, U1], "44900"))
    assert m["discovered_universe_summary"]["selected_expiry"] == "202608"
    assert m["discovered_universe_summary"]["selected_contract_type"] == "monthly"
    assert w["discovered_universe_summary"]["selected_contract_type"] == "weekly"


def test_mis_universe_drives_identity_not_openapi():
    primary = FixtureUniverseProvider([U1, U1], "44900", reference_source="fixture_mis_tx")
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), CompositeReferenceUniverseProvider(primary, openapi_reference_fetcher=lambda: "45000"))
    assert r["discovered_universe_summary"]["source_family"] == "TAIFEX_MIS"
    assert {t["strike"] for t in r["resolved_exact_targets"]} == {"44900"}


def test_openapi_does_not_define_live_availability_reference_only():
    primary = FixtureUniverseProvider([U1, U1], None)
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), CompositeReferenceUniverseProvider(primary, openapi_reference_fetcher=lambda: "44900"))
    assert r["reference_observation"]["reference_source"] == "TAIFEX_OPENAPI_TX_latest_eod_reference"
    assert r["discovered_universe_summary"]["source_family"] == "TAIFEX_MIS"


def test_strike_midpoint_is_never_used_as_market_reference():
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), FixtureUniverseProvider([U1, U1], None))
    assert r["resolution_status"] == "reference_unavailable"
    assert r["resolved_exact_targets"] == []
    assert "midpoint" not in str(r["reference_observation"]).lower()


def test_explicit_strike_anchor_does_not_need_market_reference():
    r = resolve_current_contracts(parse_derivatives_intent("看一下台指選擇權四萬五附近的 call 跟 put"), FixtureUniverseProvider([U1, U1], None))
    assert r["resolution_status"] == "resolved"
    assert {t["strike"] for t in r["resolved_exact_targets"]} == {"44900"}
    assert r["raw_payload_retained"] is False


def test_freshness_second_discovery_invalidates_and_reresolves_once():
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), FixtureUniverseProvider([U1, U2, U2], reference_sequence=["44900", "45100"]))
    assert r["reresolution_count"] == 1
    assert r["original_resolved_identity"][0]["expiry"] == "202607W4"
    assert r["final_resolved_identity"][0]["expiry"] == "202608"
    assert r["freshness_check"]["valid"] is True


def test_second_invalidation_stops_after_one_reresolution():
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), FixtureUniverseProvider([U1, U2, EMPTY], reference_sequence=["44900", "45100"]))
    assert r["reresolution_count"] == 1
    assert r["resolution_status"] == "freshness_check_failed"
    assert r["freshness_check"]["valid"] is False


def test_exact_mode_no_fallback_and_no_reresolution():
    r = resolve_current_contracts(parse_derivatives_intent("TXO 209912 99999 C monthly"), FixtureUniverseProvider([U1, U1]))
    assert r["resolution_status"] == "exact_contract_unavailable"
    assert r["reresolution_count"] == 0
    assert r["resolved_exact_targets"] == []


def test_nearest_listed_strike_tie_selects_both():
    assert nearest_strikes(["44900", "45100"], "45000") == ["44900", "45100"]


def test_lower_level_mis_reason_mapping():
    assert map_taifex_mis_detail_reason("requested_month_not_available") == "source_identity_scope_unavailable"
    assert map_taifex_mis_detail_reason("requested_strike_not_available") == "source_identity_scope_unavailable"
    assert map_taifex_mis_detail_reason("option_exact_identity_not_unique") == "source_identity_not_unique"
    assert map_taifex_mis_detail_reason("runtime_symbol_mismatch") == "source_identity_mismatch"
    assert map_taifex_mis_detail_reason("weird") == "source_payload_invalid"

class _FakeSession:
    def close(self):
        pass

class _FakeRest:
    def __init__(self):
        self.option_chain_calls = []
        self.quote_calls = []
    def products(self, market, symtype):
        return [{"CID": "TXO"}] if symtype == "O" else [{"CID": "TXF"}]
    def months(self, cid, market, symtype):
        if cid == "TXO":
            return [{"item":"202607W4"}, {"item":"202608"}]
        return [{"item":"202608"}]
    def option_chain(self, cid, expiry):
        self.option_chain_calls.append(expiry)
        if expiry == "202607W4":
            return [
                {"SymbolID":"TXO-A-O", "StrikePrice":"44900", "CP":"C"},
                {"SymbolID":"TXO-B-O", "StrikePrice":"44900", "CP":"P"},
                {"SymbolID":"TXO-C-O", "StrikePrice":"45100", "CP":"C"},
                {"SymbolID":"TXO-D-O", "StrikePrice":"45100", "CP":"P"},
            ]
        return [
            {"SymbolID":"TXO-MC-O", "StrikePrice":"45000", "CP":"C"},
            {"SymbolID":"TXO-MP-O", "StrikePrice":"45000", "CP":"P"},
        ]
    def quote_list(self, cid, expiry, kind):
        self.quote_calls.append((cid, expiry, kind))
        return [{"SymbolID":"TXF-F", "CLastPrice":"44950"}]


def test_mis_provider_fetches_only_selected_expiry_chain(monkeypatch):
    from scripts.m8r_taifex_current_contract_resolver import TaifexMisCurrentUniverseProvider
    rest = _FakeRest()
    provider = TaifexMisCurrentUniverseProvider()
    monkeypatch.setattr(provider, "_client", lambda: (_FakeSession(), rest))
    universe = provider.discover(parse_derivatives_intent("現在台指選擇權怎麼樣？"))
    assert rest.option_chain_calls == ["202607W4"]
    assert {c["expiry"] for c in universe["contracts"]} == {"202607W4"}
    assert universe["counts"]["option_chain_fetch_count"] == 1
    assert universe["counts"]["option_rows_examined"] == 4
    assert universe["full_option_chain_retained"] is False


def test_mis_provider_explicit_monthly_still_fetches_one_chain(monkeypatch):
    from scripts.m8r_taifex_current_contract_resolver import TaifexMisCurrentUniverseProvider
    rest = _FakeRest()
    provider = TaifexMisCurrentUniverseProvider()
    monkeypatch.setattr(provider, "_client", lambda: (_FakeSession(), rest))
    universe = provider.discover(parse_derivatives_intent("現在台指選擇權近月月選 call 跟 put 怎麼樣？"))
    assert rest.option_chain_calls == ["202608"]
    assert {c["expiry"] for c in universe["contracts"]} == {"202608"}
    assert universe["counts"]["selected_contract_type"] == "monthly"


def test_option_intent_obtains_current_mis_tx_reference(monkeypatch):
    from scripts.m8r_taifex_current_contract_resolver import TaifexMisCurrentUniverseProvider
    rest = _FakeRest()
    provider = TaifexMisCurrentUniverseProvider()
    monkeypatch.setattr(provider, "_client", lambda: (_FakeSession(), rest))
    universe = provider.discover(parse_derivatives_intent("現在台指選擇權怎麼樣？"))
    ref = provider.reference(parse_derivatives_intent("現在台指選擇權怎麼樣？"), universe)
    assert ref["reference_source"] == "TAIFEX_MIS_TX_current_reference"
    assert ref["reference_value"] == "44950"
    assert rest.quote_calls == [("TXF", "202608", "F")]


def test_resolver_second_discovery_checks_only_relevant_expiry(monkeypatch):
    from scripts.m8r_taifex_current_contract_resolver import TaifexMisCurrentUniverseProvider
    rest = _FakeRest()
    provider = TaifexMisCurrentUniverseProvider()
    monkeypatch.setattr(provider, "_client", lambda: (_FakeSession(), rest))
    r = resolve_current_contracts(parse_derivatives_intent("現在台指選擇權怎麼樣？"), provider)
    assert r["resolution_status"] == "resolved"
    assert rest.option_chain_calls == ["202607W4", "202607W4"]
    assert sum(d["counts"].get("option_chain_fetch_count", 0) for d in provider.diagnostics if d["stage"] == "discover") == 2
