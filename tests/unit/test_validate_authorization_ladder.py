from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.validate_authorization_ladder import validate_authorization_ladder
def test_ladder_blocks_elevation(): assert validate_authorization_ladder({'live_probe_authorized':True})
def test_ladder_local_ok(): assert validate_authorization_ladder({}) == []
