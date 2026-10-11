"""Actual Local Service with test-only raw-source child and independent HTTP log."""
from pathlib import Path
import hashlib,json,os,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from server.services import unified_mode_b2_execution
from server.main import app
from scripts.run_unified_workbench import main
unified_mode_b2_execution.WRAPPER=ROOT/'tests/helpers/phase_j_closure_r1_transport.py'
@app.middleware('http')
async def acceptance_receipt(request,call_next):
    response=await call_next(request)
    # Record response bytes/IDs independently of the agent client. No headers.
    if request.url.path.startswith('/api/unified/'):
        chunks=[part async for part in response.body_iterator];body=b''.join(chunks)
        async def stream():yield body
        response.body_iterator=stream()
        try:data=json.loads(body)
        except ValueError:data={}
        result=data.get('canonical_result',{})
        record={'timestamp_ns':time.time_ns(),'method':request.method,'path':request.url.path,'http_status':response.status_code,'response_sha256':hashlib.sha256(body).hexdigest(),'response_canonical_sha256':hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'result_id':data.get('result_id') or result.get('result_id'),'audit_package_id':data.get('audit_package_id'),'control_package_id':data.get('control_package_id')}
        with Path(os.environ['PHASE_J_CLOSURE_R1_SERVER_LOG']).open('a') as f:f.write(json.dumps(record,sort_keys=True)+'\n')
    return response
if __name__=='__main__':main()
