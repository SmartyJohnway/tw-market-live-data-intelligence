/* Persistent Watchlist and request-composition UI. No polling, storage, or network execution. */
(function persistentWatchlistWorkbench() {
    'use strict';

    const byId = (id) => document.getElementById(id);
    const stateApi = globalThis.UnifiedWorkbenchState;
    let lifecycle = stateApi.initialState();
    let watchlists = [];
    let current = null;
    let temporaryTargets = [];
    let pendingMutation = null;
    let composedBinding = null;

    const setText = (element, value) => { element.textContent = value == null ? '' : String(value); };
    const pretty = (value) => JSON.stringify(value, null, 2);
    const markBuilderDirty = () => {
        lifecycle = stateApi.transition(lifecycle, 'EDIT_SELECTION');
        document.dispatchEvent(new Event('workbench-builder-dirty'));
    };

    async function api(path, options) {
        const response = await fetch(path, options);
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
            const detail = body.detail && body.detail.error ? body.detail.error : body;
            const error = new Error(detail.code || `HTTP_${response.status}`);
            error.detail = detail;
            throw error;
        }
        return body;
    }

    function download(name, value) {
        const blob = new Blob([pretty(value)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = name;
        link.click();
        URL.revokeObjectURL(url);
    }

    function button(label, action, className) {
        const element = document.createElement('button');
        setText(element, label);
        if (className) element.className = className;
        element.addEventListener('click', action);
        return element;
    }

    function command(commandType, fields) {
        return {
            schema_version: 'persistent_watchlist_mutation_command.v1',
            command_type: commandType,
            actor_source: 'human',
            ...fields,
        };
    }

    function currentFields() {
        if (!current) throw new Error('WATCHLIST_NOT_SELECTED');
        return { watchlist_id: current.watchlist_id, expected_version: current.current_version };
    }

    async function previewMutation(mutation) {
        pendingMutation = await api('/api/watchlist-mutations/preview', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(mutation),
        });
        lifecycle = stateApi.transition(lifecycle, 'PREVIEW_MUTATION');
        byId('mutation-preview-panel').hidden = false;
        setText(byId('mutation-preview-view'), pretty(pendingMutation));
    }

    async function confirmMutation() {
        if (!pendingMutation) return;
        try {
            await api('/api/watchlist-mutations/commit', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ preview_id: pendingMutation.preview_id, preview_hash: pendingMutation.content_sha256, confirmed: true }),
            });
            lifecycle = stateApi.transition(lifecycle, 'REQUIRE_MUTATION_CONFIRMATION');
            pendingMutation = null;
            byId('mutation-preview-panel').hidden = true;
            if (composedBinding) lifecycle = stateApi.markSourceWatchlistChanged(lifecycle);
            await loadWatchlists();
            setText(byId('composition-summary'), lifecycle.sourceWatchlistStale
                ? 'Source watchlist changed after composition. The frozen request is unchanged; rebuild and revalidate before a new authorization.'
                : 'Mutation committed.');
        } catch (error) {
            lifecycle = stateApi.transition(lifecycle, 'CONFLICT');
            setText(byId('mutation-preview-view'), `${error.message}\n${pretty(error.detail || {})}`);
        }
    }

    function renderWatchlists() {
        const select = byId('watchlist-select');
        const selected = current && current.watchlist_id;
        select.replaceChildren();
        const empty = document.createElement('option');
        empty.value = '';
        setText(empty, watchlists.length ? 'Select a watchlist' : 'No watchlists');
        select.appendChild(empty);
        watchlists.forEach((watchlist) => {
            const option = document.createElement('option');
            option.value = watchlist.watchlist_id;
            setText(option, `${watchlist.name} · v${watchlist.current_version}${watchlist.is_default ? ' · default' : ''}${watchlist.deleted ? ' · deleted' : ''}`);
            if (watchlist.watchlist_id === selected) option.selected = true;
            select.appendChild(option);
        });
    }

    function entryProjection(entryId) {
        return (current.current_identity_projection || []).find((item) => item.watchlist_entry_id === entryId) || {};
    }

    function renderEntries() {
        const root = byId('watchlist-entries');
        root.replaceChildren();
        if (!current) {
            setText(byId('watchlist-summary'), watchlists.length ? 'Select a watchlist.' : 'No installation-local watchlist. Create one explicitly.');
            return;
        }
        setText(byId('watchlist-summary'), `${current.name} · version ${current.current_version} · ${current.entries.length} entries · default ${current.is_default ? 'yes' : 'no'} · deleted ${current.deleted ? 'yes' : 'no'}`);
        current.entries.forEach((entry, index) => {
            const row = document.createElement('div');
            row.className = 'entry-row';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'watchlist-entry-selection';
            checkbox.dataset.entryId = entry.watchlist_entry_id;
            checkbox.addEventListener('change', markBuilderDirty);
            const label = document.createElement('div');
            const projection = entryProjection(entry.watchlist_entry_id);
            setText(label, `${entry.display_name || entry.instrument_id} · ${entry.instrument_id} · ${entry.cached_market || 'unrouted'}:${entry.cached_security_code || '?'} · ${entry.enabled ? 'enabled' : 'disabled'} · ${projection.identity_status || 'unknown'}${projection.executable === false ? ' · non-executable' : ''}`);
            const actions = document.createElement('div');
            actions.className = 'entry-actions';
            actions.append(
                button(entry.enabled ? 'Disable' : 'Enable', () => previewMutation(command('set_entry_enabled', { ...currentFields(), watchlist_entry_id: entry.watchlist_entry_id, enabled: !entry.enabled }))),
                button('Tags', () => {
                    const value = window.prompt('Comma-separated tags', entry.tags.join(', '));
                    if (value !== null) previewMutation(command('set_entry_tags', { ...currentFields(), watchlist_entry_id: entry.watchlist_entry_id, tags: value.split(',').map((item) => item.trim()).filter(Boolean) }));
                }),
                button('Notes', () => {
                    const value = window.prompt('Notes', entry.notes || '');
                    if (value !== null) previewMutation(command('set_entry_notes', { ...currentFields(), watchlist_entry_id: entry.watchlist_entry_id, notes: value }));
                }),
                button('↑', () => reorder(index, -1)),
                button('↓', () => reorder(index, 1)),
                button('Remove', () => previewMutation(command('remove_entry', { ...currentFields(), watchlist_entry_id: entry.watchlist_entry_id })), 'danger'),
            );
            if (projection.identity_migration && projection.identity_migration.review_required) {
                actions.append(button('Review successor migration', () => previewMutation(command('confirm_identity_migration', { ...currentFields(), watchlist_entry_id: entry.watchlist_entry_id }))));
            }
            row.append(checkbox, label, actions);
            root.appendChild(row);
        });
    }

    function reorder(index, delta) {
        const target = index + delta;
        if (!current || target < 0 || target >= current.entries.length) return;
        const ids = current.entries.map((entry) => entry.watchlist_entry_id);
        [ids[index], ids[target]] = [ids[target], ids[index]];
        previewMutation(command('reorder_entries', { ...currentFields(), watchlist_entry_ids: ids }));
    }

    async function selectWatchlist(id, invalidate = true) {
        current = id ? await api(`/api/watchlists/${encodeURIComponent(id)}?include_deleted=true`) : null;
        lifecycle = stateApi.transition(lifecycle, 'LOAD_WATCHLIST');
        if (invalidate) markBuilderDirty();
        renderWatchlists();
        renderEntries();
    }

    async function loadWatchlists() {
        const include = byId('watchlist-include-deleted').checked;
        try {
            const result = await api(`/api/watchlists?include_deleted=${include ? 'true' : 'false'}`);
            watchlists = result.watchlists || [];
            const selectedId = current && current.watchlist_id;
            renderWatchlists();
            if (selectedId && watchlists.some((item) => item.watchlist_id === selectedId)) await selectWatchlist(selectedId, false);
            else { current = null; renderEntries(); }
        } catch (error) {
            if (error.message === 'SECURITY_MASTER_NOT_INITIALIZED') lifecycle = stateApi.transition(lifecycle, 'SECURITY_MASTER_FAILURE');
            setText(byId('watchlist-summary'), `${error.message}: ${pretty(error.detail || {})}`);
        }
    }

    function renderTemporaryTargets() {
        const root = byId('temporary-targets');
        root.replaceChildren();
        temporaryTargets.forEach((target, index) => {
            const row = document.createElement('div');
            row.className = 'entry-row';
            const label = document.createElement('div');
            setText(label, `${target.input}${target.market_hint ? ` · ${target.market_hint}` : ''}`);
            const actions = document.createElement('div');
            actions.className = 'entry-actions';
            actions.append(
                button('Add to Watchlist', () => {
                    if (!current) { setText(byId('composition-summary'), 'Select a watchlist before previewing persistence.'); return; }
                    previewMutation(command('add_entry', { ...currentFields(), query: target.input, ...(target.market_hint ? { market_hint: target.market_hint } : {}) }));
                }),
                button('Remove', () => { temporaryTargets.splice(index, 1); markBuilderDirty(); renderTemporaryTargets(); }, 'danger'),
            );
            row.append(document.createElement('span'), label, actions);
            root.appendChild(row);
        });
    }

    async function loadCapabilities() {
        const root = byId('capability-builder');
        root.replaceChildren();
        try {
            const result = await api('/api/unified/capabilities');
            (result.capabilities || []).forEach((capability) => {
                const row = document.createElement('div');
                row.className = 'capability-row';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'builder-capability';
                checkbox.value = capability.capability_id;
                checkbox.checked = capability.capability_id === 'identity';
                checkbox.addEventListener('change', markBuilderDirty);
                const label = document.createElement('label');
                setText(label, `${capability.capability_id} · ${capability.routing_disposition}`);
                const priority = document.createElement('select');
                priority.className = 'builder-capability-priority';
                priority.append(new Option('required', 'required'), new Option('optional', 'optional'));
                priority.addEventListener('change', markBuilderDirty);
                row.append(checkbox, label, priority);
                root.appendChild(row);
            });
        } catch (error) {
            setText(root, `Capability authority unavailable: ${error.message}`);
        }
    }

    async function composeRequest() {
        const selectedIds = Array.from(document.querySelectorAll('.watchlist-entry-selection:checked')).map((item) => item.dataset.entryId);
        const needs = Array.from(document.querySelectorAll('.builder-capability')).filter((item) => item.checked).map((item) => {
            const priority = item.parentElement.querySelector('.builder-capability-priority').value;
            const parameters = item.value === 'recent_performance' ? { lookback_trading_days: 5 } : {};
            return { type: item.value, priority, parameters, client_need_reference: `builder_${item.value}` };
        });
        if (!needs.length) { setText(byId('composition-summary'), 'Select at least one evidence need.'); return; }
        const payload = {
            schema_version: 'watchlist_evidence_selection_request.v3',
            expected_watchlist_version: current ? current.current_version : null,
            selected_entry_ids: selectedIds,
            temporary_targets: temporaryTargets,
            data_needs: needs,
            execution_mode: byId('builder-execution-mode').value,
            response_preferences: {
                include_citations: byId('builder-citations').checked,
                include_currentness: byId('builder-currentness').checked,
                include_caveats: byId('builder-caveats').checked,
                include_audit_reference: byId('builder-audit').checked,
            },
        };
        try {
            const path = current ? `/api/watchlists/${encodeURIComponent(current.watchlist_id)}/evidence-request-preview` : '/api/evidence-request-previews';
            const result = await api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            setText(byId('composition-summary'), `${result.composition_status}; targets=${result.limits.target_count}; operations=${result.limits.operation_count}; blockers=${result.blockers.length}; warnings=${result.warnings.join(', ') || 'none'}`);
            setText(byId('selection-provenance-view'), pretty(result.selection_provenance || { blockers: result.blockers, temporary_targets: result.temporary_targets }));
            if (result.composition_status !== 'composed') return;
            composedBinding = result.selection_provenance;
            lifecycle = stateApi.transition(lifecycle, 'COMPOSE_REQUEST');
            const input = byId('request-textarea');
            input.value = pretty(result.request);
            input.dispatchEvent(new Event('input', { bubbles: true }));
        } catch (error) {
            if (error.message === 'WATCHLIST_SELECTION_STALE') lifecycle = stateApi.transition(lifecycle, 'CONFLICT');
            setText(byId('composition-summary'), `${error.message}: ${pretty(error.detail || {})}`);
        }
    }

    byId('watchlist-select').addEventListener('change', (event) => selectWatchlist(event.target.value));
    byId('btn-watchlist-refresh').addEventListener('click', loadWatchlists);
    byId('watchlist-include-deleted').addEventListener('change', loadWatchlists);
    byId('btn-watchlist-create').addEventListener('click', () => {
        const name = window.prompt('Watchlist name');
        if (name) previewMutation(command('create_watchlist', { name, set_default: false }));
    });
    byId('btn-watchlist-rename').addEventListener('click', () => {
        const name = current && window.prompt('New watchlist name', current.name);
        if (name) previewMutation(command('rename_watchlist', { ...currentFields(), name }));
    });
    byId('btn-watchlist-default').addEventListener('click', () => previewMutation(command('set_default_watchlist', currentFields())));
    byId('btn-watchlist-delete').addEventListener('click', () => previewMutation(command('delete_watchlist', currentFields())));
    byId('btn-watchlist-restore').addEventListener('click', () => previewMutation(command('restore_watchlist', currentFields())));
    byId('btn-watchlist-history').addEventListener('click', async () => {
        if (!current) return;
        const value = await api(`/api/watchlists/${encodeURIComponent(current.watchlist_id)}/versions`);
        setText(byId('watchlist-history-view'), pretty(value));
    });
    byId('btn-watchlist-export').addEventListener('click', async () => current && download(`${current.watchlist_id}.json`, await api(`/api/watchlists/${encodeURIComponent(current.watchlist_id)}/export`)));
    byId('btn-watchlist-export-history').addEventListener('click', async () => current && download(`${current.watchlist_id}-history.json`, await api(`/api/watchlists/${encodeURIComponent(current.watchlist_id)}/export?include_history=true`)));
    byId('watchlist-import').addEventListener('change', async (event) => {
        if (!current || !event.target.files.length) return;
        const source = JSON.parse(await event.target.files[0].text());
        await previewMutation({ ...command('import_legacy_watchlist', { ...currentFields(), legacy_watchlist: source }), actor_source: 'import' });
        event.target.value = '';
    });
    byId('btn-watchlist-add').addEventListener('click', () => {
        const query = byId('watchlist-add-query').value.trim();
        if (query) previewMutation(command('add_entry', { ...currentFields(), query, market_hint: byId('watchlist-add-market').value }));
    });
    byId('btn-select-enabled').addEventListener('click', () => {
        document.querySelectorAll('.watchlist-entry-selection').forEach((element) => {
            const entry = current.entries.find((item) => item.watchlist_entry_id === element.dataset.entryId);
            element.checked = entry && entry.enabled;
        });
        markBuilderDirty();
    });
    byId('btn-temporary-add').addEventListener('click', () => {
        const input = byId('temporary-target-input').value.trim();
        if (!input) return;
        const hint = byId('temporary-target-market').value || null;
        temporaryTargets.push({ input, market_hint: hint, client_target_reference: `temporary_${temporaryTargets.length + 1}` });
        byId('temporary-target-input').value = '';
        markBuilderDirty();
        renderTemporaryTargets();
    });
    byId('btn-compose-request').addEventListener('click', composeRequest);
    byId('btn-confirm-mutation').addEventListener('click', confirmMutation);
    byId('btn-cancel-mutation').addEventListener('click', () => { pendingMutation = null; byId('mutation-preview-panel').hidden = true; });

    for (const element of document.querySelectorAll('#builder-execution-mode, #builder-citations, #builder-currentness, #builder-caveats, #builder-audit')) {
        element.addEventListener('change', markBuilderDirty);
    }

    loadCapabilities();
    loadWatchlists();
}());
