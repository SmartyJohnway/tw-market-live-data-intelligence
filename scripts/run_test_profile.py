#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'config/test_execution_profiles.json'
VALID_SSL={'strict','compatibility','unsafe-explicit'}

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_config(): return json.loads(CONFIG.read_text())
def command_to_display(cmd:list[str])->str: return ' '.join(cmd)

def resolve_profile(profile:str, *, confirm_bounded_live=False, ssl_policy='strict')->list[list[str]]:
    cfg=load_config()['profiles']
    if profile not in cfg: raise ValueError(f"Unknown test profile: {profile}")
    if ssl_policy not in VALID_SSL: raise ValueError(f"Invalid ssl_policy: {ssl_policy}")
    p=cfg[profile]
    if profile=='bounded-live' and not confirm_bounded_live:
        raise ValueError('bounded-live requires --confirm-bounded-live')
    if p['execution_type']=='pytest':
        return [[sys.executable,'-m','pytest','-m',p['pytest_expression'],*p.get('pytest_paths',['tests'])]]
    out=[]
    for cmd in p['authoritative_runner']:
        out.append([sys.executable if c=='python' else c.format(ssl_policy=ssl_policy) for c in cmd])
    return out

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

def run_commands(commands:list[list[str]], *, capture:bool)->tuple[list[int], str]:
    combined=[]; codes=[]
    for cmd in commands:
        proc=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None)
        codes.append(proc.returncode)
        if capture and proc.stdout: combined.append(proc.stdout)
        if proc.returncode!=0: break
    return codes, '\n'.join(combined)

def build_payload(profile, commands, codes, started, finished, output, args):
    cfg=load_config()['profiles'][profile]
    payload={
      'profile':profile,'status':'pass' if codes and all(c==0 for c in codes) else 'fail',
      'commands':[command_to_display(c) for c in commands],
      'started_at':started,'finished_at':finished,'duration_seconds':round(time.monotonic()-args._start,3),
      'return_codes':codes,
      'network_may_have_occurred': profile=='bounded-live',
      'browser_required': profile in {'browser-e2e','bounded-live'},
      'explicit_live_confirmation': bool(args.confirm_bounded_live),
      'ssl_policy': args.ssl_policy,
    }
    if cfg['execution_type']=='pytest': payload.update(parse_pytest_counts(output))
    return payload

def main(argv=None):
    ap=argparse.ArgumentParser(description='Route explicit test execution profiles.')
    ap.add_argument('profile', choices=sorted(load_config()['profiles'].keys()))
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--confirm-bounded-live', action='store_true')
    ap.add_argument('--ssl-policy', default='strict')
    args=ap.parse_args(argv); args._start=time.monotonic()
    try: commands=resolve_profile(args.profile, confirm_bounded_live=args.confirm_bounded_live, ssl_policy=args.ssl_policy)
    except ValueError as e:
        if args.json:
            print(json.dumps({'profile':args.profile,'status':'fail','error':str(e),'commands':[]}, indent=2, sort_keys=True))
        else: print(f'ERROR: {e}', file=sys.stderr)
        return 2
    started=utc(); codes, output=run_commands(commands, capture=args.json); finished=utc()
    payload=build_payload(args.profile, commands, codes, started, finished, output, args)
    if args.json: print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
