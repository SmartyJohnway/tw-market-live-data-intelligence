# Operator Staging Workflow Manual

Flow: fixture-backed staging payload -> validator -> readonly package builder -> acceptance -> cleanup. Use confirmation flags for writers and package builders. Forbidden paths include frontend/public, research/generated, credentials, cookies, tokens, broker, production, prod, and current_market_state. Failure modes include validation errors, forbidden output path, stale/delayed caveat mismatch, and missing TWSE_MIS risk flags.
