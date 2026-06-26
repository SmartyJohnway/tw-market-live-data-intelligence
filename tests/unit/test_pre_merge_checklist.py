from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_pre_merge_mentions_pr_metadata(): assert 'Codex must not edit PR metadata' in (ROOT/'docs/release/PRE_MERGE_CHECKLIST.md').read_text()
