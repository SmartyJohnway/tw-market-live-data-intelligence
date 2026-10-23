import hashlib,json,os,pathlib,subprocess,sys,time,urllib.request
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run');out=r/'evidence-p6-run3';out.mkdir(exist_ok=True)
env=dict(os.environ,TW_MARKET_COMPOSE_PROJECT='twmarket-l6-a5-3707c553-r3',TW_MARKET_IMAGE='tw-market-local-service:l6-a5-3707c553',TW_MARKET_DOCKER_HOST_PORT='18456',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
compose=['docker','compose','-f',str(pathlib.Path(r'C:\twmarket_temp\l6-a5\repo')/'packaging_docker/compose.yaml')]
pre='import os,sys,runpy; exec(compile(os.environ["A5_PYTHON_GUARD_SOURCE"],"<a5_guard>","exec")); '
override={'services':{'local-service':{'entrypoint':['python','-B','-c',pre+"sys.argv=['scripts.tw_market_docker','serve']; runpy.run_module('scripts.tw_market_docker',run_name='__main__')"],'environment':{'A5_PYTHON_GUARD_SOURCE':(r/'docker-guard/python_guard.py').read_text(encoding='utf-8')}}}}
(r/'docker-guard-override.json').write_text(json.dumps(override),encoding='utf-8')
guarded=compose+['-f',str(r/'docker-guard-override.json')]
counter=0
def save(name,data):(out/(name+'.json')).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
def call(name,args,expected=0,timeout=90):
    global counter;counter+=1
    p=subprocess.run(list(map(str,args)),env=env,cwd=pathlib.Path(r'C:\twmarket_temp\l6-a5\repo'),capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    record={'command':list(map(str,args)),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr};save(f'{counter:03d}-{name}',record)
    assert p.returncode==expected,(name,p.returncode,p.stderr,p.stdout)
    return p.stdout
def jsoncall(name,args,**kw):return json.loads(call(name,args,**kw))
def fresh(command):
    code=pre+"sys.argv=['scripts.tw_market',"+repr(command)+",'--json']; runpy.run_module('scripts.tw_market',run_name='__main__')"
    return jsoncall('fresh-'+command,guarded+['run','--rm','--no-deps','--entrypoint','python','local-service','-B','-c',code])
fingerprint="import hashlib,json,pathlib; roots={'home':pathlib.Path('/var/lib/tw-market/home'),'state':pathlib.Path('/var/lib/tw-market/state'),'app':pathlib.Path('/opt/tw-market/app')}; print(json.dumps({k:{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and not (k=='home' and p.relative_to(root).parts[0] in {'logs','cache'})} for k,root in roots.items()}))"
def snap():return jsoncall('fingerprints',guarded+['exec','-T','local-service','python','-B','-c',fingerprint])
def ready():
    for _ in range(60):
        try:
            with urllib.request.urlopen('http://127.0.0.1:18456/api/health',timeout=2) as response:
                if response.status==200:return
        except OSError:pass
        time.sleep(1)
    raise RuntimeError('Docker service health deadline')
def probes(label):
    ready();status=jsoncall(label+'-status',guarded+['exec','-T','local-service','python','-m','scripts.tw_market','status','--json'])
    before=snap();doctor=jsoncall(label+'-doctor',guarded+['exec','-T','local-service','python','-m','scripts.tw_market','doctor','--json']);after=snap();assert before==after
    assert status['installation']['installation_status']=='READY'
    cid=call(label+'-cid',compose+['ps','-q','local-service']).strip()
    inspection=jsoncall(label+'-inspect',['docker','inspect',cid])[0]
    assert inspection['HostConfig']['ReadonlyRootfs'] and inspection['Config']['User']=='10001:10001'
    binding=inspection['HostConfig']['PortBindings']['8000/tcp'];assert binding==[{'HostIp':'127.0.0.1','HostPort':'18456'}]
    guard=call(label+'-guard-log',guarded+['exec','-T','local-service','python','-c',"from pathlib import Path;p=Path('/tmp/a5-guard-events.jsonl'); print(p.read_text() if p.exists() else '')"])
    assert not guard.strip()
    write=call(label+'-app-write-os-guard',guarded+['exec','-T','local-service','python','-c',"import errno;from pathlib import Path\ntry:Path('/opt/tw-market/app/.a5-write-probe').write_text('reject')\nexcept OSError as e:print(e.errno);assert e.errno==errno.EROFS\nelse:raise AssertionError('APP_ROOT writable')"]);assert write.strip()=='30'
    return {'status':status,'doctor':doctor,'fingerprints':before,'container_id':cid,'binding':binding,'guard_events':0}
try:
    source_image=jsoncall('source-image',['docker','image','inspect',env['TW_MARKET_IMAGE']])[0]
    prestatus=fresh('status');predoctor=fresh('doctor')
    assert prestatus['status']=='INSTALLATION_NOT_INITIALIZED' and predoctor['status']=='INSTALLATION_NOT_INITIALIZED'
    first_init=fresh('init');second_init=fresh('init');assert first_init['installation']['installation_id']==second_init['installation']['installation_id']
    call('up-source',guarded+['up','-d','local-service']);first=probes('source')
    assert first['fingerprints']['state']=={}
    paths=json.loads((r/'evidence-host-run4/packaged-runtime-paths.json').read_text(encoding='utf-8'));bundle=pathlib.Path(paths['bundle']);home=r/'installations/p6-host-mcp'
    call('host-mcp-init',[bundle/'runtime/venv/Scripts/python.exe','-B',bundle/'bootstrap/launch.py','market','init','--home',home,'--json'])
    sys.path.insert(0,str(r/'sandbox/input'));from raw_stdio import probe
    mcp=probe(bundle/'runtime/venv/Scripts/python.exe',['-B',bundle/'bootstrap/launch.py','mcp','--home',home,'--service-url','http://127.0.0.1:18456'],dict(env,TW_MARKET_HOME=str(home)),bundle);save('source-host-mcp',mcp)
    call('source-down-preserve-volumes',guarded+['down'])
    volumes=jsoncall('retained-volumes',['docker','volume','inspect','twmarket-l6-a5-3707c553-r3_home','twmarket-l6-a5-3707c553-r3_state'])
    replacement='tw-market-local-service:l6-a5-3707c553-replacement'
    call('no-cache-rebuild',['docker','build','--platform','linux/amd64','--network','none','--no-cache','--build-arg','SOURCE_TREE=946e765b26b2520f623672dc49a51c913139f44f','--build-arg','DEPENDENCY_LOCK_SHA256=4dce92718699974d74e62845884f3887d6471299967e52b3a2b1191562fd7a88','--tag',replacement,'--file',r/'build/docker-final/Dockerfile',r/'build/docker-final'],timeout=300)
    replaced_image=jsoncall('replacement-image',['docker','image','inspect',replacement])[0];assert replaced_image['Id']!=source_image['Id']
    env['TW_MARKET_IMAGE']=replacement
    call('up-replacement',guarded+['up','-d','local-service']);second=probes('replacement')
    assert first['fingerprints']==second['fingerprints']
    assert first['status']['installation']['installation_id']==second['status']['installation']['installation_id']
    second_mcp=probe(bundle/'runtime/venv/Scripts/python.exe',['-B',bundle/'bootstrap/launch.py','mcp','--home',home,'--service-url','http://127.0.0.1:18456'],dict(env,TW_MARKET_HOME=str(home)),bundle);save('replacement-host-mcp',second_mcp)
    call('guarded-down',guarded+['down']);call('default-runtime-up',compose+['up','-d','local-service']);ready()
    default_status=jsoncall('default-runtime-status',compose+['exec','-T','local-service','python','-m','scripts.tw_market','status','--json'])
    assert default_status['installation']['installation_id']==first_init['installation']['installation_id']
    default_fingerprint=jsoncall('default-fingerprints',compose+['exec','-T','local-service','python','-c',fingerprint]);assert default_fingerprint==first['fingerprints']
    save('p6_docker_portability',{'status':'PASS_PENDING_NETWORK_PEER_PROBE','source_image_id':source_image['Id'],'replacement_image_id':replaced_image['Id'],'installation_id':first_init['installation']['installation_id'],'source':first,'replacement':second,'default_runtime_status':default_status,'host_mcp':[mcp,second_mcp],'volume_names':[v['Name'] for v in volumes],'network_guard_scope':'Python network audit propagated to Local Service and Python descendants during guarded source/replacement; final default entrypoint also probed','provider_attempts':0,'state_survived':True,'image_publications':0})
finally:
    p=subprocess.run(compose+['logs','--no-color','--tail','40'],env=env,cwd=pathlib.Path(r'C:\twmarket_temp\l6-a5\repo'),capture_output=True,text=True,encoding='utf-8',timeout=30)
    save('final-runtime-logs',{'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode})
    call('stop-and-down-preserve-volumes',compose+['down'])
