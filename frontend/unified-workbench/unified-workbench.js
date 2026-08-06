document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const formatBtn = document.getElementById('btn-format');
    const clearBtn = document.getElementById('btn-clear');
    const validateBtn = document.getElementById('btn-validate');
    const textarea = document.getElementById('request-textarea');
    const syntaxStatus = document.getElementById('syntax-status');
    const summaryBox = document.getElementById('validation-summary');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const exportActions = document.getElementById('export-actions');
    
    let currentValidationResult = null;
    let parsedRequest = null;

    // --- State Machine ---
    const updateSyntaxStatus = () => {
        const val = textarea.value.trim();
        if (!val) {
            syntaxStatus.textContent = 'JSON not loaded';
            syntaxStatus.className = 'syntax-empty';
            validateBtn.disabled = true;
            parsedRequest = null;
            return;
        }
        try {
            parsedRequest = JSON.parse(val);
            syntaxStatus.textContent = 'JSON syntax valid';
            syntaxStatus.className = 'syntax-valid';
            validateBtn.disabled = false;
        } catch (e) {
            syntaxStatus.textContent = `JSON syntax invalid: ${e.message}`;
            syntaxStatus.className = 'syntax-invalid';
            validateBtn.disabled = true;
            parsedRequest = null;
        }
    };

    // --- Event Listeners ---
    textarea.addEventListener('input', updateSyntaxStatus);

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            textarea.value = ev.target.result;
            updateSyntaxStatus();
        };
        reader.readAsText(file);
        fileInput.value = '';
    });

    formatBtn.addEventListener('click', () => {
        if (parsedRequest) {
            textarea.value = JSON.stringify(parsedRequest, null, 2);
        }
    });

    clearBtn.addEventListener('click', () => {
        textarea.value = '';
        updateSyntaxStatus();
        resetValidationView();
    });

    validateBtn.addEventListener('click', async () => {
        if (!parsedRequest) return;
        validateBtn.disabled = true;
        validateBtn.textContent = 'Validating...';
        
        try {
            const response = await fetch('/api/unified/validate-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request: parsedRequest })
            });
            
            const data = await response.json();
            if (response.ok) {
                renderValidationResult(data);
            } else {
                renderTransportError(data);
            }
        } catch (err) {
            renderTransportError({ error: 'network_error', detail: err.message });
        } finally {
            validateBtn.disabled = false;
            validateBtn.textContent = 'Validate';
        }
    });

    // --- Tab Switching ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
        });
    });

    // --- Actions ---
    const copyToClipboard = (data) => navigator.clipboard.writeText(typeof data === 'string' ? data : JSON.stringify(data, null, 2));
    const downloadJson = (data, prefix) => {
        const id = currentValidationResult?.request_id || 'unified-request';
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${id}.${prefix}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    document.getElementById('btn-copy-req').addEventListener('click', () => copyToClipboard(currentValidationResult?.normalized_request));
    document.getElementById('btn-dl-req').addEventListener('click', () => downloadJson(currentValidationResult?.normalized_request, 'normalized'));
    document.getElementById('btn-copy-res').addEventListener('click', () => copyToClipboard(currentValidationResult));
    document.getElementById('btn-dl-res').addEventListener('click', () => downloadJson(currentValidationResult, 'validation'));

    // --- Render Logic ---
    const resetValidationView = () => {
        currentValidationResult = null;
        summaryBox.innerHTML = '';
        document.getElementById('list-blockers').innerHTML = '';
        document.getElementById('list-warnings').innerHTML = '';
        document.getElementById('target-results').innerHTML = '';
        document.getElementById('capability-results').innerHTML = '';
        document.getElementById('normalized-request-view').textContent = '';
        document.getElementById('badge-issues').textContent = '0';
        document.getElementById('badge-targets').textContent = '0';
        document.getElementById('badge-capabilities').textContent = '0';
        exportActions.style.display = 'none';
    };

    const getStatusClass = (status) => {
        if (status === 'valid') return 'status-valid';
        if (status === 'invalid') return 'status-invalid';
        if (status === 'requires_clarification') return 'status-clarification';
        return 'status-unsupported';
    };

    const renderValidationResult = (res) => {
        currentValidationResult = res;
        exportActions.style.display = 'flex';

        // Summary
        summaryBox.innerHTML = `
            <div class="summary-grid">
                <div class="summary-label">Request ID:</div><div>${res.request_id || '-'}</div>
                <div class="summary-label">Overall Status:</div><div class="${getStatusClass(res.validation_status)}">${res.validation_status}</div>
                <div class="summary-label">Schema Status:</div><div class="${getStatusClass(res.request_schema_status)}">${res.request_schema_status}</div>
                <div class="summary-label">Target Status:</div><div class="${getStatusClass(res.target_validation_status)}">${res.target_validation_status}</div>
                <div class="summary-label">Capability Status:</div><div class="${getStatusClass(res.capability_validation_status)}">${res.capability_validation_status}</div>
                <div class="summary-label">Metadata:</div><div>Offline: ${res.validation_metadata?.offline}, Deterministic: ${res.validation_metadata?.deterministic}</div>
                <div class="summary-label">Limits:</div><div>Targets: ${res.limits?.target_count} / ${res.limits?.hard_target_limit}</div>
            </div>
        `;

        // Issues
        const blockersList = document.getElementById('list-blockers');
        blockersList.innerHTML = (res.blocking_issues || []).map(b => `<li>[${b.code}] ${b.path}: ${b.message}</li>`).join('') || '<li>No blocking issues</li>';
        
        const warningsList = document.getElementById('list-warnings');
        warningsList.innerHTML = (res.warnings || []).map(w => `<li>[${w.code}] ${w.path}: ${w.message}</li>`).join('') || '<li>No warnings</li>';
        
        document.getElementById('badge-issues').textContent = (res.blocking_issues?.length || 0) + (res.warnings?.length || 0);

        // Targets
        const targetsDiv = document.getElementById('target-results');
        targetsDiv.innerHTML = (res.target_results || []).map(t => `
            <div class="target-card">
                <h4>[${t.target_index}] ${t.input_target?.input || '-'}</h4>
                <div class="card-grid">
                    <strong>Status:</strong> <span class="${getStatusClass(t.resolution_status === 'resolved' ? 'valid' : 'invalid')}">${t.resolution_status}</span>
                    <strong>Market:</strong> <span>${t.canonical_identity?.market || '-'}</span>
                    <strong>Sec Type:</strong> <span>${t.canonical_identity?.security_type || '-'}</span>
                </div>
            </div>
        `).join('') || '<div>No targets</div>';
        document.getElementById('badge-targets').textContent = res.target_results?.length || 0;

        // Capabilities
        const capsDiv = document.getElementById('capability-results');
        capsDiv.innerHTML = (res.capability_results || []).map(c => `
            <div class="capability-card">
                <h4>[${c.data_need_index}] ${c.capability_id} (${c.priority})</h4>
                <div class="card-grid">
                    <strong>Status:</strong> <span class="${getStatusClass(c.status === 'supported' ? 'valid' : 'invalid')}">${c.status}</span>
                    <strong>Limitations:</strong> <span>${(c.limitations || []).join(', ') || 'None'}</span>
                </div>
            </div>
        `).join('') || '<div>No capabilities</div>';
        document.getElementById('badge-capabilities').textContent = res.capability_results?.length || 0;

        // Normalized Request
        document.getElementById('normalized-request-view').textContent = JSON.stringify(res.normalized_request, null, 2);
    };

    const renderTransportError = (data) => {
        resetValidationView();
        summaryBox.innerHTML = `
            <div class="summary-grid">
                <div class="summary-label">Error:</div><div class="status-invalid">${data.error || 'Unknown Error'}</div>
                <div class="summary-label">Detail:</div><div>${data.detail || JSON.stringify(data)}</div>
            </div>
        `;
    };

    // Init
    updateSyntaxStatus();
});
