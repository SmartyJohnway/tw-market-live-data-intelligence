"""Deterministic read-only publication payload scan using shared MCPB provenance policy."""
from __future__ import annotations
import argparse
import hashlib
import io
import re
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from packaging_mcpb.hygiene import scan,wheel_members,SECRET
from scripts.build_mcpb_distribution import inspect_wheels


def validate_artifact(path,wheelhouse=None):
    path=Path(path)
    accepted=inspect_wheels(Path(wheelhouse)) if wheelhouse else []
    provenance=wheel_members(Path(wheelhouse),accepted) if wheelhouse else {}
    accepted_wheels={row['wheel_filename']:row['wheel_sha256'] for row in accepted}
    observations=[]
    observed_native_wheels=set()
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
                data=z.read(info)
                nested=re.fullmatch(r'TW-Market-1\.5\.1-windows-x64/wheelhouse/([^/]+\.whl)',name)
                if nested:
                    wheel_name=nested.group(1)
                    expected=accepted_wheels.get(wheel_name)
                    # Never classify opaque compressed wheel bytes as host paths.
                    # Admission requires the exact upstream locked wheel SHA and
                    # independent per-member scan of the original, decompressed ZIP.
                    if expected is None or hashlib.sha256(data).hexdigest()!=expected:
                        observations.append({'member':name,'rule':'NATIVE_WHEEL_UNPROVEN',
                                             'classification':'FIRST_PARTY_LEAKAGE','blocking':True})
                        continue
                    observed_native_wheels.add(wheel_name)
                    with zipfile.ZipFile(io.BytesIO(data)) as wheel_zip:
                        members=wheel_zip.infolist()
                        if len({x.filename.casefold() for x in members})!=len(members):
                            observations.append({'member':name,'rule':'NATIVE_WHEEL_DUPLICATE_MEMBER',
                                                 'classification':'FIRST_PARTY_LEAKAGE','blocking':True})
                        for wm in members:
                            if wm.is_dir():continue
                            if ((wm.external_attr>>16)&0o170000)==0o120000:
                                observations.append({'member':name+'!/'+wm.filename,'rule':'UNSAFE_SYMLINK',
                                                     'classification':'FIRST_PARTY_LEAKAGE','blocking':True})
                            member_name='server/lib/'+wm.filename
                            member_proof=provenance.get(member_name)
                            for row in scan(member_name,wheel_zip.read(wm),member_proof):
                                row['nested_native_wheel']=wheel_name
                                row['member']=name+'!/'+wm.filename
                                observations.append(row)
                    continue
                rows=scan(name,data,provenance.get(name))
                # Exact committed operator documentation describes a generic
                # Windows environment variable, not a retained private path.
                if (name=='TW-Market-1.5.1-windows-x64/README-PACKAGE.md'
                    and data==(ROOT/'packaging_native/README-PACKAGE.md').read_bytes()):
                    for row in rows:
                        if row['rule']=='LOCAL_STATE_REFERENCE':
                            row.update(rule='DOCUMENTED_OPERATOR_STATE_ENV_PLACEHOLDER',
                                       blocking=False,classification='GENERIC_WINDOWS_ENVIRONMENT_VARIABLE')
                observations.extend(rows)
                parts=name.replace('\\','/').split('/')
                if parts[0] in {'tests','docs'} and ('governance' in parts or parts[0]=='tests') or name.startswith(('app/tests/','app/docs/governance/phase_l/')):
                    observations.append({'member':name,'rule':'REPOSITORY_EVIDENCE_OR_TEST','classification':'FIRST_PARTY_LEAKAGE','blocking':True})
    else:
        observations=scan(path.name,path.read_bytes())
    if (path.name=='TW-Market-1.5.1-windows-x64.zip' and wheelhouse
        and observed_native_wheels != set(accepted_wheels)):
        observations.append({'member':path.name,'rule':'NATIVE_WHEELHOUSE_INCOMPLETE',
                             'classification':'FIRST_PARTY_LEAKAGE','blocking':True})
    blocking=[r for r in observations if r['blocking']]
    return {'artifact':path.name,'status':'PASS' if not blocking else 'FAIL','blocking_count':len(blocking),'observations':observations}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('files',nargs='+',type=Path); p.add_argument('--wheelhouse',type=Path)
    a=p.parse_args(); results=[validate_artifact(path,a.wheelhouse) for path in a.files]
    print(json.dumps(results,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if all(r['status']=='PASS' for r in results) else 1)
