"""Reuse the real Local Service and independent server receipts; no browser."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.helpers.phase_j_closure_r1_server import main, unified_mode_b2_execution
unified_mode_b2_execution.WRAPPER = ROOT / 'tests/helpers/phase_j_closure_r2_r1_transport.py'
if __name__ == '__main__':
    main()
