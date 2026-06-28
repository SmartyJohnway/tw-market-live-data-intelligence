export const DEFAULT_PACKAGE_BASE_URL = '../../research/staging/m5f/m5f_canonical_market_context_01/';
export const DEFAULT_CONTEXT_URL = `${DEFAULT_PACKAGE_BASE_URL}canonical_market_context.json`;
export const DEFAULT_MANIFEST_URL = `${DEFAULT_PACKAGE_BASE_URL}sha256_manifest.json`;

export function buildDisplayModel(context) {
  if (!context || typeof context !== 'object') return { state: 'empty', symbols: [], caveats: [] };
  const symbols = Array.isArray(context.symbols) ? context.symbols : [];
  if (!symbols.length) return { state: 'empty', symbols: [], caveats: context.global_caveats || [] };
  return {
    state: 'ready', packageId: context.package_id, lineage: context.lineage_hashes || {},
    source: context.source, sourceDate: context.source_date,
    badge: context.governance?.badge || context.badge || 'historical/stale',
    staleStatus: context.governance?.stale_status || context.stale_status || 'stale',
    caveats: context.global_caveats || [], failedTargets: context.failed_targets || [],
    sourceHealth: { source: context.source, status: 'available_as_reviewed_historical_evidence', readonlyOnly: context.governance?.readonly_only === true, realtimeGuaranteed: context.governance?.realtime_guaranteed === true, productionCurrentState: context.governance?.production_current_state === true },
    symbols: symbols.map((s) => ({ symbol: s.symbol, priceLikeValue: s.price_like_value, sourceId: s.source_id, sourceAuthority: s.source_authority, sourceDate: s.source_timestamp, retrievedAt: s.retrieved_at, freshnessStatus: s.freshness_status, delayStatus: s.delay_status, riskFlags: s.source_risk_flags || [], caveats: s.display_caveats || [] }))
  };
}

function appendText(parent, tag, text) { const el = document.createElement(tag); el.textContent = text; parent.appendChild(el); return el; }
function list(parent, items) { const ul = document.createElement('ul'); (items || []).forEach(i => appendText(ul, 'li', String(i))); parent.appendChild(ul); }

export async function sha256Hex(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function fetchValidatedCanonical(packageBaseUrl = DEFAULT_PACKAGE_BASE_URL) {
  const manifestUrl = new URL('sha256_manifest.json', new URL(packageBaseUrl, window.location.href));
  const canonicalUrl = new URL('canonical_market_context.json', manifestUrl);
  const [manifestResponse, canonicalResponse] = await Promise.all([
    fetch(manifestUrl, { cache: 'no-store' }), fetch(canonicalUrl, { cache: 'no-store' })
  ]);
  if (!manifestResponse.ok) throw new Error(`manifest HTTP ${manifestResponse.status}`);
  if (!canonicalResponse.ok) throw new Error(`canonical HTTP ${canonicalResponse.status}`);
  const manifest = await manifestResponse.json();
  const canonicalText = await canonicalResponse.text();
  const expectedHash = manifest?.files?.['canonical_market_context.json'];
  if (!expectedHash) throw new Error('manifest missing canonical_market_context.json hash');
  const actualHash = await sha256Hex(canonicalText);
  if (actualHash !== expectedHash) throw new Error('canonical manifest hash mismatch');
  const context = JSON.parse(canonicalText);
  if (context?.schema_version !== 'm5f_canonical_market_context.v1') throw new Error('unsupported canonical schema');
  if (!Array.isArray(context.symbols) || context.symbols.length === 0) throw new Error('canonical symbols missing');
  return context;
}

export function renderMarketContext(root, model) {
  root.replaceChildren();
  if (!model || model.state === 'loading') { appendText(root, 'p', 'Loading local readonly market context…'); return; }
  if (model.state === 'error') { appendText(root, 'p', `Malformed/error state: ${model.message || 'unable to load context'}`); return; }
  if (model.state === 'empty') { appendText(root, 'p', 'Empty state: no symbols are available in the canonical context.'); return; }
  appendText(root, 'h2', 'M5F Canonical Market Context Preview'); appendText(root, 'p', `Package: ${model.packageId}; Badge: ${model.badge}; Freshness: ${model.staleStatus}`); appendText(root, 'p', `Source: ${model.source}; Source date: ${model.sourceDate}`);
  const table = document.createElement('table'); const thead = document.createElement('thead'); const headRow = document.createElement('tr'); ['Symbol','Price-like value','Source','Authority','Source date','Retrieved','Freshness','Delay'].forEach(h => appendText(headRow, 'th', h)); thead.appendChild(headRow); table.appendChild(thead);
  const tbody = document.createElement('tbody'); model.symbols.forEach((s) => { const tr = document.createElement('tr'); [s.symbol, s.priceLikeValue, s.sourceId, s.sourceAuthority, s.sourceDate, s.retrievedAt, s.freshnessStatus, s.delayStatus].forEach(v => appendText(tr, 'td', String(v ?? ''))); tbody.appendChild(tr); }); table.appendChild(tbody); root.appendChild(table);
  appendText(root, 'h3', 'Global caveats'); list(root, model.caveats); appendText(root, 'h3', 'Per-symbol caveats and source risk flags'); model.symbols.forEach(s => { appendText(root, 'h4', s.symbol); list(root, [...s.riskFlags, ...s.caveats]); }); appendText(root, 'h3', 'Failed targets'); list(root, model.failedTargets.length ? model.failedTargets : ['None']); appendText(root, 'h3', 'Source-health summary'); appendText(root, 'p', JSON.stringify(model.sourceHealth)); appendText(root, 'h3', 'Lineage'); appendText(root, 'p', JSON.stringify(model.lineage));
}

export async function loadAndRender(root, packageBaseUrl = DEFAULT_PACKAGE_BASE_URL) {
  renderMarketContext(root, { state: 'loading' });
  try { renderMarketContext(root, buildDisplayModel(await fetchValidatedCanonical(packageBaseUrl))); }
  catch (err) { renderMarketContext(root, { state: 'error', message: err.message }); }
}
