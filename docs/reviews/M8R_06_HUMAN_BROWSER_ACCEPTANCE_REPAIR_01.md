# M8R-06 Human Browser Acceptance Repair 01

## Status

`PASS_WITH_CAVEATS` — the post-merge human retest completed and exposed the separate AI handoff repair findings below.

- baseline_sha: `416fc4c01642909768e44e650bb71df865984717`
- external_market_network_calls: `0`
- M8R-07: `NOT_AUTHORIZED`
- M8R-08: `NOT_AUTHORIZED`

## Human reproduction

The local Workbench validated and previewed a TWSE + TPEX request successfully. The Preview reported `ready_for_confirmation`, but the Authorize button was disabled before the human could continue. No DevTools workaround was used.

## Root cause and repair

`AUTHORIZE_BUTTON_ENABLEMENT_INVERTED`: the UI assigned the authorizable-status predicate directly to `authorizeBtn.disabled`.

The Workbench now uses a small browser-loaded state module. `ready_for_confirmation` and `partial_possible` set `authorizeDisabled` to `false`; all other preview statuses remain disabled. The same state module explicitly preserves pre-authorization Execute/network disabling, network-confirmation default unchecked after authorization, and invalidation clearing of execution/Mode C controls.

## Regression proof

The deterministic Node-backed test executes the production state module and proves:

- authorizable previews enable Authorize;
- accepted non-authorizable statuses disable Authorize, Execute, and network confirmation;
- network-required authorization enables an unchecked network checkbox and Execute Once;
- invalidation clears Authorize, Execute, network confirmation, and Mode C result availability.

Adjacent assignments for Preview, Authorize, network confirmation, Execute Once, and Result Package were audited. `adjacent_state_defects: none`.

## Human browser status

`human_browser_e2e: PASS_WITH_CAVEATS`

Validate, Preview, Authorize, explicit network confirmation, Execute Once, production network execution, Mode C, and AI-ready Markdown all completed. The run accepted a partial current-observation source failure and identified: `AI_HANDOFF_CONTROLLED_PROJECTION_BYPASS`, `OFFICIAL_EOD_AI_PROJECTION_INCOMPLETE`, `TPEX_EOD_IDENTITY_CLASSIFICATION_DRIFT`, `AI_HANDOFF_TARGET_DISPLAY_INDEX_OFF_BY_ONE`, `LOCALHOST_NETWORK_BADGE_AMBIGUOUS`, and `MODE_C_NETWORK_WORDING_AMBIGUOUS`.
