# M8R-06 Human Browser Acceptance Repair 01

## Status

`CODE_REPAIR_COMPLETE; PENDING_HUMAN_RETEST`

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

`human_browser_e2e: PENDING_HUMAN_RETEST`

The repair does not claim a completed human browser run. The operator should repeat the normal browser flow after merge.
