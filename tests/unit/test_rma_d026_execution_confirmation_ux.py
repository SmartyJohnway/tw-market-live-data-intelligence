from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / 'frontend/unified-workbench/UnifiedMarketEvidenceWorkbench.html').read_text(encoding='utf-8')
JS = (ROOT / 'frontend/unified-workbench/unified-workbench.js').read_text(encoding='utf-8')


def test_execution_confirmation_is_inline_and_operator_readable():
    assert 'id="operator-confirmation-reference"' in HTML
    assert 'Audit reference' in HTML
    assert 'not a password' in HTML
    assert "window.prompt('Operator confirmation reference')" not in JS
    assert "operator-confirmation-reference" in JS


def test_execute_once_requires_confirmation_state_not_prompt_side_effect():
    assert 'executionConfirmationControls' in JS
    assert 'confirm_network_execution:networkConfirmation.checked === true' in JS
    assert 'operator_confirmation_reference:reference' in JS
