"""Historical I3 normalization accepts both captured and current H3 source."""

from scripts.phase_i_i3_a4_compat import strip_a6_transport_instrumentation


BASELINE = '''        result = fetch_twse_stock_day_month(
            target=target,
            instrument_family="company_share",
            instrument_type="common_share",
            requested_month=month,
            retrieved_at=kwargs["retrieved_at"],
            timeout_seconds=request["timeout_seconds"],
            max_response_bytes=PHASE_H_H3_MAX_RESPONSE_BYTES,
            ssl_policy="compatibility",
        )
'''

HISTORICAL_A6_WRAPPER = '''        from scripts.a6_session_transport import operation_context
        with operation_context(int(os.environ.get("A6_ATTEMPT", "1")), "H3", request["operation_id"]):
            result = fetch_twse_stock_day_month(
                target=target,
                instrument_family="company_share",
                instrument_type="common_share",
                requested_month=month,
                retrieved_at=kwargs["retrieved_at"],
                timeout_seconds=request["timeout_seconds"],
                max_response_bytes=PHASE_H_H3_MAX_RESPONSE_BYTES,
                ssl_policy="compatibility",
            )
'''


def test_historical_projection_strips_old_a6_wrapper():
    assert strip_a6_transport_instrumentation(HISTORICAL_A6_WRAPPER) == BASELINE


def test_historical_projection_accepts_current_uninstrumented_product_call():
    assert strip_a6_transport_instrumentation(BASELINE) == BASELINE
