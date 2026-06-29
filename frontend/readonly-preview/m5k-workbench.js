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
  for (const category of state.watchlist.categories || []) {
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

function selectHtml(field, value, options) {
  return `<select data-field="${field}">${options.map((opt) => `<option value="${opt}" ${opt === value ? 'selected' : ''}>${opt}</option>`).join('')}</select>`;
}

function renderWatchlist() {
  const rows = rowsFromWatchlist();
  byId('watchlistRows').innerHTML = rows.map((row, index) => `
    <tr data-index="${index}">
      <td><input data-field="enabled" type="checkbox" ${row.enabled ? 'checked' : ''}></td>
      <td><input data-field="symbol" value="${row.symbol}"></td>
      <td><input data-field="display_symbol" value="${row.display_symbol}"></td>
      <td>${selectHtml('market', row.market, marketOptions)}</td>
      <td>${selectHtml('instrument_type', row.instrument_type, typeOptions)}</td>
      <td><input data-field="preferred_sources" value="${row.preferred_sources}"></td>
      <td><input data-field="category_id" value="${row.category_id}"></td>
      <td class="row-actions"><button data-action="remove" type="button">Remove</button></td>
    </tr>`).join('');
  byId('watchlistRows').querySelectorAll('[data-action="remove"]').forEach((button) => {
    button.onclick = () => { button.closest('tr').remove(); watchlistFromRows(); updateSummary(); };
  });
  byId('watchlistJson').value = JSON.stringify(state.watchlist, null, 2);
  updateSummary();
}

function updateSummary() {
  const rows = byId('watchlistRows').querySelectorAll('tr');
  const enabled = [...rows].filter((tr) => tr.querySelector('[data-field="enabled"]').checked).length;
  byId('watchlistSummary').textContent = `${rows.length} rows; ${enabled} enabled. Plan before explicit execution.`;
}

async function loadDefaultWatchlist() {
  const data = await api('/api/m5k/watchlist/default');
  state.watchlist = data.content;
  renderWatchlist();
}

async function validateWatchlist() {
  watchlistFromRows();
  const data = await api('/api/m5k/watchlist/validate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.watchlist) });
  byId('validation').textContent = JSON.stringify(data.validation, null, 2);
}

function exportWatchlist() {
  watchlistFromRows();
  const blob = new Blob([JSON.stringify(state.watchlist, null, 2) + '\n'], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${state.watchlist.watchlist_id || 'm5k-watchlist'}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function importWatchlist(file) {
  const reader = new FileReader();
  reader.onload = () => { state.watchlist = JSON.parse(reader.result); renderWatchlist(); validateWatchlist(); };
  reader.readAsText(file);
}

function addRow() {
  watchlistFromRows();
  const category = state.watchlist.categories[0] || { category_id: 'custom', label: 'Custom', instruments: [] };
  if (!state.watchlist.categories.length) state.watchlist.categories.push(category);
  category.instruments.push({ enabled: true, symbol: '', name: '', market: 'twse', instrument_type: 'listed_equity', preferred_sources: ['TWSE_MIS'] });
  renderWatchlist();
}

async function createHandoff() {
  watchlistFromRows();
  const data = await api('/api/m5k/conversation/handoff', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.watchlist) });
  byId('handoffJson').textContent = JSON.stringify(data, null, 2);
}

function renderObservation() {
  const observation = state.observation;
  byId('observationJson').textContent = JSON.stringify(observation || { status: 'no observation loaded' }, null, 2);
  const rows = (observation && (observation.content?.observations || observation.observations)) || [];
  byId('freshness').textContent = rows.length ? rows.map((row) => `${row.symbol}: ${row.source} retrieved ${row.retrieved_at_utc} (${row.delay_status})`).join('\n') : 'No observation rows. M5F canonical context remains separate.';
}

async function planObservation() {
  watchlistFromRows();
  state.observation = await api('/api/m5k/live-observation/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.watchlist) });
  renderObservation();
}

async function executeObservation() {
  watchlistFromRows();
  state.observation = await api('/api/m5k/live-observation/execute?confirm_live_observation=true', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.watchlist) });
  renderObservation();
}

async function readLatestObservation() {
  state.observation = await api('/api/m5k/live-observation/latest');
  renderObservation();
}

window.addEventListener('DOMContentLoaded', () => {
  byId('loadDefault').onclick = loadDefaultWatchlist;
  byId('addRow').onclick = addRow;
  byId('validate').onclick = validateWatchlist;
  byId('export').onclick = exportWatchlist;
  byId('import').onchange = (event) => importWatchlist(event.target.files[0]);
  byId('handoff').onclick = createHandoff;
  byId('planObservation').onclick = planObservation;
  byId('observe').onclick = executeObservation;
  byId('readLatest').onclick = readLatestObservation;
  byId('watchlistRows').addEventListener('input', () => { watchlistFromRows(); updateSummary(); });
  loadDefaultWatchlist();
  readLatestObservation();
});
