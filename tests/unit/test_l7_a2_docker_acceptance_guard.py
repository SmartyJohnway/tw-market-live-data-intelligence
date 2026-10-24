"""Exercise argv enforcement without installing process-global audit hooks."""
import ast
import io
import json
import os
from pathlib import Path

import pytest


def guarded_class():
    path=Path(__file__).resolve().parents[2]/'packaging_docker/acceptance_guard.py'
    definition=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='GuardedPopen')
    seen=[]
    class Popen:
        def __init__(self,args,*a,**kw):seen.append(args)
    def reject(reason,value):raise PermissionError(reason)
    namespace={'_Popen':Popen,'reject':reject,'os':os,'json':json,'_open':lambda *a:io.StringIO(),'LOG':'unused'}
    exec(compile(ast.Module(body=[definition],type_ignores=[]),str(path),'exec'),namespace)
    return namespace['GuardedPopen'],seen


def test_only_exact_readonly_identity_probe_is_anchored_to_base_binary():
    guard,seen=guarded_class()
    guard(['uname','-p'])
    assert seen==[['/bin/uname','-p']]


@pytest.mark.parametrize('args', [['uname','-a'],['uname','-p','extra'],['sh','-c','uname -p'],['curl','https://example.invalid'],['/tmp/uname','-p']])
def test_other_native_children_remain_rejected_before_execution(args):
    guard,seen=guarded_class()
    with pytest.raises(PermissionError,match='UNOBSERVED_NATIVE_CHILD'):guard(args)
    assert not seen
