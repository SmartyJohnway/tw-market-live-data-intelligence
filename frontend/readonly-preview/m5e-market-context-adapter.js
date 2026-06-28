// M5E local-only adapter for the M5D candidate. It never reads or writes frontend/public.
export async function loadM5DMarketContext(fetcher = fetch, path = '../../research/staging/m5d/m5d_frontend_publication_candidate_01/market-context.json') {
  const response = await fetcher(path);
  if (!response.ok) throw new Error(`failed to load M5D market context: ${response.status}`);
  return toM5EDisplayModel(await response.json());
}
export function toM5EDisplayModel(pkg) {
  const caveats = pkg.global_caveats || [];
  return {
    landmarkTitle: 'M5E Readonly Market Context Preview',
    source: 'TWSE_OpenAPI',
    sourceDate: pkg.source_date || pkg.source_timestamp || pkg.retrieved_at || 'source date unavailable',
    staleStatus: pkg.stale_status || 'stale',
    badge: pkg.badge || 'historical/stale',
    caveats,
    rows: (pkg.symbols || []).map((s) => ({
      symbol: s.symbol,
      source: s.source_id || 'TWSE_OpenAPI',
      sourceDate: s.source_timestamp || s.source_date || pkg.source_timestamp || 'source date unavailable',
      freshness: s.freshness_status || pkg.stale_status || 'stale',
      badge: 'historical/stale',
      caveats: [...caveats, ...(s.display_caveats || [])]
    }))
  };
}
export function renderM5EPreview(model, root) {
  root.innerHTML = `<main><h1>${model.landmarkTitle}</h1><p><strong>${model.source}</strong> · ${model.sourceDate} · <span>${model.staleStatus}</span> · <span>${model.badge}</span></p><section aria-labelledby="symbols"><h2 id="symbols">Symbols</h2>${model.rows.map(r=>`<article tabindex="0"><h3>${r.symbol}</h3><p>${r.source} · ${r.sourceDate} · ${r.freshness} · ${r.badge}</p></article>`).join('')}</section><section aria-labelledby="caveats"><h2 id="caveats">Mandatory caveats</h2><ul>${model.caveats.map(c=>`<li>${c}</li>`).join('')}</ul></section></main>`;
}
