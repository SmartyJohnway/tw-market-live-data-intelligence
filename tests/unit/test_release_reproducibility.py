import io
import tarfile
import zipfile

import pytest

from scripts.compare_release_reproducibility import compare_native,compare_docker_exports


def test_native_byte_difference_is_not_waived(tmp_path):
    a,b=tmp_path/'a.zip',tmp_path/'b.zip'
    for p in (a,b):
        with zipfile.ZipFile(p,'w') as z:z.writestr(zipfile.ZipInfo('payload',(2026,1,1,0,0,0)),b'bytes')
    assert compare_native(a,b)['status']=='PASS'
    with zipfile.ZipFile(b,'a') as z:z.comment=b'different container bytes'
    with pytest.raises(ValueError,match='NATIVE_REPRODUCIBILITY'):compare_native(a,b)


def test_docker_only_timestamp_difference_has_explicit_boundary(tmp_path):
    a,b=tmp_path/'a.tar',tmp_path/'b.tar'
    def write(p,mtime,data=b'bytes'):
        with tarfile.open(p,'w') as t:
            i=tarfile.TarInfo('app/file');i.size=len(data);i.mtime=mtime;t.addfile(i,io.BytesIO(data))
    write(a,1);write(b,2)
    result=compare_docker_exports(a,b)
    assert result['status']=='PASS' and len(result['different_mtimes'])==1
    assert not result['byte_reproducible_claim']
    write(b,2,b'tampered')
    with pytest.raises(ValueError,match='DOCKER_REPRODUCIBILITY'):compare_docker_exports(a,b)
