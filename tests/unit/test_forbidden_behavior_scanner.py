from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.forbidden_behavior_scanner import scan_text
def test_scanner_detects_positive_claims(): assert scan_text('system will execute live probe now')
def test_scanner_allows_negative_wording(): assert scan_text('no trading signal and not realtime guaranteed') == []
def test_scanner_does_not_exclude_whole_line_after_no():
 findings=scan_text('no audit; execute live probe now')
 assert findings and findings[0]['code']=='live_probe_execution'
