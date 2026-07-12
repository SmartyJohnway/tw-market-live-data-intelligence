import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_probe_common import build_arg_parser, require_confirmed
if __name__=='__main__':
    p=build_arg_parser('Run M8C TAIFEX MIS preflight probes'); a=p.parse_args()
    if not require_confirmed(a): print('{"status":"operator_confirmation_required","network_performed":false,"children_invoked":false}'); raise SystemExit(0)
    print('{"status":"use individual bounded probe scripts for reviewed windows"}')
