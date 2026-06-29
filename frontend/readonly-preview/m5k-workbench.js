const state = { watchlist: null, observation: null };
const byId = (id) => document.getElementById(id);
const marketOptions = ['twse', 'tpex', 'taifex'];
const typeOptions = ['listed_etf', 'listed_equity', 'listed_or_otc_equity', 'index', 'futures'];

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(payload));
  return payload;
}

function rowsFromWatchlist() {
  const rows = [];
  for (const category of state.watchlist?.categories || []) {
    for (const instrument of category.instruments || []) {
      rows.push({
        category_id: category.category_id || 'custom',
        category_label: category.label || category.category_id || 'Custom',
        enabled: instrument.enabled !== false,
        symbol: instrument.symbol || '',
        display_symbol: instrument.display_symbol || instrument.name || instrument.symbol || '',
        market: instrument.market || 'twse',
        instrument_type: instrument.instrument_type || 'listed_equity',
        preferred_sources: (instrument.preferred_sources || []).join(', '),
      });
    }
  }
  return rows;
}

function watchlistFromRows() {
  const existing = state.watchlist || { schema_version: 'm5k_watchlist.v1', watchlist_id: 'm5k_frontend_watchlist', name: 'M5K Frontend Watchlist' };
  const categories = new Map();
  for (const tr of byId('watchlistRows').querySelectorAll('tr')) {
    const row = {
      enabled: tr.querySelector('[data-field="enabled"]').checked,
      symbol: tr.querySelector('[data-field="symbol"]').value.trim().toUpperCase(),
      display_symbol: tr.querySelector('[data-field="display_symbol"]').value.trim(),
      market: tr.querySelector('[data-field="market"]').value,
      instrument_type: tr.querySelector('[data-field="instrument_type"]').value,
      preferred_sources: tr.querySelector('[data-field="preferred_sources"]').value.split(',').map((s) => s.trim()).filter(Boolean),
    };
    row.name = row.display_symbol || row.symbol;
    const category_id = tr.querySelector('[data-field="category_id"]').value.trim() || 'custom';
    if (!categories.has(category_id)) categories.set(category_id, { category_id, label: category_id, instruments: [] });
    categories.get(category_id).instruments.push(row);
  }
  state.watchlist = { ...existing, schema_version: 'm5k_watchlist.v1', categories: [...categories.values()] };
  byId('watchlistJson').value = JSON.stringify(state.watchlist, null, 2);
  return state.watchlist;
}

function appendInputCell(tr, field, value, type = 'text') {
  const td = tr.insertCell();
  const input = document.createElement('input');
  input.dataset.field = field;
  input.type = type;
  if (type === 'checkbox') input.checked = Boolean(value); else input.value = value || '';
  td.appendChild(input);
}

function appendSelectCell(tr, field, value, options) {
  const td = tr.insertCell();
  const select = document.createElement('select');
  select.dataset.field = field;
  for (const opt of options) {
    const option = document.createElement('option');
    option.value = opt;
    option.textContent = opt;
    option.selected = opt === value;
    select.appendChild(option);
  }
  td.appendChild(select);
}

function renderWatchlist() {
  const tbody = byId('watchlistRows');
  tbody.replaceChildren();
  rowsFromWatchlist().forEach((row, index) => {
    const tr = tbody.insertRow();
    tr.dataset.index = String(index);
    appendInputCell(tr, 'enabled', row.enabled, 'checkbox');
    appendInputCell(tr, 'symbol', row.symbol);
    appendInputCell(tr, 'display_symbol', row.display_symbol);
    appendSelectCell(tr, 'market', row.market, marketOptions);
    appendSelectCell(tr, 'instrument_type', row.instrument_type, typeOptions);
    appendInputCell(tr, 'preferred_sources', row.preferred_sources);
    appendInputCell(tr, 'category_id', row.category_id);
    const td = tr.insertCell();
    td.className = 'row-actions';
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.action = 'remove';
    button.textContent = 'Remove';
    button.onclick = () => { tr.remove(); watchlistFromRows(); updateSummary(); };
    td.appendChild(button);
  });
  byId('watchlistJson').value = JSON.stringify(state.watchlist, null, 2);
  updateSummary();
}

function updateSummary() {
  const rows = byId('watchlistRows').querySelectorAll('tr');
  const enabled = [...rows].filter((tr) => tr.querySelector('[data-field="enabled"]').checked).length;
  byId('watchlistSummary').textContent = `${rows.length} rows; ${enabled} enabled. Plan before explicit execution.`;
}

async function loadDefaultWatchlist() { state.watchlist = (await api('/api/m5k/watchlist/default')).content; renderWatchlist(); }
async function validateWatchlist() { watchlistFromRows(); const data = await api('/api/m5k/watchlist/validate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.watchlist) }); byId('validation').textContent = JSON.stringify(data.validation, null, 2); }
function exportWatchlist() { watchlistFromRows(); const blob = new Blob([JSON.stringify(state.watchlist, null, 2) + '\n'], { type: 'application/json' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `${state.watchlist.watchlist_id || 'm5k-watchlist'}.json`; a.click(); URL.revokeObjectURL(a.href); }
function importWatchlist(file) { const reader = new FileReader(); reader.onload = () => { state.watchlist = JSON.parse(reader.result); renderWatchlist(); validateWatchlist(); }; reader.readAsText(file); }
function addRow() { watchlistFromRows(); const category = state.watchlist.categories[0] || { category_id: 'custom', label: 'Custom', instruments: [] }; if (!state.watchlist.categories.length) state.watchlist.categories.push(category); category.instruments.push({ enabled: true, symbol: '', name: '', market: 'twse', instrument_type: 'listed_equity', preferred_sources: ['TWSE_MIS'] }); renderWatchlist(); }
async function createHandoff() { watchlistFromRows(); byId('handoffJson').textContent = JSON.stringify(await api('/api/m5k/conversation/handoff', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.watchlist) }), null, 2); }

function renderRows(tableId, rows, columns) {
  const tbody = byId(tableId);
  tbody.replaceChildren();
  for (const row of rows || []) {
    const tr = tbody.insertRow();
    for (const [label, getter] of columns) {
      const td = tr.insertCell();
      td.dataset.label = label;
      const value = typeof getter === 'function' ? getter(row) : row[getter];
      td.textContent = value == null ? '' : String(value);
    }
  }
}

function renderObservation() {
  const payload = state.observation?.content || state.observation || {};
  byId('observationJson').textContent = JSON.stringify(state.observation || { status: 'no observation loaded' }, null, 2);
  byId('layerSeparation').textContent = 'M5F canonical context is Level 1 read-only local context. M5K live observation is Level 2 explicit, bounded, non-canonical observation.';
  renderRows('routePlanRows', payload.planned_routes || [], [['Symbol', 'symbol'], ['Market', 'market'], ['Type', 'instrument_type'], ['Source', 'source'], ['Status', 'status'], ['Route', (r) => r.ex_ch || r.reason || '']]);
  renderRows('observationRows', payload.observations || [], [['Symbol', 'symbol'], ['Source', 'source'], ['Value', 'price_like_value'], ['Retrieved UTC', 'retrieved_at_utc'], ['Source timestamp', 'source_timestamp'], ['Freshness', 'freshness_assessment'], ['Delay', 'delay_status']]);
  renderRows('failureRows', payload.failures || [], [['Symbol', 'symbol'], ['Source', 'source'], ['Status', 'status'], ['Reason', (r) => r.reason || r.ex_ch || '']]);
  const rows = payload.observations || [];
  byId('freshness').textContent = rows.length ? rows.map((row) => `${row.symbol}: ${row.source} retrieved ${row.retrieved_at_utc}; source ${row.source_timestamp}; ${row.delay_status}`).join('\n') : 'No observation rows. M5F canonical context remains separate.';
}

async function planObservation() { watchlistFromRows(); await validateWatchlist(); state.observation = await api('/api/m5k/live-observation/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.watchlist) }); renderObservation(); }
async function executeObservation() { watchlistFromRows(); await planObservation(); state.observation = await api('/api/m5k/live-observation/execute?confirm_live_observation=true', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.watchlist) }); renderObservation(); }
async function readLatestObservation() { state.observation = await api('/api/m5k/live-observation/latest'); renderObservation(); }

window.addEventListener('DOMContentLoaded', () => {
  byId('loadDefault').onclick = loadDefaultWatchlist; byId('addRow').onclick = addRow; byId('validate').onclick = validateWatchlist; byId('export').onclick = exportWatchlist; byId('import').onchange = (event) => importWatchlist(event.target.files[0]); byId('handoff').onclick = createHandoff; byId('planObservation').onclick = planObservation; byId('observe').onclick = executeObservation; byId('readLatest').onclick = readLatestObservation;
  byId('watchlistRows').addEventListener('input', () => { watchlistFromRows(); updateSummary(); });
  loadDefaultWatchlist(); readLatestObservation();
});
