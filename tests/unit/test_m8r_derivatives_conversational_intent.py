from scripts.m8r_derivatives_conversational_intent import parse_derivatives_intent


def test_chinese_future_alias_current():
    i = parse_derivatives_intent("現在台指期怎麼樣？")
    assert i["intent_mode"] == "resolve_current"
    assert i["instrument_family"] == "future"
    assert i["product"] == "TX"
    assert i["explicit_constraints"]["product"] is True


def test_chinese_option_defaults_both_and_inferred():
    i = parse_derivatives_intent("現在台指選擇權怎麼樣？")
    assert i["instrument_family"] == "option"
    assert i["call_put_scope"] == "both"
    assert i["explicit_constraints"]["call_put"] is False
    assert i["inferred_preferences"]["call_put_scope"]["value"] == "both"


def test_monthly_weekly_and_explicit_call_put():
    m = parse_derivatives_intent("現在台指選擇權近月月選 call 跟 put 怎麼樣？")
    w = parse_derivatives_intent("現在最近到期的台指週選怎麼樣？")
    assert m["contract_type_preference"] == "monthly_preferred"
    assert m["call_put_scope"] == "both"
    assert m["explicit_constraints"]["call_put"] is True
    assert w["contract_type_preference"] == "weekly_preferred"


def test_explicit_strike_anchor_bounded_chinese_number():
    i = parse_derivatives_intent("看一下台指選擇權四萬五附近的 call 跟 put")
    assert i["strike_anchor"] == "45000"
    assert i["explicit_constraints"]["strike"] is True


def test_english_aliases_and_clarification_required():
    assert parse_derivatives_intent("current TAIEX options both")['product'] == 'TXO'
    c = parse_derivatives_intent("看一下選擇權")
    assert c["clarification_required"] is True
    assert c["clarification_reason"] == "product_not_identified"


def test_exact_mode_preserved():
    i = parse_derivatives_intent("TXO 202607 40000 C monthly")
    assert i["intent_mode"] == "exact"
    assert i["expiry"] == "202607"
    assert i["strike"] == "40000"
    assert i["explicit_constraints"]["expiry"] is True
