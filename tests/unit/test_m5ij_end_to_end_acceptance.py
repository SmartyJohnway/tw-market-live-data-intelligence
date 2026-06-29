import subprocess, sys, json
from pathlib import Path
from unittest.mock import patch
import pytest

REPO = Path(__file__).resolve().parents[2]

def test_m5ij_acceptance_check_only_passes():
    r=subprocess.run([sys.executable, str(REPO/'scripts/run_m5ij_end_to_end_acceptance.py'), '--check-only'], cwd=REPO, text=True, capture_output=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'm5ij_local_product_release_candidate' in r.stdout

def run_m5ij_check_only_with_mocked_m5e(mocked_return_value, side_effect=None):
    from scripts.run_m5ij_end_to_end_acceptance import main
    with patch('scripts.run_m5e_controlled_frontend_publication.check_only') as mock_check_only:
        if side_effect:
            mock_check_only.side_effect = side_effect
        else:
            mock_check_only.return_value = mocked_return_value

        with patch('sys.argv', ['run_m5ij_end_to_end_acceptance.py', '--check-only']):
            with patch('sys.stdout', new_callable=subprocess.io.StringIO) as mock_stdout:
                exit_code = main()
                output = mock_stdout.getvalue()
                return exit_code, json.loads(output)

def test_m5e_supersession_accepted_case():
    valid_state = {
        'status': 'superseded_by_m5f',
        'superseded_by_m5f': True,
        'publication_performed': False,
        'frontend_publication_authorized': False
    }
    exit_code, output = run_m5ij_check_only_with_mocked_m5e(valid_state)
    assert exit_code == 0
    assert output['status'] == 'passed'
    m5e_check = next(c for c in output['checks'] if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e_check['status'] == 'passed'

def test_m5e_supersession_negative_no_longer_superseded():
    invalid_state = {
        'status': 'active',
        'superseded_by_m5f': False,
        'publication_performed': False,
        'frontend_publication_authorized': False
    }
    exit_code, output = run_m5ij_check_only_with_mocked_m5e(invalid_state)
    assert exit_code == 1
    assert output['status'] == 'failed'
    m5e_check = next(c for c in output['checks'] if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e_check['status'] == 'failed'
    assert m5e_check['details']['actual_status'] == 'active'

def test_m5e_supersession_negative_publication_authorized():
    invalid_state = {
        'status': 'superseded_by_m5f',
        'superseded_by_m5f': True,
        'publication_performed': False,
        'frontend_publication_authorized': True
    }
    exit_code, output = run_m5ij_check_only_with_mocked_m5e(invalid_state)
    assert exit_code == 1
    assert output['status'] == 'failed'
    m5e_check = next(c for c in output['checks'] if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e_check['status'] == 'failed'
    assert m5e_check['details']['publication_authorized'] is True

def test_m5e_supersession_negative_publication_performed():
    invalid_state = {
        'status': 'superseded_by_m5f',
        'superseded_by_m5f': True,
        'publication_performed': True,
        'frontend_publication_authorized': False
    }
    exit_code, output = run_m5ij_check_only_with_mocked_m5e(invalid_state)
    assert exit_code == 1
    assert output['status'] == 'failed'
    m5e_check = next(c for c in output['checks'] if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e_check['status'] == 'failed'
    assert m5e_check['details']['publication_performed'] is True

def test_m5e_supersession_negative_missing_fields():
    invalid_state = {}
    exit_code, output = run_m5ij_check_only_with_mocked_m5e(invalid_state)
    assert exit_code == 1
    assert output['status'] == 'failed'
    m5e_check = next(c for c in output['checks'] if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e_check['status'] == 'failed'
    assert m5e_check['details']['actual_status'] is None

def test_m5e_supersession_exception():
    exit_code, output = run_m5ij_check_only_with_mocked_m5e(None, side_effect=Exception("Simulated exception"))
    assert exit_code == 1
    assert output['status'] == 'failed'
    m5e_check = next(c for c in output['checks'] if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e_check['status'] == 'failed'
    assert m5e_check['details']['exception_type'] == 'Exception'
    assert m5e_check['details']['exception_message'] == 'Simulated exception'
    assert 'Simulated exception' in m5e_check['details']['traceback_excerpt']
