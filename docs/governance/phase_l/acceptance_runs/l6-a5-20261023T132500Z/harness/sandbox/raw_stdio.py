"""Acceptance JSON-RPC probe; no tool calls and no native taskkill subprocess."""
import json,queue,subprocess,threading,time

def probe(command,args,env,cwd):
    p=subprocess.Popen([str(command),*map(str,args)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,cwd=str(cwd))
    lines=queue.Queue();errors=[]
    def reader():
        for line in p.stdout:lines.put(line)
        lines.put(None)
    def stderr_reader():
        for line in p.stderr:errors.append(line.decode('utf-8',errors='replace'))
    threading.Thread(target=reader,daemon=True).start();threading.Thread(target=stderr_reader,daemon=True).start()
    def send(data):p.stdin.write(json.dumps(data).encode()+b'\n');p.stdin.flush()
    def receive(id):
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            raw=lines.get(timeout=max(.1,deadline-time.monotonic()))
            if raw is None:raise RuntimeError('MCP exited before response: '+''.join(errors))
            data=json.loads(raw)
            if data.get('id')==id:
                if 'error' in data:raise RuntimeError(str(data['error']))
                return data['result']
        raise TimeoutError('MCP response deadline')
    try:
        send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'a5-offline-acceptance','version':'1'}}})
        initialized=receive(1)
        send({'jsonrpc':'2.0','method':'notifications/initialized'})
        send({'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}})
        listed=receive(2);names=sorted(t['name'] for t in listed['tools'])
        assert names==['market_describe_capabilities','market_export_ai_handoff','market_fetch_evidence','market_preview_request','market_read_result','market_validate_request']
        p.stdin.close();code=p.wait(timeout=15)
        assert code==0,errors
        return {'status':'PASS','initialize':initialized,'names':names,'tool_count':len(names),'tool_calls':0,'transport':'binary UTF-8 JSON-RPC stdio','exit_code':code,'stderr':errors}
    finally:
        if p.poll() is None:p.terminate();p.wait(timeout=10)
