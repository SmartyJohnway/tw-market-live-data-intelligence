from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.run_m4_readiness_check import run_readiness_check
def test_readiness_check():
 r=run_readiness_check(); assert r['ok'] and not r['network_used'] and not r['production_ready']
