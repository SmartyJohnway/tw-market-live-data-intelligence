import ast
BAD={'requests','httpx','aiohttp','urllib','socket','subprocess','queue','sqlite3'}; CALLS={'run_source','fetch_market','mark_consumed','consume_authorization'}; RECEIVERS={'connection','cursor','session','executor','queue','registry'}
def scan(source):
 out=[]; aliases=set()
 for n in ast.walk(ast.parse(source)):
  if isinstance(n,ast.Import): out += [a.name.split('.')[0] for a in n.names if a.name.split('.')[0] in BAD]
  if isinstance(n,ast.ImportFrom):
   if (n.module or '').split('.')[0] in BAD: out.append((n.module or '').split('.')[0])
   aliases|={a.asname or a.name for a in n.names if a.name in CALLS}
  if isinstance(n,ast.Call):
   f=n.func
   if isinstance(f,ast.Name) and (f.id in CALLS or f.id in aliases or (f.id=='__import__' and n.args and isinstance(n.args[0],ast.Constant) and str(n.args[0].value).split('.')[0] in BAD) or (f.id=='import_module' and n.args and isinstance(n.args[0],ast.Constant) and str(n.args[0].value).split('.')[0] in BAD)): out.append(f.id)
   if isinstance(f,ast.Attribute):
    receiver=f.value.id if isinstance(f.value,ast.Name) else ''
    if f.attr in CALLS or (f.attr in {'execute','put'} and receiver in RECEIVERS) or (f.attr=='import_module' and n.args and isinstance(n.args[0],ast.Constant) and str(n.args[0].value).split('.')[0] in BAD):out.append(f.attr)
 return out
def test_package_ast_boundary():
 from pathlib import Path
 assert not scan('\n'.join(x.read_text() for x in Path('scripts/m8r_05b_02').glob('*.py')))
def test_ast_negative_controls():
 for x in ('__import__("requests")','from importlib import import_module\nimport_module("requests")','from x import consume_authorization as consume\nconsume()','from x import mark_consumed as mark\nmark()','connection.execute("x")','queue.put(1)','runner.run_source()'):assert scan(x)
def test_ast_allowed_local_calls(): assert not scan('local_object.execute()\nlocal_collection.put(1)')
