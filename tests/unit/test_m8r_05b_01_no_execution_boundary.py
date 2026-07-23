import ast
from pathlib import Path
from scripts.m8r_05b_01.cli import parser
DENY={'invoke_executor','execute_plan','execute_request','run_source','fetch_market','market_data_runner','consume_authorization','consume_token','issue_authorization','approve_plan','owner_approval','controlled_executor','subprocess','requests','httpx','aiohttp','urllib.request','socket'}
def _forbidden_calls(source):
 tree=ast.parse(source); found=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Import): found += [x.name for x in n.names if x.name in DENY]
  if isinstance(n,ast.ImportFrom): found += [n.module] if n.module in DENY else []
  if isinstance(n,ast.Call):
   name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else ''
   if name in DENY: found.append(name)
 return found
def test_real_package_has_no_forbidden_execution_surface():
 for path in Path('scripts/m8r_05b_01').glob('*.py'): assert _forbidden_calls(path.read_text())==[]
def test_forbidden_flags_absent():
 flags={x.option_strings[0] for x in parser()._actions if x.option_strings};assert not flags & {'--execute','--approve','--authorize','--allow-network','--invoke-executor'}
def test_negative_controls():
 assert _forbidden_calls('invoke_executor()')==['invoke_executor'];assert _forbidden_calls('executor.invoke_executor()')==['invoke_executor']
