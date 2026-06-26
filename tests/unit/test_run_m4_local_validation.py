from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.run_m4_local_validation import run_local_validation
def test_local_validation_no_network(): assert run_local_validation(ROOT)['network_used'] is False
