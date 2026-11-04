"""Executable Node regression for the narrow M8R-06 browser state repair."""
from __future__ import annotations

import subprocess
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_MODULE = ROOT / "frontend" / "unified-workbench" / "workbench-state.js"


def test_authorization_controls_follow_preview_and_invalidation_state_machine():
    script = r'''
const state = require(process.argv[1]);
const assert = (actual, expected, label) => {
  if (actual !== expected) throw new Error(`${label}: expected ${expected}, got ${actual}`);
};
for (const status of ['ready_for_confirmation', 'partial_possible']) {
  const controls = state.previewControls(status);
  assert(controls.authorizeDisabled, false, `${status} authorize`);
  assert(controls.executeOnceDisabled, true, `${status} execute`);
  assert(controls.networkConfirmationDisabled, true, `${status} network`);
}
for (const status of ['ambiguous_target', 'target_not_plannable', 'unsupported_capability', 'rejected_resource_bound', 'error']) {
  const controls = state.previewControls(status);
  assert(controls.authorizeDisabled, true, `${status} authorize`);
  assert(controls.executeOnceDisabled, true, `${status} execute`);
  assert(controls.networkConfirmationDisabled, true, `${status} network`);
}
const networkAuthorization = state.authorizationControls(true);
assert(networkAuthorization.executeOnceDisabled, true, 'network authorization waits for confirmation');
assert(networkAuthorization.networkConfirmationDisabled, false, 'network authorization checkbox');
assert(networkAuthorization.networkConfirmationChecked, false, 'network authorization checkbox default');
const networkPending = state.executionConfirmationControls(true, false, 'workbench:umea-test');
assert(networkPending.executeOnceDisabled, true, 'network execution blocked before explicit confirmation');
const networkReady = state.executionConfirmationControls(true, true, 'workbench:umea-test');
assert(networkReady.executeOnceDisabled, false, 'network execution enabled after explicit confirmation');
const missingReference = state.executionConfirmationControls(true, true, '   ');
assert(missingReference.executeOnceDisabled, true, 'execution blocked without audit reference');
const offlineAuthorization = state.authorizationControls(false);
assert(offlineAuthorization.networkConfirmationDisabled, true, 'offline authorization checkbox');
const offlineReady = state.executionConfirmationControls(false, false, 'workbench:umea-test');
assert(offlineReady.executeOnceDisabled, false, 'offline execution only needs audit reference');
const recovery = state.previewRecovery({
  status: 'unsupported_capability',
  coverage_expectation: { known_gaps: [
    'identity:plan_only_not_executable',
    'session_status:route_unavailable',
    'trading_status_context:unsupported_market',
    'PREVIEW_ONLY'
  ]},
  caveats: ['NO_NETWORK_EXECUTED']
}, { operations: [], blocked_operations: [] });
assert(recovery.blocked, true, 'blocked preview recovery');
assert(recovery.items.length, 3, 'blocked preview item count');
assert(recovery.items[0].capabilityId, 'identity', 'first blocked capability');
if (!recovery.guidance.includes('Evidence Needs')) throw new Error('recovery guidance must name Evidence Needs');
const readyRecovery = state.previewRecovery({status: 'ready_for_confirmation'}, {operations: [], blocked_operations: []});
assert(readyRecovery.blocked, false, 'ready preview recovery');
const i3Readiness = {
  status: 'blocked',
  blocking_reasons: [{capability_id: 'cash_institutional_flow_context', market: 'TWSE', code: 'i3_governed_source_date_authority_required'}],
  operator_guidance: 'Review Evidence Needs and remove TWSE institutional flow until current governed source-date authority is available.'
};
const i3Recovery = state.previewRecovery({status: 'ready_for_confirmation'}, {operations: []}, i3Readiness);
assert(i3Recovery.blocked, true, 'i3 authorization readiness blocks preview authorization');
assert(i3Recovery.items.length, 1, 'i3 readiness recovery item count');
assert(i3Recovery.items[0].capabilityId, 'cash_institutional_flow_context', 'i3 blocked capability');
if (!i3Recovery.items[0].explanation.includes('governed source-date authority')) throw new Error('i3 readiness explanation must be operator-readable');
const i3Controls = state.previewControls('ready_for_confirmation', i3Readiness);
assert(i3Controls.authorizeDisabled, true, 'i3 readiness disables authorize');
const i3Error = state.authorizationErrorMessage('i3_governed_source_date_authority_required');
if (!i3Error.includes('governed source-date authority') || i3Error.includes('i3_governed_source_date_authority_required')) {
  throw new Error('authorization error must be operator-readable');
}
const invalidated = state.invalidatedControls();
assert(invalidated.authorizeDisabled, true, 'invalidated authorize');
assert(invalidated.executeOnceDisabled, true, 'invalidated execute');
assert(invalidated.networkConfirmationDisabled, true, 'invalidated network');
assert(invalidated.networkConfirmationChecked, false, 'invalidated network checked');
assert(invalidated.buildResultDisabled, true, 'invalidated Mode C');
assert(state.validationAllowsPreview('valid'), true, 'valid request preview');
assert(state.validationAllowsPreview('invalid'), false, 'invalid request preview');
let lifecycle = state.initialState();
assert(lifecycle.state, state.STATES.BOOT, 'initial state');
lifecycle = state.transition(lifecycle, 'LOAD_WATCHLIST');
assert(lifecycle.state, state.STATES.WATCHLIST_READY, 'watchlist ready');
lifecycle = state.transition(lifecycle, 'EDIT_SELECTION');
assert(lifecycle.state, state.STATES.SELECTION_DIRTY, 'selection dirty');
lifecycle = state.transition(lifecycle, 'COMPOSE_REQUEST');
assert(lifecycle.state, state.STATES.REQUEST_COMPOSED, 'request composed');
assert(lifecycle.composedRequestFrozen, true, 'request frozen');
const stale = state.markSourceWatchlistChanged(lifecycle);
assert(stale.sourceWatchlistStale, true, 'source change is visible');
assert(stale.composedRequestFrozen, true, 'source mutation does not rewrite frozen request');
lifecycle = state.transition(lifecycle, 'PREVIEW_MUTATION');
assert(lifecycle.state, state.STATES.MUTATION_PREVIEW, 'mutation preview');
lifecycle = state.transition(lifecycle, 'CONFLICT');
assert(lifecycle.state, state.STATES.CONFLICT_OR_EXPIRY, 'conflict state');
'''
    completed = subprocess.run(
        [os.environ.get("TW_MARKET_CI_NODE", "node"), "-e", script, str(STATE_MODULE)], cwd=ROOT,
        text=True, capture_output=True, timeout=15,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
