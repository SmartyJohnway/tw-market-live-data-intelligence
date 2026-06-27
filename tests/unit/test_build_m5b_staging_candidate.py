import json, tempfile, shutil
from pathlib import Path
from scripts.build_m5b_staging_candidate import build
def test_build_staging_candidate():
    d=Path(tempfile.mkdtemp())
    base={'run_id':'x','source_id':'TWSE_OpenAPI','requested_targets':['2330','0050','00929'],'retained_targets':['2330'],'retrieved_at_utc':'2026-06-27T00:00:00+00:00','source_timestamp':None,'http_status':200,'contract_status':'partial_pass','parse_status':'parsed','normalization_status':'normalized','failed_targets':['0050','00929'],'errors':[],'caveats':[],'production_current_state':False,'realtime_guaranteed':False,'trading_signal':False,'generated_artifact_promoted':False,'frontend_published':False,'rows':[{'symbol':'2330'}]}
    (d/'bounded_probe_result.json').write_text(json.dumps(base))
    c=build(d); assert c['staging_only'] and not c['production_ready']; assert (d/'staging_candidate.json').exists()
