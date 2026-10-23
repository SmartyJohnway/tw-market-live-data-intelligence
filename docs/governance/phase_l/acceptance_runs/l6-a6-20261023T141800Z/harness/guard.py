"""Acceptance-only Python audit guard, propagated to Python descendants."""
import os,sys
from pathlib import Path
ROOTS=[os.path.normcase(r'C:\twmarket_temp\l6-a6')]
LOG=r'C:\twmarket_temp\l6-a6\ci\guard-blocks.jsonl'
_open=open
def check(path,write=False):
    if not isinstance(path,(str,bytes,os.PathLike)):return
    value=os.path.normcase(os.path.abspath(os.fsdecode(path)))
    owner=os.path.normcase(str(Path(os.environ['USERPROFILE'])/'AppData/Local/TW-Market'))
    if value==owner or value.startswith(owner+os.sep):reject('OWNER_PRODUCTION_STATE_ACCESS',value)
    if value in {'nul',r'\\.\nul',os.path.normcase(LOG)}:return
    if write and os.environ.get('A5_READ_ONLY')=='1':reject('READ_ONLY_PROCESS_WRITE',value)
    reason='D_DRIVE_ACCESS' if value.startswith('d:') else 'OUTSIDE_WRITE' if write and not any(value==r or value.startswith(r+os.sep) for r in ROOTS) else None
    if reason:reject(reason,value)
def reject(reason,value):
    import json
    with _open(LOG,'a',encoding='utf-8') as f:f.write(json.dumps({'reason':reason,'value':str(value),'pid':os.getpid()})+'\n')
    raise PermissionError(reason)
def audit(event,args):
    if event=='open':check(args[0],bool(args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
    elif event in {'os.remove','os.rmdir','os.mkdir','os.chmod','os.utime','os.truncate'}:check(args[0],True)
    elif event in {'os.rename','os.link','os.symlink'}:check(args[0],True);check(args[1],True)
    elif event in {'os.listdir','os.scandir','os.chdir'}:check(args[0])
    elif event in {'socket.connect','socket.sendto','socket.getaddrinfo'}:
        value=args[0] if event=='socket.getaddrinfo' else args[1]
        host=value[0] if isinstance(value,tuple) else value
        if host not in {'127.0.0.1','::1','localhost',None}:reject('EXTERNAL_NETWORK_ATTEMPT',host)
import tempfile
tempfile.tempdir=os.environ['TEMP']
sys.addaudithook(audit)
for name in ('stat','lstat','readlink'):
    original=getattr(os,name)
    def wrapped(path,*a,_original=original,**kw):check(path);return _original(path,*a,**kw)
    setattr(os,name,wrapped)
import subprocess
_Popen=subprocess.Popen
class GuardedPopen(_Popen):
    def __init__(self,args,*a,**kw):
        if isinstance(args,(list,tuple)) and str(args[0]).lower().endswith(('python.exe','pythonw.exe')):
            tail=list(args[1:]);flags=[]
            while tail and tail[0] in ('-I','-B','-E','-s','-S','-u'):flags.append(tail.pop(0))
            if tail:
                mode=tail.pop(0)
                pre='import sys,runpy; runpy.run_path('+repr(__file__)+',run_name="_acceptance_guard"); '
                if mode=='-m':
                    module=tail.pop(0);code=pre+'sys.argv='+repr([module]+tail)+'; runpy.run_module('+repr(module)+',run_name="__main__",alter_sys=True)'
                elif mode=='-c':
                    source=tail.pop(0);code=pre+'sys.argv='+repr(['-c']+tail)+'; exec('+repr(source)+')'
                elif not mode.startswith('-'):
                    code=pre+'sys.argv='+repr([mode]+tail)+'; sys.path.insert(0,'+repr(os.path.dirname(os.path.abspath(mode)))+'); runpy.run_path('+repr(mode)+',run_name="__main__")'
                else:code=None
                if code:args=[args[0],*flags,'-c',code]
        super().__init__(args,*a,**kw)
subprocess.Popen=GuardedPopen
