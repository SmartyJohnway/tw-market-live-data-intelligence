#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'config/test_execution_profiles.json'
VALID_SSL={'strict','compatibility','unsafe-explicit'}

CommandPlan = dict[str, Any]
CommandResult = dict[str, Any]

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_config(): return json.loads(CONFIG.read_text())
def command_to_display(cmd:list[str])->str: return ' '.join(cmd)

def _materialize_runner_command(cmd: list[str], ssl_policy: str) -> list[str]:
    return [sys.executable if c == 'python' else c.format(ssl_policy=ssl_policy) for c in cmd]

def resolve_profile_plan(profile:str, *, confirm_bounded_live=False, ssl_policy='strict')->list[CommandPlan]:
    cfg=load_config()['profiles']
    if profile not in cfg: raise ValueError(f"Unknown test profile: {profile}")
    if ssl_policy not in VALID_SSL: raise ValueError(f"Invalid ssl_policy: {ssl_policy}")
    p=cfg[profile]
    if profile=='bounded-live' and not confirm_bounded_live:
        raise ValueError('bounded-live requires --confirm-bounded-live')
    if p['execution_type']=='pytest':
        out: list[CommandPlan] = [{
            'command': [sys.executable,'-m','pytest','-m',p['pytest_expression'],*p.get('pytest_paths',['tests'])],
            'execution_kind': 'pytest',
        }]
        for cmd in p.get('authoritative_runner', []):
            out.append({'command': _materialize_runner_command(cmd, ssl_policy), 'execution_kind': 'authoritative_runner'})
        return out
    return [{'command': _materialize_runner_command(cmd, ssl_policy), 'execution_kind': 'authoritative_runner'} for cmd in p['authoritative_runner']]

def resolve_profile(profile:str, *, confirm_bounded_live=False, ssl_policy='strict')->list[list[str]]:
    return [item['command'] for item in resolve_profile_plan(profile, confirm_bounded_live=confirm_bounded_live, ssl_policy=ssl_policy)]

def parse_pytest_counts(text:str)->dict[str, int|None]:
    res={k:None for k in ['collected','selected','passed','failed','skipped','deselected']}
    m=re.search(r'collected (\d+) items?(?: / (\d+) deselected / (\d+) selected)?', text)
    if m:
        res['collected']=int(m.group(1)); res['deselected']=int(m.group(2) or 0); res['selected']=int(m.group(3) or m.group(1))
    m=re.search(r'=+\s*(.*?)\s+in [\d.]+s\s*=+', text)
    summary=m.group(1) if m else text
    for k in ['passed','failed','skipped','deselected']:
        mm=re.search(rf'(\d+) {k}', summary)
        if mm: res[k]=int(mm.group(1))
    return res

def run_commands(command_plan:list[CommandPlan], *, capture:bool)->list[CommandResult]:
    results=[]
    for item in command_plan:
        cmd=item['command']
        started=time.monotonic()
        proc=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None)
        result={
            'command': command_to_display(cmd),
            'return_code': proc.returncode,
            'duration_seconds': round(time.monotonic()-started,3),
            'execution_kind': item['execution_kind'],
            '_output': proc.stdout or '',
        }
        results.append(result)
        if proc.returncode!=0: break
    return results

def _public_command_results(results:list[CommandResult])->list[dict[str, Any]]:
    return [{k:v for k,v in result.items() if k != '_output'} for result in results]

def _pytest_output(results:list[CommandResult])->str:
    for result in results:
        if result.get('execution_kind') == 'pytest':
            return str(result.get('_output') or '')
    return ''

def build_payload(profile, command_plan, results, started, finished, args):
    cfg=load_config()['profiles'][profile]
    codes=[r['return_code'] for r in results]
    payload={
      'profile':profile,'status':'pass' if codes and all(c==0 for c in codes) else 'fail',
      'commands':[command_to_display(item['command']) for item in command_plan],
      'started_at':started,'finished_at':finished,'duration_seconds':round(time.monotonic()-args._start,3),
      'return_codes':codes,
      'command_results': _public_command_results(results),
      'network_may_have_occurred': profile=='bounded-live',
      'browser_required': profile in {'browser-e2e','bounded-live'},
      'explicit_live_confirmation': bool(args.confirm_bounded_live),
      'ssl_policy': args.ssl_policy,
    }
    if cfg['execution_type']=='pytest': payload.update(parse_pytest_counts(_pytest_output(results)))
    return payload

def main(argv=None):
    ap=argparse.ArgumentParser(description='Route explicit test execution profiles.')
    ap.add_argument('profile', choices=sorted(load_config()['profiles'].keys()))
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--confirm-bounded-live', action='store_true')
    ap.add_argument('--ssl-policy', default='strict')
    args=ap.parse_args(argv); args._start=time.monotonic()
    try: command_plan=resolve_profile_plan(args.profile, confirm_bounded_live=args.confirm_bounded_live, ssl_policy=args.ssl_policy)
    except ValueError as e:
        if args.json:
            print(json.dumps({'profile':args.profile,'status':'fail','error':str(e),'commands':[]}, indent=2, sort_keys=True))
        else: print(f'ERROR: {e}', file=sys.stderr)
        return 2
    started=utc(); results=run_commands(command_plan, capture=args.json); finished=utc()
    payload=build_payload(args.profile, command_plan, results, started, finished, args)
    if args.json: print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
