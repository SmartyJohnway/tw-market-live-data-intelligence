"""Acceptance instrumentation, mounted read-only; never part of the image."""
import os,sys,json,subprocess
LOG='/tmp/a5-guard-events.jsonl'
_open=open
def reject(reason,value):
    with _open(LOG,'a') as f:f.write(json.dumps({'reason':reason,'value':str(value),'pid':os.getpid()})+'\n')
    raise PermissionError(reason)
def check(path,write=False):
    if not isinstance(path,(str,bytes,os.PathLike)):return
    value=os.fsdecode(path)
    if value.lower().startswith(('d:/','d:\\')):reject('D_DRIVE_PATH_RESOLUTION',value)
    absolute=os.path.abspath(value)
    if write and (absolute=='/opt/tw-market/app' or absolute.startswith('/opt/tw-market/app/')):reject('APP_ROOT_WRITE',absolute)
def audit(event,args):
    if event=='open':check(args[0],bool(args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
    elif event in {'os.remove','os.rmdir','os.mkdir','os.chmod','os.utime','os.truncate'}:check(args[0],True)
    elif event in {'os.rename','os.link','os.symlink'}:check(args[0],True);check(args[1],True)
    elif event in {'socket.connect','socket.sendto','socket.getaddrinfo'}:
        value=args[0] if event=='socket.getaddrinfo' else args[1];host=value[0] if isinstance(value,tuple) else value
        if host not in {'127.0.0.1','::1','localhost',None}:reject('PROVIDER_OR_EXTERNAL_NETWORK_ATTEMPT',host)
sys.addaudithook(audit)
for name in ('stat','lstat','readlink'):
    original=getattr(os,name)
    def wrapped(path,*a,_original=original,**kw):check(path);return _original(path,*a,**kw)
    setattr(os,name,wrapped)
_Popen=subprocess.Popen
class GuardedPopen(_Popen):
    def __init__(self,args,*a,**kw):
        if isinstance(args,(tuple,list)) and os.path.basename(str(args[0])).startswith('python'):
            tail=list(args[1:]);flags=[]
            while tail and tail[0] in ('-I','-B','-E','-s','-S','-u'):flags.append(tail.pop(0))
            if tail:
                mode=tail.pop(0);pre='import os,sys,runpy; exec(compile(os.environ["A5_PYTHON_GUARD_SOURCE"],"<a5_guard>","exec")); '
                if mode=='-m':
                    module=tail.pop(0);code=pre+'sys.argv='+repr([module]+tail)+'; runpy.run_module('+repr(module)+',run_name="__main__",alter_sys=True)'
                elif mode=='-c':code=pre+'sys.argv='+repr(['-c']+tail[1:])+'; exec('+repr(tail[0])+')'
                elif not mode.startswith('-'):code=pre+'sys.argv='+repr([mode]+tail)+'; sys.path.insert(0,'+repr(os.path.dirname(os.path.abspath(mode)))+'); runpy.run_path('+repr(mode)+',run_name="__main__")'
                else:code=None
                if code:args=[args[0],*flags,'-c',code]
        super().__init__(args,*a,**kw)
subprocess.Popen=GuardedPopen
