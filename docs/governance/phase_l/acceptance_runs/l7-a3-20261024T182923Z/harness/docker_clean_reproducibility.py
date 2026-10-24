import sys,subprocess,json,hashlib,time,tarfile
from pathlib import Path
r=Path(r'C:\twmarket_temp\l7-a3\repo');sys.path.insert(0,str(r))
from scripts.build_docker_context import build_context
from scripts.compare_release_reproducibility import compare_docker_exports
out=r.parent/'docker-reproducibility-clean';out.mkdir();docker=r'C:\Users\weitang\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'
def save(n,x):(out/(n+'.json')).write_bytes((json.dumps(x,indent=2,sort_keys=True)+'\n').encode())
def run(n,*args,timeout=900):
 p=subprocess.run([docker,*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout);save(n,dict(args=args,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,n;return p.stdout
source='ab2b2dc941aea68187145166a519757622d092e8';tree='1ccdb3e77ca99972d965a3f7eb771d2807fd7e73';lock=hashlib.sha256((r/'packaging_docker/dependency-lock-linux-amd64-cp313.json').read_bytes()).hexdigest()
run('engine','version','--format','{{json .}}');run('buildx','buildx','version')
images=[]
for name in ['a','b']:
 context=out/('context-'+name);save('context-'+name,build_context(r.parent/'artifacts/linux',context,release_validation_source=source,release_validation_tree=tree))
 tag='tw-market-l7-a3-repro-clean:'+name;container='tw-market-l7-a3-repro-clean-'+name
 run('build-'+name,'build','--no-cache','--network','none','--pull=false','--platform','linux/amd64','--build-arg','SOURCE_TREE='+tree,'--build-arg','DEPENDENCY_LOCK_SHA256='+lock,'--label','org.opencontainers.image.revision='+source,'-t',tag,str(context))
 image=json.loads(run('image-'+name,'image','inspect',tag))[0];images.append(image)
 run('create-'+name,'create','--name',container,'--network','none',tag)
 try:run('export-'+name,'export','-o',str(out/(name+'.tar')),container)
 finally:run('remove-'+name,'rm',container)
 run('save-'+name,'image','save','-o',str(out/('image-'+name+'.tar')),tag)
 with tarfile.open(out/('image-'+name+'.tar')) as t:
  manifest=json.load(t.extractfile('manifest.json'));save('manifest-'+name,manifest)
  save('config-'+name,json.load(t.extractfile(manifest[0]['Config'])))
 print('built/exported',name,image['Id'],flush=True)
assert images[0]['Config']==images[1]['Config'],'runtime config differs'
comparison=compare_docker_exports(out/'a.tar',out/'b.tar');comparison.update(image_ids=[i['Id'] for i in images],RootFS=[i['RootFS'] for i in images],runtime_config_equal=True,source_commit=source,source_tree=tree,dependency_lock_sha256=lock,base_digest='sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741',clean_no_cache_builds=2)
if images[0]['Id']==images[1]['Id']:comparison['boundary']='BYTE_IDENTICAL_IMAGE_CONFIG_AND_ROOTFS';comparison['byte_reproducible_claim']=True
save('comparison',comparison);print(comparison['boundary'],flush=True)
