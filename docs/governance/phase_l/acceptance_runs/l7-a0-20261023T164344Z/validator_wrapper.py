"""Bound validator process with Python audit hooks; no live execution."""
import os
import pathlib
import runpy
import sys

BOUND = pathlib.Path(sys.argv[1]).resolve()
def audit(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'socket.sendto', 'socket.bind'):
        raise RuntimeError('A0_NETWORK_DENIED:' + event)
    if event == 'open':
        p, mode, flags = args
        if not isinstance(p, (str, bytes, os.PathLike)):
            return
        path = pathlib.Path(os.fsdecode(p))
        if path.drive.upper() == 'D:':
            raise RuntimeError('A0_D_DRIVE_DENIED')
        write = any(c in (mode or '') for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if write and not path.resolve().is_relative_to(BOUND):
            raise RuntimeError('A0_WRITE_OUTSIDE_BOUNDARY')
    if event in ('os.mkdir','os.remove','os.rmdir','os.rename'):
        for p in args[:2] if event == 'os.rename' else args[:1]:
            if isinstance(p, (str, bytes, os.PathLike)) and not pathlib.Path(os.fsdecode(p)).resolve().is_relative_to(BOUND):
                raise RuntimeError('A0_MUTATION_OUTSIDE_BOUNDARY')
sys.addaudithook(audit)
target = pathlib.Path(sys.argv[2]).resolve()
assert target.is_relative_to(BOUND / 'repo/scripts')
sys.argv = [str(target)]
sys.path.insert(0, str(BOUND / 'repo'))
runpy.run_path(str(target), run_name='__main__')
