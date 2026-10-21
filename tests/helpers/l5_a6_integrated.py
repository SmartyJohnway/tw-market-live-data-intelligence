"""Explicit two-family acceptance harness, never runtime authority or discovery."""
from __future__ import annotations

import asyncio
from copy import deepcopy
import hashlib
from contextlib import ExitStack
import json
import ipaddress
import os
from pathlib import Path
import socket
from unittest.mock import patch

import httpx

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = ('monthly_revenue', 'material_disclosures')


def request_for(market):
    code = '2330' if market == 'TWSE' else '6488'
    return {'schema_version': 'unified_market_evidence_request.v3',
            'request_id': f'l5-a6-{market.lower()}', 'execution_mode': 'execute',
            'targets': [{'input': f'{market}:{code}', 'resolution_requirement': 'exact'}],
            'data_needs': [{'type': f, 'priority': 'required', 'parameters': {}} for f in FAMILIES]}


def run_trace(root: Path, market='TWSE', scenario='positive'):
    from scripts.run_v1_workbench_browser_e2e import bootstrap_deterministic_fixture_release
    from scripts.m8r_06_01c2_mode_a_security_master_loader import reset_production_mode_a_security_master_for_tests
    from server.main import app
    from server.services import unified_mode_b2 as b2, unified_mode_c as c, unified_mode_b2_execution as execution
    from server.unified_mcp.local_service_client import UnifiedLocalServiceClient
    from server.unified_mcp.server import dispatch_safe_tool
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot

    root.mkdir(parents=True, exist_ok=True)
    bootstrap_deterministic_fixture_release(root / 'security', eligible_targets=('TWSE:2330', 'TPEX:6488'))
    control = root / 'control'
    log = root / 'transport.jsonl'
    original = httpx.AsyncClient
    class InProcessClient(original):
        def __init__(self, *args, **kwargs):
            kwargs['transport'] = httpx.ASGITransport(app=app)
            super().__init__(*args, **kwargs)

    attempts = []
    original_connect, original_connect_ex = socket.socket.connect, socket.socket.connect_ex
    original_getaddrinfo = socket.getaddrinfo
    def is_loopback(host):
        try: return host == 'localhost' or ipaddress.ip_address(host).is_loopback
        except ValueError: return False
    def guarded(original):
        def reject(sock, address):
            if isinstance(address, tuple) and is_loopback(address[0]):
                return original(sock, address)  # Windows asyncio self-pipe only; ASGI uses no socket.
            attempts.append(str(address))
            raise AssertionError('A6_UNEXPECTED_PARENT_SOCKET')
        return reject
    def guarded_dns(host,*args,**kwargs):
        if is_loopback(host): return original_getaddrinfo(host,*args,**kwargs)
        attempts.append(str(host))
        raise AssertionError('A6_UNEXPECTED_PARENT_DNS')
    env = {'TW_MARKET_SECURITY_MASTER_ROOT': str(root / 'security'),
           'M8R_06_03_CONTROL_ROOT': str(control), 'M8R_06_03_EXECUTION_ENVIRONMENT': 'test',
           'M8R_06_03_TEST_SOURCE_TRANSPORT': 'deterministic', 'L5_A6_CODE': '2330' if market == 'TWSE' else '6488',
           'L5_A6_SCENARIO': scenario, 'L5_A6_TRANSPORT_LOG': str(log),
           'L5_A6_SOCKET_LOG':str(root/'socket_denials.jsonl'),
           'TW_MARKET_OPERATIONAL_EVENT_PATH':str(root / 'operational.jsonl'),
           'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}
    reset_production_mode_a_security_master_for_tests()
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, env))
            stack.enter_context(patch.object(b2, 'CONTROL_ROOT', control))
            stack.enter_context(patch.object(c, 'CONTROL_ROOT', control))
            # Existing accepted raw-transport child bootstrap pattern; fixed
            # wrapper.main(), ticket, claim and production registry still run.
            stack.enter_context(patch.object(execution, 'WRAPPER', ROOT / 'tests/helpers/l5_a6_source_transport.py'))
            stack.enter_context(patch('server.unified_mcp.local_service_client.httpx.AsyncClient', InProcessClient))
            stack.enter_context(patch.object(socket.socket, 'connect', guarded(original_connect)))
            stack.enter_context(patch.object(socket.socket, 'connect_ex', guarded(original_connect_ex)))
            stack.enter_context(patch.object(socket, 'getaddrinfo', guarded_dns))
            snapshot = build_tool_contract_snapshot()
            client = UnifiedLocalServiceClient('http://127.0.0.1:8000')
            request = request_for(market)
            async def lifecycle():
                records = {}
                rejections = {}
                for mutation in ('financial_statements', 'capability_id', 'extra_capability_id'):
                    bad = deepcopy(request)
                    if mutation == 'financial_statements': bad['data_needs'][0]['type'] = mutation
                    elif mutation == 'capability_id': bad['data_needs'][0]['capability_id'] = bad['data_needs'][0].pop('type')
                    else: bad['data_needs'][0]['capability_id'] = bad['data_needs'][0]['type']
                    r = await dispatch_safe_tool('market_validate_request', {'request':bad}, client=client, tool_contract_snapshot=snapshot)
                    assert r.isError and r.structuredContent == {'error':'invalid_tool_arguments'}
                    rejections[mutation] = r.structuredContent
                for name, args in (
                    ('market_describe_capabilities', {}),
                    ('market_validate_request', {'request': request}),
                    ('market_preview_request', {'request': request}),
                    ('market_fetch_evidence', {'request': request}),
                ):
                    r = await dispatch_safe_tool(name, args, client=client, tool_contract_snapshot=snapshot)
                    assert not r.isError, (name, r)
                    records[name] = r.structuredContent
                    if name == 'market_preview_request':
                        bad = deepcopy(request)
                        bad['request_id'] += '-changed-after-preview'
                        p = r.structuredContent
                        async with original(transport=httpx.ASGITransport(app=app), base_url='http://127.0.0.1:8000') as transport:
                            rejected = await transport.post('/api/unified/authorizations', json={'request':bad,
                                'expected_preview_id':p['preview']['internal_execution_reference']['preview_id'],
                                'expected_plan_id':p['orchestration_plan']['plan_id'], 'expected_plan_hash':p['orchestration_plan']['plan_hash'],
                                'confirm_authorization':True})
                            assert rejected.status_code != 200, rejected.text
                            rejections['request_changed_after_preview'] = {'http_status':rejected.status_code,'response':rejected.json()}
                identifier = records['market_fetch_evidence']['control_package_id']
                for name in ('market_read_result', 'market_export_ai_handoff'):
                    r = await dispatch_safe_tool(name, {'control_package_id': identifier}, client=client, tool_contract_snapshot=snapshot)
                    assert not r.isError, (name, r)
                    records[name] = r.structuredContent
                return records, rejections
            records, rejections = asyncio.run(lifecycle())
            package = control / records['market_fetch_evidence']['control_package_id']
            artifacts = {str(p.relative_to(package)).replace('\\', '/'): json.loads(p.read_text(encoding='utf-8'))
                         for p in package.rglob('*.json')}
            return {'market': market, 'scenario': scenario, 'request': request,
                    'tool_names': [t.name for t in snapshot.tools], 'calls': records,
                    'public_rejections': rejections,
                    'operational_events': [json.loads(x) for x in (root/'operational.jsonl').read_text(encoding='utf-8').splitlines()],
                    'artifacts': artifacts,
                    'retained_bytes': {str(p.relative_to(package)).replace('\\', '/'): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': len(p.read_bytes())} for p in package.rglob('*.json')},
                    'transport_calls': [json.loads(x) for x in log.read_text().splitlines()],
                    'socket_attempts': attempts + ([json.loads(x) for x in (root/'socket_denials.jsonl').read_text().splitlines()] if (root/'socket_denials.jsonl').exists() else []),
                    'socket_scope': 'parent connect/connect_ex/getaddrinfo (loopback permitted for Windows asyncio self-pipe); child Python audit connect/getaddrinfo/sendto; not OS-wide'}
    finally:
        reset_production_mode_a_security_master_for_tests()
