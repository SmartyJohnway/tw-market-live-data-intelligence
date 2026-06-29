import subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

def test_m5ij_acceptance_check_only_passes():
    r=subprocess.run([sys.executable, str(REPO/'scripts/run_m5ij_end_to_end_acceptance.py'), '--check-only'], cwd=REPO, text=True, capture_output=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'm5ij_local_product_release_candidate' in r.stdout

def test_m5e_supersession_accepted_by_default():
    import scripts.run_m5ij_end_to_end_acceptance as acc
    checks, _ = acc.run_checks()
    m5e = next(c for c in checks if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e['status'] == 'passed'

def test_m5e_not_superseded_fails(monkeypatch):
    import scripts.run_m5ij_end_to_end_acceptance as acc
    import scripts.run_m5e_controlled_frontend_publication as m5e_script

    monkeypatch.setattr(m5e_script, 'check_only', lambda: {
        'status': 'not_superseded',
        'superseded_by_m5f': False,
        'publication_performed': False,
        'frontend_publication_authorized': False
    })

    checks, _ = acc.run_checks()
    m5e = next(c for c in checks if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e['status'] == 'failed'
    assert m5e['details']['actual_status'] == 'not_superseded'

def test_m5e_frontend_publication_authorized_true_fails(monkeypatch):
    import scripts.run_m5ij_end_to_end_acceptance as acc
    import scripts.run_m5e_controlled_frontend_publication as m5e_script

    monkeypatch.setattr(m5e_script, 'check_only', lambda: {
        'status': 'superseded_by_m5f',
        'superseded_by_m5f': True,
        'publication_performed': False,
        'frontend_publication_authorized': True
    })

    checks, _ = acc.run_checks()
    m5e = next(c for c in checks if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e['status'] == 'failed'
    assert m5e['details']['publication_authorized'] is True

def test_m5e_publication_performed_true_fails(monkeypatch):
    import scripts.run_m5ij_end_to_end_acceptance as acc
    import scripts.run_m5e_controlled_frontend_publication as m5e_script

    monkeypatch.setattr(m5e_script, 'check_only', lambda: {
        'status': 'superseded_by_m5f',
        'superseded_by_m5f': True,
        'publication_performed': True,
        'frontend_publication_authorized': False
    })

    checks, _ = acc.run_checks()
    m5e = next(c for c in checks if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e['status'] == 'failed'
    assert m5e['details']['publication_performed'] is True

def test_m5e_malformed_result_fails(monkeypatch):
    import scripts.run_m5ij_end_to_end_acceptance as acc
    import scripts.run_m5e_controlled_frontend_publication as m5e_script

    monkeypatch.setattr(m5e_script, 'check_only', lambda: {'unexpected_format': True})

    checks, _ = acc.run_checks()
    m5e = next(c for c in checks if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e['status'] == 'failed'
    assert m5e['details']['actual_status'] is None
    assert 'mismatched state fields' in m5e['details']['reason']

def test_m5e_exception_from_check_only_fails_with_diagnostics(monkeypatch):
    import scripts.run_m5ij_end_to_end_acceptance as acc
    import scripts.run_m5e_controlled_frontend_publication as m5e_script

    def failing_check():
        raise RuntimeError("Injected exception during M5E check")

    monkeypatch.setattr(m5e_script, 'check_only', failing_check)

    checks, _ = acc.run_checks()
    m5e = next(c for c in checks if c['check'] == 'm5e_superseded_by_m5f')
    assert m5e['status'] == 'failed'
    assert m5e['details']['exception_type'] == 'RuntimeError'
    assert 'Injected exception' in m5e['details']['exception_message']
    assert 'traceback_excerpt' in m5e['details']
