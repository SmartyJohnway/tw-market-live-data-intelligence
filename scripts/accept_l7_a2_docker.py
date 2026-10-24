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
import urllib.request

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
        p=subprocess.run([a.docker,*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=900 if args[0]=='build' else 150)
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
        # Transport external instrumentation through dedicated named volumes.
        # No Windows filesystem bind or host file-sharing dependency is needed.
        guard_volume=prefix+'-guard';evidence_volume=prefix+'-evidence';stage=prefix+'-stage'
        docker('guard-volume','volume','create',guard_volume);docker('evidence-volume','volume','create',evidence_volume)
        docker('stage-create','create','--name',stage,'--network','none','--user','0:0','--mount',f'type=volume,source={guard_volume},target=/a2-guard','--mount',f'type=volume,source={evidence_volume},target=/a2-evidence','--entrypoint','python',prefix+':a','-c',"import os;os.chown('/a2-evidence',10001,10001)")
        active.append(stage)
        docker('stage-copy','cp',str(guard)+os.sep+'.',stage+':/a2-guard')
        docker('stage-permissions','start','-a',stage)
        docker('stage-remove','rm',stage);active.remove(stage)
        common=['--read-only','--user','10001:10001','--security-opt','no-new-privileges','--cap-drop','ALL','--pids-limit','128','--network',network,'--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777','--mount',f'type=volume,source={home},target=/var/lib/tw-market/home','--mount',f'type=volume,source={state},target=/var/lib/tw-market/state','--mount',f'type=volume,source={guard_volume},target=/a2-guard,readonly','--mount',f'type=volume,source={evidence_volume},target=/a2-evidence','-e','PYTHONPATH=/a2-guard:/opt/tw-market/app','-e','TW_MARKET_NETWORK_PROFILE=docker-local-service','--entrypoint','python']
        def one(label,*cmd,check=True):
            name=prefix+'-'+label;active.append(name)
            result=docker(label,'run','--rm','--name',name,*common,'-e','TW_MARKET_A2_GUARD_LOG=/a2-evidence/'+label+'.jsonl',prefix+':a',*cmd,check=check)
            active.remove(name);return result
        # Probe read-only pre-init and preserve the absence of identity/state.
        pre=one('preinit','/a2-guard/run.py','status',check=False)
        assert 'INSTALLATION_NOT_INITIALIZED' in pre.stdout
        predoctor=one('preinit-doctor','/a2-guard/run.py','doctor',check=False)
        assert 'INSTALLATION_NOT_INITIALIZED' in predoctor.stdout
        empty=json.loads(one('preinit-readonly','-c',"import acceptance_guard,json,pathlib;print(json.dumps({p:list(str(q.relative_to(pathlib.Path(p))) for q in pathlib.Path(p).rglob('*')) for p in ['/var/lib/tw-market/home','/var/lib/tw-market/state']}))").stdout)
        assert not any(empty.values()),empty
        init=one('init','/a2-guard/run.py','init')
        again=one('init-again','/a2-guard/run.py','init')
        assert json.loads(init.stdout)['installation']['installation_id']==json.loads(again.stdout)['installation']['installation_id']
        # The actual installation metadata is the authority; state sentinel is
        # validation-only, explicitly not a new persistence/backup contract.
        one('create-validation-witness','-c',"import acceptance_guard,pathlib;pathlib.Path('/var/lib/tw-market/state/a2-validation-witness.json').write_text('{\"validation_only\":true}')")
        witness="import acceptance_guard,json,pathlib,hashlib;h=pathlib.Path('/var/lib/tw-market/home');s=pathlib.Path('/var/lib/tw-market/state');p=s/'a2-validation-witness.json';print(json.dumps({'installation':json.loads((h/'meta/installation.json').read_text()),'state_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'durable_files':{str(q.relative_to(pathlib.Path('/var/lib/tw-market'))):hashlib.sha256(q.read_bytes()).hexdigest() for q in pathlib.Path('/var/lib/tw-market').rglob('*') if q.is_file() and '/home/logs/' not in str(q)}}))"
        before=json.loads(one('state-before','-c',witness).stdout)
        for variant in ('a','b'):
            name=prefix+'-'+variant
            active.append(name)
            docker('start-'+variant,'run','-d','--name',name,*common,'-p','127.0.0.1::8000','-e','TW_MARKET_A2_GUARD_LOG=/a2-evidence/service-'+variant+'.jsonl',prefix+':'+variant,'/a2-guard/run.py','serve')
            for attempt in range(40):
                p=docker(f'status-{variant}-{attempt}','exec',name,'python','/a2-guard/run.py','status',check=False)
                if p.returncode==0:
                    payload=json.loads(p.stdout)
                    if payload.get('status')=='RUNNING' and payload.get('service',{}).get('alive') is True:break
                time.sleep(1)
            else:raise RuntimeError('service failed to become RUNNING')
            docker('doctor-'+variant,'exec',name,'python','/a2-guard/run.py','doctor')
            endpoint=docker('port-'+variant,'port',name,'8000/tcp').stdout.strip()
            assert endpoint.startswith('127.0.0.1:') and '\n' not in endpoint
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://'+endpoint+'/api/health',timeout=10) as response:
                save('host-health-'+variant,{'status':response.status,'endpoint':endpoint,'body':response.read().decode(),'network_class':'localhost only'})
            docker('startup-'+variant,'exec',name,'python','-c',"import acceptance_guard,runpy,sys;sys.argv=['scripts/run_unified_market_evidence_mcp.py','--startup-check'];runpy.run_path('scripts/run_unified_market_evidence_mcp.py',run_name='__main__')")
            docker('config-'+variant,'inspect',name)
            app_hashes=json.loads(docker('app-hashes-'+variant,'exec',name,'python','-c',"import acceptance_guard,json,pathlib,hashlib;p=pathlib.Path('/opt/tw-market/app');print(json.dumps({'app/'+str(q.relative_to(p)):hashlib.sha256(q.read_bytes()).hexdigest() for q in p.rglob('*') if q.is_file()}))").stdout)
            assert app_hashes=={row['destination']:row['sha256'] for row in metadata['application_members']}
            docker('logs-'+variant,'logs',name)
            docker('guard-evidence-'+variant,'cp',name+':/a2-evidence/.',str(evidence))
            docker('stop-'+variant,'stop','--time','20',name);docker('remove-'+variant,'rm',name);active.remove(name)
        after=json.loads(one('state-after','-c',witness).stdout)
        assert before==after,'replacement changed installation/state'
        readback=prefix+'-readback'
        docker('readback-create','create','--name',readback,'--network','none','--mount',f'type=volume,source={evidence_volume},target=/a2-evidence','--entrypoint','python',prefix+':b','-V');active.append(readback)
        docker('readback-copy','cp',readback+':/a2-evidence/.',str(evidence))
        docker('readback-remove','rm',readback);active.remove(readback)
        events=[json.loads(line) for path in evidence.glob('*.jsonl') for line in path.read_text().splitlines()]
        assert events and not [e for e in events if e['event']=='denied']
        save('result',{'status':'PASS','source_commit':a.source_commit,'source_tree':a.source_tree,'before':before,'after':after,'images':[x['Id'] for x in images],'same_application_layers':True,'app_hashes_match_committed_manifest':True,'loopback_only_host_exposure':True,'guard_events':len(events),'external_product_network_attempts':0,'scope':'Python and inherited Python instrumentation, read-only container; no OS firewall claim','retained_resources':{'home':home,'state':state,'network':network,'guard':guard_volume,'evidence':evidence_volume},'sequence':sequence})
    except Exception as ex:
        save('result',{'status':'FAIL','error':str(ex),'sequence':sequence});raise
    finally:
        for name in active:
            docker('cleanup-logs','logs',name,check=False)
            docker('cleanup-stop','stop','--time','20',name,check=False)
            docker('cleanup-remove','rm',name,check=False)


if __name__=='__main__':main()
