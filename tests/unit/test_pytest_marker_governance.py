import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

def test_network_marker_declared():
    text=(ROOT/'pytest.ini').read_text()
    assert 'network:' in text and 'pytest -m "not network"' in text
