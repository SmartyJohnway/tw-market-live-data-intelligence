import ast
BAD={'requests','httpx','aiohttp','urllib','socket','subprocess','queue','sqlite3'}
CALLS={'run_source','fetch_market','mark_consumed','consume_authorization','execute','put'}
def scan(source):
 out=[]
 for n in ast.walk(ast.parse(source)):
  if isinstance(n,ast.Import): out += [a.name.split('.')[0] for a in n.names if a.name.split('.')[0] in BAD]
  if isinstance(n,ast.ImportFrom) and (n.module or '').split('.')[0] in BAD: out.append((n.module or '').split('.')[0])
  if isinstance(n,ast.Call):
   f=n.func
   if isinstance(f,ast.Name) and f.id in CALLS: out.append(f.id)
   if isinstance(f,ast.Attribute) and f.attr in CALLS: out.append(f.attr)
   if isinstance(f,ast.Attribute) and f.attr=='import_module' and n.args and isinstance(n.args[0],ast.Constant) and str(n.args[0].value).split('.')[0] in BAD: out.append('dynamic_import')
 return out
def test_package_ast_boundary():
 from pathlib import Path
 assert not scan('\n'.join(x.read_text() for x in Path('scripts/m8r_05b_02').glob('*.py')))
def test_ast_negative_controls():
 for text in ('import httpx as client','from urllib import request','import importlib\nimportlib.import_module("requests")','runner.run_source()','adapter.fetch_market()','registry.mark_consumed()','registry.consume_authorization()','queue.put(1)','connection.execute("x")','executor.execute()'):
  assert scan(text)
