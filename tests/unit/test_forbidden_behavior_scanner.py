from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.forbidden_behavior_scanner import scan_text
def test_scanner_detects_positive_claims(): assert scan_text('system will execute live probe now')
def test_scanner_allows_negative_wording(): assert scan_text('no trading signal and not realtime guaranteed') == []
