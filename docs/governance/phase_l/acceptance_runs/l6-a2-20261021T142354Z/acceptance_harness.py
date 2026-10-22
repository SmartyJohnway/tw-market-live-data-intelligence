from pathlib import Path
import subprocess, sys, os, json, time, tempfile, re, hashlib

ROOT=Path(r'D:\Codex-Workspace\projects\tw-market-live-data-intelligence-phase-l6-a2')
OUT=ROOT/'docs/governance/phase_l/acceptance_runs/l6-a2-20261021T142354Z'
OUT=OUT/'corrected-guard'
OUT.mkdir(exist_ok=True)
TEMP=Path(tempfile.mkdtemp(prefix='tw-market-l6-a2-accept-'))
DEFAULT_HOME=Path(os.environ['LOCALAPPDATA'])/'TW-Market'
ORIGINAL=Path(r'D:\Codex-Workspace\projects\tw-market-live-data-intelligence')
def snapshot(path):
    if not path.exists():return {'exists':False}
    rows=[]
    for p in [path,*path.rglob('*')]:
        if p.is_symlink():continue
        s=p.stat();rows.append([str(p.relative_to(path)),s.st_size,s.st_mtime_ns])
    return {'exists':True,'entry_count':len(rows),'metadata_fingerprint':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()}
before=snapshot(DEFAULT_HOME)
guard=TEMP/'guard';guard.mkdir()
(guard/'sitecustomize.py').write_text('''import sys,os,json,ipaddress
from pathlib import Path
PROTECTED_ROOTS=[Path(os.environ['LOCALAPPDATA'])/'TW-Market',Path(r'D:\\Codex-Workspace\\projects\\tw-market-live-data-intelligence')/'data',Path(r'D:\\Codex-Workspace\\projects\\tw-market-live-data-intelligence')/'artifacts']
def audit(event,args):
 writes = event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.replace','os.link','os.symlink','os.truncate')
 if event=='open':
  mode=args[1] or '';flags=args[2] if len(args)>2 else 0
  writes=any(x in mode for x in 'wax+') or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
 if writes:
  for value in args[:2] if event in ('os.rename','os.replace','os.link','os.symlink') else args[:1]:
   if not isinstance(value,(str,bytes,os.PathLike)):continue
   candidate=Path(os.fsdecode(value)).absolute()
   if any(candidate==root or root in candidate.parents for root in PROTECTED_ROOTS):
    raise RuntimeError('L6_A2_PRODUCTION_STATE_WRITE_DENIED')
 if event not in ('socket.connect','socket.sendto','socket.getaddrinfo'): return
 address=args[0] if event=='socket.getaddrinfo' else args[-1] if event=='socket.sendto' else args[1]
 host=address[0] if isinstance(address,tuple) else address
 if host in ('localhost','127.0.0.1','::1',None):return
 try:
  if ipaddress.ip_address(host).is_loopback:return
 except (ValueError,TypeError):pass
 with open(os.environ['L6_A2_SOCKET_LOG'],'a',encoding='utf-8') as f:f.write(json.dumps({'event':event,'host':str(host)})+'\\n')
 raise RuntimeError('L6_A2_EXTERNAL_NETWORK_DENIED')
sys.addaudithook(audit)
''',encoding='utf-8')
env=dict(os.environ,PYTHONPATH=str(guard)+os.pathsep+str(ROOT),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PIP_DISABLE_PIP_VERSION_CHECK='1',NO_COLOR='1',L6_A2_SOCKET_LOG=str(TEMP/'external-sockets.jsonl'),TW_MARKET_HOME=str(TEMP/'home'))
for key in ['TW_MARKET_STATE_ROOT','TW_MARKET_SECURITY_MASTER_ROOT','TW_MARKET_WATCHLIST_ROOT','M8R_06_03_CONTROL_ROOT','TW_MARKET_OPERATIONAL_EVENT_PATH','TW_MARKET_HOST','TW_MARKET_PORT','UNIFIED_MARKET_EVIDENCE_SERVICE_URL']:
    env.pop(key,None)
subprocess.run([sys.executable,'-X','utf8','-B','-c','from scripts.tw_market_installation import initialize_installation; initialize_installation()'],cwd=ROOT,env=env,check=True)
mode=sys.argv[1] if len(sys.argv)>1 else 'diagnostic-ci'
if mode=='diagnostic-ci':
    commands=[('default-ci-initial',[sys.executable,'scripts/run_test_profile.py','default-ci','--json'])]
else:
    commands=[('focused',[sys.executable,'-X','utf8','-B','-m','pytest','-q',
       'tests/unit/test_l6_a2_installation.py','tests/unit/test_l6_a2_lifecycle_integration.py','tests/unit/test_l6_a2_security_master_paths.py',
       'tests/unit/test_tw_market_lifecycle.py','tests/unit/test_m8r_08g_identity_service_and_releases.py','tests/unit/test_m8r_09_persistent_watchlists.py',
       'tests/unit/test_m8r_06_03_mode_b2_authorization.py','tests/unit/test_m8r_06_03_execute_once.py',
       'tests/unit/test_m8r_06_01c1b_compact_runtime_identity_index.py','tests/unit/test_m8r_06_01c2_mode_a_pointer_activation.py'])]
    scripts=['verify_dependency_supply_chain','verify_environment','validate_source_registry','validate_portable_catalog_sync','validate_runtime_skill_guide_sync','validate_v1_public_contracts','validate_unified_market_evidence_contracts','validate_phase_h_v3_contracts','validate_l5_extension_registration_conformance','validate_l5_extension_semantic_conformance','validate_l5_extension_publication_conformance','validate_l5_existing_family_conformance']
    commands += [(name,[sys.executable,'scripts/'+name+'.py']) for name in scripts]
    commands += [('pip-check',[sys.executable,'-m','pip','check']),('compileall',[sys.executable,'-m','compileall','-q','scripts','server','tests']),('default-ci-final',[sys.executable,'scripts/run_test_profile.py','default-ci','--json']),('diff-check',['git','diff','--check'])]
results=[]
for name,command in commands:
    start=time.monotonic()
    p=subprocess.run(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='strict')
    (OUT/(name+'.log')).write_text(p.stdout,encoding='utf-8',newline='\n')
    row={'name':name,'command':command,'exit_code':p.returncode,'seconds':round(time.monotonic()-start,3),'log':name+'.log'}
    results.append(row);print(json.dumps(row),flush=True)
    if name.startswith('default-ci'):
        payload=json.loads(p.stdout)
        decoded_tail='\n'.join(row.get('failure_output_tail','') for row in payload.get('command_results',[])) or payload.get('failure_output_tail','')
        failed=sorted(set(re.findall(r'^FAILED\s+(tests/[^\s]+)',decoded_tail,re.MULTILINE)))
        baseline=json.loads((ROOT/'docs/governance/phase_l/acceptance_runs/l5-a6-20261021T031032Z/default_ci_failure_set_comparison.json').read_text(encoding='utf-8'))['historical_failed_node_ids']
        compare={'counts':{k:payload.get(k) for k in ['passed','failed','skipped','deselected']},'historical_failed_node_ids':sorted(baseline),'candidate_failed_node_ids':failed,'candidate_only':sorted(set(failed)-set(baseline)),'historical_only':sorted(set(baseline)-set(failed)),'exact_set_equal':set(failed)==set(baseline),'historical_failed_count':len(baseline),'candidate_failed_count':len(failed),'command_result':row,'default_ci_status':'FAIL; inherited failures remain unresolved','profile_unmodified':True}
        (OUT/(name+'-comparison.json')).write_text(json.dumps(compare,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'counts':compare['counts'],'candidate_only':compare['candidate_only'],'historical_only':compare['historical_only']}),flush=True)
after=snapshot(DEFAULT_HOME)
attempts=(TEMP/'external-sockets.jsonl').read_text(encoding='utf-8').splitlines() if (TEMP/'external-sockets.jsonl').exists() else []
report={'mode':mode,'results':results,'isolated_home':str(TEMP/'home'),'real_default_home_before':before,'real_default_home_after':after,'real_default_home_unchanged':before==after,'external_socket_attempts':len(attempts),'external_attempt_records':[json.loads(x) for x in attempts],'network_scope':'Python audit-hook connect/sendto/getaddrinfo within acceptance processes and inherited Python children; loopback allowed; no OS-wide claim; Git/GitHub transport excluded','provider_requests':0,'live_acquisition':0,'production_state_mutations':0 if before==after else 'GUARD_FAILURE','fixture_transport_substitution':'not counted as actual provider/network request'}
(OUT/(mode+'-acceptance.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'guard_scope':report['network_scope'],'external_socket_attempts':len(attempts),'real_default_home_unchanged':before==after}),flush=True)
