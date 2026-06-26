// Source authority display. Local readonly preview only; no production current state claim.
export function sourceAuthorityDisplay(sourceId, authority){
  if (sourceId === 'TWSE_MIS') return 'TWSE MIS unofficial frontend endpoint caveat';
  if (sourceId === 'Yahoo_Finance') return 'Yahoo Finance third-party caveat';
  if ((authority||'').includes('official_openapi')) return 'Official OpenAPI source authority';
  return 'Unknown or validation-only source authority';
}
