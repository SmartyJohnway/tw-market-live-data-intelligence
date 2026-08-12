"""Executable Node regression for the narrow M8R-06 browser state repair."""
from __future__ import annotations

import subprocess
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
assert(networkAuthorization.executeOnceDisabled, false, 'network authorization execute');
assert(networkAuthorization.networkConfirmationDisabled, false, 'network authorization checkbox');
assert(networkAuthorization.networkConfirmationChecked, false, 'network authorization checkbox default');
const offlineAuthorization = state.authorizationControls(false);
assert(offlineAuthorization.networkConfirmationDisabled, true, 'offline authorization checkbox');
const invalidated = state.invalidatedControls();
assert(invalidated.authorizeDisabled, true, 'invalidated authorize');
assert(invalidated.executeOnceDisabled, true, 'invalidated execute');
assert(invalidated.networkConfirmationDisabled, true, 'invalidated network');
assert(invalidated.networkConfirmationChecked, false, 'invalidated network checked');
assert(invalidated.buildResultDisabled, true, 'invalidated Mode C');
assert(state.validationAllowsPreview('valid'), true, 'valid request preview');
assert(state.validationAllowsPreview('invalid'), false, 'invalid request preview');
'''
    completed = subprocess.run(
        ["node", "-e", script, str(STATE_MODULE)], cwd=ROOT,
        text=True, capture_output=True, timeout=15,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
