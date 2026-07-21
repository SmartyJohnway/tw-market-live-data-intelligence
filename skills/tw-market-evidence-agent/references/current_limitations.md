# Current Limitations

- **Unified Orchestrator API Pending**: The automated HTTP executor or MCP tool for intake processing of `unified_market_evidence_request.v1` is not yet implemented (scheduled for 05B/05C). However, the F3 Request Intake and Validation layer is available for verifying schemas and targets locally.
- **Manual Workbench Fallback**: AI agents must author requests, validate them via F3, display the preview to the operator, and rely on the operator manually pasting results back into the conversation.
- **Underlying Active Runtime**: The active backend planners (M8R-03C, M8R-03D, M8R-03E) remain the authoritative engine. New unified integrations are simulated via legacy/compatibility wrappers.
- **R2 Filesystem Containment**: File reads and writes remain strictly sandboxed. No absolute local paths may be written or requested.
- **No Raw Payloads**: Exposure of raw JSON adapter feeds is restricted. AI must only process normalized evidence envelopes.
- **No Trading or Orders**: Direct order routing, stock broker mutations, or portfolio writes are permanently disabled.
