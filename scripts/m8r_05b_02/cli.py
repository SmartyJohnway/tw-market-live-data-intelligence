"""Local-only materializer for immutable authorization artifacts."""
import argparse,json,sys
from scripts.m8r_filesystem_safety import atomic_write_text,FilesystemSafetyError
from .artifact_loader import load_json
from .authorization import build_execution_authorization
from .canonical import canonical_json
from .preflight import evaluate_authorization_preflight
from .models import AuthorizationError
class Parser(argparse.ArgumentParser):
 def error(self,message): raise AuthorizationError('authorization_schema_invalid',message)
def parser():
 p=Parser();p.add_argument('--plan-input',required=True);p.add_argument('--decision-input',required=True);p.add_argument('--evaluation-timestamp',required=True);p.add_argument('--check-only',action='store_true');p.add_argument('--output-root');p.add_argument('--output-relative');return p
def main(argv=None):
 try:
  a=parser().parse_args(argv)
  if a.check_only and (a.output_root or a.output_relative): raise AuthorizationError('filesystem_output_invalid')
  if not a.check_only and (not a.output_root or not a.output_relative): raise AuthorizationError('filesystem_output_invalid')
  artifact=build_execution_authorization(load_json(a.plan_input),load_json(a.decision_input));evaluate_authorization_preflight(artifact,load_json(a.plan_input),a.evaluation_timestamp)
  if not a.check_only: atomic_write_text(a.output_root,a.output_relative,canonical_json(artifact))
  return 0
 except (AuthorizationError,FilesystemSafetyError,ValueError,json.JSONDecodeError) as e:
  print(json.dumps({'error_code':getattr(e,'code','authorization_schema_invalid')},sort_keys=True),file=sys.stderr);return 2
if __name__=='__main__': raise SystemExit(main())
