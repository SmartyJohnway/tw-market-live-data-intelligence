/* Lightweight, deterministic control-state decisions for the local Workbench. */
(function exposeWorkbenchState(root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    root.UnifiedWorkbenchState = api;
}(globalThis, function buildWorkbenchState() {
    const AUTHORIZEABLE_PREVIEW_STATUSES = Object.freeze([
        'ready_for_confirmation',
        'partial_possible',
    ]);
    const STATES = Object.freeze({
        BOOT: 'BOOT',
        SECURITY_MASTER_UNAVAILABLE: 'SECURITY_MASTER_UNAVAILABLE',
        WATCHLIST_READY: 'WATCHLIST_READY',
        SELECTION_DIRTY: 'SELECTION_DIRTY',
        REQUEST_COMPOSED: 'REQUEST_COMPOSED',
        VALIDATED: 'VALIDATED',
        EVIDENCE_PREVIEWED: 'EVIDENCE_PREVIEWED',
        AUTHORIZED: 'AUTHORIZED',
        EXECUTION_CONFIRMATION_REQUIRED: 'EXECUTION_CONFIRMATION_REQUIRED',
        EXECUTING: 'EXECUTING',
        EXECUTED: 'EXECUTED',
        RESULT_READY: 'RESULT_READY',
        MUTATION_PREVIEW: 'MUTATION_PREVIEW',
        MUTATION_CONFIRMATION_REQUIRED: 'MUTATION_CONFIRMATION_REQUIRED',
        CONFLICT_OR_EXPIRY: 'CONFLICT_OR_EXPIRY',
    });

    const TRANSITIONS = Object.freeze({
        LOAD_WATCHLIST: STATES.WATCHLIST_READY,
        EDIT_SELECTION: STATES.SELECTION_DIRTY,
        COMPOSE_REQUEST: STATES.REQUEST_COMPOSED,
        VALIDATE_REQUEST: STATES.VALIDATED,
        PREVIEW_EVIDENCE: STATES.EVIDENCE_PREVIEWED,
        AUTHORIZE_EVIDENCE: STATES.AUTHORIZED,
        REQUIRE_EXECUTION_CONFIRMATION: STATES.EXECUTION_CONFIRMATION_REQUIRED,
        START_EXECUTION: STATES.EXECUTING,
        COMPLETE_EXECUTION: STATES.EXECUTED,
        LOAD_RESULT: STATES.RESULT_READY,
        PREVIEW_MUTATION: STATES.MUTATION_PREVIEW,
        REQUIRE_MUTATION_CONFIRMATION: STATES.MUTATION_CONFIRMATION_REQUIRED,
        CONFLICT: STATES.CONFLICT_OR_EXPIRY,
        EXPIRE: STATES.CONFLICT_OR_EXPIRY,
        SECURITY_MASTER_FAILURE: STATES.SECURITY_MASTER_UNAVAILABLE,
    });

    const initialState = () => ({
        state: STATES.BOOT,
        composedRequestFrozen: false,
        sourceWatchlistStale: false,
        mutationConfirmed: false,
        evidenceAuthorized: false,
        executionConfirmed: false,
    });

    const transition = (current, event) => {
        const next = TRANSITIONS[event];
        if (!next) return Object.freeze({ ...current });
        const value = { ...current, state: next };
        if (event === 'COMPOSE_REQUEST') {
            value.composedRequestFrozen = true;
            value.sourceWatchlistStale = false;
            value.evidenceAuthorized = false;
            value.executionConfirmed = false;
        }
        if (event === 'EDIT_SELECTION') {
            value.composedRequestFrozen = false;
            value.evidenceAuthorized = false;
            value.executionConfirmed = false;
        }
        if (event === 'AUTHORIZE_EVIDENCE') value.evidenceAuthorized = true;
        if (event === 'START_EXECUTION') value.executionConfirmed = true;
        return Object.freeze(value);
    };

    const markSourceWatchlistChanged = (current) => Object.freeze({
        ...current,
        sourceWatchlistStale: current.composedRequestFrozen === true,
    });

    const RECOVERY_REASON_TEXT = Object.freeze({
        plan_only_not_executable: 'Planning information only; it cannot be executed. Deselect it or change its priority to optional.',
        route_unavailable: 'No executable route is currently available. Deselect it or change its priority to optional.',
        unsupported_market: 'This evidence is not executable for the selected market. Deselect it or change its priority to optional.',
        required_h3_dependency_missing: 'A required supporting evidence dependency is missing. Add the required dependency or make this need optional.',
        unsupported_security_type: 'This evidence is not executable for the selected security type. Deselect it or change its priority to optional.',
        i3_governed_source_date_authority_required: 'TWSE institutional flow needs a current governed source-date authority before authorization. This Workbench will not guess a date. Deselect TWSE institutional flow before continuing.',
    });

    const previewRecovery = (preview, plan = {}, authorizationReadiness = {}) => {
        const status = preview?.status;
        const readinessBlocked = authorizationReadiness?.status === 'blocked';
        if (!status || (AUTHORIZEABLE_PREVIEW_STATUSES.includes(status) && !readinessBlocked)) {
            return Object.freeze({ blocked: false, items: Object.freeze([]), guidance: '' });
        }
        const rows = [];
        const add = (capabilityId, reasonCode) => {
            if (!capabilityId || !reasonCode || !RECOVERY_REASON_TEXT[reasonCode]) return;
            if (rows.some((row) => row.capabilityId === capabilityId && row.reasonCode === reasonCode)) return;
            rows.push(Object.freeze({ capabilityId, reasonCode, explanation: RECOVERY_REASON_TEXT[reasonCode] }));
        };
        const notes = [
            ...(preview?.coverage_expectation?.known_gaps || []),
            ...(preview?.caveats || []),
        ];
        notes.forEach((note) => {
            if (typeof note !== 'string' || !note.includes(':')) return;
            const [capabilityId, reasonCode] = note.split(':', 2);
            add(capabilityId, reasonCode);
        });
        (plan.operations || []).forEach((operation) => {
            if (operation?.operation_status === 'plan_only_not_executable') add(operation.capability_id, 'plan_only_not_executable');
        });
        (plan.blocked_operations || []).forEach((operation) => {
            (operation?.blocking_reason_codes || []).forEach((reasonCode) => add(operation.capability_id, reasonCode));
        });
        (authorizationReadiness?.blocking_reasons || []).forEach((reason) => {
            add(reason?.capability_id, reason?.code);
        });
        return Object.freeze({
            blocked: true,
            items: Object.freeze(rows),
            guidance: authorizationReadiness?.operator_guidance || 'Return to Evidence Needs. Review the items below, deselect a blocked required item or change its priority to optional, then Compose Frozen Request → Validate → Build Offline Preview again. Nothing will be changed automatically.',
        });
    };

    const previewControls = (status, authorizationReadiness = {}) => ({
        authorizeDisabled: !AUTHORIZEABLE_PREVIEW_STATUSES.includes(status) || authorizationReadiness?.status === 'blocked',
        executeOnceDisabled: true,
        networkConfirmationDisabled: true,
        networkConfirmationChecked: false,
    });

    const validationAllowsPreview = (validationStatus) => validationStatus === 'valid';

    const authorizationErrorMessage = (code) => (
        RECOVERY_REASON_TEXT[code]
        || (code ? `Authorization is unavailable (${code}).` : 'Authorization is unavailable.')
    );

    const authorizationControls = (networkRequired) => ({
        executeOnceDisabled: true,
        networkConfirmationDisabled: networkRequired !== true,
        networkConfirmationChecked: false,
    });

    const executionConfirmationControls = (networkRequired, networkConfirmed, operatorReference) => {
        const referenceValid = typeof operatorReference === 'string'
            && operatorReference.trim().length > 0
            && operatorReference.trim().length <= 128;
        const networkSatisfied = networkRequired !== true || networkConfirmed === true;
        return Object.freeze({ executeOnceDisabled: !(referenceValid && networkSatisfied) });
    };

    const invalidatedControls = () => ({
        authorizeDisabled: true,
        executeOnceDisabled: true,
        networkConfirmationDisabled: true,
        networkConfirmationChecked: false,
        buildResultDisabled: true,
    });

    return Object.freeze({
        AUTHORIZEABLE_PREVIEW_STATUSES,
        previewRecovery,
        previewControls,
        validationAllowsPreview,
        authorizationErrorMessage,
        authorizationControls,
        executionConfirmationControls,
        invalidatedControls,
        STATES,
        initialState,
        transition,
        markSourceWatchlistChanged,
    });
}));
