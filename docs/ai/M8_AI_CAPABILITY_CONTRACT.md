# M8 AI Capability Contract

Baseline SHA: `d6b83313bb301e652ae82b8583d73d2aaa1d753e`

The authoritative structured contract is [`m8_ai_capability_contract.json`](m8_ai_capability_contract.json). It defines capability IDs, maturity states, timing classes, source-authority classes, sufficiency statuses, calculation semantics, internal mappings, deprecated compatibility fields, and the Phase C dependency on R2.

## Architecture principle

The repository provides governed market evidence, deterministic calculations, timing semantics, provenance, and controlled data access. The agent or human discussion layer decides interpretation, comparison, opinion, scenario, recommendation, and risk/reward discussion subject to deployed policy and user request.

## Internal mapping mode

Normal agents should use `request`, `target`, `capability`, `evidence package`, `coverage`, `missing evidence`, `citation`, `lineage`, and `timing class`. Advanced audit mode may inspect internal producers, validators, current artifacts, and future Phase C operation names from the JSON `internal_mappings` object.

## Deprecated AI behavior fields

Existing compatibility fields such as `no_recommendation`, `no_trading_advice`, `no_trading_signal`, `recommendation_allowed=false`, and `trading_signal_allowed=false` are documented as deprecated compatibility fields. They are not authoritative Agent policy in F1 and remain scheduled for migration.

## Phase C boundary

F1 does not implement the Unified Market Evidence Tool API, MCP, HTTP endpoints, LLM invocation, scheduler, polling, persistent watchlists, broker integration, or new source adapters. Phase C remains blocked until `M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION` is complete.
