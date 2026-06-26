from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
import subprocess, sys
def test_fixture_replay_script(): assert subprocess.run([sys.executable,str(ROOT/'scripts/run_m4_fixture_replay.py'),'--check-only'],capture_output=True,text=True).returncode==0
