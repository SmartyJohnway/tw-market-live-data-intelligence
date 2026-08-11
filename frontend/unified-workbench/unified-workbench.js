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
    const previewBtn = document.getElementById('btn-preview');
    const previewSummary = document.getElementById('preview-summary');
    const authorizeBtn = document.getElementById('btn-authorize');
    const executeOnceBtn = document.getElementById('btn-execute-once');
    const modeB2Summary = document.getElementById('mode-b2-summary');
    
    let currentValidationResult = null;
    let currentPreviewResult = null;
    let validatedRequestFingerprint = null;
    let parsedRequest = null;
    let currentAuthorization = null;

    const fingerprint = (value) => JSON.stringify(value);

    const invalidateDerivedState = () => {
        currentValidationResult = null;
        currentPreviewResult = null;
        validatedRequestFingerprint = null;
        currentAuthorization = null;
        previewBtn.disabled = true;
        authorizeBtn.disabled = true;
        executeOnceBtn.disabled = true;
        modeB2Summary.textContent = 'Authorization required. Execution performed = NO.';
        resetPreviewView();
    };

    // --- State Machine ---
    const updateSyntaxStatus = () => {
        invalidateDerivedState();
        resetValidationView();
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

    const MAX_BODY_SIZE = 1 * 1024 * 1024; // 1 MiB

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > MAX_BODY_SIZE) {
            alert(`File size exceeds 1 MiB limit.`);
            fileInput.value = '';
            return;
        }
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
            updateSyntaxStatus();
        }
    });

    clearBtn.addEventListener('click', () => {
        textarea.value = '';
        updateSyntaxStatus();
        resetValidationView();
    });

    validateBtn.addEventListener('click', async () => {
        if (!parsedRequest) return;
        const payloadStr = JSON.stringify({ request: parsedRequest });
        const encoder = new TextEncoder();
        if (encoder.encode(payloadStr).length > MAX_BODY_SIZE) {
            renderTransportError({ error: 'request_too_large', detail: 'Request exceeds 1 MiB limit.' });
            return;
        }

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
                validatedRequestFingerprint = fingerprint(parsedRequest);
                previewBtn.disabled = false;
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

    previewBtn.addEventListener('click', async () => {
        if (!parsedRequest || fingerprint(parsedRequest) !== validatedRequestFingerprint) {
            invalidateDerivedState();
            return;
        }
        previewBtn.disabled = true;
        previewBtn.textContent = 'Building Preview...';
        try {
            const response = await fetch('/api/unified/preview-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request: parsedRequest })
            });
            const data = await response.json();
            if (response.ok) {
                renderPreviewResult(data);
            } else {
                renderPreviewError(data);
            }
        } catch (err) {
            renderPreviewError({ error: 'network_error', detail: err.message });
        } finally {
            previewBtn.textContent = 'Build Offline Preview';
            previewBtn.disabled = fingerprint(parsedRequest) !== validatedRequestFingerprint;
        }
    });

    authorizeBtn.addEventListener('click', async () => {
        if (!currentPreviewResult?.preview || !currentPreviewResult?.orchestration_plan) return;
        const reference = currentPreviewResult.preview.internal_execution_reference || {};
        const payload = { request: parsedRequest, expected_preview_id: reference.preview_id,
            expected_plan_id: currentPreviewResult.orchestration_plan.plan_id,
            expected_plan_hash: currentPreviewResult.orchestration_plan.plan_hash,
            confirm_authorization: true, approval_scope_mode: 'whole_plan_executable_scope' };
        const response = await fetch('/api/unified/authorizations', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
        const data = await response.json();
        if (!response.ok) { modeB2Summary.textContent = `Authorization unavailable: ${data.error || 'unknown'}`; return; }
        currentAuthorization = data;
        modeB2Summary.textContent = `AUTHORIZED — execution performed = NO; network executed = NO; single use = YES; expires ${data.expires_at}`;
        executeOnceBtn.disabled = false;
    });

    executeOnceBtn.addEventListener('click', async () => {
        if (!currentAuthorization) return;
        const reference = window.prompt('Operator confirmation reference');
        if (!reference) return;
        const response = await fetch('/api/unified/executions', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
            control_package_id: currentAuthorization.control_package_id, confirm_execution:true,
            operator_confirmation_reference:reference, confirm_network_execution:currentAuthorization.network_required === true
        })});
        const data = await response.json();
        modeB2Summary.textContent = response.ok ? `EXECUTION ATTEMPTED — ${data.aggregation_status}; authorization consumed = YES.` : `Execution unavailable: ${data.error || 'unknown'}`;
        executeOnceBtn.disabled = true;
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
        previewBtn.disabled = true;
    };

    function resetPreviewView() {
        previewSummary.textContent = 'Validate the current request before building a Preview.';
        document.getElementById('preview-planning').innerHTML = '';
        document.getElementById('preview-coverage').innerHTML = '';
        document.getElementById('preview-gaps').innerHTML = '';
        document.getElementById('preview-plan-view').textContent = '';
        authorizeBtn.disabled = true;
        executeOnceBtn.disabled = true;
    }

    const appendDetail = (container, label, value) => {
        const term = document.createElement('dt');
        term.textContent = label;
        const description = document.createElement('dd');
        description.textContent = Array.isArray(value) ? (value.join(', ') || 'None') : String(value ?? '-');
        container.appendChild(term);
        container.appendChild(description);
    };

    const renderPreviewResult = (result) => {
        currentPreviewResult = result;
        const preview = result.preview;
        previewSummary.textContent = preview
            ? `Preview status: ${preview.status}`
            : 'No Preview was produced because request schema validation did not run.';
        const planning = document.getElementById('preview-planning');
        const coverage = document.getElementById('preview-coverage');
        const gaps = document.getElementById('preview-gaps');
        planning.innerHTML = '';
        coverage.innerHTML = '';
        gaps.innerHTML = '';
        if (!preview) {
            document.getElementById('preview-plan-view').textContent = '';
            return;
        }
        appendDetail(planning, 'Requested needs', preview.requested_data_needs);
        appendDetail(planning, 'Planned evidence', preview.planned_evidence);
        appendDetail(planning, 'Approval required', preview.approval?.required ? 'YES' : 'NO');
        appendDetail(planning, 'Execution authorized', 'NO');
        appendDetail(coverage, 'Coverage', preview.coverage_expectation?.status);
        appendDetail(coverage, 'Targets', preview.bounds?.target_count);
        appendDetail(coverage, 'Logical operations', preview.bounds?.operation_count);
        appendDetail(coverage, 'Estimated source calls', preview.bounds?.estimated_network_calls);
        appendDetail(coverage, 'Executor invocations', result.orchestration_plan?.accounting?.executor_invocation_count ?? 0);
        appendDetail(coverage, 'Expanded scope', preview.bounds?.expanded_scope ? 'YES' : 'NO');
        const notes = [
            ...(preview.coverage_expectation?.known_gaps || []),
            ...(preview.caveats || [])
        ];
        (notes.length ? notes : ['No known gaps']).forEach(note => {
            const item = document.createElement('li');
            item.textContent = note;
            gaps.appendChild(item);
        });
        document.getElementById('preview-plan-view').textContent = JSON.stringify(result.orchestration_plan, null, 2);
        authorizeBtn.disabled = preview.status === 'ready_for_confirmation' || preview.status === 'partial_possible';
    };

    const renderPreviewError = (data) => {
        currentPreviewResult = null;
        previewSummary.textContent = `Preview unavailable: ${data.error || data.detail || 'unknown error'}`;
        document.getElementById('preview-plan-view').textContent = '';
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
        summaryBox.innerHTML = '';
        const summaryGrid = document.createElement('div');
        summaryGrid.className = 'summary-grid';
        
        const appendSummaryRow = (label, value, valueClass = '') => {
            const labelEl = document.createElement('div');
            labelEl.className = 'summary-label';
            labelEl.textContent = label;
            const valueEl = document.createElement('div');
            valueEl.className = valueClass;
            valueEl.textContent = value;
            summaryGrid.appendChild(labelEl);
            summaryGrid.appendChild(valueEl);
        };

        appendSummaryRow('Request ID:', res.request_id || '-');
        appendSummaryRow('Overall Status:', res.validation_status, getStatusClass(res.validation_status));
        appendSummaryRow('Schema Status:', res.request_schema_status, getStatusClass(res.request_schema_status));
        appendSummaryRow('Target Status:', res.target_validation_status, getStatusClass(res.target_validation_status));
        appendSummaryRow('Capability Status:', res.capability_validation_status, getStatusClass(res.capability_validation_status));
        appendSummaryRow('Metadata:', `Offline: ${res.validation_metadata?.offline}, Deterministic: ${res.validation_metadata?.deterministic}`);
        appendSummaryRow('Limits:', `Targets: ${res.limits?.target_count} / ${res.limits?.hard_target_limit}`);
        
        summaryBox.appendChild(summaryGrid);

        // Issues
        const blockersList = document.getElementById('list-blockers');
        blockersList.innerHTML = '';
        if (res.blocking_issues && res.blocking_issues.length > 0) {
            res.blocking_issues.forEach(b => {
                const li = document.createElement('li');
                li.textContent = `[${b.code}] ${b.path}: ${b.message}`;
                blockersList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'No blocking issues';
            blockersList.appendChild(li);
        }
        
        const warningsList = document.getElementById('list-warnings');
        warningsList.innerHTML = '';
        if (res.warnings && res.warnings.length > 0) {
            res.warnings.forEach(w => {
                const li = document.createElement('li');
                li.textContent = `[${w.code}] ${w.path}: ${w.message}`;
                warningsList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'No warnings';
            warningsList.appendChild(li);
        }
        
        document.getElementById('badge-issues').textContent = (res.blocking_issues?.length || 0) + (res.warnings?.length || 0);

        // Targets
        const targetsDiv = document.getElementById('target-results');
        targetsDiv.innerHTML = '';
        if (res.target_results && res.target_results.length > 0) {
            res.target_results.forEach(t => {
                const card = document.createElement('div');
                card.className = 'target-card';
                
                const h4 = document.createElement('h4');
                h4.textContent = `[${t.target_index}] ${t.input_target?.input || '-'}`;
                card.appendChild(h4);
                
                const grid = document.createElement('div');
                grid.className = 'card-grid';
                
                const appendGridRow = (label, val, valClass = '') => {
                    const l = document.createElement('strong');
                    l.textContent = label;
                    const v = document.createElement('span');
                    v.textContent = val;
                    if (valClass) v.className = valClass;
                    grid.appendChild(l);
                    grid.appendChild(v);
                };
                
                appendGridRow('Status:', t.resolution_status, getStatusClass(t.resolution_status === 'resolved' ? 'valid' : 'invalid'));
                appendGridRow('Market:', t.canonical_identity?.market || '-');
                appendGridRow('Sec Type:', t.canonical_identity?.security_type || '-');
                
                card.appendChild(grid);
                targetsDiv.appendChild(card);
            });
        } else {
            const div = document.createElement('div');
            div.textContent = 'No targets';
            targetsDiv.appendChild(div);
        }
        document.getElementById('badge-targets').textContent = res.target_results?.length || 0;

        // Capabilities
        const capsDiv = document.getElementById('capability-results');
        capsDiv.innerHTML = '';
        if (res.capability_results && res.capability_results.length > 0) {
            res.capability_results.forEach(c => {
                const card = document.createElement('div');
                card.className = 'capability-card';
                
                const h4 = document.createElement('h4');
                h4.textContent = `[${c.data_need_index}] ${c.capability_id} (${c.priority})`;
                card.appendChild(h4);
                
                const grid = document.createElement('div');
                grid.className = 'card-grid';
                
                const appendGridRow = (label, val, valClass = '') => {
                    const l = document.createElement('strong');
                    l.textContent = label;
                    const v = document.createElement('span');
                    v.textContent = val;
                    if (valClass) v.className = valClass;
                    grid.appendChild(l);
                    grid.appendChild(v);
                };
                
                appendGridRow('Status:', c.status, getStatusClass(c.status === 'supported' ? 'valid' : 'invalid'));
                appendGridRow('Limitations:', (c.limitations || []).join(', ') || 'None');
                
                card.appendChild(grid);
                capsDiv.appendChild(card);
            });
        } else {
            const div = document.createElement('div');
            div.textContent = 'No capabilities';
            capsDiv.appendChild(div);
        }
        document.getElementById('badge-capabilities').textContent = res.capability_results?.length || 0;

        // Normalized Request
        document.getElementById('normalized-request-view').textContent = JSON.stringify(res.normalized_request, null, 2);
    };

    const renderTransportError = (data) => {
        resetValidationView();
        summaryBox.innerHTML = '';
        const summaryGrid = document.createElement('div');
        summaryGrid.className = 'summary-grid';
        
        const appendSummaryRow = (label, value, valueClass = '') => {
            const labelEl = document.createElement('div');
            labelEl.className = 'summary-label';
            labelEl.textContent = label;
            const valueEl = document.createElement('div');
            valueEl.className = valueClass;
            valueEl.textContent = value;
            summaryGrid.appendChild(labelEl);
            summaryGrid.appendChild(valueEl);
        };
        
        appendSummaryRow('Error:', data.error || 'Unknown Error', 'status-invalid');
        appendSummaryRow('Detail:', data.trace_id || data.detail || JSON.stringify(data));
        
        summaryBox.appendChild(summaryGrid);
    };

    // Init
    updateSyntaxStatus();
});
