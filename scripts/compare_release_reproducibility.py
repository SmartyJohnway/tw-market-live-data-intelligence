"""Compare artifact bytes and exported OCI content without claiming false byte identity."""
from __future__ import annotations
import hashlib
from pathlib import Path
import tarfile
import zipfile


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        while data:=stream.read(1024*1024):h.update(data)
    return h.hexdigest()


def compare_native(a: Path,b: Path):
    def members(p):
        with zipfile.ZipFile(p) as z:
            return [{'name':i.filename,'sha256':hashlib.sha256(z.read(i)).hexdigest(),
                'timestamp':i.date_time,'attributes':i.external_attr,'compression':i.compress_type,
                'flags':i.flag_bits,'extra':i.extra.hex(),'comment':i.comment.hex()}
                for i in z.infolist()]
    left,right=members(a),members(b)
    if left!=right or sha(a)!=sha(b):raise ValueError('L7_A3_NATIVE_REPRODUCIBILITY_UNEXPLAINED')
    return {'status':'PASS','boundary':'BYTE_FOR_BYTE_REPRODUCIBLE','zip_sha256':sha(a),
        'member_count':len(left),'members':left,'metadata_and_order_equal':True}


def exported_files(path):
    result={}
    with tarfile.open(path,'r') as archive:
        for member in archive:
            assert member.name not in result,'duplicate export member'
            stream=archive.extractfile(member) if member.isfile() else None
            h=hashlib.sha256()
            if stream:
                while data:=stream.read(1024*1024):h.update(data)
            result[member.name]={'type':member.type.hex(),'mode':member.mode,'uid':member.uid,
                'gid':member.gid,'link':member.linkname,'bytes':member.size,
                'sha256':h.hexdigest() if stream else None,'mtime':member.mtime}
    return result


def compare_docker_exports(a: Path,b: Path):
    left,right=exported_files(a),exported_files(b)
    if left.keys()!=right.keys():raise ValueError('L7_A3_DOCKER_REPRODUCIBILITY_UNEXPLAINED: member set')
    metadata=[]
    for name in sorted(left):
        l,r=left[name].copy(),right[name].copy();lm=l.pop('mtime');rm=r.pop('mtime')
        if l!=r:raise ValueError('L7_A3_DOCKER_REPRODUCIBILITY_UNEXPLAINED: content/ownership/mode/link '+name)
        if lm!=rm:metadata.append({'path':name,'a_mtime':lm,'b_mtime':rm})
    projection={n:{k:v for k,v in row.items() if k!='mtime'} for n,row in sorted(left.items())}
    import json
    return {'status':'PASS','boundary':'REPRODUCIBLE_ROOTFS_CONTENT_WITH_EXPLICIT_OCI_METADATA_BOUNDARY',
        'member_count':len(left),'content_projection_sha256':hashlib.sha256(json.dumps(projection,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'different_mtimes':metadata,'byte_reproducible_claim':False}
