import subprocess, sys

def test_m5ij_acceptance_check_only_passes():
    r=subprocess.run([sys.executable,'scripts/run_m5ij_end_to_end_acceptance.py','--check-only'],text=True,capture_output=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'm5ij_local_product_release_candidate' in r.stdout
