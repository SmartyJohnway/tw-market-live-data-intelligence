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
  if cap['maturity_status'] in {'planned','contract_only'} and cap.get('ai_facing_runtime_available'): fail('planned/contract-only ai operation executable')
  if cap.get('ai_facing_runtime_available'): fail('F1 Phase C operation marked runtime available')
  if cap.get('network_required') and not cap.get('authorization_required'): fail('network capability missing authorization requirement')
  if cap.get('network_required') and cap.get('network_default_enabled') is not False: fail('network capability enabled by default')
  for t in cap['supported_timing_classes']:
   if t not in timing: fail(f'unknown timing {t}')
  if cap.get('underlying_runtime_available'):
   for p in cap.get('internal_dependencies',[]):
    if not (ROOT/p).exists(): fail(f'missing dependency {p}')
 for row in m['intents']:
  for cid in row['required_capabilities']+row.get('optional_capabilities',[]):
   if cid not in ids: fail(f'unknown capability {cid}')
  for t in row['timing_requirements']:
   if t not in timing: fail(f'unknown matrix timing {t}')
 if (ROOT/'docs/ai/m8_ai_capability_contract.json').read_text(encoding='utf-8') != (SKILL/'assets/m8_ai_capability_contract.json').read_text(encoding='utf-8'): fail('embedded skill contract differs from authoritative contract')
 if c.get('raw_payload_exposure_allowed') is not False: fail('raw payload restriction missing')
 if c.get('recommended_next_task')!='M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION': fail('successor is not R2')
 reg=json.load(open(ROOT/'docs/data_capabilities/m8_source_capability_registry.json'))
 for surface_name, surface in [('root',reg),('active',reg.get('m8_active_consolidated_status',{})),('planning',reg.get('planning_state',{}))]:
  if surface.get('implemented_through_track')!='M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION': fail(f'{surface_name} implemented track mismatch')
  if surface.get('agent_skill_contract')!='implemented': fail(f'{surface_name} skill status mismatch')
  if surface.get('ai_capability_guide')!='implemented': fail(f'{surface_name} guide status mismatch')
  if surface.get('recommended_next_task')!='M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP': fail(f'{surface_name} successor mismatch')
  if surface.get('registry_successor')!='M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP': fail(f'{surface_name} registry successor mismatch')
 health=json.load(open(ROOT/'docs/data_capabilities/m8_repository_health_status.json'))
 if health.get('implemented_through_track')!='M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION': fail('health implemented track mismatch')
 if health.get('agent_skill_contract')!='implemented': fail('health skill status mismatch')
 if health.get('ai_capability_guide')!='implemented': fail('health guide status mismatch')
 if health.get('recommended_next_task')!='M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP': fail('health successor mismatch')
 if health.get('registry_successor')!='M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP': fail('health registry successor mismatch')
 old=reg.get('recommended_successor_after_m8r_03e')
 if not (isinstance(old,dict) and old.get('status') in {'historical_superseded','superseded'}): fail('old M8R-03F successor is still active')
 active='\n'.join(p.read_text(encoding='utf-8') for p in [SKILL/'SKILL.md',SKILL/'references/capability_quick_guide.md',SKILL/'references/evidence_semantics.md',SKILL/'references/tool_selection_examples.md',SKILL/'references/current_limitations.md',ROOT/'docs/ai/M8_AI_CAPABILITY_QUICK_GUIDE.md'])
 for pat in PROHIB:
  if re.search(pat,active,re.I): fail(f'prohibited blanket policy {pat}')
 if re.search(r'(api[_ -]?key|token|cookie|secret)\s*[:=]\s*[A-Za-z0-9_\-]{8,}',active,re.I): fail('secret-like value exposed')
 print('tw-market-evidence-agent skill validation passed')
if __name__=='__main__': main()
