# M7G-08 Controlled Refresh Request Package

Status: `controlled_refresh_request_package_defined`

Schema version: `m7g_controlled_refresh_request_package.v1`

M7G-07/08 does not execute refresh. The package is a local, inspectable, copyable request object prepared by explicit operator preflight for future M7G-09 handling.

## Required package shape

```json
{
  "schema_version": "m7g_controlled_refresh_request_package.v1",
  "package_type": "controlled_manual_refresh_request",
  "package_status": "prepared_not_executed",
  "created_at_utc": "operator_action_runtime",
  "created_by": "operator_explicit_preflight",
  "active_context_mode": "loaded_safe_artifact",
  "source_artifact_id": "safe-context-demo-20260709",
  "source_artifact_schema_version": "m7g_safe_context_artifact.v1",
  "source_validation_status": "accepted",
  "source_observation_count": 1,
  "requested_symbols": ["2330"],
  "requested_markets": ["TWSE"],
  "requested_source_families": ["TWSE_MIS"],
  "refresh_scope": "bounded_watchlist",
  "bounded_watchlist_only": true,
  "execution_eligible_for_m7g09": true,
  "execution_authorized": false,
  "execution_performed": false,
  "requires_m7g09_execution_gate": true,
  "network_intent": "declared_for_future_m7g09_only",
  "raw_payload_requested": false,
  "raw_forbidden_values_requested": false,
  "ai_model_call_requested": false,
  "trading_advice_requested": false,
  "currentness_before_refresh": {
    "currentness_label": "live_candidate",
    "calendar_confidence": "controlled_twse_holiday_schedule_artifact",
    "trading_day_status": "trading_day"
  },
  "source_health_before_refresh": {
    "source_health_status": "artifact_reported",
    "source_health_schema_version": "m7g_source_health.v1"
  },
  "operator_confirmation": {
    "required": true,
    "confirmation_phrase_required": "PREPARE_REFRESH_REQUEST_ONLY",
    "confirmed": true,
    "confirmation_phrase_matched": true
  },
  "governance_guardrails": {
    "not_trading_signal": true,
    "not_recommendation": true,
    "not_market_prediction": true,
    "not_capital_flow": true,
    "not_full_market_breadth": true,
    "raw_payload_exposed": false,
    "raw_rich_facts_exposed": false,
    "raw_full_ladder_exposed": false
  }
}
```

## Static demo behavior

If active context mode is `static_demo`:

- package may be prepared for UI/test preview;
- `execution_eligible_for_m7g09` must be false;
- `source_artifact_id` must be `static_demo`;
- `package_status` remains `prepared_not_executed` when operator confirmation matches.

## Loaded safe artifact behavior

If active context mode is `loaded_safe_artifact`:

- validation status must be `accepted`;
- `safe_to_render` must be true;
- `execution_eligible_for_m7g09` may be true;
- `execution_authorized` remains false;
- `execution_performed` remains false.

## Required downstream gate

- M7G-09 controlled manual refresh execution remains mandatory.
- M7G-09 is the earliest task allowed to execute refresh.
- M7G-07/08 does not execute refresh.
