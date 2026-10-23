import hashlib,json,os,pathlib,socket,subprocess,time,urllib.request
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run');out=r/'evidence-p6-run3';counter=100
env=dict(os.environ,TW_MARKET_COMPOSE_PROJECT='twmarket-l6-a5-3707c553-r3',TW_MARKET_IMAGE='tw-market-local-service:l6-a5-3707c553-replacement',TW_MARKET_DOCKER_HOST_PORT='18456')
compose=['docker','compose','-f',str(pathlib.Path(r'C:\twmarket_temp\l6-a5\repo')/'packaging_docker/compose.yaml')]
def call(name,args,expected=0):
    global counter;counter+=1
    p=subprocess.run(list(map(str,args)),env=env,cwd=pathlib.Path(r'C:\twmarket_temp\l6-a5\repo'),capture_output=True,text=True,encoding='utf-8',timeout=90)
    (out/f'{counter}-{name}.json').write_text(json.dumps({'command':list(map(str,args)),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2),encoding='utf-8')
    assert p.returncode==expected,(name,p.stderr,p.stdout);return p.stdout
try:
    call('network-up',compose+['up','-d','local-service'])
    for _ in range(60):
        try:
            if urllib.request.urlopen('http://127.0.0.1:18456/api/health',timeout=2).status==200:break
        except OSError:pass
        time.sleep(1)
    else:raise RuntimeError('health deadline')
    cid=call('cid',compose+['ps','-q','local-service']).strip();inspect=json.loads(call('inspect',['docker','inspect',cid]))[0]
    network=next(iter(inspect['NetworkSettings']['Networks'].values()));ip=network['IPAddress']
    code="import urllib.request,urllib.error\nopener=urllib.request.build_opener(urllib.request.ProxyHandler({}))\ntry:opener.open('http://"+ip+":8000/api/health',timeout=5);raise AssertionError('non-gateway peer admitted')\nexcept urllib.error.HTTPError as e:print(e.code);assert e.code==403"
    peer=call('non-gateway-peer',['docker','run','--rm','--read-only','--network','twmarket-l6-a5-3707c553-r3_default','--entrypoint','python',env['TW_MARKET_IMAGE'],'-B','-c',code]);assert peer.strip()=='403'
    addresses=json.loads(subprocess.check_output([r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe','-NoProfile','-Command',"@(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' } | ForEach-Object { [string]$_.IPAddress }) | ConvertTo-Json -Compress"],text=True,encoding='utf-8'))
    if isinstance(addresses,str):addresses=[addresses]
    probes=[]
    for address in addresses:
        try:
            with socket.create_connection((address,18456),timeout=1):reachable=True
        except OSError:reachable=False
        assert not reachable,'non-loopback Windows host interface reached published service'
        probes.append({'address_sha256':hashlib.sha256(address.encode()).hexdigest(),'reachable':reachable})
    network_result={'host_binding':inspect['HostConfig']['PortBindings'],'non_gateway_peer_http_status':403,'windows_nonloopback_interface_probes':probes,'status':'PASS'}
finally:call('network-down-preserve-volumes',compose+['down'])
env['TW_MARKET_COMPOSE_PROJECT']='twmarket-l6-a5-preinit-3707c553';env['TW_MARKET_IMAGE']='tw-market-local-service:l6-a5-3707c553'
guarded=compose+['-f',str(r/'docker-guard-override.json')]
pre='import os,sys,runpy; exec(compile(os.environ["A5_PYTHON_GUARD_SOURCE"],"<a5_guard>","exec")); '
snap="import pathlib,json,hashlib; print(json.dumps({k:{'files':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()},'directories':sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_dir())} for k,root in {'home':pathlib.Path('/var/lib/tw-market/home'),'state':pathlib.Path('/var/lib/tw-market/state')}.items()}))"
def oneshot(name,code,expected=0):return json.loads(call(name,guarded+['run','--rm','--no-deps','--entrypoint','python','local-service','-B','-c',code],expected))
before=oneshot('fresh-before',snap)
results={}
for cmd in ['status','doctor','start']:
    code=pre+"sys.argv=['scripts.tw_market',"+repr(cmd)+",'--json'];runpy.run_module('scripts.tw_market',run_name='__main__')"
    results[cmd]=oneshot('preinit-'+cmd,code,1 if cmd=='start' else 0);assert results[cmd]['status']=='INSTALLATION_NOT_INITIALIZED'
after=oneshot('fresh-after',snap);assert before==after
call('preinit-down-preserve-volumes',guarded+['down'])
data=json.loads((out/'p6_docker_portability.json').read_text(encoding='utf-8'));data.update(status='PASS',network_boundary=network_result,preinit_read_only={'before':before,'after':after,'results':results,'start_did_not_initialize':True})
(out/'p6_docker_portability.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8');print('P6 PASS')
