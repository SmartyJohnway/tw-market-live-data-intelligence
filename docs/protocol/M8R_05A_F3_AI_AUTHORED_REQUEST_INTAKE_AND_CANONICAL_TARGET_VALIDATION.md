# M8R-05A-F3 AI-authored request intake and canonical target validation

F3 is a pure, offline gate between an AI-authored `unified_market_evidence_request.v1` and later orchestration.  The AI understands conversation and authors targets, needs, and scope; F3 only validates schema/bounds, resolves governed identities, checks market consistency and catalog capability support.

It never interprets natural language, retrieves data, plans operations, approves execution, maintains state, or exposes a router/UI/MCP service.  It uses the M8R-03D-F1 strict verified-security-master loader with explicit artifacts only.  Missing or invalid artifacts, malformed catalog data, blocked eligibility, and unrecognized values fail closed.

The output is `unified_market_evidence_request_validation.v1`. Target outcomes are resolved, ambiguous, not found, market mismatch, unsupported market/type, invalid input/hint, duplicate, and quarantined. Capability outcomes preserve `contract_supported`, `runtime_executable`, and `provisional`; pending target resolution is a dependency, not unsupported.

Status precedence is schema/hard bound invalidity, non-ambiguous target invalidity, ambiguous targets requiring clarification, then required unsupported/invalid/unknown capability. Optional unsupported capabilities are warnings. Candidate and issue ordering is stable. Normalized requests are deep copies.

The production loader requires explicit snapshot and manifest paths and rejects fixture observation records. Tests may opt into fixture records; that exception is request-scoped and never mutates the immutable validated snapshot. F3 makes no network calls and M8R-05B remains responsible for any later approval/orchestration handoff.
