"""External validation instrumentation; never copied into the application image."""
import ipaddress
import json
import os
import subprocess
import sys

_open=open
LOG=os.environ['TW_MARKET_A2_GUARD_LOG']


def reject(reason,value):
    with _open(LOG,'a') as stream:
        stream.write(json.dumps({'event':'denied','reason':reason,'value':str(value),'pid':os.getpid()})+'\n')
    raise PermissionError('A2_ACCEPTANCE_'+reason)


def check(path,write=False):
    if not isinstance(path,(str,bytes,os.PathLike)):return
    value=os.fsdecode(path)
    if value.lower().startswith('d:'):reject('D_DRIVE',value)
    value=os.path.abspath(value)
    if write and value!='/dev/null' and not any(value==p or value.startswith(p+'/') for p in ('/tmp','/var/lib/tw-market','/a2-evidence')):
        reject('WRITE_OUTSIDE_STATE',value)


def audit(event,args):
    if event=='open':check(args[0],bool(args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
    elif event in ('os.mkdir','os.remove','os.rmdir','os.chmod','os.utime','os.truncate'):check(args[0],True)
    elif event in ('os.rename','os.link','os.symlink'):check(args[0],True);check(args[1],True)
    elif event in ('socket.connect','socket.sendto','socket.getaddrinfo'):
        value=args[0] if event=='socket.getaddrinfo' else args[1]
        host=value[0] if isinstance(value,tuple) else value
        try:allowed=host=='localhost' or ipaddress.ip_address(host).is_loopback
        except ValueError:allowed=False
        if not allowed:reject('EXTERNAL_NETWORK_ATTEMPT',host)
    elif event in ('os.system','os.posix_spawn','os.exec','os.fork'):reject('UNOBSERVED_NATIVE_CHILD',event)


sys.addaudithook(audit)
_Popen=subprocess.Popen


class GuardedPopen(_Popen):
    def __init__(self,args,*a,**kw):
        if not isinstance(args,(list,tuple)) or kw.get('shell'):
            reject('UNOBSERVED_NATIVE_CHILD',args)
        executable=str(args[0])
        if os.path.basename(executable).startswith('python'):
            tail=list(args[1:]);flags=[]
            while tail and tail[0] in ('-B','-I','-E','-s','-S','-u'):flags.append(tail.pop(0))
            if not tail:reject('UNOBSERVED_PYTHON_MODE',args)
            mode=tail.pop(0)
            pre="import sys,runpy;exec(compile(open('/a2-guard/acceptance_guard.py').read(),'/a2-guard/acceptance_guard.py','exec'));"
            if mode=='-m':
                module=tail.pop(0);code=pre+'sys.argv='+repr([module]+tail)+";runpy.run_module("+repr(module)+",run_name='__main__',alter_sys=True)"
            elif mode=='-c':code=pre+tail.pop(0)
            elif not mode.startswith('-'):
                code=pre+'sys.argv='+repr([mode]+tail)+";runpy.run_path("+repr(mode)+",run_name='__main__')"
            else:reject('UNOBSERVED_PYTHON_MODE',args)
            args=[executable,*flags,'-c',code]
        elif list(args)==['uname','-p']:
            # CPython platform._Processor.from_subprocess uses this exact
            # read-only identity probe. Anchor it to the pinned base binary.
            args=['/bin/uname','-p']
            with _open(LOG,'a') as stream:
                stream.write(json.dumps({'event':'allowed_native_identity_probe','argv':args,'pid':os.getpid()})+'\n')
        elif args!=['git','rev-parse','HEAD']:
            reject('UNOBSERVED_NATIVE_CHILD',args)
        super().__init__(args,*a,**kw)


subprocess.Popen=GuardedPopen
with _open(LOG,'a') as stream:
    stream.write(json.dumps({'event':'guard_installed','pid':os.getpid()})+'\n')
