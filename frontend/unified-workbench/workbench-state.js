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

    const previewControls = (status) => ({
        authorizeDisabled: !AUTHORIZEABLE_PREVIEW_STATUSES.includes(status),
        executeOnceDisabled: true,
        networkConfirmationDisabled: true,
        networkConfirmationChecked: false,
    });

    const validationAllowsPreview = (validationStatus) => validationStatus === 'valid';

    const authorizationControls = (networkRequired) => ({
        executeOnceDisabled: false,
        networkConfirmationDisabled: networkRequired !== true,
        networkConfirmationChecked: false,
    });

    const invalidatedControls = () => ({
        authorizeDisabled: true,
        executeOnceDisabled: true,
        networkConfirmationDisabled: true,
        networkConfirmationChecked: false,
        buildResultDisabled: true,
    });

    return Object.freeze({
        AUTHORIZEABLE_PREVIEW_STATUSES,
        previewControls,
        validationAllowsPreview,
        authorizationControls,
        invalidatedControls,
        STATES,
        initialState,
        transition,
        markSourceWatchlistChanged,
    });
}));
