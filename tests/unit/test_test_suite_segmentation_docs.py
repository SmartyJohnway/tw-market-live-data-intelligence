from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
def test_segmentation_doc_boundaries():
 t=(ROOT/'docs/testing/TEST_SUITE_SEGMENTATION.md').read_text(encoding="utf-8"); assert 'Future network tests are unauthorized' in t and 'Do not run live probes' in t
