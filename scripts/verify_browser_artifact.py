"""Acquire/replay exact official browser archives without a mutable installer lookup."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
if not __debug__:
    raise RuntimeError('Browser verification requires assertions enabled')


def install_archive(archive, row, destination):
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==row['sha256']
    assert archive.stat().st_size==row['bytes']
    assert not destination.exists(), 'fresh browser destination required'
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            path=PurePosixPath(info.filename)
            assert not path.is_absolute() and '..' not in path.parts and ':' not in info.filename and '\\' not in info.filename
            assert not stat.S_ISLNK(info.external_attr>>16), 'unexpected archive symlink'
        destination.mkdir(parents=True)
        for info in z.infolist():
            target=destination/info.filename
            if info.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(z.read(info))
            if os.name!='nt':target.chmod((info.external_attr>>16)&0o777 or 0o644)
    assert (destination/row['executable']).is_file()
    (destination/'INSTALLATION_COMPLETE').write_bytes(b'')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--cache',type=Path)
    ap.add_argument('--acquire',action='store_true')
    a=ap.parse_args();work=a.work.resolve()
    if os.name=='nt':assert work.is_relative_to(Path(r'C:\twmarket_temp\l7-a3'))
    work.mkdir(parents=True,exist_ok=False)
    policy=json.loads((ROOT/'config/browser_artifact_authority.json').read_bytes())
    cache=a.cache or work/'archives';cache.mkdir(parents=True,exist_ok=True)
    requests=[]
    for row in policy['artifacts']:
        assert Path(row['filename']).name==row['filename']
        archive=cache/row['filename']
        if not archive.exists():
            assert a.acquire,'missing frozen browser archive'
            assert row['url'].startswith('https://cdn.playwright.dev/')
            with urllib.request.urlopen(row['url'],timeout=120) as response:
                data=response.read()
            requests.append({'url':row['url'],'bytes':len(data),'phase':'setup'})
            archive.write_bytes(data)
        install_archive(archive,row,work/'browsers'/row['install_directory'])
    result={'status':'PASS','network_requests':requests,'browser_root':str(work/'browsers'),'archives':policy['artifacts']}
    (work/'result.json').write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    if os.environ.get('GITHUB_ENV'):
        with open(os.environ['GITHUB_ENV'],'a',encoding='utf-8') as f:f.write('PLAYWRIGHT_BROWSERS_PATH='+str(work/'browsers')+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
