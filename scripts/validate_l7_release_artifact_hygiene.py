"""Deterministic read-only publication payload scan using shared MCPB provenance policy."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from packaging_mcpb.hygiene import scan,wheel_members
from scripts.build_mcpb_distribution import inspect_wheels


def validate_artifact(path,wheelhouse=None):
    path=Path(path)
    provenance=wheel_members(Path(wheelhouse),inspect_wheels(Path(wheelhouse))) if wheelhouse else {}
    observations=[]
    if path.suffix.lower() in {'.zip','.mcpb'}:
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
            if len(set(n.casefold() for n in names))!=len(names):
                raise ValueError('duplicate ZIP member')
            for info in z.infolist():
                if info.is_dir(): continue
                name=info.filename
                if ((info.external_attr>>16)&0o170000)==0o120000:
                    observations.append({'member':name,'rule':'UNSAFE_SYMLINK','classification':'FIRST_PARTY_LEAKAGE','blocking':True})
                observations.extend(scan(name,z.read(info),provenance.get(name)))
                parts=name.replace('\\','/').split('/')
                if parts[0] in {'tests','docs'} and ('governance' in parts or parts[0]=='tests') or name.startswith(('app/tests/','app/docs/governance/phase_l/')):
                    observations.append({'member':name,'rule':'REPOSITORY_EVIDENCE_OR_TEST','classification':'FIRST_PARTY_LEAKAGE','blocking':True})
    else:
        observations=scan(path.name,path.read_bytes())
    blocking=[r for r in observations if r['blocking']]
    return {'artifact':path.name,'status':'PASS' if not blocking else 'FAIL','blocking_count':len(blocking),'observations':observations}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('files',nargs='+',type=Path); p.add_argument('--wheelhouse',type=Path)
    a=p.parse_args(); results=[validate_artifact(path,a.wheelhouse) for path in a.files]
    print(json.dumps(results,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if all(r['status']=='PASS' for r in results) else 1)
