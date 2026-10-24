"""Process-local test execution containment, including Python/Node descendants.

This is a CI harness, not an OS firewall or a product network policy.
"""
from __future__ import annotations
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys

_installed = False


def install() -> None:
    global _installed
    if _installed:
        return
    _installed = True
    log = os.environ['TW_MARKET_CI_GUARD_LOG']
    bound = os.path.normcase(os.path.abspath(os.environ['TW_MARKET_CI_BOUND']))
    original_open = open
    def record(event, **details):
        with original_open(log, 'a', encoding='utf-8') as stream:
            stream.write(json.dumps({'event':event,'pid':os.getpid(),**details},sort_keys=True)+'\n')
    def reject(reason, value):
        record('denied', reason=reason, value=str(value))
        raise PermissionError('DETERMINISTIC_CI_' + reason)
    def check(path, write=False):
        if not isinstance(path,(str,bytes,os.PathLike)):
            return
        value=os.path.normcase(os.path.abspath(os.fsdecode(path)))
        if value.startswith('d:'):
            reject('D_DRIVE_ACCESS',value)
        if value in {os.path.normcase(log),os.path.normcase(os.devnull), 'nul', r'\\.\nul'}:
            return
        owner=os.path.normcase(str(Path(os.environ.get('USERPROFILE','~'))/'AppData/Local/TW-Market'))
        if value==owner or value.startswith(owner+os.sep):
            reject('PRODUCTION_STATE_ACCESS',value)
        if write and value!=bound and not value.startswith(bound+os.sep):
            reject('WRITE_OUTSIDE_BOUNDARY',value)
    def loopback(host):
        if isinstance(host,bytes):host=host.decode('ascii','strict')
        if host=='localhost':return True
        try:return ipaddress.ip_address(host).is_loopback
        except ValueError:return False
    def audit(event,args):
        if event=='open':
            check(args[0],bool(args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        elif event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.utime','os.truncate'}:check(args[0],True)
        elif event in {'os.rename','os.link','os.symlink'}:check(args[0],True);check(args[1],True)
        elif event in {'os.listdir','os.scandir','os.chdir'}:check(args[0])
        elif event in {'socket.connect','socket.sendto','socket.getaddrinfo'}:
            value=args[0] if event=='socket.getaddrinfo' else args[1]
            host=value[0] if isinstance(value,tuple) else value
            if not loopback(host):reject('EXTERNAL_NETWORK_ATTEMPT',host)
        elif event in {'os.system','os.posix_spawn','os.spawn','os.exec','os.fork','os.startfile','os.startfile/2'}:
            reject('UNOBSERVED_NATIVE_PROCESS',event)
    sys.addaudithook(audit)
    for name in ('stat','lstat','readlink'):
        original=getattr(os,name)
        def wrapped(path,*args,_original=original,**kwargs):
            check(path)
            return _original(path,*args,**kwargs)
        setattr(os,name,wrapped)
    original_popen=subprocess.Popen
    guard=str(Path(__file__).resolve())
    node_guard=str(Path(__file__).with_name('deterministic_ci_node_guard.cjs').resolve())
    class GuardedPopen(original_popen):
        def __init__(self,args,*pos,**kwargs):
            if kwargs.get('shell') or not isinstance(args,(list,tuple)) or not args:
                reject('UNOBSERVED_NATIVE_PROCESS',args)
            executable=str(kwargs.get('executable') or args[0]);check(executable)
            name=Path(executable).name.lower()
            env=dict(os.environ if kwargs.get('env') is None else kwargs['env'])
            for key in list(env):
                if key.lower() in {'http_proxy','https_proxy','all_proxy'}:env.pop(key)
            env.update(TW_MARKET_CI_GUARD_LOG=log,TW_MARKET_CI_BOUND=bound,PYTHONDONTWRITEBYTECODE='1')
            if name in {'python','python.exe','pythonw.exe','python3','python3.11','python3.13'} or executable==sys.executable:
                tail=list(args[1:]);flags=[]
                while tail:
                    if tail[0] in ('-I','-E','-S','-s','-B','-u'):
                        flags.append(tail.pop(0))
                    elif tail[0]=='-X' and len(tail)>1 and tail[1]=='utf8':
                        flags.extend(tail[:2]);tail=tail[2:]
                    else:break
                if tail in (['--version'],['-V']):
                    record('child_identity_only',executable=executable)
                else:
                    if not tail:reject('UNOBSERVED_PYTHON_MODE',args)
                    mode=tail.pop(0)
                    # Install containment before site/custom-site code can run.
                    original_no_site='-S' in flags
                    if not original_no_site:flags.append('-S')
                    pre='import sys,runpy;runpy.run_path('+repr(guard)+',run_name="_deterministic_ci_guard");'
                    if not original_no_site:pre+='import site;site.main();'
                    if mode=='-m' and tail:
                        module=tail.pop(0);code=pre+'sys.argv='+repr([module]+tail)+';runpy.run_module('+repr(module)+',run_name="__main__",alter_sys=True)'
                    elif mode=='-c' and tail:
                        source=tail.pop(0);code=pre+'sys.argv='+repr(['-c']+tail)+';exec('+repr(source)+')'
                    elif not mode.startswith('-'):
                        code=pre+'sys.argv='+repr([mode]+tail)+';sys.path.insert(0,'+repr(str(Path(mode).absolute().parent))+');runpy.run_path('+repr(mode)+',run_name="__main__")'
                    else:reject('UNOBSERVED_PYTHON_MODE',args)
                    args=[args[0],*flags,'-c',code]
                    record('child_python_injected',executable=executable)
            elif name in {'node','node.exe'}:
                # The only Node surface is the explicit deterministic JS state contract.
                if len(args)<4 or args[1]!='-e' or not str(args[-1]).endswith('workbench-state.js'):
                    reject('UNOBSERVED_NODE_MODE',args)
                args=[args[0],'--require',node_guard,*args[1:]]
                record('child_node_injected',executable=executable)
            elif name in {'git','git.exe'}:
                allowed={'show','diff','rev-parse','rev-list','ls-tree','ls-files','status','log','merge-base','cat-file','hash-object','init','add','commit','config','check-ignore','branch'}
                if len(args)<2 or str(args[1]) not in allowed:
                    reject('UNOBSERVED_GIT_OPERATION',args)
                if any(str(x).lower().startswith(('https:','http:','ssh:','git:','d:')) for x in args[1:]):
                    reject('GIT_NETWORK_OR_FORBIDDEN_PATH',args)
                record('child_git_local',operation=str(args[1]))
            else:reject('UNOBSERVED_NATIVE_PROCESS',args)
            kwargs['env']=env
            super().__init__(args,*pos,**kwargs)
    subprocess.Popen=GuardedPopen
    record('guard_loaded',python=sys.version.split()[0])


if __name__ == '_deterministic_ci_guard':
    install()
