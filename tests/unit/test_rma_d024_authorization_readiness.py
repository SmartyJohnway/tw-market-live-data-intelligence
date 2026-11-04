from server.services.unified_mode_b1 import authorization_readiness_for_plan


def _operation(*, capability_id="current_observation", market="TWSE"):
    return {
        "capability_id": capability_id,
        "market": market,
        "operation_status": "executable_pending_approval",
    }


def test_non_i3_plan_is_authorization_ready():
    result = authorization_readiness_for_plan({"operations": [_operation()]})
    assert result == {"status": "ready", "blocking_reasons": []}


def test_twse_i3_without_governed_date_binding_is_blocked():
    plan = {"operations": [_operation(capability_id="cash_institutional_flow_context")]}
    result = authorization_readiness_for_plan(plan)
    assert result["status"] == "blocked"
    assert result["blocking_reasons"] == [{
        "capability_id": "cash_institutional_flow_context",
        "market": "TWSE",
        "code": "i3_governed_source_date_authority_required",
    }]


def test_twse_i3_with_bound_source_date_is_ready():
    plan = {
        "operations": [_operation(capability_id="cash_institutional_flow_context")],
        "resolved_source_trade_date": "2026-10-23",
        "source_date_binding": {
            "market": "TWSE",
            "resolved_source_trade_date": "2026-10-23",
        },
    }
    result = authorization_readiness_for_plan(plan)
    assert result == {"status": "ready", "blocking_reasons": []}


def test_tpex_i3_does_not_require_twse_source_date_binding():
    plan = {"operations": [_operation(capability_id="cash_institutional_flow_context", market="TPEX")]}
    result = authorization_readiness_for_plan(plan)
    assert result == {"status": "ready", "blocking_reasons": []}
