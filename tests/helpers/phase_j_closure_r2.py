"""Capture the same Closure-R1 source-boundary path, only for J1-21."""
import json
from pathlib import Path
from tests.helpers.phase_j_closure_r1 import service, seed

def read_json_utf8(path):
    """Read generated/committed JSON independently of the Windows code page."""
    return json.loads(Path(path).read_text(encoding='utf-8'))

def execute(root):
    root = Path(root)
    with service('J1-21', root) as url:
        record = seed('J1-21', root, url)
    artifacts = [p for p in (root / 'control').rglob('evidence/*.json')]
    source_path = next(p for p in artifacts if read_json_utf8(p).get('capability_id') == 'current_observation')
    artifact = read_json_utf8(source_path)
    import hashlib
    record.update(normalized_observation=artifact['records'][0], source_artifact=artifact, source_artifact_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(), source_invocations=[read_json_utf8(p) for p in sorted((root / 'invocations').glob('*.invoked'))], real_agent_sessions=0, real_agent_tool_calls=0, agent_provider_transport=0)
    return record
