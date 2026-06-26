from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_governance_console_accessibility():
 t=(ROOT/'frontend/readonly-preview/GovernanceConsolePreview.html').read_text().lower(); assert '<title>' in t and '<main>' in t and 'not a trading signal' in t and 'no realtime guarantee' in t
