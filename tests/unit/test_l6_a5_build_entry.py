from pathlib import Path

import pytest

from scripts import build_native_distribution as native
from scripts import build_docker_context as docker


@pytest.mark.parametrize('module,function', [(native, native.build), (docker, docker.build_context)])
def test_a5_build_rejects_entry_drift_before_artifact_reads(monkeypatch, tmp_path, module, function):
    def git(*args):
        return b'' if args[0] == 'status' else b'0' * 40
    monkeypatch.setattr(module, 'git' if module is native else '_git', git)
    with pytest.raises(ValueError, match='L6_A5_ENTRY_BASE_DRIFT'):
        function(tmp_path / 'one', tmp_path / 'two', acceptance_base=module.A5_BASE)
    assert not list(tmp_path.iterdir())


def test_a5_native_clean_source_with_merged_history_before_entry_is_allowed(monkeypatch, tmp_path):
    def git(*args):
        if args[0] in {'status', 'rev-list'}:
            return b''
        if args == ('rev-parse', 'origin/main'):
            return native.A5_BASE.encode()
        if args == ('show', 'HEAD:VERSION'):
            return b'1.0.0'
        if args == ('show', 'HEAD:packaging_native/resource-policy.json'):
            return b'{"members": []}'
        return native.A5_BASE.encode()
    monkeypatch.setattr(native, 'git', git)
    monkeypatch.setattr(native.subprocess, 'run', lambda *a, **k: None)
    def stop_before_wheel_reads(path):
        raise RuntimeError('artifact-stage-reached')
    monkeypatch.setattr(native, 'inspect_wheels', stop_before_wheel_reads)
    with pytest.raises(RuntimeError, match='artifact-stage-reached'):
        native.build(tmp_path / 'out', tmp_path / 'wheels', acceptance_base=native.A5_BASE)
