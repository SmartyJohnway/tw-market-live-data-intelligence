"""Fresh Package C acceptance; writes only beneath the explicit C workspace.

No acquisition, provider calls or non-loopback network is authorized. Python
process guards cover this harness and inherited Python, not the whole OS.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,shutil,subprocess,sys,zipfile,socket,queue,threading,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=Path(r'C:\twmarket_temp')
EXPECTED_TOOLS={'market_describe_capabilities','market_validate_request','market_preview_request','market_read_result','market_export_ai_handoff','market_fetch_evidence'}

def fingerprint(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--zip',type=Path,required=True);ap.add_argument('--python',required=True);ap.add_argument('--run',type=Path,required=True);ap.add_argument('--guard-base',type=Path,default=WORK);a=ap.parse_args()
    guard_base=a.guard_base.resolve();assert guard_base.is_relative_to(WORK)
    run=a.run.resolve();assert run.is_relative_to(guard_base);run.mkdir(parents=True,exist_ok=False)
    logdir=run/'logs';logdir.mkdir();tmp=run/'tmp';tmp.mkdir();cwd=run/'outside cwd';cwd.mkdir()
    guard=run/'acceptance_guard.py';shutil.copyfile(ROOT/'packaging_native/acceptance_guard.py',guard)
    # Guard is installed before any child creates runtime files. Propagation is
    # explicit and independent of PYTHONPATH, which launchers deliberately clear.
    os.environ.update(TEMP=str(tmp),TMP=str(tmp),PYTHONDONTWRITEBYTECODE='1',TW_MARKET_ACCEPTANCE_GUARD='1',TW_MARKET_GUARD_LOG=str(run/'guard-events.jsonl'),TW_MARKET_ACCEPTANCE_GUARD_BASE=str(guard_base))
    exec(compile(guard.read_text(encoding='utf-8-sig'),str(guard),'exec'),{'__file__':str(guard)})
    env={k:v for k,v in os.environ.items() if not k.startswith(('TW_MARKET_','UNIFIED_MARKET_','M8R_','PYTHON'))}
    env.update(TEMP=str(tmp),TMP=str(tmp),PYTHONDONTWRITEBYTECODE='1',TW_MARKET_ACCEPTANCE_GUARD='1',TW_MARKET_GUARD_LOG=str(run/'guard-events.jsonl'),
               TW_MARKET_HOME=str(run/'home 非ASCII'),TW_MARKET_STATE_ROOT=str(run/'business state'),
               TW_MARKET_ACCEPTANCE_GUARD_BASE=str(guard_base),LOCALAPPDATA=str(run/'isolated-localappdata'),
               PATH=r'C:\Windows\System32;C:\Windows',PYTHONPATH='invalid-inherited-checkout',PYTHONHOME='invalid-inherited-home')
    # Select a free local port without contacting any provider.
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    env['TW_MARKET_PORT']=str(port)
    evidence={};sequence=[]
    def write(name,value):
        evidence[name]=value;(run/(name+'.json')).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    def command(label,args,*,stdin=None,check=True,cmd=False):
        if cmd:
            line='"'+str(args[0])+'"'+(' '+subprocess.list2cmdline(args[1:]) if len(args)>1 else '')
            args='"C:\\Windows\\System32\\cmd.exe" /d /s /c "'+line+'"'
        proc=subprocess.run(args,cwd=cwd,env=env,input=stdin,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=150)
        record={'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}
        (logdir/(label+'.json')).write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        sequence.append({'label':label,'exit_code':proc.returncode})
        if check and proc.returncode:raise AssertionError(label+': '+proc.stdout[-1200:]+' '+proc.stderr[-1200:])
        return proc
    def cli(bundle,label,*args,check=True):return command(label,[str(bundle/'tw-market.cmd'),*args],check=check,cmd=True)
    def parse(p):
        try:return json.loads(p.stdout)
        except json.JSONDecodeError:return json.loads(p.stdout.strip().splitlines()[-1])
    def extract(label):
        location=run/label;location.mkdir()
        with zipfile.ZipFile(a.zip) as z:
            for n in z.namelist():assert not Path(n).is_absolute() and '..' not in Path(n).parts
            z.extractall(location)
        return next(location.iterdir())
    def bootstrap(bundle,label):
        clean=dict(env);clean.pop('PYTHONPATH',None);clean.pop('PYTHONHOME',None)
        old=env.copy();env.clear();env.update(clean)
        try:return command(label,[a.python,'-B',str(bundle/'bootstrap/bootstrap.py')])
        finally:env.clear();env.update(old)
    try:
        A=extract('Location A With Spaces 非ASCII');B=extract('Location-B')
        tamper=[]
        for relative in ('app/VERSION','distribution-manifest.json'):
            target=B/relative;original=target.read_bytes()
            target.write_bytes(original+b' altered')
            clean=env.copy();env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
            try:rejected=command('tamper-'+target.name,[a.python,'-B',str(B/'bootstrap/bootstrap.py')],check=False)
            finally:env.clear();env.update(clean);target.write_bytes(original)
            assert rejected.returncode!=0 and not (B/'runtime').exists()
            tamper.append({'member':relative,'rejected':True,'runtime_created':False})
        write('distribution_manifest_verification',{'tamper_cases':tamper,'fail_closed_before_runtime':True})
        boot=bootstrap(A,'bootstrap-A');second=bootstrap(A,'bootstrap-A-again')
        assert parse(second)['status']=='verified-existing'
        assert not Path(env['TW_MARKET_HOME']).exists()
        write('bootstrap_acceptance',{'first':parse(boot),'second':parse(second),'home_created':False,'offline_flags':'--no-index --find-links --only-binary=:all: --require-hashes','scope':'Python process and inherited Python guard'})
        # Add acceptance-only instrumentation to each created runtime. The
        # portable app/ and its manifest remain untouched.
        def instrument(bundle):
            pth=bundle/'runtime/venv/Lib/site-packages/acceptance_guard.pth'
            code="import builtins; exec(compile(builtins.open("+repr(str(guard))+",encoding='utf-8-sig').read(),"+repr(str(guard))+",'exec'),{'__file__':"+repr(str(guard))+"})\n"
            pth.write_text(code,encoding='utf-8')
        instrument(A)
        before=fingerprint(A/'app')
        pre=parse(cli(A,'preinit','status','--json'))
        assert pre['status']=='INSTALLATION_NOT_INITIALIZED' and not Path(env['TW_MARKET_HOME']).exists()
        pre_doctor=parse(cli(A,'preinit-doctor','doctor','--json'))
        assert pre_doctor['status']=='INSTALLATION_NOT_INITIALIZED' and not Path(env['TW_MARKET_HOME']).exists()
        write('preinit_package_acceptance',{'payload':pre,'doctor':pre_doctor,'home_created':False})
        init=parse(cli(A,'init','init','--json'))
        assert init['installation']['installation_status']=='READY'
        assert init['identity']['status']=='NOT_INITIALIZED'
        again=parse(cli(A,'init-again','init','--json'))
        assert again['installation']['installation_id']==init['installation']['installation_id']
        write('initialized_package_acceptance',init)
        quoted=parse(cli(A,'quoted-cli-args','status','--json','--home',env['TW_MARKET_HOME'],'--state-root',env['TW_MARKET_STATE_ROOT']))
        assert quoted['installation']['installation_id']==init['installation']['installation_id']
        code="import sys,json,os;sys.path.insert(0,"+repr(str(A/'app'))+");from scripts.tw_market_installation import resolve_installation;from scripts.product_version import product_version;from scripts.m8r_08g_security_master_releases import _commit;print(json.dumps({'sys_path':sys.path,'sys_executable':sys.executable,'version':product_version(),'installation':resolve_installation().as_dict(),'source_commit':_commit()}))"
        probe=parse(command('isolation-A',[str(A/'runtime/venv/Scripts/python.exe'),'-I','-B','-c',code]))
        assert all(str(ROOT).lower() not in p.lower() for p in probe['sys_path'])
        assert all('tools-venv' not in p.lower() for p in probe['sys_path'])
        assert probe['sys_executable']==str(A/'runtime/venv/Scripts/python.exe')
        assert not (A/'.git').exists();write('sys_path_isolation',probe)
        # Capture failure evidence rather than treating historical start failure
        # as a current defect. Final acceptance requires successful lifecycle.
        start=cli(A,'start','start','--json',check=False);payload=parse(start)
        write('lifecycle_start_attempt',payload)
        if payload['status']!='STARTED':
            inst=init['installation'];runtime=Path(inst['runtime_root'])
            owners={p.name:p.read_text() for p in runtime.glob('service-*.json')}
            write('service_start_failure_adjudication',{'outcome':'UNRESOLVED','payload':payload,'ownership_markers':owners,'environment':{k:env[k] for k in ['TEMP','TMP','TW_MARKET_HOME','TW_MARKET_STATE_ROOT','TW_MARKET_PORT']},'cwd':str(A/'app')})
            debugenv=env.copy();debugenv.pop('PYTHONHOME',None);debugenv.pop('PYTHONPATH',None);debugenv['TW_MARKET_LIFECYCLE_INSTANCE']='acceptance-debug'
            try:
                p=subprocess.run([str(A/'runtime/venv/Scripts/python.exe'),'-B','-m','scripts.tw_market_lifecycle','_serve','--host','127.0.0.1','--port',str(port)],cwd=A/'app',env=debugenv,capture_output=True,text=True,timeout=12)
                write('service_foreground_diagnostic',{'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
            except subprocess.TimeoutExpired as ex:write('service_foreground_diagnostic',{'timeout':True,'stdout':str(ex.stdout),'stderr':str(ex.stderr)})
            raise AssertionError('lifecycle start failed: '+payload.get('reason_code','unknown'))
        def business_fingerprint():
            return {k:v for k,v in fingerprint(Path(env['TW_MARKET_HOME'])).items() if not k.startswith('logs/')},fingerprint(Path(env['TW_MARKET_STATE_ROOT']))
        readonly_before=business_fingerprint()
        status=parse(cli(A,'running-status','status','--json'));doctor=parse(cli(A,'doctor','doctor','--json'))
        assert readonly_before==business_fingerprint()
        write('doctor_read_only',{'status':'PASS','HOME_STATE_unchanged':True})
        mcp=command('mcp-startup',[str(A/'tw-market-mcp.cmd'),'--startup-check'],cmd=True)
        frames=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'a3-acceptance','version':'1'}}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}}]
        # Keep stdin open until each corresponding protocol response arrives.
        # A batch followed immediately by EOF can cancel pending SDK requests.
        line='"C:\\Windows\\System32\\cmd.exe" /d /s /c ""'+str(A/'tw-market-mcp.cmd')+'""'
        proc=subprocess.Popen(line,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',bufsize=1)
        incoming=queue.Queue();stdout=[];stderr=[];replies=[];sent=[]
        def read_stdout():
            for line in proc.stdout:
                stdout.append(line);incoming.put(json.loads(line))
            incoming.put(None)
        def read_stderr():
            stderr.extend(proc.stderr.readlines())
        reader=threading.Thread(target=read_stdout,daemon=True);errors=threading.Thread(target=read_stderr,daemon=True)
        reader.start();errors.start()
        def send(frame):
            sent.append(frame);proc.stdin.write(json.dumps(frame)+'\n');proc.stdin.flush()
        def response(request_id):
            deadline=time.monotonic()+45
            while True:
                item=incoming.get(timeout=max(0.01,deadline-time.monotonic()))
                if item is None:raise AssertionError('MCP EOF before response '+str(request_id))
                replies.append(item)
                if item.get('id')==request_id:
                    assert 'result' in item and 'error' not in item,item
                    return item
        try:
            send(frames[0]);response(1)
            send(frames[1]);send(frames[2]);response(2)
            proc.stdin.close();exit_code=proc.wait(timeout=20)
            reader.join(timeout=5);errors.join(timeout=5)
            assert exit_code==0
        finally:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
            write('mcp_interactive_protocol',{'sent':sent,'responses':replies,'stdout':''.join(stdout),'stderr':''.join(stderr),'exit_code':proc.returncode,'stdin_closed_after_tools_response':any(x.get('id')==2 for x in replies)})
        raw=subprocess.CompletedProcess(line,exit_code,''.join(stdout),''.join(stderr))
        sequence.append({'label':'mcp-stdio-interactive','exit_code':exit_code})
        tools=next(x['result']['tools'] for x in replies if x.get('id')==2)
        assert {t['name'] for t in tools}==EXPECTED_TOOLS and len(tools)==6
        write('mcp_package_acceptance',{'startup_exit':mcp.returncode,'stdio_exit':raw.returncode,'tool_names':sorted(t['name'] for t in tools),'public_tool_count':len(tools),'responses':replies})
        sm=parse(command('sm-status',[str(A/'tw-market-security-master.cmd'),'status'],cmd=True))
        assert sm['status']=='NOT_INITIALIZED'
        assert init['installation']['security_master_root']==str(Path(env['TW_MARKET_STATE_ROOT'])/'security-master')
        assert Path(init['installation']['temp_root']).is_relative_to(tmp)
        write('security_master_package_acceptance',sm)
        stop=parse(cli(A,'stop','stop','--json'));assert stop['status']=='STOPPED'
        write('lifecycle_acceptance',{'start':payload,'status':status,'doctor':doctor,'stop':stop})
        write('app_root_write_guard',{'before':before,'after':fingerprint(A/'app'),'equal':before==fingerprint(A/'app')})
        assert before==fingerprint(A/'app')
        # CLI parser exit propagation and actual quoted argument preservation.
        bad=cli(A,'invalid-cli','unknown-command',check=False);assert bad.returncode==2
        write('launcher_acceptance',{'unknown_command_exit':bad.returncode,'paths_with_spaces_and_non_ascii':True,'home':env['TW_MARKET_HOME'],'inherited_python_environment_cleared':True})
        beforemeta=(Path(env['TW_MARKET_HOME'])/'meta/installation.json').read_bytes()
        settings=Path(init['installation']['settings_path'])
        settings_before=settings.read_bytes() if settings.exists() else b''
        bootstrap(B,'bootstrap-B');instrument(B)
        beforeB=fingerprint(B/'app')
        relocated=parse(cli(B,'relocation-status','status','--json'))
        assert relocated['installation']['installation_id']==init['installation']['installation_id']
        assert relocated['installation']['state_root']==init['installation']['state_root']
        assert (Path(env['TW_MARKET_HOME'])/'meta/installation.json').read_bytes()==beforemeta
        assert (settings.read_bytes() if settings.exists() else b'')==settings_before
        assert beforeB==fingerprint(B/'app')
        # Simulate a stale moved runtime using a copied marker, not venv relocation.
        marker=B/'runtime/runtime-marker.json';saved=marker.read_bytes();old=json.loads(saved);old['bundle_root']=str(A);marker.write_text(json.dumps(old))
        stale=bootstrap(B,'stale-runtime') if False else None
        clean=env.copy();env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
        try:stale=command('stale-runtime',[a.python,'-B',str(B/'bootstrap/bootstrap.py')],check=False)
        finally:env.clear();env.update(clean)
        assert stale.returncode!=0 and 'relocated' in stale.stderr;marker.write_bytes(saved)
        write('distribution_relocation_probe',{'name':'A3_DISTRIBUTION_RELOCATION_PROBE','APP_ROOT_A':str(A/'app'),'APP_ROOT_B':str(B/'app'),'same_installation_id':relocated['installation']['installation_id'],'same_state_root':relocated['installation']['state_root'],'settings_unchanged':True,'independent_local_venvs':True,'stale_marker_rejected':True,'app_B_immutable':True})
        guard_log=run/'guard-events.jsonl'
        events=[json.loads(line) for line in guard_log.read_text().splitlines()] if guard_log.exists() else []
        assert not events, 'guard denied an operation; inspect guard-events.jsonl'
        write('final_result',{'status':'PASS','sequence':sequence,'scope':'Python process/inherited Python; not OS-wide','guard_events':events,'provider_acquisition_attempts':0,'external_network_attempts':0,'source_commit':probe['source_commit']})
    except Exception as ex:
        write('final_result',{'status':'FAIL','error':str(ex),'sequence':sequence});raise
    finally:
        # Always stop through the product's validated ownership mechanism.
        if 'A' in locals():
            try:cli(A,'cleanup-stop','stop','--json',check=False)
            except Exception:pass
    print(str(run))
if __name__=='__main__':main()
