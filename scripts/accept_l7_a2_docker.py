"""Fresh-state and replacement proof using the canonical Docker context builder."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_docker_context import build_context


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--docker',required=True)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--wheelhouse',type=Path,required=True)
    ap.add_argument('--source-commit',required=True)
    ap.add_argument('--source-tree',required=True)
    a=ap.parse_args();work=a.work.resolve()
    if os.name=='nt' and not work.is_relative_to(Path(r'C:\twmarket_temp\l7-a2')):raise ValueError('bounded A2 workspace required')
    work.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        (work/(name+'.json')).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    sequence=[]
    def docker(label,*args,check=True):
        p=subprocess.run([a.docker,*args],capture_output=True,text=True,encoding='utf-8',errors='replace')
        save(label,{'args':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});sequence.append(label)
        if check and p.returncode:raise RuntimeError(label+' failed')
        return p
    prefix='tw-market-l7-a2-'+str(time.time_ns())
    home=prefix+'-home';state=prefix+'-state';network=prefix+'-network'
    active=[]
    try:
        save('context',build_context(a.wheelhouse.resolve(),work/'context',release_validation_source=a.source_commit,release_validation_tree=a.source_tree))
        docker('environment','version','--format','{{json .}}')
        base='python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741'
        docker('base-identity','image','inspect',base)
        metadata=json.loads((work/'context/build-metadata.json').read_text())
        images=[]
        for variant in ('a','b'):
            image=prefix+':'+variant
            docker('build-'+variant,'build','--network','none','--pull=false','--build-arg','SOURCE_TREE='+a.source_tree,'--build-arg','DEPENDENCY_LOCK_SHA256='+hashlib.sha256((ROOT/'packaging_docker/dependency-lock-linux-amd64-cp313.json').read_bytes()).hexdigest(),'--label','org.opencontainers.image.revision='+a.source_commit,'--label','org.twmarket.validation-variant='+variant,'-t',image,str(work/'context'))
            images.append(json.loads(docker('image-'+variant,'image','inspect',image).stdout)[0])
        assert images[0]['Id']!=images[1]['Id']
        assert images[0]['RootFS']==images[1]['RootFS'],'replacement must retain exact application layers'
        docker('volume-home','volume','create',home);docker('volume-state','volume','create',state)
        docker('network','network','create','--driver','bridge',network)
        guard=work/'guard';guard.mkdir();shutil.copyfile(ROOT/'packaging_docker/acceptance_guard.py',guard/'acceptance_guard.py')
        (guard/'run.py').write_text("import acceptance_guard,runpy;runpy.run_module('scripts.tw_market_docker',run_name='__main__',alter_sys=True)\n")
        evidence=work/'guard-evidence';evidence.mkdir()
        common=['--read-only','--user','10001:10001','--security-opt','no-new-privileges','--cap-drop','ALL','--pids-limit','128','--network',network,'--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777','--mount',f'type=volume,source={home},target=/var/lib/tw-market/home','--mount',f'type=volume,source={state},target=/var/lib/tw-market/state','--mount',f'type=bind,source={guard},target=/a2-guard,readonly','--mount',f'type=bind,source={evidence},target=/a2-evidence','-e','PYTHONPATH=/a2-guard:/opt/tw-market/app','-e','TW_MARKET_NETWORK_PROFILE=docker-local-service','--entrypoint','python']
        def one(label,*cmd,check=True):
            return docker(label,'run','--rm',*common,'-e','TW_MARKET_A2_GUARD_LOG=/a2-evidence/'+label+'.jsonl',prefix+':a',*cmd,check=check)
        # Probe read-only pre-init and preserve the absence of identity/state.
        pre=one('preinit','/a2-guard/run.py','status',check=False)
        assert 'INSTALLATION_NOT_INITIALIZED' in pre.stdout
        predoctor=one('preinit-doctor','/a2-guard/run.py','doctor',check=False)
        assert 'INSTALLATION_NOT_INITIALIZED' in predoctor.stdout
        init=one('init','/a2-guard/run.py','init')
        again=one('init-again','/a2-guard/run.py','init')
        # The actual installation metadata is the authority; state sentinel is
        # validation-only, explicitly not a new persistence/backup contract.
        witness="import acceptance_guard,json,pathlib,hashlib;h=pathlib.Path('/var/lib/tw-market/home');s=pathlib.Path('/var/lib/tw-market/state');p=s/'a2-validation-witness.json';p.write_text('{\"validation_only\":true}') if not p.exists() else None;print(json.dumps({'installation':json.loads((h/'meta/installation.json').read_text()),'state_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))"
        before=json.loads(one('state-before','-c',witness).stdout)
        for variant in ('a','b'):
            name=prefix+'-'+variant
            docker('start-'+variant,'run','-d','--name',name,*common,'-e','TW_MARKET_A2_GUARD_LOG=/a2-evidence/service-'+variant+'.jsonl',prefix+':'+variant,'/a2-guard/run.py','serve');active.append(name)
            for attempt in range(40):
                p=docker(f'status-{variant}-{attempt}','exec',name,'python','/a2-guard/run.py','status',check=False)
                if 'RUNNING' in p.stdout:break
                time.sleep(1)
            else:raise RuntimeError('service failed to become RUNNING')
            docker('doctor-'+variant,'exec',name,'python','/a2-guard/run.py','doctor')
            docker('startup-'+variant,'exec',name,'python','-c',"import acceptance_guard,runpy,sys;sys.argv=['server/mcp_server.py','--startup-check'];runpy.run_path('server/mcp_server.py',run_name='__main__')")
            docker('config-'+variant,'inspect',name)
            docker('logs-'+variant,'logs',name)
            docker('stop-'+variant,'stop','--time','20',name);docker('remove-'+variant,'rm',name);active.remove(name)
        after=json.loads(one('state-after','-c',witness).stdout)
        assert before==after,'replacement changed installation/state'
        events=[json.loads(line) for path in evidence.glob('*.jsonl') for line in path.read_text().splitlines()]
        assert events and not [e for e in events if e['event']=='denied']
        save('result',{'status':'PASS','source_commit':a.source_commit,'source_tree':a.source_tree,'before':before,'after':after,'images':[x['Id'] for x in images],'same_application_layers':True,'guard_events':len(events),'external_product_network_attempts':0,'scope':'Python and inherited Python instrumentation, read-only container; no OS firewall claim','retained_resources':{'home':home,'state':state,'network':network},'sequence':sequence})
    except Exception as ex:
        save('result',{'status':'FAIL','error':str(ex),'sequence':sequence});raise
    finally:
        for name in active:
            docker('cleanup-logs','logs',name,check=False)
            docker('cleanup-stop','stop','--time','20',name,check=False)
            docker('cleanup-remove','rm',name,check=False)


if __name__=='__main__':main()
