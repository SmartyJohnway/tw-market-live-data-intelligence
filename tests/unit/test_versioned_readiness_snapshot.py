from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_readiness_false_flags():
 s=load('docs/release/readiness_snapshot_m4_omega.json'); assert not s['production_ready'] and not s['live_probe_authorized'] and not s['trading_signal_allowed']
