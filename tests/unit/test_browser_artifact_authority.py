import hashlib
import zipfile

import pytest

from scripts.verify_browser_artifact import install_archive


def test_hash_verified_archive_can_replay_offline(tmp_path):
    archive=tmp_path/'browser.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('bin/browser',b'frozen browser')
    row={'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'executable':'bin/browser'}
    install_archive(archive,row,tmp_path/'installed')
    assert (tmp_path/'installed/bin/browser').read_bytes()==b'frozen browser'
    assert (tmp_path/'installed/INSTALLATION_COMPLETE').exists()
    row['sha256']='0'*64
    with pytest.raises(AssertionError):install_archive(archive,row,tmp_path/'rejected')


def test_hash_match_does_not_allow_archive_traversal(tmp_path):
    archive=tmp_path/'bad.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape',b'bad')
    row={'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'executable':'escape'}
    with pytest.raises(AssertionError):install_archive(archive,row,tmp_path/'installed')
    assert not (tmp_path/'escape').exists()
