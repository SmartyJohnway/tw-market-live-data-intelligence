#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SKILL=ROOT/'skills/tw-market-evidence-agent'
REQ=[SKILL/'SKILL.md',SKILL/'references/capability_quick_guide.md',SKILL/'references/evidence_semantics.md',SKILL/'references/tool_selection_examples.md',SKILL/'references/current_limitations.md',SKILL/'assets/m8_ai_capability_contract.json',ROOT/'docs/ai/m8_ai_capability_contract.json',ROOT/'docs/ai/m8_ai_tool_selection_matrix.json',ROOT/'docs/ai/m8_evidence_sufficiency_model.json']
VALID={'implemented','implemented_with_caveats','fixture_validated','contract_only','planned','unavailable','deprecated'}
PROHIB=[r'no_recommendation\s*[:=]\s*true',r'recommendation_allowed\s*[:=]\s*false',r'must_not_provide_investment_advice',r'buy/sell\s+(questions\s+are\s+)?unsupported',r'no trading advice',r'no_trading_advice\s*[:=]\s*true',r'no_trading_signal\s*[:=]\s*true']
def fail(m): print(f'ERROR: {m}',file=sys.stderr); sys.exit(1)
def main():
 for p in REQ:
  if not p.exists(): fail(f'missing {p}')
 c=json.load(open(ROOT/'docs/ai/m8_ai_capability_contract.json'))
 m=json.load(open(ROOT/'docs/ai/m8_ai_tool_selection_matrix.json'))
 ids=[x['capability_id'] for x in c['capabilities']]
 if len(ids)!=len(set(ids)): fail('capability ids not unique')
 intents=[x['intent_id'] for x in m['intents']]
 if len(intents)!=len(set(intents)): fail('intent ids not unique')
 timing=set(c['timing_classes']); src=set(c['source_authority_classes']); suff=set(c['sufficiency_statuses'])
 if not {'current_bounded_observation','completed_session_eod'}<=timing: fail('missing current/eod timing classes')
 if 'retrieved_at is not exchange event time' not in json.dumps(c): fail('retrieved_at semantic missing')
 if 'unadjusted; not total return' not in json.dumps(c): fail('unadjusted return semantic missing')
 for cap in c['capabilities']:
  if cap['maturity_status'] not in VALID: fail('bad maturity')
  if cap['maturity_status']=='planned' and cap['runtime_available']: fail('planned runtime available')
  for t in cap['supported_timing_classes']:
   if t not in timing: fail(f'unknown timing {t}')
  if cap['runtime_available']:
   for p in cap.get('internal_dependencies',[]):
    if not (ROOT/p).exists(): fail(f'missing dependency {p}')
 for row in m['intents']:
  for cid in row['required_capabilities']+row.get('optional_capabilities',[]):
   if cid not in ids: fail(f'unknown capability {cid}')
  for t in row['timing_requirements']:
   if t not in timing: fail(f'unknown matrix timing {t}')
 if c.get('raw_payload_exposure_allowed') is not False: fail('raw payload restriction missing')
 if c.get('recommended_next_task')!='M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION': fail('successor is not R2')
 active='\n'.join(p.read_text(encoding='utf-8') for p in [SKILL/'SKILL.md',SKILL/'references/capability_quick_guide.md',SKILL/'references/evidence_semantics.md',SKILL/'references/tool_selection_examples.md',SKILL/'references/current_limitations.md',ROOT/'docs/ai/M8_AI_CAPABILITY_QUICK_GUIDE.md'])
 for pat in PROHIB:
  if re.search(pat,active,re.I): fail(f'prohibited blanket policy {pat}')
 if re.search(r'(api[_ -]?key|token|cookie|secret)\s*[:=]\s*[A-Za-z0-9_\-]{8,}',active,re.I): fail('secret-like value exposed')
 print('tw-market-evidence-agent skill validation passed')
if __name__=='__main__': main()
