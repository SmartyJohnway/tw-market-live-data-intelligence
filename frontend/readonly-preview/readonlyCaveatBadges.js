// Caveat badge mapping for local preview only; no trading interpretation.
export function freshnessBadge(status){
  const map={stale:'Stale source - display caveat',delayed:'Delayed candidate - display caveat',live_candidate:'Live candidate, not realtime guaranteed',eod_batch:'End-of-day batch',unknown:'Freshness unknown'};
  return map[status] || map.unknown;
}
export function sourceRiskBadge(flags){ return (flags||[]).length ? 'Source risk present and must be visible' : 'No source risk flag in fixture'; }
