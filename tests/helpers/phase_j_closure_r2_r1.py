"""Capture a production-reachable retrieved-only fixture using existing harness."""
import hashlib
import json
from pathlib import Path
from tests.helpers.phase_j_closure_r1 import service, seed, ROOT

def execute(root):
    root = Path(root)
    with service('J1-04', root, launcher=ROOT / 'tests/helpers/phase_j_closure_r2_r1_server.py') as url:
        record = seed('J1-04', root, url)
    source_path = next(p for p in (root / 'control').rglob('evidence/*.json')
                       if json.loads(p.read_text()).get('capability_id') == 'current_observation')
    artifact = json.loads(source_path.read_text())
    record.update(case_id='TWSE_MIS_RETRIEVED_ONLY_RECENT',
                  normalized_observation=artifact['records'][0], source_artifact=artifact,
                  source_artifact_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                  source_invocations=[json.loads(p.read_text()) for p in sorted((root / 'invocations').glob('*.invoked'))],
                  real_agent_sessions=0, real_agent_tool_calls=0, agent_provider_transport=0)
    return record
