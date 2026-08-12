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
    });
}));
