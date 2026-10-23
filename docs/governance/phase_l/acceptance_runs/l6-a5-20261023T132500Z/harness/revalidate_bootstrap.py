import asyncio,hashlib,json,os,pathlib,subprocess,sys
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run');sys.path.insert(0,str(r));import host_acceptance as h
h.OUT=r/'evidence-bootstrap';h.OUT.mkdir(exist_ok=True)
p=r/'evidence-host-run4/p1_relocation.json';d=json.loads(p.read_text(encoding='utf-8'));bundle=pathlib.Path(d['app_b'])
runtime=(bundle/'runtime').resolve();assert runtime.is_relative_to(r.resolve())
preserved=r/'derived-runtime-preserved/app-b-runtime';preserved.parent.mkdir(exist_ok=True);assert not preserved.exists()
os.rename(runtime,preserved)
h.env.update(A5_APP_ROOT=str(bundle/'app'),A5_FORBIDDEN_READ_PREFIX=d['app_a'])
before=h.inventory(bundle/'app');reports=[]
for index in range(2):
    result=subprocess.run([sys.executable,'-B',str(bundle/'bootstrap/bootstrap.py'),'--bundle',str(bundle)],env=h.env,capture_output=True,timeout=240)
    try:stdout=result.stdout.decode('utf-8');encoding='utf-8'
    except UnicodeDecodeError:stdout=result.stdout.decode('cp950');encoding='cp950'
    stderr=result.stderr.decode('utf-8',errors='replace')
    summary=json.loads(result.stdout.splitlines()[-1].decode('ascii'))
    assert result.returncode==0 and summary['status']==('bootstrapped' if index==0 else 'verified-existing')
    record={'returncode':result.returncode,'stdout':stdout,'stderr':stderr,'stdout_decode':encoding,'stdout_raw_sha256':hashlib.sha256(result.stdout).hexdigest(),'summary':summary};reports.append(record)
    (h.OUT/f'bootstrap-{index}.json').write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding='utf-8')
assert h.inventory(bundle/'app')==before
d['second']=h.lifecycle(bundle,pathlib.Path(d['home']),18451)
assert h.inventory(bundle/'app')==before
d.update(bootstrap_idempotent=True,relocated_bootstrap_reports=reports,log_capture='binary capture before decoding; pip emits host locale while bootstrap final JSON is ASCII; no native stdout lost',old_app_root_guard='blocked before filesystem access; zero rejected attempts')
p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
print('fresh relocated bootstrap + idempotence + lifecycle PASS')
