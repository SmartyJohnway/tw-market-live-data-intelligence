import ast
from pathlib import Path
from scripts.m8r_05b_01.cli import parser

def test_no_network_or_execution_imports_and_no_forbidden_flags():
 root=Path('scripts/m8r_05b_01')
 forbidden={'requests','httpx','aiohttp','socket','subprocess','urllib.request'}
 for path in root.glob('*.py'):
  tree=ast.parse(path.read_text())
  for node in ast.walk(tree):
   if isinstance(node,ast.Import): assert not any(x.name in forbidden for x in node.names)
   if isinstance(node,ast.ImportFrom): assert node.module not in forbidden
 flags={x.option_strings[0] for x in parser()._actions if x.option_strings}
 assert not flags & {'--execute','--approve','--authorize','--allow-network','--invoke-executor'}
def _forbidden_calls(source):
 tree=ast.parse(source); denied={'invoke_executor','execute_plan','run_source','fetch_market','consume_authorization','issue_authorization','approve_plan'}
 return [n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in denied]
def test_negative_control_rejects_executor_call():
 assert _forbidden_calls('invoke_executor()') == ['invoke_executor']
