from pathlib import Path
import urllib.request,json,hashlib,email,zipfile,datetime
root=Path(r'C:\twmarket_temp\l6-a3-clean\repo');w=Path(r'C:\twmarket_temp\build\dependency-probe');records=[]
for p in sorted(w.glob('*.whl')):
    with zipfile.ZipFile(p) as z:
        n=next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'));m=email.message_from_bytes(z.read(n))
    url='https://pypi.org/pypi/'+m['Name']+'/'+m['Version']+'/json'
    with urllib.request.urlopen(url,timeout=30) as response:data=json.load(response)
    entries=[x for x in data['urls'] if x['filename']==p.name];assert len(entries)==1,p.name
    expected=entries[0]['digests']['sha256'];actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==expected,p.name
    records.append({'wheel_filename':p.name,'sha256':expected,'project':m['Name'],'version':m['Version'],'release_metadata_url':url,'yanked':entries[0]['yanked']})
result={'schema_version':1,'source_dependency_authority':'requirements-lock.txt','requirements_lock_sha256':hashlib.sha256((root/'requirements-lock.txt').read_bytes()).hexdigest(),'artifact_authority':'PyPI official release metadata over HTTPS; exact published wheel digest','wheels':records}
(root/'packaging_native/wheelhouse-lock.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps({'official_hash_matches':len(records),'yanked':sum(x['yanked'] for x in records)}))
