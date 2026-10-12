"""Thin test-only launcher reusing the shipped Workbench and execution workflow."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from server.services import unified_mode_b2_execution
from scripts.run_unified_workbench import main
unified_mode_b2_execution.WRAPPER = ROOT/'tests/helpers/phase_j_j2_r1_transport.py'
if __name__ == '__main__': main()
