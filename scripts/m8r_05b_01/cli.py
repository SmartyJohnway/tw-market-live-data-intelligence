"""Offline, non-authorizing command boundary for M8R-05B-01."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from scripts.m8r_filesystem_safety import atomic_write_text, FilesystemSafetyError
from .artifact_loader import load_json
from .canonical import canonical_json
from .models import PlanningError
from .planner import build_plan

def parser():
 p=argparse.ArgumentParser(description='offline deterministic orchestration-plan projection')
 for name in ('validation-input','capability-catalog','routing-matrix','handoff-contract','executor-disposition','input-bindings'):
  p.add_argument('--'+name,required=True)
 p.add_argument('--planning-timestamp',required=True); p.add_argument('--output'); p.add_argument('--check-only',action='store_true')
 return p

def main(argv=None):
 a=parser().parse_args(argv)
 if not a.check_only and not a.output: parser().error('--output is required unless --check-only')
 try:
  plan=build_plan(load_json(a.validation_input),capability_catalog=load_json(a.capability_catalog),routing_matrix=load_json(a.routing_matrix),handoff_contract=load_json(a.handoff_contract),executor_disposition=load_json(a.executor_disposition),input_bindings=load_json(a.input_bindings),planning_timestamp=a.planning_timestamp)
  if not a.check_only:
   target=Path(a.output)
   if target.exists() and target.is_dir(): raise PlanningError('output_path_forbidden','directory_output')
   # The explicit parent is the authorized root; only its basename is accepted by containment.
   atomic_write_text(target.parent.resolve(),target.name,canonical_json(plan))
  return 0
 except (PlanningError,FilesystemSafetyError,ValueError,json.JSONDecodeError) as e:
  code=e.code if hasattr(e,'code') else 'input_schema_invalid'; print(json.dumps({'error_code':code},sort_keys=True),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
