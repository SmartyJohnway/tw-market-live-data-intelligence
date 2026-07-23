"""Offline, non-authorizing command boundary for M8R-05B-01."""
from __future__ import annotations
import argparse,json,sys
from scripts.m8r_filesystem_safety import atomic_write_text, FilesystemSafetyError
from .artifact_loader import load_json
from .canonical import canonical_json
from .models import PlanningError
from .planner import build_plan
class Parser(argparse.ArgumentParser):
 def error(self,message): raise PlanningError('input_schema_invalid',message)
def parser():
 p=Parser(description='offline deterministic orchestration-plan projection')
 for name in ('validation-input','capability-catalog','routing-matrix','handoff-contract','executor-disposition','input-bindings'): p.add_argument('--'+name,required=True)
 p.add_argument('--planning-timestamp',required=True);p.add_argument('--output-root');p.add_argument('--output-relative');p.add_argument('--check-only',action='store_true');return p
def main(argv=None):
 try:
  a=parser().parse_args(argv)
  if not a.check_only and (not a.output_root or not a.output_relative): raise PlanningError('output_path_forbidden','output_contract_missing')
  if a.check_only and (a.output_root or a.output_relative): raise PlanningError('output_path_forbidden','check_only_output_forbidden')
  plan=build_plan(load_json(a.validation_input),capability_catalog=load_json(a.capability_catalog),routing_matrix=load_json(a.routing_matrix),handoff_contract=load_json(a.handoff_contract),executor_disposition=load_json(a.executor_disposition),input_bindings=load_json(a.input_bindings),planning_timestamp=a.planning_timestamp)
  if not a.check_only: atomic_write_text(a.output_root,a.output_relative,canonical_json(plan))
  return 0
 except (PlanningError,FilesystemSafetyError,ValueError,json.JSONDecodeError) as e:
  print(json.dumps({'error_code':getattr(e,'code','input_schema_invalid')},sort_keys=True),file=sys.stderr);return 2
if __name__=='__main__': raise SystemExit(main())
