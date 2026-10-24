"""Acceptance-only Python filesystem/network guard; not distributed."""
import os, sys, socket
BASE = os.path.normcase(os.path.abspath(os.environ.get('TW_MARKET_ACCEPTANCE_GUARD_BASE',r'C:\twmarket_temp')))
LOG = r'C:\twmarket_temp\build\guard-events.jsonl'
_raw_open = open

def normalized(p):
    if not isinstance(p,(str,bytes,os.PathLike)): return ''
    return os.path.normcase(os.path.abspath(os.fsdecode(p)))

def reject(reason, path=None):
    import json, traceback
    record={'blocked':reason,'path':path,'pid':os.getpid(),
            'stack':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_stack(limit=7)[:-1]]}
    with _raw_open(os.environ.get('TW_MARKET_GUARD_LOG',LOG),'a',encoding='utf-8') as f: f.write(json.dumps(record)+'\n')
    raise PermissionError('acceptance guard: '+reason)

def check(p,write=False):
    if isinstance(p, str) and p.lower() in {'nul', '\\\\.\\nul'}: return
    name=normalized(p)
    if name.startswith('d:'): reject('D_DRIVE_ACCESS',name)
    owner=normalized(os.path.join(os.environ.get('USERPROFILE',''), 'AppData', 'Local', 'TW-Market'))
    if name and (name==owner or name.startswith(owner+os.sep)): reject('OWNER_PRODUCTION_STATE_ACCESS',name)
    if write and name and name != BASE and not name.startswith(BASE+os.sep) and name not in {'nul','\\\\.\\nul'}:
        reject('OUTSIDE_WRITE',name)

def audit(event,args):
    if event=='open':
        p,mode,flags=args
        write= bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        check(p,write)
    elif event in {'os.remove','os.rmdir','os.mkdir','os.chmod','os.utime','os.truncate'}: check(args[0],True)
    elif event in {'os.rename','os.link','os.symlink'}:
        check(args[0],event!='os.symlink'); check(args[1],True)
    elif event in {'os.listdir','os.scandir','os.chdir'}: check(args[0])
    elif event in {'socket.connect','socket.sendto','socket.getaddrinfo'}:
        address=args[1] if event!='socket.getaddrinfo' else args[0]
        host=address[0] if isinstance(address,tuple) else address
        if host not in {'127.0.0.1','::1','localhost',None}: reject('EXTERNAL_NETWORK')
    elif event=='subprocess.Popen':
        exe,cmd,cwd,env=args
        check(exe); check(cwd)
        seq=cmd if isinstance(cmd,(list,tuple)) else [cmd]
        for token in seq:
            if isinstance(token,str) and token.lower().startswith('d:'): reject('D_SUBPROCESS')
    elif event in {'winreg.CreateKey','winreg.SetValue','winreg.DeleteKey','winreg.DeleteValue'}: reject('REGISTRY_WRITE')
sys.addaudithook(audit)
# stat is not an audit event; block drive access before calling the OS.
for name in ('stat','lstat','readlink'):
    original=getattr(os,name)
    def wrapped(path,*args,_original=original,**kwargs):
        check(path)
        return _original(path,*args,**kwargs)
    setattr(os,name,wrapped)
sys.dont_write_bytecode=True
# Propagate instrumentation even when product launchers sanitize PYTHONPATH.
# Applied only in acceptance, and explicitly reported as Python process scope.
if os.environ.get('TW_MARKET_ACCEPTANCE_GUARD') == '1':
    import subprocess
    _Popen = subprocess.Popen
    _guard_path = __file__
    class GuardedPopen(_Popen):
        def __init__(self,args,*a,**kw):
            if isinstance(args,(list,tuple)) and str(args[0]).lower().endswith(('python.exe','pythonw.exe')):
                tail=list(args[1:]);flags=[]
                while tail and tail[0] in ('-I','-B','-E','-s','-S','-u'):
                    flags.append(tail.pop(0))
                if tail:
                    mode=tail.pop(0)
                    pre="import sys,runpy; exec(compile(open("+repr(_guard_path)+",encoding='utf-8-sig').read(),"+repr(_guard_path)+",'exec'),{'__file__':"+repr(_guard_path)+"}); "
                    if mode=='-m':
                        module=tail.pop(0);code=pre+'sys.argv='+repr([module]+tail)+"; runpy.run_module("+repr(module)+",run_name='__main__',alter_sys=True)"
                    elif mode=='-c':
                        source=tail.pop(0);code=pre+'sys.argv='+repr(['-c']+tail)+'; exec('+repr(source)+')'
                    elif not mode.startswith('-'):
                        code=pre+'sys.argv='+repr([mode]+tail)+'; sys.path.insert(0,'+repr(os.path.dirname(os.path.abspath(mode)))+'); runpy.run_path('+repr(mode)+",run_name='__main__')"
                    else:code=None
                    if code: args=[args[0],*flags,'-c',code]
            super().__init__(args,*a,**kw)
    subprocess.Popen=GuardedPopen
