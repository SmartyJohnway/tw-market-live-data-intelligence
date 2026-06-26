from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_observability_model_flags():
 t=(ROOT/'frontend/readonly-preview/observabilityModel.js').read_text(); assert 'tradingSignal:false' in t and 'realtimeGuaranteed:false' in t
