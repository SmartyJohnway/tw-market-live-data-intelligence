import ast
from pathlib import Path
BAD={"requests","httpx","aiohttp","socket","subprocess","queue","sqlite3"}
def scan(source):
 tree=ast.parse(source); found=[]
 for node in ast.walk(tree):
  if isinstance(node,(ast.Import,ast.ImportFrom)):
   names=[x.name.split('.')[0] for x in node.names] if isinstance(node,ast.Import) else [(node.module or '').split('.')[0]]
   found += [x for x in names if x in BAD]
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {"consume_authorization","mark_consumed","run_source","fetch_market"}: found.append(node.func.id)
 return found
def test_package_ast_boundary():
 assert not scan('\n'.join(x.read_text() for x in Path('scripts/m8r_05b_02').glob('*.py')))
def test_ast_negative_controls():
 assert scan('import httpx')==['httpx']; assert scan('from socket import socket')==['socket']; assert scan('consume_authorization()')==['consume_authorization']
